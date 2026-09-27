from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module


def read_skill_with_references(skill_dir: Path) -> str:
    """SKILL.md text plus every references/*.md file concatenated — mirrors how
    scripts/check_compat_matrix.py and audit_skills_repo.py already read a skill
    after content was split out for the agentskills.io 500-line guideline (KI-008)."""
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        text += "\n" + "\n".join(
            ref.read_text(encoding="utf-8") for ref in sorted(references_dir.glob("*.md"))
        )
    return text


def read_command_with_phases(command: str) -> str:
    """A command's own text plus any phase reference files it delegates to.

    `/kmp-new-project` is a thin phase index; its actual procedure lives in
    `skills/kmp-expert/references/new-project-phase-*.md` (KI-009). Same reasoning as
    read_skill_with_references above — assert against the whole procedure, not just the
    index, or these checks silently stop testing anything the moment content moves.
    """
    text = (REPO_ROOT / "commands" / f"{command}.md").read_text(encoding="utf-8")
    phase_dir = REPO_ROOT / "skills" / "kmp-expert" / "references"
    stem = command.replace("kmp-", "", 1)
    text += "\n" + "\n".join(
        f.read_text(encoding="utf-8") for f in sorted(phase_dir.glob(f"{stem}-phase-*.md"))
    )
    return text


class DocsScopeBoundaryTests(unittest.TestCase):
    def test_repo_and_consumer_docs_boundary_is_explicit(self) -> None:
        normalize = lambda text: " ".join(text.lower().split())

        docs_maintainer = normalize((REPO_ROOT / "agents" / "docs-maintainer.md").read_text(encoding="utf-8"))
        planner = normalize((REPO_ROOT / "agents" / "planner.md").read_text(encoding="utf-8"))
        expert = normalize((REPO_ROOT / "skills" / "kmp-expert" / "SKILL.md").read_text(encoding="utf-8"))
        project_docs = normalize((REPO_ROOT / "skills" / "kmp-project-docs-maintainer" / "SKILL.md").read_text(encoding="utf-8"))
        readme = normalize((REPO_ROOT / "README.md").read_text(encoding="utf-8"))

        self.assertIn("repo-internal docs", docs_maintainer)
        self.assertIn("downstream consumer docs", docs_maintainer)
        self.assertIn("repo-internal docs -> `docs-maintainer`", planner)
        self.assertIn("downstream consumer docs -> `project-docs-maintainer`", planner)
        self.assertIn("docs scope guard", expert)
        self.assertIn("repo-internal docs", expert)
        self.assertIn("downstream consumer docs", expert)
        self.assertIn("downstream consumer-facing kmp project documentation only", project_docs)
        self.assertIn("if the target is this repository, route to `docs-maintainer` instead.", project_docs)
        self.assertIn("classify it as repo-internal or downstream consumer", readme)

    def test_local_assistant_sync_is_documented_separately(self) -> None:
        normalize = lambda text: " ".join(
            text.lower().replace("`", "").replace(":", "").replace(".", "").split()
        )

        readme = normalize((REPO_ROOT / "README.md").read_text(encoding="utf-8"))
        install = normalize((REPO_ROOT / "INSTALL.md").read_text(encoding="utf-8"))
        command = normalize((REPO_ROOT / "commands" / "kmp-sync-local-skills.md").read_text(encoding="utf-8"))

        self.assertIn("kmp-sync-local-skills", readme)
        self.assertIn("local claude / codex / gemini installs on this mac", install)
        self.assertIn("sync the latest kmp-agent-skills release into the local assistant skill bundles", command)
        self.assertIn("does not copy commands/", command)

    def test_benchmark_tables_have_a_canonical_reference_home(self) -> None:
        docs = (REPO_ROOT / "skills" / "kmp-project-docs-maintainer" / "SKILL.md").read_text(encoding="utf-8").lower()

        self.assertIn("benchmark or performance comparison tables", docs)
        self.assertIn("docs/reference/benchmark-matrix.md", docs)

    def test_claude_scaffold_contract_is_documented_as_project_owned_plus_runtime(self) -> None:
        normalize = lambda text: " ".join(text.lower().replace("`", "").split())

        expert = normalize(read_skill_with_references(REPO_ROOT / "skills" / "kmp-expert"))
        setup_agents = normalize((REPO_ROOT / "commands" / "kmp-setup-agents.md").read_text(encoding="utf-8"))
        new_project = normalize(read_command_with_phases("kmp-new-project"))

        for text in (expert, setup_agents, new_project):
            self.assertIn("rules/", text)
            self.assertIn("docs/reference/ai-collaboration.md", text)
            self.assertIn("claude.md", text)
            self.assertIn("project-owned", text)

    def test_cross_agent_reference_docs_cover_docs_vs_skills_and_model_tiers(self) -> None:
        ai = (REPO_ROOT / "docs" / "reference" / "ai-collaboration.md").read_text(encoding="utf-8").lower()
        catalog = (REPO_ROOT / "docs" / "reference" / "agent-catalog.md").read_text(encoding="utf-8").lower()

        self.assertIn("how is this project designed?", ai)
        self.assertIn("how should an agent work in this repo?", ai)
        self.assertIn("agents.md", ai)
        self.assertIn("claude.md", ai)
        self.assertIn("gemini.md", ai)

        self.assertIn("flagship-coding", catalog)
        self.assertIn("balanced-coding", catalog)
        self.assertIn("fast-utility", catalog)
        self.assertIn("precision-review", catalog)
        self.assertIn("provider-specific model mapping", catalog)


