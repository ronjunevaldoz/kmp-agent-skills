from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

release_scripts = load_module(
    "release",
    REPO_ROOT / "scripts" / "release.py",
)

class ReleaseScriptTests(unittest.TestCase):
    def test_release_validation_invokes_all_gates_in_order(self) -> None:
        calls: list[str] = []

        def record(name: str):
            def inner() -> None:
                calls.append(name)
            return inner

        with (
            mock.patch.object(release_scripts, "run_audit", record("audit")),
            mock.patch.object(release_scripts, "run_scan_skill_issues", record("scan")),
            mock.patch.object(release_scripts, "run_skill_map_validation", record("skill_map")),
            mock.patch.object(release_scripts, "run_keyword_routing_validation", record("keyword_routing")),
            mock.patch.object(release_scripts, "run_tests", record("tests")),
        ):
            release_scripts.run_release_validation()

        self.assertEqual(calls, ["audit", "scan", "skill_map", "keyword_routing", "tests"])

    def test_release_validation_scripts_use_repo_root_flags(self) -> None:
        commands: list[list[str]] = []

        def fake_run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="OK", stderr="")

        with mock.patch.object(release_scripts, "run", fake_run):
            release_scripts.run_skill_map_validation()
            release_scripts.run_keyword_routing_validation()

        self.assertIn(
            [
                "python3",
                str(release_scripts.VALIDATE_SKILL_MAP_SCRIPT),
                "--repo-root",
                str(release_scripts.REPO_ROOT),
            ],
            commands,
        )
        self.assertIn(
            [
                "python3",
                str(release_scripts.VALIDATE_KEYWORD_ROUTING_SCRIPT),
                "--repo-root",
                str(release_scripts.REPO_ROOT),
            ],
            commands,
        )


class ExtractSkillsDescriptionTests(unittest.TestCase):
    """Real bug shipped in the public skills.json artifact (what `npx skills add`
    reads): description: >- (YAML strip-chomp) fell through to the single-line
    fallback regex and captured the literal ">-" as the description, for 18 of
    64 skills, before this fix.
    """

    def _write_skill(self, root: Path, name: str, description_block: str) -> None:
        skill_dir = root / "skills" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\n{description_block}\nlast-updated: '2026-07-31'\n---\n\nBody.\n",
            encoding="utf-8",
        )

    def test_strip_chomp_folded_description_parsed_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_skill(
                root, "kmp-foo",
                "description: >-\n  Real content that spans\n  multiple lines.",
            )
            with mock.patch.object(release_scripts, "SKILLS_DIR", root / "skills"):
                skills = release_scripts.extract_skills()
        self.assertEqual(len(skills), 1)
        self.assertNotIn(">-", skills[0]["description"])
        self.assertIn("Real content", skills[0]["description"])

    def test_bare_folded_description_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_skill(
                root, "kmp-foo",
                "description: >\n  Real content that spans\n  multiple lines.",
            )
            with mock.patch.object(release_scripts, "SKILLS_DIR", root / "skills"):
                skills = release_scripts.extract_skills()
        self.assertIn("Real content", skills[0]["description"])

    def test_single_line_description_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_skill(root, "kmp-foo", "description: A short one-liner.")
            with mock.patch.object(release_scripts, "SKILLS_DIR", root / "skills"):
                skills = release_scripts.extract_skills()
        self.assertEqual(skills[0]["description"], "A short one-liner.")


