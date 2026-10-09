from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

update_design_system_scripts = load_module(
    "update_design_system",
    REPO_ROOT / "skills" / "kmp-compose-design-system" / "scripts" / "update_design_system.py",
)

class UpdateDesignSystemTests(unittest.TestCase):
    """Tests for update_design_system.py — compare/diff logic."""

    _SKILL_MD_TEMPLATE = (
        "---\nname: test\n---\n\n"
        "### `components/AppFoo.kt`\n"
        "```kotlin\n"
        "fun AppFoo() {{ }}\n"
        "```\n"
        "\n"
        "### `components/AppBar.kt`\n"
        "```kotlin\n"
        "fun AppBar() {{ }}\n"
        "```\n"
    )

    def _write_skill_md(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    _SKILL_MD_WITH_PREVIEWS = (
        "---\nname: test\n---\n\n"
        "### `components/AppFoo.kt`\n"
        "```kotlin\n"
        "fun AppFoo() {{ }}\n"
        "```\n"
        "\n"
        "### `previews/AppFooPreview.kt`\n"
        "```kotlin\n"
        "@Preview\nfun AppFooPreview() {{ AppFoo() }}\n"
        "```\n"
    )

    def test_extract_reference_components_finds_all_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_md = Path(tmp) / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_TEMPLATE)
            refs = update_design_system_scripts.extract_reference_components(skill_md)
        # Keys are now relative paths
        self.assertIn("components/AppFoo.kt", refs)
        self.assertIn("components/AppBar.kt", refs)
        self.assertEqual(len(refs), 2)

    def test_extract_reference_components_body_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_md = Path(tmp) / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_TEMPLATE)
            refs = update_design_system_scripts.extract_reference_components(skill_md)
        self.assertIn("AppFoo", refs["components/AppFoo.kt"])

    def test_extract_reference_components_finds_preview_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_md = Path(tmp) / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_WITH_PREVIEWS)
            refs = update_design_system_scripts.extract_reference_components(skill_md)
        self.assertIn("components/AppFoo.kt", refs)
        self.assertIn("previews/AppFooPreview.kt", refs)
        self.assertEqual(len(refs), 2)

    def test_compare_status_missing_when_no_project_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_md = root / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_TEMPLATE)
            results = update_design_system_scripts.compare(root, skill_md)
        statuses = {r["file"]: r["status"] for r in results}
        self.assertEqual(statuses["components/AppFoo.kt"], "MISSING")
        self.assertEqual(statuses["components/AppBar.kt"], "MISSING")

    def test_compare_status_current_when_file_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_md = root / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_TEMPLATE)
            refs = update_design_system_scripts.extract_reference_components(skill_md)

            comp_dir = root / "core" / "designsystem" / "components"
            comp_dir.mkdir(parents=True)
            (comp_dir / "AppFoo.kt").write_text(refs["components/AppFoo.kt"], encoding="utf-8")

            results = update_design_system_scripts.compare(root, skill_md)
        foo = next(r for r in results if r["file"] == "components/AppFoo.kt")
        self.assertEqual(foo["status"], "CURRENT")

    def test_compare_status_modified_when_file_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_md = root / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_TEMPLATE)

            comp_dir = root / "core" / "designsystem" / "components"
            comp_dir.mkdir(parents=True)
            (comp_dir / "AppFoo.kt").write_text(
                "fun AppFoo() { /* project customisation */ }", encoding="utf-8"
            )

            results = update_design_system_scripts.compare(root, skill_md)
        foo = next(r for r in results if r["file"] == "components/AppFoo.kt")
        self.assertEqual(foo["status"], "MODIFIED")

    def test_compare_preview_status_current_when_file_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_md = root / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_WITH_PREVIEWS)
            refs = update_design_system_scripts.extract_reference_components(skill_md)

            comp_dir = root / "core" / "designsystem" / "components"
            comp_dir.mkdir(parents=True)
            (comp_dir / "AppFoo.kt").write_text(refs["components/AppFoo.kt"], encoding="utf-8")

            prev_dir = root / "core" / "designsystem" / "previews"
            prev_dir.mkdir(parents=True)
            (prev_dir / "AppFooPreview.kt").write_text(
                refs["previews/AppFooPreview.kt"], encoding="utf-8"
            )

            results = update_design_system_scripts.compare(root, skill_md)
        preview = next(r for r in results if r["file"] == "previews/AppFooPreview.kt")
        self.assertEqual(preview["status"], "CURRENT")

    def test_compare_preview_status_missing_when_no_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_md = root / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_WITH_PREVIEWS)
            results = update_design_system_scripts.compare(root, skill_md)
        preview = next(r for r in results if r["file"] == "previews/AppFooPreview.kt")
        self.assertEqual(preview["status"], "MISSING")

    def test_resolve_filename_normalises_component_name(self) -> None:
        self.assertEqual(
            update_design_system_scripts._resolve_filename("AppButton"),
            "components/AppButton.kt",
        )

    def test_resolve_filename_normalises_name_with_app_prefix(self) -> None:
        self.assertEqual(
            update_design_system_scripts._resolve_filename("Button"),
            "components/AppButton.kt",
        )

    def test_resolve_filename_passthrough_for_full_kt_path(self) -> None:
        self.assertEqual(
            update_design_system_scripts._resolve_filename("components/AppButton.kt"),
            "components/AppButton.kt",
        )

    def test_resolve_filename_maps_preview_to_previews_dir(self) -> None:
        self.assertEqual(
            update_design_system_scripts._resolve_filename("AppButtonPreview"),
            "previews/AppButtonPreview.kt",
        )

    def test_resolve_filename_maps_preview_kt_to_previews_dir(self) -> None:
        self.assertEqual(
            update_design_system_scripts._resolve_filename("AppButtonPreview.kt"),
            "previews/AppButtonPreview.kt",
        )

    def test_find_component_dir_returns_none_for_empty_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = update_design_system_scripts.find_component_dir(Path(tmp))
        self.assertIsNone(result)

    def test_find_component_dir_detects_components_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comp_dir = Path(tmp) / "core" / "designsystem" / "components"
            comp_dir.mkdir(parents=True)
            result = update_design_system_scripts.find_component_dir(Path(tmp))
        self.assertIsNotNone(result)
        # Returns parent of components/ (i.e. core/designsystem/) so rglob finds previews/ too
        self.assertTrue(str(result).endswith("designsystem"))

    def test_main_exit_2_when_skill_md_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rc = update_design_system_scripts.main.__wrapped__ if hasattr(
                update_design_system_scripts.main, "__wrapped__"
            ) else None
            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "skills" / "kmp-compose-design-system" / "scripts" / "update_design_system.py"),
                 tmp,
                 "--skill-root", tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 2)

    def test_main_exit_1_when_components_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_root = root / "fake_skills"
            skill_md_dir = skill_root / "skills" / "kmp-compose-design-system"
            skill_md_dir.mkdir(parents=True)
            (skill_md_dir / "SKILL.md").write_text(self._SKILL_MD_TEMPLATE, encoding="utf-8")
            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "skills" / "kmp-compose-design-system" / "scripts" / "update_design_system.py"),
                 str(root),
                 "--skill-root", str(skill_root)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 1)

    def test_main_exit_0_when_all_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_root = root / "fake_skills"
            skill_md_dir = skill_root / "skills" / "kmp-compose-design-system"
            skill_md_dir.mkdir(parents=True)
            skill_md = skill_md_dir / "SKILL.md"
            self._write_skill_md(skill_md, self._SKILL_MD_TEMPLATE)
            refs = update_design_system_scripts.extract_reference_components(skill_md)

            # refs keys are "components/AppFoo.kt" — write files into their subdirs
            base_dir = root / "core" / "designsystem"
            base_dir.mkdir(parents=True)
            for rel_path, code in refs.items():
                dest = base_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(code, encoding="utf-8")

            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "skills" / "kmp-compose-design-system" / "scripts" / "update_design_system.py"),
                 str(root),
                 "--skill-root", str(skill_root)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
