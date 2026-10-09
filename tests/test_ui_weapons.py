# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from _helpers import REPO_ROOT, load_module_registered

# The copies that ship with the skill, which are the ones its docs tell people to run.
_SCRIPTS = REPO_ROOT / "skills" / "kmp-shadcn-compose" / "scripts"
_contrast = load_module_registered("theme_contrast_audit", _SCRIPTS / "theme_contrast_audit.py")
evaluate_contrast, hex_to_rgb, oklch_to_rgb = _contrast.evaluate_contrast, _contrast.hex_to_rgb, _contrast.oklch_to_rgb
audit_compose_performance = load_module_registered(
    "audit_compose_perf", _SCRIPTS / "audit_compose_perf.py").audit_compose_performance
scaffold_component_slice = load_module_registered(
    "scaffold_shadcn_component", _SCRIPTS / "scaffold_shadcn_component.py").scaffold_component_slice


def test_theme_contrast_audit_math():
    white = hex_to_rgb("#FFFFFF")
    black = hex_to_rgb("#000000")
    res = evaluate_contrast("White on Black", white, black)
    assert res["ratio"] >= 20.0
    assert res["aa_normal"] is True
    assert res["aaa"] is True


def test_compose_performance_linter(tmp_path: Path):
    components_dir = tmp_path / "awake" / "ui" / "components"
    components_dir.mkdir(parents=True)
    comp_file = components_dir / "BadButton.kt"
    comp_file.write_text(
        "package io.github.awake.ui.components\n\n"
        "import io.github.awake.core.color.Color\n\n"
        "fun BadButton() {\n"
        "    val c = Color.White\n"
        "}\n"
    )

    violations = audit_compose_performance(tmp_path)
    assert len(violations) >= 1
    assert violations[0].rule == "HARDCODED_COLOR_TOKEN"


def test_scaffold_shadcn_component(tmp_path: Path):
    scaffold_component_slice(
        project_root=tmp_path,
        name="Sheet",
        category_key="overlays",
        dry_run=False,
    )

    comp_file = tmp_path / "awake" / "ui" / "designsystem" / "src" / "commonMain" / "kotlin" / "io" / "github" / "ronjunevaldoz" / "awake" / "ui" / "designsystem" / "components" / "ShadcnSheet.kt"
    page_file = tmp_path / "samples" / "ui-showcase" / "src" / "commonMain" / "kotlin" / "io" / "github" / "ronjunevaldoz" / "awake" / "sample" / "uishowcase" / "ui" / "pages" / "overlays" / "SheetPage.kt"

    assert comp_file.exists()
    assert page_file.exists()
    assert "fun ShadcnSheet" in comp_file.read_text()
    assert "val SheetPage" in page_file.read_text()
