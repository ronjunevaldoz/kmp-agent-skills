# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from scripts.refactor_rename import plan_rename, execute_rename


def test_refactor_rename_class_across_modules(tmp_path: Path):
    # Setup declaration file
    core_dir = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "com" / "math"
    core_dir.mkdir(parents=True)
    def_file = core_dir / "TransformMatrix.kt"
    def_file.write_text(
        "package com.math\n\n"
        "/** Reference: [TransformMatrix] */\n"
        "class TransformMatrix {\n"
        "    fun multiply(other: TransformMatrix): TransformMatrix = this\n"
        "}\n"
    )

    # Setup consumer file
    feature_dir = tmp_path / "feature" / "src" / "commonMain" / "kotlin" / "com" / "render"
    feature_dir.mkdir(parents=True)
    consumer_file = feature_dir / "Camera.kt"
    consumer_file.write_text(
        "package com.render\n\n"
        "import com.math.TransformMatrix\n\n"
        "class Camera(val matrix: TransformMatrix) {\n"
        "    val identity = TransformMatrix()\n"
        "}\n"
    )

    # 1. Plan Rename
    plan = plan_rename(
        project_root=tmp_path,
        old_symbol="TransformMatrix",
        new_symbol="Mat4",
        target_file=def_file,
    )

    assert plan.old_name == "TransformMatrix"
    assert plan.new_name == "Mat4"
    assert len(plan.affected_files) == 2
    assert plan.new_target_file == core_dir / "Mat4.kt"

    # 2. Dry Run
    execute_rename(plan, dry_run=True)
    assert def_file.exists()
    assert not (core_dir / "Mat4.kt").exists()

    # 3. Execution
    execute_rename(plan, dry_run=False)
    assert not def_file.exists()
    new_def_file = core_dir / "Mat4.kt"
    assert new_def_file.exists()

    # Check updated definition
    def_content = new_def_file.read_text(encoding="utf-8")
    assert "class Mat4" in def_content
    assert "fun multiply(other: Mat4): Mat4" in def_content
    assert "[Mat4]" in def_content
    assert "TransformMatrix" not in def_content

    # Check updated consumer
    consumer_content = consumer_file.read_text(encoding="utf-8")
    assert "import com.math.Mat4" in consumer_content
    assert "class Camera(val matrix: Mat4)" in consumer_content
    assert "val identity = Mat4()" in consumer_content
    assert "TransformMatrix" not in consumer_content


def test_refactor_rename_does_not_corrupt_string_literals(tmp_path: Path):
    # A @SerialName wire-format string, a log message, and a char literal must all
    # survive untouched — only real code identifiers get renamed.
    src_dir = tmp_path / "src" / "commonMain" / "kotlin" / "com" / "app"
    src_dir.mkdir(parents=True)
    def_file = src_dir / "User.kt"
    def_file.write_text(
        "package com.app\n\n"
        "@Serializable\n"
        'data class User(@SerialName("User") val name: String) {\n'
        '    fun log() = println("User not found")\n'
        "}\n"
    )

    plan = plan_rename(
        project_root=tmp_path,
        old_symbol="User",
        new_symbol="Account",
        target_file=def_file,
    )
    execute_rename(plan, dry_run=False)

    new_file = src_dir / "Account.kt"
    content = new_file.read_text(encoding="utf-8")
    assert "data class Account(" in content
    assert '@SerialName("User")' in content
    assert 'println("User not found")' in content
