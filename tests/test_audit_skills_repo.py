from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

audit_repo_scripts = load_module(
    "audit_skills_repo",
    REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_skills_repo.py",
)

class AuditSkillsRepoTests(unittest.TestCase):
    def test_audit_skills_repo_flags_missing_freshness_and_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            skill_dir = root / "skills" / "example-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: Ktor example\n---\n\n## When to Use This Skill\n\nUses ktor client code.\n",
                encoding="utf-8",
            )
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("missing freshness guidance" in finding for finding in findings))

    def test_audit_skills_repo_flags_assets_dir_without_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            skill_dir = root / "skills" / "example-skill"
            (skill_dir / "assets").mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: example\n---\n\n## When to Use This Skill\n\nExample.\n",
                encoding="utf-8",
            )
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("has assets/ but no assets guidance" in f for f in findings))

    def test_audit_skills_repo_does_not_flag_assets_dir_with_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            skill_dir = root / "skills" / "example-skill"
            (skill_dir / "assets").mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: example\n---\n\n"
                "## When to Use This Skill\n\nExample.\n\n"
                "## Assets\n\nCopy `assets/logo.png` when scaffolding.\n",
                encoding="utf-8",
            )
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertFalse(any("has assets/ but no assets guidance" in f for f in findings))

    def test_audit_skills_repo_flags_missing_all_targets_branch_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            scaffold_dir = root / "skills" / "kmp-feature-scaffold"
            scaffold_dir.mkdir(parents=True)
            (scaffold_dir / "SKILL.md").write_text(
                "---\nname: kmp-feature-scaffold\ndescription: scaffold\n---\n\n## When to Use This Skill\n\nall-frontends-shared\n",
                encoding="utf-8",
            )
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("missing all-targets branch guidance" in finding for finding in findings))

    def test_audit_skills_repo_flags_missing_build_logic_toml_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            scaffold_dir = root / "skills" / "kmp-feature-scaffold"
            scaffold_dir.mkdir(parents=True)
            (scaffold_dir / "SKILL.md").write_text(
                "---\nname: kmp-feature-scaffold\ndescription: scaffold\n---\n\n## When to Use This Skill\n\nbuild-logic only\n",
                encoding="utf-8",
            )
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("missing build-logic and libs.versions.toml guidance" in finding for finding in findings))


    def test_audit_skills_repo_flags_all_missing_required_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            skill_dir = root / "skills" / "example-skill"
            skill_dir.mkdir(parents=True)
            # SKILL.md with none of the 4 required markers
            (skill_dir / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: example\n---\n\nSome content.\n",
                encoding="utf-8",
            )

            findings = audit_repo_scripts.audit_skills_repo(root)
            marker_finding = next((f for f in findings if "missing markers" in f), None)

            self.assertIsNotNone(marker_finding, "expected a 'missing markers' finding")
            self.assertIn("## When to Use This Skill", marker_finding)
            self.assertIn("Trigger keywords:", marker_finding)
            self.assertIn("metadata:", marker_finding)
            self.assertIn("last-updated:", marker_finding)

    def test_audit_skills_repo_no_marker_finding_when_all_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            skill_dir = root / "skills" / "example-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: example\nmetadata:\n  last-updated: '2026-06-18'\n---\n\n"
                "## When to Use This Skill\n\n**Trigger keywords:** example.\n\n## Changelog\n\n| Date | Change |\n|---|---|\n| 2026-06-18 | Initial release. |\n",
                encoding="utf-8",
            )

            findings = audit_repo_scripts.audit_skills_repo(root)

            self.assertFalse(any("missing markers" in f for f in findings))


    # ── Design-system content checks ────────────────────────────────────────────

    def _make_ds_skill(self, root: Path, name: str, content: str) -> None:
        skill_dir = root / "skills" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

    _DS_GOOD_CONTENT = (
        "## When to Use This Skill\n\n**Trigger keywords:** design system.\n\nmetadata:\n"
        "  last-updated: '2026-06-22'\n\n"
        "OptIn(ExperimentalStylesApi\n"
        "fun AppButton(\nfun AppBadge(\nfun AppCard(\nfun AppChip(\nfun AppTextField(\nfun AppText(\n"
        "## Component Previews\n\n### `previews/AppButtonPreview.kt`\n```kotlin\n// preview\n```\n\n"
        "## Changelog\n\n| Date | Change |\n|---|---|\n| 2026-06-22 | v1. |\n"
    )

    def test_ds_flags_missing_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            # AppTextField omitted
            content = self._DS_GOOD_CONTENT.replace("fun AppTextField(\n", "")
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("fun AppTextField" in f for f in findings))

    def test_ds_flags_textstyle_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            content = self._DS_GOOD_CONTENT + "enum class TextStyle {\n  BodyMedium\n}\n"
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("enum class TextStyle" in f for f in findings))

    def test_ds_flags_missing_optins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            content = self._DS_GOOD_CONTENT.replace("OptIn(ExperimentalStylesApi\n", "ExperimentalStylesApi\n")
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("ExperimentalStylesApi" in f and "@OptIn" in f for f in findings))

    def test_ds_flags_static_apptheme_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            content = self._DS_GOOD_CONTENT + "padding(AppTheme.spacing.lg)\n"
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("AppTheme" in f and "static" in f for f in findings))

    def test_ds_flags_hardcoded_dp_in_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            content = self._DS_GOOD_CONTENT + "override val contentPadding = 24.dp\n"
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("override val" in f and "N.dp" in f for f in findings))

    def test_ds_exempts_component_dimension_dp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            # `override val dp = 24.dp` is an IconSize/AvatarSize enum — exempt
            content = self._DS_GOOD_CONTENT + "override val dp = 24.dp\n"
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertFalse(any("override val" in f and "N.dp" in f for f in findings))

    def test_ds_clean_passes_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            self._make_ds_skill(root, "kmp-compose-design-system", self._DS_GOOD_CONTENT)
            findings = audit_repo_scripts.audit_skills_repo(root)
            ds_findings = [f for f in findings if "design-system" in f]
            self.assertEqual([], ds_findings)

    def test_ds_flags_missing_component_previews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# r\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            content = self._DS_GOOD_CONTENT.replace(
                "## Component Previews\n\n### `previews/AppButtonPreview.kt`\n```kotlin\n// preview\n```\n\n",
                "",
            )
            self._make_ds_skill(root, "kmp-compose-design-system", content)
            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("Component Previews" in f for f in findings))

    # ── Detekt rules module structure ────────────────────────────────────────────

    def test_detekt_rules_directory_exists(self) -> None:
        """detekt-rules/ directory must exist in the design-system skill."""
        detekt_dir = (
            REPO_ROOT / "skills" / "kmp-compose-design-system" / "detekt-rules"
        )
        self.assertTrue(detekt_dir.is_dir(), "detekt-rules/ directory missing")

    def test_detekt_rules_contains_all_rule_files(self) -> None:
        rules_dir = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "kotlin"
            / "GROUP_ID" / "designsystem" / "detekt"
        )
        expected = [
            "DesignSystemRuleSetProvider.kt",
            "HardcodedColorRule.kt",
            "HardcodedDpRule.kt",
            "MaterialThemeUsageRule.kt",
            "DirectTextStyleRule.kt",
            "NestedContainerRule.kt",
            "ComponentRegistryRule.kt",
            "ImportBoundaryRule.kt",
            "RedundantScreenTitleRule.kt",
            "HardcodedGridColumnsRule.kt",
        ]
        for fname in expected:
            self.assertTrue((rules_dir / fname).exists(), f"Missing rule file: {fname}")

    def test_detekt_rules_build_gradle_exists(self) -> None:
        build_file = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "build.gradle.kts"
        )
        self.assertTrue(build_file.exists())
        content = build_file.read_text()
        self.assertIn("detekt-api", content)

    def test_detekt_rules_config_exists(self) -> None:
        config_file = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "config" / "detekt-design-system.yml"
        )
        self.assertTrue(config_file.exists())
        content = config_file.read_text()
        for rule in ("HardcodedColor", "HardcodedDp", "MaterialThemeUsage",
                     "DirectTextStyle", "NestedContainer",
                     "ComponentRegistryRule", "ImportBoundaryRule",
                     "RedundantScreenTitleRule", "HardcodedGridColumnsRule"):
            self.assertIn(rule, content, f"Config missing rule: {rule}")

    def test_detekt_rules_service_loader_file_exists(self) -> None:
        svc_file = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "resources"
            / "META-INF" / "services"
            / "io.gitlab.arturbosch.detekt.api.RuleSetProvider"
        )
        self.assertTrue(svc_file.exists())
        self.assertIn("DesignSystemRuleSetProvider", svc_file.read_text())

    def test_detekt_rule_set_provider_has_all_9_rules(self) -> None:
        provider_kt = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "kotlin"
            / "GROUP_ID" / "designsystem" / "detekt"
            / "DesignSystemRuleSetProvider.kt"
        )
        content = provider_kt.read_text()
        for rule in ("HardcodedColorRule", "HardcodedDpRule", "MaterialThemeUsageRule",
                     "DirectTextStyleRule", "NestedContainerRule",
                     "ComponentRegistryRule", "ImportBoundaryRule",
                     "RedundantScreenTitleRule", "HardcodedGridColumnsRule"):
            self.assertIn(rule, content, f"RuleSetProvider missing: {rule}")

    def test_redundant_screen_title_rule_exists(self) -> None:
        rule_kt = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "kotlin"
            / "GROUP_ID" / "designsystem" / "detekt"
            / "RedundantScreenTitleRule.kt"
        )
        content = rule_kt.read_text()
        self.assertIn("RedundantScreenTitle", content)
        self.assertIn("KtTreeVisitorVoid", content)
        self.assertIn("AppTopAppBar", content)

    def test_hardcoded_grid_columns_rule_exists(self) -> None:
        rule_kt = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "kotlin"
            / "GROUP_ID" / "designsystem" / "detekt"
            / "HardcodedGridColumnsRule.kt"
        )
        content = rule_kt.read_text()
        self.assertIn("HardcodedGridColumns", content)
        self.assertIn("GridCells", content)
        self.assertIn("Adaptive", content)

    def test_component_registry_rule_uses_configurable_prefix(self) -> None:
        rule_kt = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "kotlin"
            / "GROUP_ID" / "designsystem" / "detekt"
            / "ComponentRegistryRule.kt"
        )
        content = rule_kt.read_text()
        self.assertIn("componentPrefix", content)
        self.assertIn("valueOrDefault", content)

    def test_import_boundary_rule_scoped_to_feature_ui(self) -> None:
        rule_kt = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "detekt-rules" / "src" / "main" / "kotlin"
            / "GROUP_ID" / "designsystem" / "detekt"
            / "ImportBoundaryRule.kt"
        )
        content = rule_kt.read_text()
        self.assertIn("/feature/", content)
        self.assertIn("/ui/", content)

    # ── New commands exist ────────────────────────────────────────────────────────

    def test_design_system_template_exists(self) -> None:
        template = (
            REPO_ROOT / "skills" / "kmp-compose-design-system"
            / "references" / "design-system-template.md"
        )
        self.assertTrue(template.exists(), "design-system-template.md missing from references/")
        content = template.read_text()
        for section in ("PROJECT_NAME", "GROUP_ID", "COMPONENT_PREFIX",
                        "Color palette", "Typography", "Spacing scale",
                        "Component Inventory", "Ownership Model",
                        "Detekt Rules", "Multi-Device Preview", "Design Audit Log"):
            self.assertIn(section, content, f"Template missing section: {section}")

    def test_record_design_baselines_command_exists(self) -> None:
        cmd = REPO_ROOT / "commands" / "kmp-record-design-baselines.md"
        self.assertTrue(cmd.exists())
        content = cmd.read_text()
        self.assertIn("roborazzi.record=true", content)
        self.assertIn("roborazzi.verify=true", content)

    def test_audit_design_visual_command_exists(self) -> None:
        cmd = REPO_ROOT / "commands" / "kmp-audit-design-visual.md"
        self.assertTrue(cmd.exists())
        content = cmd.read_text()
        self.assertIn("snapshots", content)
        self.assertIn("vision", content.lower())

    def test_fix_design_references_detekt_as_primary(self) -> None:
        cmd = REPO_ROOT / "commands" / "kmp-fix-design.md"
        content = cmd.read_text()
        self.assertIn("detekt", content)
        self.assertIn("detekt-design-system.yml", content)

    # ── Naming conventions ───────────────────────────────────────────────────────

    def test_naming_flags_uppercase_file_in_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            cmd_dir = root / "commands"
            cmd_dir.mkdir()
            (cmd_dir / "NewFeature.md").write_text("# cmd\n", encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("naming" in f and "NewFeature.md" in f for f in findings))

    def test_naming_flags_lowercase_root_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "changelog.md").write_text("# log\n", encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any("naming" in f and "changelog.md" in f for f in findings))

    def test_naming_clean_on_correct_conventions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "PLAN.md").write_text("# plan\n", encoding="utf-8")
            (root / "skills").mkdir()
            cmd_dir = root / "commands"
            cmd_dir.mkdir()
            (cmd_dir / "new-feature.md").write_text("# cmd\n", encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertFalse(any("naming" in f for f in findings))

    # ── Doc lifecycle: stale Task-kind docs at root ──────────────────────────────

    def test_flags_task_kind_doc_at_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "AUDIT_REPORT.md").write_text("# audit\n", encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any(
                "docs-hygiene" in f and "AUDIT_REPORT.md" in f and "docs/tasks/" in f
                for f in findings
            ))

    def test_permanent_root_docs_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            for name in (
                "AGENTS", "CHANGELOG", "CLAUDE", "CONTRIBUTING", "FUNDING",
                "GETTING_STARTED", "INSTALL", "KNOWN_ISSUES", "PLAN", "RELEASING",
            ):
                (root / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertFalse(any("docs-hygiene" in f for f in findings))

    def test_flags_oversized_root_doc(self) -> None:
        # _check_docs_hygiene's 150-line limit only ever scanned docs/ — every
        # _PERMANENT_ROOT_DOCS file sits one directory above that and was invisible to
        # any size check. Real bug: INSTALL.md grew to 609 lines unnoticed.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "INSTALL.md").write_text("# install\n" + "line\n" * 501, encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertTrue(any(
                "docs-hygiene" in f and "INSTALL.md" in f and "500" in f
                for f in findings
            ))

    def test_does_not_flag_root_doc_under_the_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "INSTALL.md").write_text("# install\n" + "line\n" * 100, encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertFalse(any("INSTALL.md" in f and "docs-hygiene" in f for f in findings))

    def test_changelog_is_exempt_from_the_root_doc_size_limit(self) -> None:
        # CHANGELOG.md is auto-generated and append-only by design (release.py prepends
        # a section per release) — flagging it as bloated would be a permanent false
        # positive, not a real finding to act on.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# repo\n\nStart here\n\nRoadmap\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "CHANGELOG.md").write_text("# changelog\n" + "line\n" * 3000, encoding="utf-8")

            findings = audit_repo_scripts.audit_skills_repo(root)
            self.assertFalse(any("CHANGELOG.md" in f for f in findings))


class DocsHygieneNamingTests(unittest.TestCase):
    def test_flags_screaming_case_filename_in_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "MVP_PLAN.md").write_text("# plan\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "MVP_PLAN.md" in f and "kebab-case" in f and "mvp-plan.md" in f
                for f in findings
            ))

    def test_flags_snake_case_filename_in_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "auth_flow_internals.md").write_text("# auth\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "auth_flow_internals.md" in f and "auth-flow-internals.md" in f
                for f in findings
            ))

    def test_does_not_flag_kebab_case_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "auth-flow-internals.md").write_text("# auth\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("kebab-case" in f for f in findings))


class TaskFileConventionTests(unittest.TestCase):
    """docs/tasks/<parent>/<NN>-<slug>-<status>.md — status lives in the filename,
    the date lives inside the content instead of a filename prefix.
    """

    def _write_task(self, root: Path, parent: str, name: str, body: str) -> Path:
        task_dir = root / "docs" / "tasks" / parent
        task_dir.mkdir(parents=True, exist_ok=True)
        path = task_dir / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_valid_task_file_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app", "01-add-auth-doing.md",
                "# Add auth\n\n**Date:** 2026-08-22\n\nBody.\n",
            )
            (root / "docs" / "tasks.md").write_text(
                "# Tasks\n\n| Task | Status | Parent |\n|---|---|---|\n"
                "| [01-add-auth](tasks/todo-app/01-add-auth-doing.md) | doing | todo-app |\n",
                encoding="utf-8",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("task" in f.lower() or "01-add-auth" in f for f in findings))

    def test_flags_filename_not_matching_convention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app", "2026-08-22-add-auth.md",
                "**Date:** 2026-08-22\n",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "2026-08-22-add-auth.md" in f and "does not match" in f for f in findings
            ))

    def test_flags_done_file_still_in_active_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app", "01-add-auth-done.md",
                "# Add auth\n\n**Date:** 2026-08-22\n",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "01-add-auth-done.md" in f and "archive" in f for f in findings
            ))

    def test_does_not_flag_done_file_inside_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app/archive", "01-add-auth-done.md",
                "# Add auth\n\n**Date:** 2026-08-22\n",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("01-add-auth-done.md" in f for f in findings))

    def test_does_not_flag_historical_tasks_in_archive_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Direct docs/tasks/archive directory
            self._write_task(
                root, "archive", "2026-08-23-vendor-components.md",
                "# Historical\n\nNo date header needed in archive.\n",
            )
            # Sub-archive docs/tasks/<parent>/archive directory
            self._write_task(
                root, "feature-x/archive", "2026-08-20-old-plan.md",
                "# Old plan\n",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("does not match <NN>-<slug>-<status>.md" in f for f in findings))
            self.assertFalse(any("missing a **Date:**" in f for f in findings))
            self.assertFalse(any("not indexed in docs/tasks.md" in f for f in findings))

    def test_flags_missing_date_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app", "01-add-auth-todo.md",
                "# Add auth\n\nNo date here.\n",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "01-add-auth-todo.md" in f and "Date" in f for f in findings
            ))

    def test_flags_loose_file_directly_in_tasks_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks_dir = root / "docs" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "01-add-auth-todo.md").write_text("**Date:** 2026-08-22\n", encoding="utf-8")
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "sits directly in docs/tasks/" in f for f in findings
            ))

    def test_flags_active_task_not_indexed_in_tasks_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app", "01-add-auth-doing.md",
                "# Add auth\n\n**Date:** 2026-08-22\n",
            )
            (root / "docs" / "tasks.md").write_text("# Tasks\n\nNothing here yet.\n", encoding="utf-8")
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "01-add-auth-doing.md" in f and "not indexed in docs/tasks.md" in f
                for f in findings
            ))

    def test_does_not_flag_task_indexed_in_tasks_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app", "01-add-auth-doing.md",
                "# Add auth\n\n**Date:** 2026-08-22\n",
            )
            (root / "docs" / "tasks.md").write_text(
                "# Tasks\n\n| Task | Status | Parent |\n|---|---|---|\n"
                "| [01-add-auth](tasks/todo-app/01-add-auth-doing.md) | doing | todo-app |\n",
                encoding="utf-8",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("not indexed in docs/tasks.md" in f for f in findings))

    def test_does_not_flag_archived_task_for_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_task(
                root, "todo-app/archive", "01-add-auth-done.md",
                "# Add auth\n\n**Date:** 2026-08-22\n",
            )
            (root / "docs" / "tasks.md").write_text("# Tasks\n\nNothing here yet.\n", encoding="utf-8")
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("not indexed in docs/tasks.md" in f for f in findings))


