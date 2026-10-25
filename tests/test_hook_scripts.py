from __future__ import annotations

import datetime
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from _helpers import BASH, REPO_ROOT, load_module

HOOKS_DIR = REPO_ROOT / "hooks"
_SRC = Path("feature") / "ui" / "src" / "commonMain" / "kotlin"

# Loaded on the audit's interpreter through PYTHONPATH: reading Slow.kt records the pid and
# hangs, so only the audit's own deadline can end the process.
_SLOW_SITECUSTOMIZE = '''
import os, pathlib, time
_read_text = pathlib.Path.read_text
def read_text(self, *args, **kwargs):
    if self.name == "Slow.kt":
        pathlib.Path(os.environ["KMP_TEST_PID_FILE"]).write_text(str(os.getpid()))
        time.sleep(120)
    return _read_text(self, *args, **kwargs)
pathlib.Path.read_text = read_text
'''


def _make_hook_project(tmp: str) -> Path:
    root = Path(tmp) / "proj"
    (root / _SRC).mkdir(parents=True)
    (root / "settings.gradle.kts").write_text('rootProject.name = "demo"\n', encoding="utf-8")
    (root / _SRC / "Bad.kt").write_text(
        "package a\nimport kotlinx.coroutines.GlobalScope\nfun f() = GlobalScope\n", encoding="utf-8")
    (root / _SRC / "Good.kt").write_text("package a\nfun g() = 1\n", encoding="utf-8")
    (root / _SRC / "Slow.kt").write_text("package a\n", encoding="utf-8")
    return root


def _run_hook(root: Path, file: Path, env: dict, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(HOOKS_DIR / "validate-architecture.sh"), str(file), str(root)],
        stdin=subprocess.DEVNULL, capture_output=True, env=env, timeout=timeout,
    )


def _slow_audit_env(tmp: str, locks: str, timeout: str) -> dict:
    site_dir = Path(tmp) / "site"
    site_dir.mkdir()
    (site_dir / "sitecustomize.py").write_text(_SLOW_SITECUSTOMIZE, encoding="utf-8")
    return {
        **os.environ,
        "PYTHONPATH": str(site_dir),
        "KMP_AUDIT_LOCK_DIR": locks,
        "KMP_ARCH_HOOK_TIMEOUT": timeout,
        "KMP_TEST_PID_FILE": str(Path(tmp) / "audit.pid"),
    }


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # an exited orphan can linger as a zombie until its new parent reaps it
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


def _wait_for_exit(pid: int, seconds: float) -> bool:
    """True if `pid` is still alive after `seconds`."""
    deadline = time.monotonic() + seconds
    while _pid_alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    return _pid_alive(pid)


