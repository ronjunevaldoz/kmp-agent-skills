from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import BASH, REPO_ROOT, bash_path

SCRIPT = REPO_ROOT / "skills" / "kmp-token-saver" / "scripts" / "install-rtk.sh"

# A stand-in rtk: answers --version and the Phase 2 dry run, nothing else.
FAKE_RTK = """#!/bin/sh
case "$*" in
  --version) echo "rtk 9.9.9" ;;
  "init -g --dry-run") echo "[dry-run] Nothing written." ;;
esac
"""
# A stand-in package manager: logs its arguments and "installs" the fake rtk.
FAKE_INSTALLER = """#!/bin/sh
echo "$(basename "$0") $*" >> "$INSTALL_LOG"
cp "$FAKE_RTK_SRC" "$FAKE_BIN/rtk"
chmod +x "$FAKE_BIN/rtk"
"""


class InstallRtkTests(unittest.TestCase):
    """Runs the script against fake brew/winget/rtk on a PATH without the real ones."""

    def _run(self, tools: list[str]) -> tuple[subprocess.CompletedProcess, str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            rtk_src = root / "rtk-src"
            rtk_src.write_text(FAKE_RTK, encoding="utf-8", newline="\n")
            log = root / "install.log"
            log.touch()
            for tool in tools:
                content = FAKE_RTK if tool == "rtk" else FAKE_INSTALLER
                (fake_bin / tool).write_text(content, encoding="utf-8", newline="\n")
                (fake_bin / tool).chmod(0o755)
            env = {
                **os.environ,
                "PATH": f"{bash_path(fake_bin)}:/usr/bin:/bin",
                "INSTALL_LOG": bash_path(log),
                "FAKE_BIN": bash_path(fake_bin),
                "FAKE_RTK_SRC": bash_path(rtk_src),
            }
            result = subprocess.run([BASH, str(SCRIPT)], capture_output=True, text=True,
                                    encoding="utf-8", env=env)
            return result, log.read_text(encoding="utf-8")

    def test_skips_install_when_rtk_is_already_on_path(self) -> None:
        result, log = self._run(["rtk", "brew", "winget"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already installed (rtk 9.9.9)", result.stdout)
        self.assertIn("[dry-run] Nothing written.", result.stdout)
        self.assertEqual(log, "")

    def test_prefers_brew(self) -> None:
        result, log = self._run(["brew", "winget"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log.strip(), "brew install rtk")
        self.assertIn("[dry-run] Nothing written.", result.stdout)

    def test_uses_the_official_winget_package_without_brew(self) -> None:
        result, log = self._run(["winget"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log.strip(), "winget install --id rtk-ai.rtk --exact --source winget --disable-interactivity")
        self.assertIn("[dry-run] Nothing written.", result.stdout)
        self.assertIn("rtk init -g --hook-only", result.stdout)

    def test_fails_clearly_without_brew_or_winget(self) -> None:
        result, log = self._run([])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Neither Homebrew nor winget found", result.stderr)
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
