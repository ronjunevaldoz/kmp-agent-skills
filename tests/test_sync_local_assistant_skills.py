from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import BASH, REPO_ROOT, minimal_path

SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-local-assistant-skills.sh"


class SyncLocalAssistantSkillsTests(unittest.TestCase):
    """Never touches real global assistant skill directories (dry-run or fake HOME)."""

    def _fake_source(self, tmp: str) -> Path:
        source = Path(tmp) / "kmp-agent-skills"
        (source / "skills").mkdir(parents=True)
        (source / "skills.json").write_text(json.dumps({"version": "0.0.0-test"}), encoding="utf-8")
        return source

    def test_dry_run_lists_supported_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            result = subprocess.run(
                [BASH, str(SYNC_SCRIPT), "--source", str(source), "--dry-run"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        for target in (".claude/skills", ".codex/skills", ".gemini/skills", ".agents/skills", ".gemini/config/plugins/kmp-agent-skills/skills"):
            self.assertIn(target, result.stdout, f"missing target: {target}")

    def test_dry_run_does_not_create_agents_dir(self) -> None:
        # Dry-run must be side-effect-free — confirms no accidental write path exists.
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            fake_home = Path(tmp) / "fake_home"
            fake_home.mkdir()
            env = {"HOME": str(fake_home), "PATH": minimal_path()}
            result = subprocess.run(
                [BASH, str(SYNC_SCRIPT), "--source", str(source), "--dry-run"],
                capture_output=True, text=True, encoding="utf-8", env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((fake_home / ".agents").exists())

    def test_real_sync_keeps_client_dirs_and_only_newest_backup(self) -> None:
        # Fake HOME, never the real one. Real bugs: --delete wiped Codex's bundled
        # ~/.codex/skills/.system on every sync, and a backup dir piled up per sync.
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            (source / "skills" / "kmp-x").mkdir()
            (source / "skills" / "kmp-x" / "SKILL.md").write_text("x", encoding="utf-8")
            home = Path(tmp) / "home"
            codex = home / ".codex" / "skills"
            (codex / ".system" / "imagegen").mkdir(parents=True)
            (codex / "kmp-stale").mkdir()
            old_backup = home / ".codex" / "skills-backup-kmp-agent-skills-20000101000000"
            old_backup.mkdir()

            result = subprocess.run(
                [BASH, str(SYNC_SCRIPT), "--source", str(source), "--skip-commands"],
                capture_output=True, text=True, encoding="utf-8", env={**os.environ, "HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((codex / ".system" / "imagegen").is_dir(), "client .system deleted")
            self.assertTrue((codex / "kmp-x" / "SKILL.md").is_file())
            self.assertFalse((codex / "kmp-stale").exists(), "stale synced skill kept")
            self.assertFalse(old_backup.exists(), "old backup not pruned")
            self.assertEqual(len(list((home / ".codex").glob("skills-backup-kmp-agent-skills-*"))), 1)

    def test_skips_claude_targets_when_plugin_installed(self) -> None:
        # With the Claude Code plugin installed, syncing ~/.claude too would list every skill twice.
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            home = Path(tmp) / "home"
            (home / ".claude" / "plugins").mkdir(parents=True)
            (home / ".claude" / "plugins" / "installed_plugins.json").write_text(json.dumps(
                {"version": 2, "plugins": {"kmp-agent-skills@kmp-agent-skills": [{"scope": "user"}]}}))
            result = subprocess.run(
                [BASH, str(SYNC_SCRIPT), "--source", str(source), "--dry-run"],
                capture_output=True, text=True, encoding="utf-8", env={**os.environ, "HOME": str(home)},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(".claude/skills", result.stdout)
        self.assertNotIn(".claude/commands", result.stdout)
        self.assertIn(".codex/skills", result.stdout)
        self.assertIn("plugin installed", result.stdout)

    def test_unexpected_installed_plugins_format_keeps_claude_targets_quietly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fake_source(tmp)
            home = Path(tmp) / "home"
            (home / ".claude" / "plugins").mkdir(parents=True)
            (home / ".claude" / "plugins" / "installed_plugins.json").write_text(json.dumps(
                {"version": 9, "plugins": {"kmp-agent-skills@kmp-agent-skills": "unknown"}}))
            result = subprocess.run(
                [BASH, str(SYNC_SCRIPT), "--source", str(source), "--dry-run"],
                capture_output=True, text=True, encoding="utf-8", env={**os.environ, "HOME": str(home)},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(".claude/skills", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_source_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "not-a-skills-repo"
            empty.mkdir()
            result = subprocess.run(
                [BASH, str(SYNC_SCRIPT), "--source", str(empty), "--dry-run"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
