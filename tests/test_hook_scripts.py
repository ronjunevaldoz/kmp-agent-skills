from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

HOOKS_DIR = REPO_ROOT / "hooks"

class HookScriptTests(unittest.TestCase):
    """KI-006 — hook shell script plumbing tests.

    Tests exit-code forwarding and argument handling for the two non-blocking
    hooks. The pre-commit hook is covered indirectly by the Python scripts it
    wraps; these tests cover the shell plumbing that the other tests do not.
    """

    # --- validate-architecture.sh ---

    def test_validate_arch_skips_non_kotlin_file(self) -> None:
        result = subprocess.run(
            ["bash", str(HOOKS_DIR / "validate-architecture.sh"), "readme.txt"],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, (
            "validate-architecture.sh should exit 0 (skip) for non-.kt/.kts/.md files. "
            f"stderr: {result.stderr.decode()}"
        ))

    def test_validate_arch_runs_on_kotlin_file(self) -> None:
        # Pass a clean temp dir as $2 so the audit doesn't scan SKILL.md examples.
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "validate-architecture.sh"), "SomeFile.kt", tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "validate-architecture.sh should exit 0 on a clean project for a .kt file. "
            f"stdout: {result.stdout.decode()}  stderr: {result.stderr.decode()}"
        ))

    def test_validate_arch_runs_when_no_arg(self) -> None:
        # No file arg → audit runs; use a clean temp dir as $2 to avoid SKILL.md false positives.
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "validate-architecture.sh"), "", tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "validate-architecture.sh should exit 0 on a clean project when called with no file arg. "
            f"stderr: {result.stderr.decode()}"
        ))

    def test_validate_arch_skips_non_md_non_kt(self) -> None:
        for ext in (".json", ".sh", ".py", ".toml", ".xml"):
            with self.subTest(ext=ext):
                result = subprocess.run(
                    ["bash", str(HOOKS_DIR / "validate-architecture.sh"), f"file{ext}"],
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, (
                    f"validate-architecture.sh should skip and exit 0 for {ext} files."
                ))

    # --- check-skill-freshness.sh ---

    def _make_skill_dir(self, tmp: str, name: str, last_updated: str) -> Path:
        skills_dir = Path(tmp) / "skills"
        skill_dir = skills_dir / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\nmetadata:\n  last-updated: '{last_updated}'\n---\n",
            encoding="utf-8",
        )
        return skills_dir

    def test_freshness_exits_0_when_all_skills_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = self._make_skill_dir(tmp, "kmp-foo", "2026-06-21")
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "check-skill-freshness.sh"), str(skills_dir)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "check-skill-freshness.sh should exit 0 when all skills are fresh. "
            f"stdout: {result.stdout.decode()}"
        ))

    def test_freshness_exits_1_when_skill_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = self._make_skill_dir(tmp, "kmp-old", "2020-01-01")
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "check-skill-freshness.sh"), str(skills_dir)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 1, (
            "check-skill-freshness.sh should exit 1 when a skill is >90 days stale. "
            f"stdout: {result.stdout.decode()}"
        ))
        self.assertIn(b"STALE", result.stdout)

    def test_freshness_warns_on_missing_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill_dir = skills_dir / "kmp-nodates"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: kmp-nodates\n---\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "check-skill-freshness.sh"), str(skills_dir)],
                capture_output=True,
            )
        # No stale count incremented — exits 0 but prints WARN
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"WARN", result.stdout)

    def test_freshness_exits_0_when_no_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_skills = Path(tmp) / "skills"
            empty_skills.mkdir()
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "check-skill-freshness.sh"), str(empty_skills)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "check-skill-freshness.sh should exit 0 when the skills directory is empty."
        ))

    # --- session-start-check-updates.sh ---

    def test_session_start_check_updates_always_exits_0(self) -> None:
        # A SessionStart hook must never fail the session — exit 0 regardless of
        # whether check_updates.py reports up-to-date, behind, or unreachable.
        result = subprocess.run(
            ["bash", str(HOOKS_DIR / "session-start-check-updates.sh")],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, (
            "session-start-check-updates.sh must always exit 0 (non-blocking hook). "
            f"stdout: {result.stdout.decode()}  stderr: {result.stderr.decode()}"
        ))

    def test_session_start_check_updates_prints_status(self) -> None:
        result = subprocess.run(
            ["bash", str(HOOKS_DIR / "session-start-check-updates.sh")],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertIn(b"Checking for skill updates", result.stdout)

    def test_session_start_check_updates_exits_0_even_when_offline(self) -> None:
        # Simulate check_updates.py's own offline path (exit 2) by pointing the
        # hook's REPO_ROOT resolution at a directory with no git remote at all.
        with tempfile.TemporaryDirectory() as tmp:
            fake_repo = Path(tmp)
            (fake_repo / "hooks").mkdir()
            (fake_repo / "scripts").mkdir()
            hook_src = (HOOKS_DIR / "session-start-check-updates.sh").read_text()
            (fake_repo / "hooks" / "session-start-check-updates.sh").write_text(hook_src)
            check_updates_src = (REPO_ROOT / "scripts" / "check_updates.py").read_text()
            (fake_repo / "scripts" / "check_updates.py").write_text(check_updates_src)
            result = subprocess.run(
                ["bash", str(fake_repo / "hooks" / "session-start-check-updates.sh")],
                capture_output=True,
                cwd=str(fake_repo),
            )
        self.assertEqual(result.returncode, 0, (
            "session-start-check-updates.sh must exit 0 even when the wrapped "
            "check_updates.py can't reach a git remote. "
            f"stdout: {result.stdout.decode()}  stderr: {result.stderr.decode()}"
        ))


    # --- block-computer-use-for-compose.sh ---

    def test_blocks_computer_use_in_compose_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "build.gradle.kts").write_text(
                'plugins { id("org.jetbrains.compose") }\n', encoding="utf-8"
            )
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 2, (
            "should exit 2 (block) when the project pins org.jetbrains.compose. "
            f"stdout: {result.stdout.decode()}"
        ))
        self.assertIn(b"Roborazzi", result.stderr)

    def test_blocks_computer_use_via_version_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gradle_dir = Path(tmp) / "gradle"
            gradle_dir.mkdir()
            (gradle_dir / "libs.versions.toml").write_text(
                'compose-multiplatform = "1.11.1"\n', encoding="utf-8"
            )
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 2)

    def test_allows_computer_use_in_non_compose_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "build.gradle.kts").write_text(
                'plugins { id("java") }\n', encoding="utf-8"
            )
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "should allow computer-use in a non-Compose project. "
            f"stderr: {result.stderr.decode()}"
        ))

    def test_allows_computer_use_when_no_gradle_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0)

    # --- block-edit-vendored-skills.sh ---

    def test_blocks_edit_under_each_mirror_path(self) -> None:
        mirror_paths = [
            ".claude/skills/kmp-mvi/SKILL.md",
            ".agents/skills/kmp-mvi/SKILL.md",
            ".codex/skills/kmp-mvi/SKILL.md",
            ".gemini/skills/kmp-mvi/SKILL.md",
            "/Users/dev/project/.claude/skills/kmp-mvi/SKILL.md",
        ]
        for path in mirror_paths:
            with self.subTest(path=path):
                result = subprocess.run(
                    ["bash", str(HOOKS_DIR / "block-edit-vendored-skills.sh"), path],
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2, (
                    f"should block edits under {path}. stderr: {result.stderr.decode()}"
                ))
                self.assertIn(b"deployed skill mirror", result.stderr)

    def test_allows_edit_under_source_skills_dir(self) -> None:
        result = subprocess.run(
            ["bash", str(HOOKS_DIR / "block-edit-vendored-skills.sh"), "skills/kmp-mvi/SKILL.md"],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_allows_edit_of_unrelated_file(self) -> None:
        result = subprocess.run(
            ["bash", str(HOOKS_DIR / "block-edit-vendored-skills.sh"), "src/commonMain/kotlin/Foo.kt"],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_allows_when_no_path_given(self) -> None:
        result = subprocess.run(
            ["bash", str(HOOKS_DIR / "block-edit-vendored-skills.sh")],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)


class PreCommitAuditDocsHygieneTests(unittest.TestCase):
    """pre-commit-audit.sh's docs-hygiene gating and REPO_ROOT resolution — new
    shell plumbing not covered by audit_skills_repo.py's own tests. Verified live
    that the original ${BASH_SOURCE[0]}-based REPO_ROOT computation resolved to
    "$REPO_ROOT/.git" (one level short) when invoked through the real symlinked
    .git/hooks/pre-commit, silently no-op'ing every check — `git rev-parse
    --show-toplevel` is invocation-path independent, these tests pin that down.
    """

    def _init_repo_with_audit(self, tmp: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
        claude_skills = tmp / ".claude" / "skills"
        claude_skills.mkdir(parents=True)
        (claude_skills / "kmp-audit").symlink_to(
            REPO_ROOT / "skills" / "kmp-audit", target_is_directory=True
        )

    def test_blocks_on_oversized_staged_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            self._init_repo_with_audit(tmp)
            docs_dir = tmp / "docs"
            docs_dir.mkdir()
            (docs_dir / "big.md").write_text("# Big\n" + "line\n" * 300, encoding="utf-8")
            subprocess.run(["git", "add", "docs/big.md"], cwd=tmp, check=True)

            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "pre-commit-audit.sh")],
                cwd=tmp, capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"docs hygiene found issues", result.stdout)

    def test_allows_commit_when_no_docs_or_kotlin_staged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            self._init_repo_with_audit(tmp)
            (tmp / "notes.txt").write_text("just a text file\n", encoding="utf-8")
            subprocess.run(["git", "add", "notes.txt"], cwd=tmp, check=True)

            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "pre-commit-audit.sh")],
                cwd=tmp, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout.decode() + result.stderr.decode())

    def test_allows_commit_when_staged_doc_is_small_and_linked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            self._init_repo_with_audit(tmp)
            docs_dir = tmp / "docs"
            docs_dir.mkdir()
            (docs_dir / "small.md").write_text("# Small\n" + "line\n" * 10, encoding="utf-8")
            (tmp / "README.md").write_text(
                "# Test\n\nSee [small.md](docs/small.md) for details.\n", encoding="utf-8",
            )
            subprocess.run(["git", "add", "docs/small.md", "README.md"], cwd=tmp, check=True)

            result = subprocess.run(
                ["bash", str(HOOKS_DIR / "pre-commit-audit.sh")],
                cwd=tmp, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout.decode() + result.stderr.decode())


