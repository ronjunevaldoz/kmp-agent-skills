from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

check_updates_scripts = load_module(
    "check_updates",
    REPO_ROOT / "scripts" / "check_updates.py",
)

class CheckUpdatesTests(unittest.TestCase):
    def test_read_version_valid_json(self) -> None:
        result = check_updates_scripts.read_version('{"version": "1.7.0"}')
        self.assertEqual(result, "1.7.0")

    def test_read_version_missing_key(self) -> None:
        result = check_updates_scripts.read_version('{"other": "x"}')
        self.assertEqual(result, "?")

    def test_read_version_malformed_json(self) -> None:
        result = check_updates_scripts.read_version("not-json")
        self.assertEqual(result, "?")

    def test_read_version_empty_string(self) -> None:
        result = check_updates_scripts.read_version("")
        self.assertEqual(result, "?")

    def _run_main_with_run(self, run_responses: list) -> int:
        """Patch check_updates_scripts.run and call main(), returning the exit code."""
        from unittest.mock import patch
        responses = iter(run_responses)

        def fake_run(cmd: str) -> tuple:
            return next(responses)

        with patch.object(check_updates_scripts, "run", side_effect=fake_run):
            return check_updates_scripts.main()

    def test_main_exit_2_when_fetch_fails(self) -> None:
        # git fetch returns non-zero → offline → exit 2
        rc = self._run_main_with_run([("", 1)])
        self.assertEqual(rc, 2)

    def test_main_exit_0_when_up_to_date(self) -> None:
        # fetch ok, 0 commits behind, 0 commits ahead → exit 0
        rc = self._run_main_with_run([
            ("", 0),    # git fetch
            ("0", 0),   # rev-list behind
            ("0", 0),   # rev-list ahead
        ])
        self.assertEqual(rc, 0)

    def test_main_exit_0_with_local_commits_ahead(self) -> None:
        # fetch ok, 0 behind, 2 ahead (unpushed local commits) → still exit 0
        rc = self._run_main_with_run([
            ("", 0),    # git fetch
            ("0", 0),   # rev-list behind
            ("2", 0),   # rev-list ahead
        ])
        self.assertEqual(rc, 0)

    def test_main_exit_1_when_behind_remote(self) -> None:
        # fetch ok, 3 commits behind → updates available → exit 1
        import tempfile, json as _json
        with tempfile.TemporaryDirectory() as tmp:
            skills_json = Path(tmp) / "skills.json"
            skills_json.write_text(_json.dumps({"version": "1.7.0"}))
            (Path(tmp) / ".git").mkdir()

            from unittest.mock import patch
            responses = iter([
                ("", 0),                    # git fetch
                ("3", 0),                   # rev-list behind
                (_json.dumps({"version": "1.9.0"}), 0),  # git show remote skills.json
                ("skills/foo/SKILL.md\nagents/planner.md", 0),  # git diff changed files
                ("", 0),                    # git diff changelog
            ])

            def fake_run(cmd: str) -> tuple:
                return next(responses)

            old_root = check_updates_scripts.ROOT
            check_updates_scripts.ROOT = Path(tmp)
            try:
                with patch.object(check_updates_scripts, "run", side_effect=fake_run):
                    rc = check_updates_scripts.main()
            finally:
                check_updates_scripts.ROOT = old_root

        self.assertEqual(rc, 1)

    def test_main_exit_2_without_git_checkout_and_runs_no_git(self) -> None:
        # The Claude Code plugin is a plain copy: point at `claude plugin update` instead of
        # running git, which would otherwise inspect the caller's own project.
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            old_root = check_updates_scripts.ROOT
            check_updates_scripts.ROOT = Path(tmp)
            try:
                with patch.object(check_updates_scripts, "run") as run:
                    rc = check_updates_scripts.main()
            finally:
                check_updates_scripts.ROOT = old_root
        self.assertEqual(rc, 2)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