class AgentSetupSingleOwnerTests(unittest.TestCase):
    """`/kmp-setup-agents` is the single owner of the agent-scaffold templates.

    `/kmp-new-project` used to inline its own duplicate of them, and the two copies
    drifted in production: the `[Library]` AGENTS.md written by new-project had lost five
    skill-routing rows and used different placeholder names than the one setup-agents
    writes, so a library scaffolded through new-project silently got a worse AGENTS.md.
    Nothing checked for it, which is exactly why it drifted unnoticed.
    """

    def _read(self, rel: str) -> str:
        return (REPO_ROOT / rel).read_text(encoding="utf-8")

    def test_new_project_delegates_agent_setup_instead_of_inlining_it(self) -> None:
        new_project = read_command_with_phases("kmp-new-project")

        self.assertIn("/kmp-setup-agents", new_project)
        # The AGENTS.md body template must exist in exactly one command. These marker
        # lines are the template payload, not prose about it.
        for marker in ("# AGENTS.md — <PROJECT_NAME>", "## Published artifacts"):
            self.assertNotIn(
                marker, new_project,
                f"{marker!r} is back in kmp-new-project.md — the AGENTS.md template "
                f"belongs to /kmp-setup-agents alone, or the two copies will drift again",
            )

    def test_the_agents_md_template_lives_in_exactly_one_deployed_place(self) -> None:
        # The template moved out of the command and into a skill reference — a command is
        # copied to a consumer as a single bare .md (update-consumer-skills.sh's
        # `cp "$cmd_file"`), while skills are always deployed, so a skill reference is
        # the only location a consumer-facing command can actually resolve at runtime.
        ref = self._read("skills/kmp-expert/references/agents-md-templates.md")
        self.assertIn("## Published artifacts", ref)
        self.assertIn("### For APP projects", ref)
        self.assertIn("### For LIBRARY projects", ref)

        for command in ("kmp-setup-agents", "kmp-new-project"):
            body = read_command_with_phases(command)
            self.assertNotIn(
                "## Published artifacts", body,
                f"the AGENTS.md template body is back in {command}.md — it belongs only "
                f"in kmp-expert/references/agents-md-templates.md",
            )
            self.assertIn("agents-md-templates.md", body)

    def test_new_project_still_owns_what_setup_agents_does_not_write(self) -> None:
        # setup-agents runs against existing projects that already have a README and
        # docs/, so it deliberately never writes them — new-project must keep those.
        new_project = read_command_with_phases("kmp-new-project")
        setup_agents = self._read("commands/kmp-setup-agents.md")

        self.assertIn("README.md", new_project)
        self.assertIn("docs/decisions/", new_project)
        self.assertNotIn("docs/decisions/", setup_agents)

    def test_setup_agents_scopes_gitignore_instead_of_only_documenting_it(self) -> None:
        # A real consumer project (awaken) had .claude/ blanket-gitignored, so
        # .claude/AGENTS.md — the file CLAUDE.md loads as the literal system prompt —
        # was never tracked. Docs alone don't prevent a fresh project from inheriting
        # the same bug; the command has to actually apply the scoped .gitignore.
        setup_agents = self._read("commands/kmp-setup-agents.md")
        ref = self._read("skills/kmp-expert/references/agents-md-templates.md")

        self.assertIn("Step 7b", setup_agents)
        self.assertIn(".gitignore", setup_agents)
        self.assertIn("What to commit vs gitignore", ref)
        self.assertIn(".claude/skills/", ref)
        self.assertIn("!.claude/AGENTS.md", ref)


