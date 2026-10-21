"""Portable-path, local-only execution and failure-boundary regression checks."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/kmp-token-saver/scripts/graphify_local.py"
SPEC = importlib.util.spec_from_file_location("graphify_local", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


class GraphifyLocalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="graphify paths with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "checkout"
        self.scope = self.root / "module with spaces"
        self.scope.mkdir(parents=True)
        self.env = patch.dict(os.environ, {
            "LOCALAPPDATA": str(self.base / "cache"),
            "XDG_CACHE_HOME": str(self.base / "cache"),
            "GRAPHIFY_BACKEND": "openai", "GRAPHIFY_OUT": "inherited-output",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def args(self, action, *extra):
        return [action, "--root", str(self.root), "--scope", "module with spaces", *extra]

    def version(self, command, **kwargs):
        return subprocess.CompletedProcess(command, 0, f"graphify {helper.GRAPHIFY_VERSION}\n")

    def test_scopes_cannot_escape_the_checkout(self):
        with self.assertRaises(ValueError):
            helper.paths(self.root, "../cache")
        with self.assertRaises(ValueError):
            helper.paths(self.root, str(self.base))

    def test_cache_is_external_and_separate_for_relocated_checkouts(self):
        moved = self.base / "another checkout"
        (moved / "module with spaces").mkdir(parents=True)
        source, cache = helper.paths(self.root, "module with spaces")
        _, moved_cache = helper.paths(moved, "module with spaces")
        self.assertEqual(source, self.scope.resolve())
        self.assertNotEqual(cache, moved_cache)
        self.assertFalse(cache.is_relative_to(self.root))

    def test_build_keeps_paths_as_arguments_and_disables_model_work_only_in_children(self):
        with patch.object(helper.shutil, "which", return_value="graphify"), \
             patch.object(helper.subprocess, "run", side_effect=self.version) as child:
            self.assertEqual(helper.main(self.args("build")), 0)
        calls = child.call_args_list
        extraction = calls[1]
        self.assertIn(str(self.scope.resolve()), extraction.args[0])
        self.assertIn("--code-only", extraction.args[0])
        for call in calls:
            env = call.kwargs["env"]
            self.assertEqual(env["GRAPHIFY_BACKEND"], "none")
            self.assertEqual(env["GRAPHIFY_QUERY_LOG_DISABLE"], "1")
            self.assertEqual(env["GRAPHIFY_OUT"], "graphify-out")
        self.assertEqual(os.environ["GRAPHIFY_BACKEND"], "openai")
        self.assertEqual(os.environ["GRAPHIFY_OUT"], "inherited-output")

    def test_failed_extraction_does_not_run_clustering(self):
        failure = subprocess.CalledProcessError(7, ["graphify", "extract"])
        with patch.object(helper.shutil, "which", return_value="graphify"), \
             patch.object(helper.subprocess, "run", side_effect=[self.version([],), failure]) as child, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(helper.main(self.args("build")), 7)
        self.assertEqual(child.call_count, 2)

    def test_wrong_version_does_not_extract(self):
        wrong = subprocess.CompletedProcess([], 0, "graphify 999.0\n")
        with patch.object(helper.shutil, "which", return_value="graphify"), \
             patch.object(helper.subprocess, "run", return_value=wrong) as child, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(helper.main(self.args("build")), 1)
        self.assertEqual(child.call_count, 1)

    def test_query_without_graph_does_not_trigger_a_build(self):
        with patch.object(helper.shutil, "which", return_value="graphify"), \
             patch.object(helper.subprocess, "run", side_effect=self.version) as child, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(helper.main(self.args("query", "--text", "symbol")), 1)
        self.assertEqual(child.call_count, 1)


if __name__ == "__main__":
    unittest.main()