class CommitMsgHookTests(unittest.TestCase):
    def _run_commit_msg(self, msg: str) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as f:
            f.write(msg)
            f_path = f.name
        try:
            return subprocess.run(
                ["bash", str(HOOKS_DIR / "commit-msg"), f_path],
                capture_output=True,
            )
        finally:
            Path(f_path).unlink(missing_ok=True)

    def test_allows_valid_conventional_commit(self) -> None:
        res = self._run_commit_msg("feat(auth): add biometric login\n")
        self.assertEqual(res.returncode, 0)

    def test_allows_fixup_and_squash_commits(self) -> None:
        res1 = self._run_commit_msg("fixup! feat(auth): add biometric login\n")
        self.assertEqual(res1.returncode, 0)
        res2 = self._run_commit_msg("squash! feat(auth): add biometric login\n")
        self.assertEqual(res2.returncode, 0)

    def test_rejects_non_conventional_commit(self) -> None:
        res = self._run_commit_msg("random commit message without type\n")
        self.assertEqual(res.returncode, 1)
        self.assertIn(b"does not follow Conventional Commit", res.stderr)

    def test_rejects_low_entropy_micro_commits(self) -> None:
        for msg in ("fix: wip\n", "feat(tasks): wip\n", "fix: typo\n", "test: fix\n", "chore: temp\n", "feat: update\n"):
            with self.subTest(msg=msg):
                res = self._run_commit_msg(msg)
                self.assertEqual(res.returncode, 1)
                self.assertIn(b"low-entropy / micro-commit", res.stderr)


class PrePushHookTests(unittest.TestCase):
    def test_pre_push_hook_exists_and_runs(self) -> None:
        # Runs cleanly in current repo with no un-squashed fixups
        res = subprocess.run(
            ["bash", str(HOOKS_DIR / "pre-push")],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()