class DecisionRecordConventionTests(unittest.TestCase):
    """docs/decisions/<NNNN>-<slug>.md — one ADR per file, Status readable without
    opening it, verified against the real Nygard ADR pattern.
    """

    def test_valid_decision_record_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs" / "decisions"
            decisions_dir.mkdir(parents=True)
            (decisions_dir / "0001-use-sqldelight.md").write_text(
                "# 0001. Use SQLDelight\n\n**Status:** Accepted\n\n## Context\n\nWhy.\n",
                encoding="utf-8",
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("0001-use-sqldelight.md" in f for f in findings))

    def test_flags_filename_not_matching_convention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs" / "decisions"
            decisions_dir.mkdir(parents=True)
            (decisions_dir / "use-sqldelight.md").write_text(
                "**Status:** Accepted\n", encoding="utf-8"
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "use-sqldelight.md" in f and "does not match" in f for f in findings
            ))

    def test_flags_missing_status_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs" / "decisions"
            decisions_dir.mkdir(parents=True)
            (decisions_dir / "0001-use-sqldelight.md").write_text(
                "# 0001. Use SQLDelight\n\nNo status here.\n", encoding="utf-8"
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any(
                "0001-use-sqldelight.md" in f and "Status" in f for f in findings
            ))

    def test_accepts_superseded_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs" / "decisions"
            decisions_dir.mkdir(parents=True)
            (decisions_dir / "0001-use-sqldelight.md").write_text(
                "**Status:** Superseded by ADR-0002\n", encoding="utf-8"
            )
            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any(
                "0001-use-sqldelight.md" in f and "Status" in f for f in findings
            ))


