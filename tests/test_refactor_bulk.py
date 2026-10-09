# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from scripts.refactor_bulk import plan_bulk_refactor, execute_bulk_refactor


def test_bulk_symbol_refactoring(tmp_path: Path):
    src_dir = tmp_path / "src" / "commonMain" / "kotlin"
    src_dir.mkdir(parents=True)
    file1 = src_dir / "EngineTypes.kt"
    file1.write_text(
        "package com.engine\n\n"
        "class LegacyShader\n"
        "class LegacyTexture\n"
        "class ShaderRegistry(val shader: LegacyShader, val texture: LegacyTexture)\n"
    )

    mappings = {
        "LegacyShader": "AslShader",
        "LegacyTexture": "GpuTexture",
    }

    plan = plan_bulk_refactor(
        project_root=tmp_path,
        mappings=mappings,
        is_package=False,
    )

    assert len(plan.affected_files) == 1

    execute_bulk_refactor(plan, dry_run=False)

    updated_content = file1.read_text(encoding="utf-8")
    assert "class AslShader" in updated_content
    assert "class GpuTexture" in updated_content
    assert "class ShaderRegistry(val shader: AslShader, val texture: GpuTexture)" in updated_content
    assert "LegacyShader" not in updated_content
    assert "LegacyTexture" not in updated_content


def test_bulk_symbol_refactoring_does_not_corrupt_string_literals(tmp_path: Path):
    src_dir = tmp_path / "src" / "commonMain" / "kotlin"
    src_dir.mkdir(parents=True)
    file1 = src_dir / "User.kt"
    file1.write_text(
        "package com.app\n\n"
        '@SerialName("LegacyShader")\n'
        "class LegacyShader {\n"
        '    fun log() = println("LegacyShader not found")\n'
        "}\n"
    )

    plan = plan_bulk_refactor(
        project_root=tmp_path,
        mappings={"LegacyShader": "AslShader"},
        is_package=False,
    )
    execute_bulk_refactor(plan, dry_run=False)

    updated_content = file1.read_text(encoding="utf-8")
    assert "class AslShader" in updated_content
    assert '@SerialName("LegacyShader")' in updated_content
    assert 'println("LegacyShader not found")' in updated_content


def test_bulk_package_refactoring(tmp_path: Path):
    src_dir = tmp_path / "src" / "commonMain" / "kotlin"
    src_dir.mkdir(parents=True)
    file1 = src_dir / "Imports.kt"
    file1.write_text(
        "package com.app\n\n"
        "import com.old.auth.User\n"
        "import com.old.render.Camera\n"
    )

    mappings = {
        "com.old.auth": "io.github.security",
        "com.old.render": "io.github.graphics",
    }

    plan = plan_bulk_refactor(
        project_root=tmp_path,
        mappings=mappings,
        is_package=True,
    )

    execute_bulk_refactor(plan, dry_run=False)

    updated_content = file1.read_text(encoding="utf-8")
    assert "import io.github.security.User" in updated_content
    assert "import io.github.graphics.Camera" in updated_content
    assert "com.old.auth" not in updated_content
    assert "com.old.render" not in updated_content
