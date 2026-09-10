from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import REPO_ROOT


class UpdateConsumerSkillsScriptTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _minimal_source(self, source: Path, version: str = "9.9.9") -> None:
        """A fake kmp-agent-skills checkout with one bundled skill."""
        self._write(source, "skills.json", '{"version":"%s"}\n' % version)
        self._write(
            source,
            "skills/shared-skill/SKILL.md",
            "---\nname: shared-skill\ndescription: Shared bundle skill.\n---\n",
        )
        self._write(source, "CHANGELOG.md", "## [v%s]\n- init\n---\n" % version)

    def _run_update(self, source: Path, project: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "update-consumer-skills.sh"),
                "--source", str(source),
                "--agent-dir", ".agents/skills",
                *extra,
            ],
            cwd=project,
            capture_output=True,
            text=True,
        )

    def test_writes_version_marker_for_the_option_e_hook(self) -> None:
        # Real bug: commands/kmp-setup-hooks.md's Option E documents this script as one
        # of the two that write `.kmp-agent-skills-version`, but only
        # sync-local-assistant-skills.sh actually did. Every consumer project wired to
        # that SessionStart hook therefore printed "No version marker" every session and
        # the stale-skills check never ran.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source, version="9.9.9")
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            (project / ".agents" / "skills").mkdir(parents=True)

            result = self._run_update(source, project)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            marker = project / ".agents" / "skills" / ".kmp-agent-skills-version"
            self.assertTrue(marker.is_file(), f"missing marker: {marker}")
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "9.9.9")

    def test_prunes_a_skill_that_no_longer_exists_upstream(self) -> None:
        # `cp -r` only adds and overwrites — a skill renamed or removed upstream used to
        # linger in the deployed copy forever (what migrate-kmm-to-kmp.sh cleaned up by
        # hand after the kmm-*/kmp-* rename).
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            # A previously-deployed bundled skill that upstream has since dropped.
            self._write(
                project,
                ".agents/skills/kmp-removed-upstream/SKILL.md",
                "---\nname: kmp-removed-upstream\ndescription: Gone.\n---\n",
            )

            result = self._run_update(source, project)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertFalse((project / ".claude" / "skills" / "kmp-removed-upstream").exists())
            self.assertTrue((project / ".agents" / "skills" / "shared-skill" / "SKILL.md").is_file())

    def test_pruning_never_removes_a_project_owned_custom_skill(self) -> None:
        # A project-owned skill lives only in ./skills and is absent from the source, so
        # a naive prune would delete it on every run.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            self._write(
                project,
                "skills/my-app-skill/SKILL.md",
                "---\nname: my-app-skill\ndescription: Project-owned.\n---\n",
            )
            self._write(
                project,
                ".claude/skills/my-app-skill/SKILL.md",
                "---\nname: my-app-skill\ndescription: Project-owned.\n---\n",
            )

            result = self._run_update(source, project)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue((project / ".claude" / "skills" / "my-app-skill" / "SKILL.md").is_file())

    def test_flags_an_installed_command_whose_source_changed(self) -> None:
        # Reporting a changed command as plain "[installed]" is how a consumer silently
        # keeps running a stale copy of a command that was fixed upstream.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(source, "commands/kmp-drifted.md", "# /kmp-drifted\n\nNew body.\n")
            self._write(source, "commands/kmp-current.md", "# /kmp-current\n\nSame body.\n")
            self._write(source, "commands/kmp-brand-new.md", "# /kmp-brand-new\n\nBody.\n")
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            self._write(project, ".agents/commands/kmp-drifted.md", "# /kmp-drifted\n\nOLD body.\n")
            self._write(project, ".agents/commands/kmp-current.md", "# /kmp-current\n\nSame body.\n")

            result = self._run_update(source, project, "--install-commands", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("[outdated] /kmp-drifted", result.stdout)
            self.assertIn("[installed] /kmp-current", result.stdout)
            self.assertIn("[new] /kmp-brand-new", result.stdout)

    def test_warns_about_drifted_commands_without_install_commands_flag(self) -> None:
        # Real bug: the "slash commands not updated" warning used to print
        # unconditionally on every run, even when every command was already current —
        # training consumers to ignore it. It should only fire, and name the actual
        # drifted commands, when something genuinely changed upstream.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(source, "commands/kmp-drifted.md", "# /kmp-drifted\n\nNew body.\n")
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            self._write(project, ".claude/commands/kmp-drifted.md", "# /kmp-drifted\n\nOLD body.\n")

            result = self._run_update(source, project)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("1 slash command(s)", result.stdout)
            self.assertIn("/kmp-drifted", result.stdout)
            self.assertIn("--install-commands", result.stdout)

    def test_no_command_warning_when_everything_is_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(source, "commands/kmp-current.md", "# /kmp-current\n\nSame body.\n")
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            self._write(project, ".agents/commands/kmp-current.md", "# /kmp-current\n\nSame body.\n")

            result = self._run_update(source, project)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertNotIn("slash command(s)", result.stdout)
            self.assertNotIn("NOT copied automatically", result.stdout)

    def test_deploys_correctly_when_each_skill_is_individually_symlinked(self) -> None:
        # Real production shape found in a consumer project: .claude/skills/<name> is a
        # symlink to .agents/skills/<name>, per skill (not the whole directory mirrored
        # at once). Writing to that destination directly broke on both tools this script
        # can use: BSD/macOS `cp -r` errored "Not a directory" on a directory source
        # copied onto a destination whose last path component is a symlink, even though
        # the link resolves to a real directory. Apple's openrsync (shipped since macOS
        # 15, not GPL rsync) reported success and "sent N bytes" while silently writing
        # nothing through it — worse than the cp error, since it looked like it worked.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')

            real_dir = project / ".agents" / "skills" / "shared-skill"
            real_dir.mkdir(parents=True)
            (real_dir / "SKILL.md").write_text("stale content\n", encoding="utf-8")
            (project / ".claude" / "skills").mkdir(parents=True)
            (project / ".claude" / "skills" / "shared-skill").symlink_to(
                Path("../../.agents/skills/shared-skill"), target_is_directory=True
            )

            result = self._run_update(source, project)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            # Content must have actually updated — both through the symlink and at the
            # real path it points to.
            via_symlink = (project / ".claude" / "skills" / "shared-skill" / "SKILL.md")
            real_path = (project / ".agents" / "skills" / "shared-skill" / "SKILL.md")
            self.assertIn("Shared bundle skill", via_symlink.read_text(encoding="utf-8"))
            self.assertIn("Shared bundle skill", real_path.read_text(encoding="utf-8"))
            # The symlink itself must survive — not get clobbered into a real directory.
            self.assertTrue((project / ".claude" / "skills" / "shared-skill").is_symlink())

    def test_dry_run_survives_a_source_with_no_reflog(self) -> None:
        # `HEAD@{1}` needs a reflog entry, absent in a fresh/shallow/CI checkout. Under
        # `set -o pipefail` that git failure used to propagate and abort the whole run
        # partway through, right after "Deploying skills…" — silently, exit 1.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source, project = tmp_root / "source", tmp_root / "project"
            source.mkdir()
            project.mkdir()
            self._minimal_source(source)
            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')

            result = self._run_update(source, project, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("[dry-run]", result.stdout)

    def test_setup_agents_scaffolds_root_sources_and_syncs_project_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source = tmp_root / "source"
            project = tmp_root / "project"
            source.mkdir()
            project.mkdir()

            self._write(source, "skills.json", '{"version":"0.0.1"}\n')
            self._write(
                source,
                "skills/shared-skill/SKILL.md",
                "---\nname: shared-skill\ndescription: Shared bundle skill.\n---\n",
            )
            self._write(source, "CHANGELOG.md", "## [v0.0.1]\n- init\n---\n")

            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            (project / ".claude" / "skills").mkdir(parents=True)
            self._write(
                project,
                "skills/demo-skill/SKILL.md",
                "---\nname: demo-skill\ndescription: Project-owned skill.\n---\n\n## Rules\n- Demo\n",
            )

            result = subprocess.run(
                [
                    "bash",
                    str(REPO_ROOT / "scripts" / "update-consumer-skills.sh"),
                    "--source",
                    str(source),
                    "--setup-agents",
                ],
                cwd=project,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue((project / ".agents" / "skills" / "shared-skill" / "SKILL.md").is_file())
            self.assertTrue((project / ".agents" / "skills" / "demo-skill" / "SKILL.md").is_file())
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertFalse((project / "CLAUDE.md").exists())
            self.assertTrue((project / "docs" / "reference" / "ai-collaboration.md").is_file())
            self.assertTrue((project / "docs" / "reference" / "agent-catalog.md").is_file())
            self.assertTrue((project / "agents" / "README.md").is_file())
            self.assertTrue((project / "rules" / "README.md").is_file())
            self.assertTrue((project / "hooks" / "README.md").is_file())
            self.assertTrue((project / "commands" / "README.md").is_file())
            self.assertTrue((project / "skills" / "README.md").is_file())

            # Real gaps fixed: .agents/skills cross-client mirror, pipeline-context.json
            # seeding, and the mandatory-baseline rows in the fallback AGENTS.md template.
            self.assertTrue((project / ".agents" / "skills" / "shared-skill" / "SKILL.md").is_file())
            # Project-owned custom skills mirror too, not just the bundled ones.
            self.assertTrue((project / ".agents" / "skills" / "demo-skill" / "SKILL.md").is_file())
            self.assertTrue((project / ".agents" / "pipeline-context.json").is_file())
            agents_md = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("kmp-code-quality", agents_md)
            self.assertIn("kmp-unit-testing", agents_md)
            self.assertIn("kmp-android-cli", agents_md)
            self.assertIn("kmp-project-docs-maintainer", agents_md)
            self.assertIn("/kmp-setup-hooks", result.stdout)

    def test_symlinked_bundled_skill_mirror_does_not_false_positive_as_a_collision(self) -> None:
        # Real bug: a project that mirrors skills/ as symlinks into .agents/skills/<name>
        # (rather than real project-owned directories) tripped the collision check for
        # every single bundled skill mirrored this way, since `-d` follows symlinks and
        # the loop never distinguished a symlink from a real project-owned directory.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source = tmp_root / "source"
            project = tmp_root / "project"
            source.mkdir()
            project.mkdir()

            self._write(source, "skills.json", '{"version":"0.0.1"}\n')
            self._write(
                source,
                "skills/shared-skill/SKILL.md",
                "---\nname: shared-skill\ndescription: Shared bundle skill.\n---\n",
            )
            self._write(source, "CHANGELOG.md", "## [v0.0.1]\n- init\n---\n")

            self._write(project, "settings.gradle.kts", 'rootProject.name = "DemoApp"\n')
            (project / ".claude" / "skills").mkdir(parents=True)
            self._write(
                project,
                "skills/real-project-skill/SKILL.md",
                "---\nname: real-project-skill\ndescription: A real project-owned skill.\n---\n",
            )
            # Mirror the bundled skill as a symlink, same shape as .agents/skills/<name>.
            (project / ".agents" / "skills" / "shared-skill").mkdir(parents=True)
            self._write(
                project,
                ".agents/skills/shared-skill/SKILL.md",
                "---\nname: shared-skill\ndescription: Shared bundle skill.\n---\n",
            )
            (project / "skills" / "shared-skill").symlink_to(
                project / ".agents" / "skills" / "shared-skill", target_is_directory=True
            )

            result = subprocess.run(
                [
                    "bash",
                    str(REPO_ROOT / "scripts" / "update-consumer-skills.sh"),
                    "--source",
                    str(source),
                    "--agent-dir",
                    ".claude/skills",
                ],
                cwd=project,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertNotIn("collides with a bundled", result.stdout)
            self.assertTrue(
                (project / ".claude" / "skills" / "real-project-skill" / "SKILL.md").is_file()
            )

    def test_agents_skills_mirror_skipped_when_agent_dir_is_already_agents_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source = tmp_root / "source"
            project = tmp_root / "project"
            source.mkdir()
            project.mkdir()

            self._write(source, "skills.json", '{"version":"0.0.1"}\n')
            self._write(
                source, "skills/shared-skill/SKILL.md",
                "---\nname: shared-skill\ndescription: Shared bundle skill.\n---\n",
            )
            self._write(source, "CHANGELOG.md", "## [v0.0.1]\n- init\n---\n")
            (project / ".agents" / "skills").mkdir(parents=True)

            result = subprocess.run(
                [
                    "bash", str(REPO_ROOT / "scripts" / "update-consumer-skills.sh"),
                    "--source", str(source), "--agent-dir", ".agents/skills",
                ],
                cwd=project, capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            # Only one deploy message, not a redundant self-mirror.
            self.assertNotIn("cross-client convention", result.stdout)

    def test_auto_detects_agents_skills_without_agent_dir_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source = tmp_root / "source"
            project = tmp_root / "project"
            source.mkdir()
            project.mkdir()

            self._write(source, "skills.json", '{"version":"0.0.1"}\n')
            self._write(
                source, "skills/shared-skill/SKILL.md",
                "---\nname: shared-skill\ndescription: Shared bundle skill.\n---\n",
            )
            self._write(source, "CHANGELOG.md", "## [v0.0.1]\n- init\n---\n")
            # Only .agents/skills/ exists — no --agent-dir passed, no .claude/skills/ present.
            (project / ".agents" / "skills").mkdir(parents=True)

            result = subprocess.run(
                ["bash", str(REPO_ROOT / "scripts" / "update-consumer-skills.sh"), "--source", str(source)],
                cwd=project, capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue((project / ".agents" / "skills" / "shared-skill" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