class CleanCommentsCoversEveryCommentDetectorTests(unittest.TestCase):
    """`/kmp-clean-comments` must name every comment finding the audit can emit.

    It shipped naming one (`what-comment in control flow`) and asserting it was "the only
    one of the four categories with an automated detector". Four more comment detectors
    landed after that sentence was written, so the dedicated comment-cleanup command was
    acting on less than the audit already knew — true when written, silently stale after.
    """

    COMMENT_FINDINGS = (
        "what-comment in control flow",
        "long stacked comment block",
        "justification comment above single statement",
        "undocumented public api",
        "partial param documentation",
    )

    def test_command_names_every_comment_finding_the_auditor_emits(self) -> None:
        command = (REPO_ROOT / "commands" / "kmp-clean-comments.md").read_text(encoding="utf-8")
        for finding in self.COMMENT_FINDINGS:
            self.assertIn(
                finding, command,
                f"/kmp-clean-comments doesn't mention the {finding!r} finding — a comment "
                f"detector exists that the comment-cleanup command won't act on",
            )

    def test_the_finding_strings_still_exist_in_the_auditor(self) -> None:
        # Guards the other direction: if a finding string is renamed in audit_project.py,
        # the command's filter list silently stops matching anything.
        auditor = (REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_project.py").read_text(
            encoding="utf-8"
        )
        for finding in self.COMMENT_FINDINGS:
            self.assertIn(finding, auditor, f"{finding!r} no longer emitted by audit_project.py")


class SetupAgentsCommandClassificationTests(unittest.TestCase):
    """`kmp-setup-agents.md`'s consumer-safe / repo-internal command lists must cover
    every file in commands/ between them. Found stale by audit: kmp-clean-comments.md
    and kmp-migrate-to-shadcn.md were added to commands/ after this list was written
    and sat in neither bucket — not flagged unsafe, not confirmed safe, silently
    excluded from --install-commands guidance either way.
    """

    def test_every_command_is_classified_as_consumer_safe_or_repo_internal(self) -> None:
        all_commands = {p.name for p in (REPO_ROOT / "commands").glob("*.md")}
        text = (REPO_ROOT / "commands" / "kmp-setup-agents.md").read_text(encoding="utf-8")
        unclassified = {name for name in all_commands if name not in text}
        self.assertEqual(
            unclassified, set(),
            f"commands/ files missing from both the consumer-safe and repo-internal "
            f"lists in kmp-setup-agents.md: {sorted(unclassified)}",
        )