def _audit_module():
    return load_module("audit_project_hook_tests", REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_project.py")

class HookScriptTests(unittest.TestCase):
    """KI-006 — hook shell script plumbing tests.

    Tests exit-code forwarding and argument handling for the two non-blocking
    hooks. The pre-commit hook is covered indirectly by the Python scripts it
    wraps; these tests cover the shell plumbing that the other tests do not.
    """

    # --- validate-architecture.sh ---

    def test_validate_arch_skips_non_kotlin_file(self) -> None:
        result = subprocess.run(
            [BASH, str(HOOKS_DIR / "validate-architecture.sh"), "readme.txt"],
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
                [BASH, str(HOOKS_DIR / "validate-architecture.sh"), "SomeFile.kt", tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "validate-architecture.sh should exit 0 on a clean project for a .kt file. "
            f"stdout: {result.stdout.decode()}  stderr: {result.stderr.decode()}"
        ))

    def test_validate_arch_skips_when_no_file(self) -> None:
        # No edited file → nothing to audit; a whole-project audit per edit is what issue #29 removed.
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_hook_project(tmp)
            result = subprocess.run(
                [BASH, str(HOOKS_DIR / "validate-architecture.sh"), "", str(root)],
                capture_output=True,
            )
        self.assertEqual((result.returncode, result.stdout), (0, b""), result.stderr.decode())

    def test_validate_arch_audits_only_the_edited_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_hook_project(tmp)
            env = {**os.environ, "KMP_AUDIT_LOCK_DIR": locks}
            bad = _run_hook(root, root / _SRC / "Bad.kt", env)
            self.assertEqual(bad.returncode, 1, bad.stdout.decode() + bad.stderr.decode())
            self.assertIn(b"globalscope usage", bad.stdout)
            self.assertNotIn(b"AGENTS.md", bad.stdout, "project-level findings belong to the full audit")

            good = _run_hook(root, root / _SRC / "Good.kt", env)
            self.assertEqual(good.returncode, 0, good.stdout.decode() + good.stderr.decode())

    def test_validate_arch_disable_switches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_hook_project(tmp)
            env = {**os.environ, "KMP_AUDIT_LOCK_DIR": locks}
            off = _run_hook(root, root / _SRC / "Bad.kt", {**env, "KMP_ARCH_HOOK_DISABLE": "1"})
            self.assertEqual((off.returncode, off.stdout), (0, b""), "KMP_ARCH_HOOK_DISABLE=1 turns it off")

            (root / ".claude").mkdir()
            (root / ".claude" / "kmp-arch-hook-disabled").write_text("", encoding="utf-8")
            marker = _run_hook(root, root / _SRC / "Bad.kt", env)
            self.assertEqual((marker.returncode, marker.stdout), (0, b""), "the marker file turns it off")

    def test_validate_arch_skips_while_an_audit_holds_the_project_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_hook_project(tmp)
            env = {**os.environ, "KMP_AUDIT_LOCK_DIR": locks}
            with mock.patch.dict(os.environ, env):
                lock = _audit_module()._lock_path(root.resolve())
            lock.parent.mkdir(parents=True, exist_ok=True)
            lock.write_text("held", encoding="utf-8")

            skipped = _run_hook(root, root / _SRC / "Bad.kt", env)
            self.assertEqual((skipped.returncode, skipped.stdout), (0, b""), skipped.stderr.decode())
            self.assertIn(b"SKIPPED", skipped.stderr)

            old = datetime.datetime.now().timestamp() - 3600
            os.utime(lock, (old, old))
            stale = _run_hook(root, root / _SRC / "Bad.kt", env)
            self.assertEqual(stale.returncode, 1, "a stale lock is taken over")
            self.assertFalse(lock.exists(), "the audit removes the lock it took over")

    def test_validate_arch_timeout_stops_the_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_hook_project(tmp)
            env = _slow_audit_env(tmp, locks, timeout="1")
            started = time.monotonic()
            result = _run_hook(root, root / _SRC / "Slow.kt", env, timeout=60)
            self.assertLess(time.monotonic() - started, 20)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertIn(b"exceeded 1s", result.stderr)
            pid = int((Path(tmp) / "audit.pid").read_text(encoding="utf-8"))
            self.assertFalse(_wait_for_exit(pid, 5), "the timed-out audit process must be gone")
            self.assertEqual(list(Path(locks).iterdir()), [])

    def test_validate_arch_audit_outlives_a_killed_hook_only_until_its_deadline(self) -> None:
        # Claude Code kills the hook's bash on timeout; on Windows that leaves the python child
        # running. The child's own deadline must still end it and free the project lock.
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as locks:
            root = _make_hook_project(tmp)
            env = _slow_audit_env(tmp, locks, timeout="4")
            pid_file = Path(tmp) / "audit.pid"
            hook = subprocess.Popen(
                [BASH, str(HOOKS_DIR / "validate-architecture.sh"), str(root / _SRC / "Slow.kt"), str(root)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
            )
            try:
                deadline = time.monotonic() + 20
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                self.assertTrue(pid_file.exists(), "the audit never started")
            finally:
                hook.kill()
                hook.wait()
            pid = int(pid_file.read_text(encoding="utf-8"))
            self.assertTrue(_pid_alive(pid), "precondition: killing the hook leaves the audit running")
            self.assertFalse(_wait_for_exit(pid, 15), "the orphaned audit must stop at its deadline")
            self.assertEqual(list(Path(locks).iterdir()), [], "and release the project lock")

    def test_validate_arch_skips_non_md_non_kt(self) -> None:
        for ext in (".json", ".sh", ".py", ".toml", ".xml"):
            with self.subTest(ext=ext):
                result = subprocess.run(
                    [BASH, str(HOOKS_DIR / "validate-architecture.sh"), f"file{ext}"],
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
            skills_dir = self._make_skill_dir(tmp, "kmp-foo", datetime.date.today().isoformat())
            result = subprocess.run(
                [BASH, str(HOOKS_DIR / "check-skill-freshness.sh"), str(skills_dir)],
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
                [BASH, str(HOOKS_DIR / "check-skill-freshness.sh"), str(skills_dir)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 1, (
            "check-skill-freshness.sh should exit 1 when a skill is >6 months stale. "
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
                [BASH, str(HOOKS_DIR / "check-skill-freshness.sh"), str(skills_dir)],
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
                [BASH, str(HOOKS_DIR / "check-skill-freshness.sh"), str(empty_skills)],
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
            [BASH, str(HOOKS_DIR / "session-start-check-updates.sh")],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, (
            "session-start-check-updates.sh must always exit 0 (non-blocking hook). "
            f"stdout: {result.stdout.decode()}  stderr: {result.stderr.decode()}"
        ))

    def test_session_start_check_updates_prints_status(self) -> None:
        result = subprocess.run(
            [BASH, str(HOOKS_DIR / "session-start-check-updates.sh")],
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
            hook_src = (HOOKS_DIR / "session-start-check-updates.sh").read_text(encoding="utf-8")
            (fake_repo / "hooks" / "session-start-check-updates.sh").write_text(hook_src, encoding="utf-8")
            check_updates_src = (REPO_ROOT / "scripts" / "check_updates.py").read_text(encoding="utf-8")
            (fake_repo / "scripts" / "check_updates.py").write_text(check_updates_src, encoding="utf-8")
            result = subprocess.run(
                [BASH, str(fake_repo / "hooks" / "session-start-check-updates.sh")],
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
                [BASH, str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
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
                [BASH, str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 2)

    def test_allows_computer_use_in_non_compose_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "build.gradle.kts").write_text(
                'plugins { id("java") }\n', encoding="utf-8"
            )
            result = subprocess.run(
                [BASH, str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, (
            "should allow computer-use in a non-Compose project. "
            f"stderr: {result.stderr.decode()}"
        ))

    def test_allows_computer_use_when_no_gradle_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [BASH, str(HOOKS_DIR / "block-computer-use-for-compose.sh"), tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0)

    def test_validate_arch_reads_hook_stdin_and_skips_non_gradle_project(self) -> None:
        # Real plugin bug: hooks.json passed $CLAUDE_TOOL_INPUT_FILE_PATH, which Claude Code
        # never sets (hook input is JSON on stdin), and the audit root defaulted to the
        # plugin's own folder instead of $CLAUDE_PROJECT_DIR.
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "CLAUDE_PROJECT_DIR": tmp}
            skipped = subprocess.run(
                [BASH, str(HOOKS_DIR / "validate-architecture.sh")],
                input=json.dumps({"tool_input": {"file_path": "src/Foo.kt"}}).encode(),
                capture_output=True, env=env,
            )
            self.assertEqual((skipped.returncode, skipped.stdout), (0, b""),
                             "non-Gradle project must not be audited")

            (Path(tmp) / "settings.gradle.kts").write_text('rootProject.name = "demo"\n')
            non_kotlin = subprocess.run(
                [BASH, str(HOOKS_DIR / "validate-architecture.sh")],
                input=json.dumps({"tool_input": {"file_path": "notes.txt"}}).encode(),
                capture_output=True, env=env,
            )
            self.assertEqual((non_kotlin.returncode, non_kotlin.stdout), (0, b""),
                             "stdin file_path must drive the extension filter")

    # --- block-edit-vendored-skills.sh ---

    def test_blocks_mirror_edit_from_hook_stdin(self) -> None:
        payload = json.dumps({"tool_input": {"file_path": "/p/.claude/skills/kmp-mvi/SKILL.md"}})
        result = subprocess.run(
            [BASH, str(HOOKS_DIR / "block-edit-vendored-skills.sh")],
            input=payload.encode(), capture_output=True,
        )
        self.assertEqual(result.returncode, 2, result.stderr.decode())

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
                    [BASH, str(HOOKS_DIR / "block-edit-vendored-skills.sh"), path],
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2, (
                    f"should block edits under {path}. stderr: {result.stderr.decode()}"
                ))
                self.assertIn(b"deployed skill mirror", result.stderr)

    def test_allows_edit_under_source_skills_dir(self) -> None:
        result = subprocess.run(
            [BASH, str(HOOKS_DIR / "block-edit-vendored-skills.sh"), "skills/kmp-mvi/SKILL.md"],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_allows_edit_of_unrelated_file(self) -> None:
        result = subprocess.run(
            [BASH, str(HOOKS_DIR / "block-edit-vendored-skills.sh"), "src/commonMain/kotlin/Foo.kt"],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_allows_when_no_path_given(self) -> None:
        result = subprocess.run(
            [BASH, str(HOOKS_DIR / "block-edit-vendored-skills.sh")],
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
                [BASH, str(HOOKS_DIR / "pre-commit-audit.sh")],
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
                [BASH, str(HOOKS_DIR / "pre-commit-audit.sh")],
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
                [BASH, str(HOOKS_DIR / "pre-commit-audit.sh")],
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
                [BASH, str(HOOKS_DIR / "commit-msg"), f_path],
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

    def test_rejects_ai_attribution_trailer_and_footer(self) -> None:
        trailer = self._run_commit_msg("feat(auth): add biometric login\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
        self.assertEqual(trailer.returncode, 1)
        self.assertIn(b"no Co-Authored-By trailer", trailer.stderr)
        footer = self._run_commit_msg(
            "feat(auth): add biometric login\n\n\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)\n")
        self.assertEqual(footer.returncode, 1)
        self.assertIn(b"no AI attribution footer", footer.stderr)

    def test_allows_generated_in_ordinary_prose(self) -> None:
        res = self._run_commit_msg(
            "fix(build): skip files generated by KSP\n\nGenerated sources move to build/.\n"
            '"Generated with Claude Code"-style footers are rejected; prose about them is not.\n')
        self.assertEqual(res.returncode, 0, res.stderr)

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
            [BASH, str(HOOKS_DIR / "pre-push")],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()

