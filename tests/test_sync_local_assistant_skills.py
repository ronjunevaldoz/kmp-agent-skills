from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import REPO_ROOT

SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-local-assistant-skills.sh"


class SyncLocalAssistantSkillsTests(unittest.TestCase):
    """Dry-run only — never touches real global assistant skill directories."""

    def _fake_source(self, tmp: str) -> Path:
        source = Path(tmp) / "kmp-agent-skills"
        (source / "skills").mkdir(parents=True)
        (source / "skills.json").write_text(json.dumps({"version": "0.0.0-test"}), encoding="utf-8")
        return source

    def test_dry_run_lists_supported_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            result = subprocess.run(
                ["bash", str(SYNC_SCRIPT), "--source", str(source), "--dry-run"],
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        for target in (".claude/skills", ".codex/skills", ".gemini/skills", ".agents/skills"):
            self.assertIn(target, result.stdout, f"missing target: {target}")

    def test_dry_run_does_not_create_agents_dir(self) -> None:
        # Dry-run must be side-effect-free — confirms no accidental write path exists.
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            fake_home = Path(tmp) / "fake_home"
            fake_home.mkdir()
            env = {"HOME": str(fake_home), "PATH": "/usr/bin:/bin"}
            result = subprocess.run(
                ["bash", str(SYNC_SCRIPT), "--source", str(source), "--dry-run"],
                capture_output=True, text=True, env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((fake_home / ".agents").exists())

    def test_missing_source_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "not-a-skills-repo"
            empty.mkdir()
            result = subprocess.run(
                ["bash", str(SYNC_SCRIPT), "--source", str(empty), "--dry-run"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