class OrphanedReferenceDocTests(unittest.TestCase):
    """docs-hygiene.md already tells a human to grep for inbound links before
    deleting a reference doc — this automates that grep as a review nudge.
    """

    def test_flags_reference_doc_with_no_inbound_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref_dir = root / "docs" / "reference"
            ref_dir.mkdir(parents=True)
            (ref_dir / "orphaned-doc.md").write_text("# Orphaned\n\nNothing links here.\n", encoding="utf-8")
            (root / "README.md").write_text("# Test project\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_orphaned_reference_docs(root, findings)
            self.assertTrue(any("orphaned-doc.md" in f and "no inbound links" in f for f in findings))

    def test_does_not_flag_linked_reference_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref_dir = root / "docs" / "reference"
            ref_dir.mkdir(parents=True)
            (ref_dir / "linked-doc.md").write_text("# Linked\n\nReal content.\n", encoding="utf-8")
            (root / "README.md").write_text(
                "# Test project\n\nSee [linked-doc.md](docs/reference/linked-doc.md) for details.\n",
                encoding="utf-8",
            )

            findings: list[str] = []
            audit_repo_scripts._check_orphaned_reference_docs(root, findings)
            self.assertFalse(any("linked-doc.md" in f for f in findings))

    def test_does_not_flag_when_no_docs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test project\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_orphaned_reference_docs(root, findings)
            self.assertEqual(findings, [])


class ChangelogUnreleasedBacklogTests(unittest.TestCase):
    """git-cliff only flushes [Unreleased] into a dated section on an actual
    `--tag` release run — a project that never releases silently accumulates
    entries there forever. This check catches that case without depending on git.
    """

    def test_flags_backlog_over_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entries = "\n".join(f"- feat: thing {i}" for i in range(1, 26))
            (root / "CHANGELOG.md").write_text(
                f"# Changelog\n\n## [Unreleased]\n\n{entries}\n\n## [v1.0.0] - 2026-01-01\n- initial\n",
                encoding="utf-8",
            )

            findings: list[str] = []
            audit_repo_scripts._check_changelog_unreleased_backlog(root, findings)
            self.assertTrue(any("[Unreleased]" in f and "25 entries" in f for f in findings))

    def test_does_not_flag_backlog_under_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n- feat: one thing\n\n## [v1.0.0] - 2026-01-01\n- initial\n",
                encoding="utf-8",
            )

            findings: list[str] = []
            audit_repo_scripts._check_changelog_unreleased_backlog(root, findings)
            self.assertEqual(findings, [])

    def test_does_not_flag_when_no_unreleased_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## [v1.0.0] - 2026-01-01\n- initial\n",
                encoding="utf-8",
            )

            findings: list[str] = []
            audit_repo_scripts._check_changelog_unreleased_backlog(root, findings)
            self.assertEqual(findings, [])

    def test_does_not_flag_when_no_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test project\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_changelog_unreleased_backlog(root, findings)
            self.assertEqual(findings, [])


