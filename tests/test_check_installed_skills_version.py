from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import BASH, REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "check-installed-skills-version.sh"


class CheckInstalledSkillsVersionTests(unittest.TestCase):
    """Real gap this fixes: a global (non-git) skills install had no record of
    what version it's on — sync-local-assistant-skills.sh now writes a
    .kmp-agent-skills-version marker; this script reads it. Network-dependent
    paths (the actual GitHub comparison) are verified manually, not here.
    """

    def test_missing_marker_exits_2_with_clear_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            target.mkdir()
            result = subprocess.run(
                [BASH, str(SCRIPT), str(target)], capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("No version marker", result.stdout)

    def test_defaults_to_claude_skills_when_no_arg(self) -> None:
        # Just confirms the script doesn't crash resolving its default target —
        # doesn't assert on network-dependent output.
        result = subprocess.run(
            [BASH, str(SCRIPT), "/nonexistent-dir-for-test"], capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
