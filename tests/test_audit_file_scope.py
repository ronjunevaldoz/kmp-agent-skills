from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

AUDIT_SCRIPT = REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_project.py"
audit_scripts = load_module("audit_project_file_scope", AUDIT_SCRIPT)
audit_scripts.INSTALLED_PLUGINS_JSON = Path(tempfile.gettempdir()) / "no-such-dir" / "installed_plugins.json"

BAD_KT = "package a\nimport kotlinx.coroutines.GlobalScope\nfun f() = GlobalScope\n"
GOOD_KT = "package a\nfun g() = 1\n"


def _make_project(tmp: str) -> Path:
    """A Gradle project with one violating file, one clean file and no AGENTS.md
    (a project-level finding the whole-project audit always reports)."""
    root = Path(tmp).resolve()
    src = root / "feature" / "ui" / "src" / "commonMain" / "kotlin"
    src.mkdir(parents=True)
    (root / "settings.gradle.kts").write_text('rootProject.name = "demo"\n', encoding="utf-8")
    (src / "Bad.kt").write_text(BAD_KT, encoding="utf-8")
    (src / "Good.kt").write_text(GOOD_KT, encoding="utf-8")
    return root


class AuditFilesTests(unittest.TestCase):
    """Per-file mode used by the PostToolUse hook (issue #29)."""

    def test_reports_only_findings_for_the_given_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_project(tmp)
            src = root / "feature" / "ui" / "src" / "commonMain" / "kotlin"

            findings, _ = audit_scripts.audit_files(root, [src / "Bad.kt"])
            self.assertEqual(len(findings), 1, findings)
            self.assertIn("globalscope usage", findings[0])
            self.assertIn("Bad.kt", findings[0])

            clean, _ = audit_scripts.audit_files(root, [src / "Good.kt"])
            self.assertEqual(clean, [], "project-level findings must not surface for a clean file")

    def test_does_not_walk_the_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_project(tmp)
            src = root / "feature" / "ui" / "src" / "commonMain" / "kotlin"
            with mock.patch.object(Path, "rglob", side_effect=AssertionError("project walked")):
                findings, _ = audit_scripts.audit_files(root, [src / "Good.kt"])
            self.assertEqual(findings, [])
            self.assertIsNone(audit_scripts._FILE_SCOPE, "scope must be reset after the call")

    def test_relative_missing_and_outside_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
            root = _make_project(tmp)
            rel = Path("feature/ui/src/commonMain/kotlin/Bad.kt")
            findings, _ = audit_scripts.audit_files(root, [rel])
            self.assertEqual(len(findings), 1, "relative paths resolve against the project root")

            outside = Path(other) / "Bad.kt"
            outside.write_text(BAD_KT, encoding="utf-8")
            self.assertEqual(audit_scripts.audit_files(root, [outside, root / "Gone.kt"]), ([], []))

    def test_cli_files_mode_and_whole_project_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_project(tmp)
            good = root / "feature" / "ui" / "src" / "commonMain" / "kotlin" / "Good.kt"

            scoped = subprocess.run(
                [sys.executable, str(AUDIT_SCRIPT), str(root), "--files", str(good)],
                capture_output=True, text=True,
            )
            self.assertEqual(scoped.returncode, 0, scoped.stdout + scoped.stderr)

            whole = subprocess.run(
                [sys.executable, str(AUDIT_SCRIPT), str(root)], capture_output=True, text=True,
            )
            self.assertEqual(whole.returncode, 1, "the whole-project CLI keeps its behavior")
            self.assertIn("globalscope usage", whole.stdout)
            self.assertIn("AGENTS.md", whole.stdout)


class AuditDeadlineTests(unittest.TestCase):
    def test_timeout_ends_the_process_and_releases_the_lock(self) -> None:
        # The audit is replaced by a 60 s sleep so only the watchdog can end the process.
        driver = textwrap.dedent(f"""
            import sys, time
            sys.path.insert(0, {str(REPO_ROOT / "tests")!r})
            from _helpers import load_module
            mod = load_module("audit_project", {str(AUDIT_SCRIPT)!r})
            mod.audit_files = lambda *a: time.sleep(60)
            sys.argv = ["audit_project.py", *sys.argv[1:]]
            raise SystemExit(mod.main())
        """)
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_project(tmp)
            env = {**os.environ, "KMP_AUDIT_LOCK_DIR": locks}
            started = time.monotonic()
            result = subprocess.run(
                [sys.executable, "-c", driver, str(root), "--files", "Good.kt", "--timeout", "1", "--lock"],
                capture_output=True, text=True, env=env, timeout=30,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(result.returncode, audit_scripts.TIMEOUT_EXIT, result.stderr)
            self.assertIn("TIMEOUT", result.stderr)
            self.assertLess(elapsed, 15)
            self.assertEqual(list(Path(locks).iterdir()), [], "a timed-out audit must release its lock")


class AuditLockTests(unittest.TestCase):
    def test_lock_is_exclusive_and_stale_locks_are_taken_over(self) -> None:
        with tempfile.TemporaryDirectory() as locks:
            path = Path(locks) / "p.lock"
            token = audit_scripts._acquire_lock(path, stale_after=60)
            self.assertIsNotNone(token)
            self.assertIsNone(audit_scripts._acquire_lock(path, stale_after=60))

            old = time.time() - 120
            os.utime(path, (old, old))
            takeover = audit_scripts._acquire_lock(path, stale_after=60)
            self.assertIsNotNone(takeover)

            audit_scripts._release_lock(path, token)
            self.assertTrue(path.exists(), "a former holder must not remove the new holder's lock")
            audit_scripts._release_lock(path, takeover)
            self.assertFalse(path.exists())

    def test_cli_skips_while_the_project_lock_is_held(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_project(tmp)
            with mock.patch.dict(os.environ, {"KMP_AUDIT_LOCK_DIR": locks}):
                lock = audit_scripts._lock_path(root)
            lock.parent.mkdir(parents=True, exist_ok=True)
            lock.write_text("held", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(AUDIT_SCRIPT), str(root), "--files", "feature/ui/src/commonMain/kotlin/Bad.kt", "--lock"],
                capture_output=True, text=True, env={**os.environ, "KMP_AUDIT_LOCK_DIR": locks},
            )
            self.assertEqual((result.returncode, result.stdout), (0, ""))
            self.assertIn("SKIPPED", result.stderr)
            self.assertEqual(lock.read_text(encoding="utf-8"), "held", "the holder's lock is left alone")


if __name__ == "__main__":
    unittest.main()
