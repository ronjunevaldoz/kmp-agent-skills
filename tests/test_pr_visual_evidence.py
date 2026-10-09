# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
Tests for kmp-roborazzi/scripts/pr_visual_evidence.py.
"""
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, load_module

SCRIPT = REPO_ROOT / "skills" / "kmp-roborazzi" / "scripts" / "pr_visual_evidence.py"
mod = load_module("pr_visual_evidence", SCRIPT)

REPO = "owner/app"


def png(width: int, height: int, seed: bytes = b"") -> bytes:
    # Header only — enough for the IHDR width/height read; seed makes content differ.
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height) + seed


class TestParseGithubRepo(unittest.TestCase):

    def test_remote_formats(self) -> None:
        for url in (
            "git@github.com:owner/app.git",
            "https://github.com/owner/app.git",
            "https://github.com/owner/app",
            "ssh://git@github.com/owner/app.git\n",
        ):
            self.assertEqual(mod.parse_github_repo(url), REPO, url)

    def test_non_github_remote(self) -> None:
        self.assertIsNone(mod.parse_github_repo("git@gitlab.com:owner/app.git"))


class TestSnapshotDiff(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._git("init", "-q")
        snaps = self.root / "feature" / "ui" / "src" / "desktopTest" / "snapshots"
        snaps.mkdir(parents=True)
        self.snaps = snaps
        (snaps / "changed.png").write_bytes(png(400, 800, b"v1"))
        (snaps / "removed.png").write_bytes(png(400, 800, b"gone" * 100))
        (snaps / "old name.png").write_bytes(png(1280, 800, b"same" * 50))
        (snaps / "changed.bounds.json").write_text("{}")
        (self.root / "README.md").write_text("app")
        self.base = self._commit("base")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=self.root, check=True, capture_output=True, text=True, encoding="utf-8",
        ).stdout.strip()

    def _commit(self, msg: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", msg)
        return self._git("rev-parse", "HEAD")

    def _pr_head(self) -> str:
        (self.snaps / "changed.png").write_bytes(png(400, 800, b"v2"))
        (self.snaps / "removed.png").unlink()
        (self.snaps / "added.png").write_bytes(png(1280, 800, b"new!" * 100))
        (self.snaps / "old name.png").rename(self.snaps / "new name.png")
        (self.snaps / "changed.bounds.json").write_text('{"x": 1}')
        (self.root / "README.md").write_text("app v2")
        return self._commit("head")

    def test_diff_classifies_statuses(self) -> None:
        head = self._pr_head()
        entries = mod.diff_snapshots(self.base, head, mod.DEFAULT_GLOBS, cwd=str(self.root))
        by_status = {status: new.rsplit("/", 1)[-1] for status, _old, new in entries}
        self.assertEqual(
            by_status,
            {"A": "added.png", "D": "removed.png", "M": "changed.png", "R": "new name.png"},
        )  # README.md and .bounds.json are filtered out

    def test_render_links_are_sha_pinned(self) -> None:
        head = self._pr_head()
        entries = mod.diff_snapshots(self.base, head, mod.DEFAULT_GLOBS, cwd=str(self.root))
        out = mod.render(entries, REPO, self.base, head, cwd=str(self.root))
        prefix = f"https://github.com/{REPO}/blob"
        path = "feature/ui/src/desktopTest/snapshots"
        self.assertIn(mod.MARKER, out)
        self.assertIn(f'{prefix}/{self.base}/{path}/changed.png?raw=true" width="360" alt="before"', out)
        self.assertIn(f'{prefix}/{head}/{path}/changed.png?raw=true" width="360" alt="after"', out)
        self.assertIn(f'{prefix}/{head}/{path}/added.png?raw=true" width="420" alt="new"', out)
        self.assertIn(f'{prefix}/{self.base}/{path}/removed.png?raw=true" width="360" alt="removed"', out)
        # rename: before at old path/base, after at new path/head, spaces URL-quoted
        self.assertIn(f"{prefix}/{self.base}/{path}/old%20name.png?raw=true", out)
        self.assertIn(f"{prefix}/{head}/{path}/new%20name.png?raw=true", out)
        for heading in ("### Changed (2)", "### New (1)", "### Removed (1)"):
            self.assertIn(heading, out)

    def test_custom_glob_narrows_scope(self) -> None:
        head = self._pr_head()
        entries = mod.diff_snapshots(self.base, head, ["**/added.png"], cwd=str(self.root))
        self.assertEqual([e[0] for e in entries], ["A"])

    def test_no_snapshot_change_prints_one_line(self) -> None:
        (self.root / "README.md").write_text("server-only change")
        head = self._commit("server")
        entries = mod.diff_snapshots(self.base, head, mod.DEFAULT_GLOBS, cwd=str(self.root))
        out = mod.render(entries, REPO, self.base, head, cwd=str(self.root))
        self.assertEqual(
            out,
            f"{mod.MARKER}\nNo before/after: no committed snapshot changed in `{self.base[:7]}`..`{head[:7]}`.\n",
        )  # marker kept so a CI comment can be updated in place

    def test_long_section_collapses_into_details(self) -> None:
        rows = [("A", f"s/snapshots/{i}.png", f"s/snapshots/{i}.png") for i in range(mod.DETAILS_THRESHOLD + 1)]
        out = mod.render(rows, REPO, "a" * 40, "b" * 40, width=360)
        self.assertIn("<details>", out)
        short = mod.render(rows[:1], REPO, "a" * 40, "b" * 40, width=360)
        self.assertNotIn("<details>", short)


if __name__ == "__main__":
    unittest.main()