class DocsHygieneTopologyAndNonDocTests(unittest.TestCase):
    """Verify canonical docs/ subdirectories and recursive non-doc / asset detection."""

    def test_flags_non_canonical_top_level_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            for rogue in ("plans", "handoffs", "benchmarks", "layout-system"):
                (docs / rogue).mkdir(parents=True)
                (docs / rogue / "note.md").write_text("# Note\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            for rogue in ("plans", "handoffs", "benchmarks", "layout-system"):
                self.assertTrue(any(f"docs/{rogue}/ is not a canonical docs subdirectory" in f for f in findings))

    def test_allows_canonical_top_level_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            for canonical in ("reference", "tasks", "decisions", "lessons", "bugs", "mvp", "archive", "audits", "assets", "images"):
                (docs / canonical).mkdir(parents=True)

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("is not a canonical docs subdirectory" in f for f in findings))

    def test_flags_nested_non_doc_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            (docs / "reference" / "fixtures").mkdir(parents=True)
            (docs / "reference" / "fixtures" / "data.json").write_text("{}", encoding="utf-8")
            (docs / "reference" / "sub").mkdir(parents=True)
            (docs / "reference" / "sub" / "script.py").write_text("print(1)\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any("data.json is a non-doc file inside docs/" in f for f in findings))
            self.assertTrue(any("script.py is a non-doc file inside docs/" in f for f in findings))

    def test_flags_image_assets_outside_assets_or_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            (docs / "reference" / "previews").mkdir(parents=True)
            (docs / "reference" / "previews" / "button.png").write_bytes(b"\x89PNG\r\n\x1a\n")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertTrue(any("button.png is an asset file outside docs/assets/ or docs/images/" in f for f in findings))

    def test_allows_image_assets_in_assets_or_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            (docs / "assets" / "diagrams").mkdir(parents=True)
            (docs / "assets" / "diagrams" / "arch.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (docs / "images").mkdir(parents=True)
            (docs / "images" / "logo.svg").write_text("<svg></svg>", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("is an asset file outside" in f for f in findings))
            self.assertFalse(any("is a non-doc file" in f for f in findings))

    def test_does_not_flag_non_docs_in_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            (docs / "archive" / "old-run").mkdir(parents=True)
            (docs / "archive" / "old-run" / "dump.json").write_text("{}", encoding="utf-8")
            (docs / "tasks" / "archive").mkdir(parents=True)
            (docs / "tasks" / "archive" / "result.csv").write_text("a,b\n", encoding="utf-8")

            findings: list[str] = []
            audit_repo_scripts._check_docs_hygiene(root, findings)
            self.assertFalse(any("dump.json" in f for f in findings))
            self.assertFalse(any("result.csv" in f for f in findings))


if __name__ == "__main__":
    unittest.main()