class ChangelogSectionForTagTests(unittest.TestCase):
    """The `publish` command reads a version's notes from CHANGELOG.md by tag,
    since it runs as a separate process from the release commit and has no
    in-memory changelog_section to reuse.
    """

    def test_extracts_the_matching_section_only(self) -> None:
        content = (
            "# Changelog\n\n"
            "## [v1.2.0] — 2026-07-31\n\n### Feat\n\n- new thing\n\n---\n\n"
            "## [v1.1.0] — 2026-07-20\n\n### Fixed\n\n- old thing\n\n---\n\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            changelog = Path(tmp) / "CHANGELOG.md"
            changelog.write_text(content, encoding="utf-8")
            with mock.patch.object(release_scripts, "CHANGELOG_MD", changelog):
                section = release_scripts.changelog_section_for_tag("v1.2.0")
        self.assertIn("new thing", section)
        self.assertNotIn("old thing", section)

    def test_returns_empty_for_unknown_tag(self) -> None:
        content = "# Changelog\n\n## [v1.2.0] — 2026-07-31\n\n### Feat\n\n- new thing\n\n---\n\n"
        with tempfile.TemporaryDirectory() as tmp:
            changelog = Path(tmp) / "CHANGELOG.md"
            changelog.write_text(content, encoding="utf-8")
            with mock.patch.object(release_scripts, "CHANGELOG_MD", changelog):
                section = release_scripts.changelog_section_for_tag("v9.9.9")
        self.assertEqual(section, "")


class CmdPublishTests(unittest.TestCase):
    """Real bug this fixes: create_github_release used to run before `git push`,
    so `gh release create` always failed (the tag didn't exist on the remote yet)
    — confirmed via `gh release list`: 142 of 255 tags had no GitHub Release.
    `publish` is a separate, later step that verifies the tag is actually on the
    remote before attempting to create the release.
    """

    def test_fails_clearly_when_tag_not_on_remote(self) -> None:
        def fake_run(cmd: list[str], check: bool = True):
            if cmd[:3] == ["git", "ls-remote", "--tags"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with (
            mock.patch.object(release_scripts, "run", fake_run),
            mock.patch.object(release_scripts, "create_github_release") as mock_create,
        ):
            with self.assertRaises(SystemExit):
                release_scripts.cmd_publish("v1.2.3")
        mock_create.assert_not_called()

    def test_creates_release_when_tag_is_on_remote(self) -> None:
        def fake_run(cmd: list[str], check: bool = True):
            if cmd[:3] == ["git", "ls-remote", "--tags"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="abc123\trefs/tags/v1.2.3\n", stderr="")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with (
            mock.patch.object(release_scripts, "run", fake_run),
            mock.patch.object(release_scripts, "changelog_section_for_tag", return_value="- did stuff"),
            mock.patch.object(release_scripts, "create_github_release") as mock_create,
        ):
            rc = release_scripts.cmd_publish("v1.2.3")

        self.assertEqual(rc, 0)
        mock_create.assert_called_once_with("v1.2.3", "- did stuff", dry_run=False, prerelease=False)

    def test_rc_tag_marks_prerelease(self) -> None:
        def fake_run(cmd: list[str], check: bool = True):
            if cmd[:3] == ["git", "ls-remote", "--tags"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="abc\trefs/tags/v1.2.3-rc.1\n", stderr="")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with (
            mock.patch.object(release_scripts, "run", fake_run),
            mock.patch.object(release_scripts, "changelog_section_for_tag", return_value=""),
            mock.patch.object(release_scripts, "create_github_release") as mock_create,
        ):
            release_scripts.cmd_publish("v1.2.3-rc.1")

        mock_create.assert_called_once_with("v1.2.3-rc.1", "", dry_run=False, prerelease=True)


class PluginManifestTests(unittest.TestCase):
    """The plugin lists commands and agents explicitly (that replaces the default folder
    scan and keeps commands/references/ and agent aliases out of Claude Code), so a new
    command or a renamed agent must be reflected in plugin.json."""

    def test_plugin_commands_match_commands_dir(self) -> None:
        release = load_module("release_plugin", REPO_ROOT / "scripts" / "release.py")
        manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["commands"], release.plugin_command_paths(),
                         "run scripts/release.py or add the command to plugin.json")

    def test_plugin_agents_exist_with_frontmatter(self) -> None:
        manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
        for rel in manifest["agents"]:
            text = (REPO_ROOT / rel).read_text()
            self.assertTrue(text.startswith("---\nname: "), rel)
            self.assertIn("\ndescription: ", text.split("\n---", 1)[0], rel)


if __name__ == "__main__":
    unittest.main()