class FrameworkAgnosticStoreTests(unittest.TestCase):
    """kmp-mvi's Contract pattern is plain Kotlin — a real consumer project needed the
    non-Compose/non-ViewModel variant (a custom Vulkan/WebGPU/OpenGL renderer with no
    coroutine-driven recomposition loop), and it didn't exist anywhere in the skill.
    """

    def test_skill_md_points_at_the_reference_and_lists_it_in_decision_table(self) -> None:
        skill = (REPO_ROOT / "skills" / "kmp-mvi" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("framework-agnostic-store", skill)
        self.assertIn("Non-Compose consumer", skill)

    def test_reference_file_covers_scope_ownership_and_pull_based_draining(self) -> None:
        ref = (REPO_ROOT / "skills" / "kmp-mvi" / "references" / "framework-agnostic-store.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CoroutineScope", ref)
        self.assertIn("drainEffects", ref)
        self.assertIn("tryReceive", ref)

    def test_kmp_api_mimicry_cross_links_back(self) -> None:
        mimicry = (REPO_ROOT / "skills" / "kmp-api-mimicry" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("kmp-mvi", mimicry)


class CommonFirstSharedCodeTests(unittest.TestCase):
    def test_common_first_formatting_rule_is_explicit(self) -> None:
        normalize = lambda text: " ".join(text.lower().replace("`", "").split())

        expert = normalize(read_skill_with_references(REPO_ROOT / "skills" / "kmp-expert"))
        expect_actual = normalize((REPO_ROOT / "skills" / "kmp-expect-actual" / "SKILL.md").read_text(encoding="utf-8"))
        audit = normalize((REPO_ROOT / "skills" / "kmp-audit" / "SKILL.md").read_text(encoding="utf-8"))

        self.assertIn("string.format", expert)
        self.assertIn("shared formatter", expert)
        self.assertIn("implementing the behavior in commonmain first", expect_actual)
        self.assertIn("commonmain can express it cleanly and portably", expect_actual)
        self.assertIn("jvm-only utility in commonmain", expect_actual)
        self.assertIn("prefer a pure commonmain implementation before abstractions", audit)
        self.assertIn("jvm-only utilities in commonmain", audit)


heal_docs = load_module(
    "heal_docs",
    REPO_ROOT / "skills" / "kmp-project-docs-maintainer" / "scripts" / "heal_docs.py",
)


class HealDocsTests(unittest.TestCase):
    def test_heal_docs_syncs_sitemap_and_task_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            tasks_dir = docs / "tasks" / "auth"
            tasks_dir.mkdir(parents=True)
            
            task_file = tasks_dir / "01-login-doing.md"
            task_file.write_text(
                "# Login Flow\n\n**Date:** 2026-09-11\n\n"
                "- [x] Model setup\n- [x] Domain use case\n- [ ] UI screen\n",
                encoding="utf-8",
            )
            
            # Run heal_docs
            heal_docs.heal_docs(root, dry_run=False)
            
            readme = (docs / "README.md").read_text(encoding="utf-8")
            self.assertIn("Documentation Sitemap & System Status", readme)
            self.assertIn("tasks/auth/01-login-doing.md", readme)
            
            tasks_md = (docs / "tasks.md").read_text(encoding="utf-8")
            self.assertIn("# Tasks", tasks_md)
            self.assertIn("66% (2/3)", tasks_md)
            self.assertIn("tasks/auth/01-login-doing.md", tasks_md)
            self.assertIn("`doing`", tasks_md)
            self.assertIn("`auth`", tasks_md)

    def test_auto_archives_task_with_done_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            tasks_dir = docs / "tasks" / "auth"
            tasks_dir.mkdir(parents=True)

            task_file = tasks_dir / "01-login-done.md"
            task_file.write_text(
                "# Login Flow\n\n**Status:** done\n**Date:** 2026-09-11\n\n- [x] All done\n",
                encoding="utf-8",
            )

            heal_docs.heal_docs(root, dry_run=False)

            self.assertFalse(task_file.exists())
            archived = tasks_dir / "archive" / "01-login-done.md"
            self.assertTrue(archived.exists())
            self.assertIn("tasks/auth/archive/01-login-done.md", (docs / "README.md").read_text(encoding="utf-8"))

    def test_auto_archives_task_with_100_percent_checkboxes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            tasks_dir = docs / "tasks" / "auth"
            tasks_dir.mkdir(parents=True)

            task_file = tasks_dir / "02-biometric-doing.md"
            task_file.write_text(
                "# Biometric Flow\n\n**Status:** doing\n**Date:** 2026-09-11\n\n- [x] Step 1\n- [x] Step 2\n",
                encoding="utf-8",
            )

            heal_docs.heal_docs(root, dry_run=False)

            self.assertFalse(task_file.exists())
            archived = tasks_dir / "archive" / "02-biometric-done.md"
            self.assertTrue(archived.exists())
            content = archived.read_text(encoding="utf-8")
            self.assertIn("**Status:** done", content)

    def test_auto_renames_snake_case_and_updates_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            ref_dir = docs / "reference"
            ref_dir.mkdir(parents=True)

            guide_file = ref_dir / "my_cool_guide.md"
            guide_file.write_text("# Cool Guide\n\nSome guide content\n", encoding="utf-8")

            caller = docs / "architecture.md"
            caller.write_text("# Arch\n\nSee [Guide](reference/my_cool_guide.md)\n", encoding="utf-8")

            heal_docs.heal_docs(root, dry_run=False)

            self.assertFalse(guide_file.exists())
            new_guide = ref_dir / "my-cool-guide.md"
            self.assertTrue(new_guide.exists())

            updated_caller = caller.read_text(encoding="utf-8")
            self.assertIn("reference/my-cool-guide.md", updated_caller)

    def test_check_consumer_skills_and_agents_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True)

            # Create bad skill (micro-scoped, name mismatch)
            bad_skill_dir = root / "skills" / "fix-login-error"
            bad_skill_dir.mkdir(parents=True)
            (bad_skill_dir / "SKILL.md").write_text(
                "---\nname: other-name\ndescription: A fix.\n---\n\nBody.\n",
                encoding="utf-8",
            )

            # Create bad agent (redundant suffix, action-named)
            agents_dir = root / "agents"
            agents_dir.mkdir(parents=True)
            (agents_dir / "deploy-app-agent.md").write_text(
                "---\nname: deploy-app\ndescription: Deploys.\n---\n\nBody.\n",
                encoding="utf-8",
            )

            warnings = heal_docs.check_consumer_skills_and_agents(root)
            self.assertTrue(any("directory name" in w for w in warnings))
            self.assertTrue(any("micro-scoped" in w for w in warnings))
            self.assertTrue(any("redundant suffix" in w for w in warnings))
            self.assertTrue(any("action-named" in w for w in warnings))



new_task = load_module(
    "new_task",
    REPO_ROOT / "skills" / "kmp-project-docs-maintainer" / "scripts" / "new_task.py",
)


class NewTaskTests(unittest.TestCase):
    def test_scaffolds_task_with_proper_sequence_and_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Create first task
            t1 = new_task.create_task(root, "auth", "session-refresh")
            self.assertEqual(t1.name, "01-session-refresh-todo.md")
            self.assertTrue(t1.exists())
            content1 = t1.read_text(encoding="utf-8")
            self.assertIn("**Status:** todo", content1)
            self.assertIn("**Date:**", content1)
            self.assertIn("- [ ] `:model`", content1)
            self.assertIn("- [ ] `:ui`", content1)

            # Create second task in same parent
            t2 = new_task.create_task(root, "auth", "biometric-login")
            self.assertEqual(t2.name, "02-biometric-login-todo.md")


if __name__ == "__main__":
    unittest.main()
