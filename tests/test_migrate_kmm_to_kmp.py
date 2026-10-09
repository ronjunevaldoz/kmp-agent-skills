from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import BASH, REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "migrate-kmm-to-kmp.sh"


class MigrateKmmToKmpTests(unittest.TestCase):
    def _run(self, project: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [BASH, str(SCRIPT), *args],
            cwd=str(project),
            capture_output=True,
            text=True, encoding="utf-8",
        )

    def _make_stale_project(self, project: Path) -> None:
        (project / ".claude" / "skills" / "kotlin-multiplatform-mvi").mkdir(parents=True)
        (project / ".claude" / "skills" / "kmp-design-system").mkdir(parents=True)
        (project / ".claude" / "skills" / "kmp-compose-design-system").mkdir(parents=True)
        commands_dir = project / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "kmm-verify.md").write_text("old", encoding="utf-8")
        (commands_dir / "kmp-verify.md").write_text("new", encoding="utf-8")
        (project / ".kmm-skills").write_text("v1.20.0\n", encoding="utf-8")

    def test_removes_stale_directories_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self._make_stale_project(project)

            result = self._run(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((project / ".claude" / "skills" / "kotlin-multiplatform-mvi").exists())
            self.assertFalse((project / ".claude" / "skills" / "kmp-design-system").exists())
            self.assertFalse((project / ".claude" / "commands" / "kmm-verify.md").exists())
            self.assertFalse((project / ".kmm-skills").exists())

    def test_preserves_current_named_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self._make_stale_project(project)

            self._run(project)

            self.assertTrue((project / ".claude" / "skills" / "kmp-compose-design-system").exists())
            self.assertTrue((project / ".claude" / "commands" / "kmp-verify.md").exists())
            self.assertTrue((project / ".kmp-skills").exists())
            self.assertEqual(
                (project / ".kmp-skills").read_text(encoding="utf-8"), "v1.20.0\n"
            )

    def test_dry_run_deletes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self._make_stale_project(project)

            result = self._run(project, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("dry-run", result.stdout)
            self.assertTrue((project / ".claude" / "skills" / "kotlin-multiplatform-mvi").exists())
            self.assertTrue((project / ".kmm-skills").exists())

    def test_clean_project_reports_nothing_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".claude" / "skills" / "kmp-compose-design-system").mkdir(parents=True)

            result = self._run(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Nothing stale found", result.stdout)


if __name__ == "__main__":
    unittest.main()
