# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from scripts.refactor_move import plan_refactor, execute_refactor


def test_refactor_move_package_and_dry_run(tmp_path: Path):
    src_dir = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "com" / "oldpkg"
    src_dir.mkdir(parents=True)
    source_file = src_dir / "UserSession.kt"
    source_file.write_text(
        "package com.oldpkg\n\n"
        "/** Reference: [com.oldpkg.UserSession] */\n"
        "data class UserSession(val id: String)\n"
    )

    consumer_dir = tmp_path / "feature" / "src" / "commonMain" / "kotlin" / "com" / "app"
    consumer_dir.mkdir(parents=True)
    consumer_file = consumer_dir / "AppViewModel.kt"
    consumer_file.write_text(
        "package com.app\n\n"
        "import com.oldpkg.UserSession\n\n"
        "class AppViewModel(val session: UserSession)\n"
    )

    # 1. Dry Run test
    plan = plan_refactor(
        project_root=tmp_path,
        source_file=source_file,
        target_package="com.newpkg",
    )

    assert plan.old_package == "com.oldpkg"
    assert plan.new_package == "com.newpkg"
    assert plan.old_symbols == ["UserSession"]
    assert len(plan.affected_files) == 2

    execute_refactor(plan, dry_run=True)
    # File should still be at old location after dry run
    assert source_file.exists()

    # 2. Execution test
    execute_refactor(plan, dry_run=False)

    # Old file removed, new file created in correct package path
    assert not source_file.exists()
    expected_new_file = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "com" / "newpkg" / "UserSession.kt"
    assert expected_new_file.exists()
    assert "package com.newpkg" in expected_new_file.read_text(encoding="utf-8")
    assert "[com.newpkg.UserSession]" in expected_new_file.read_text(encoding="utf-8")

    # Consumer imports updated
    consumer_content = consumer_file.read_text(encoding="utf-8")
    assert "import com.newpkg.UserSession" in consumer_content
    assert "import com.oldpkg.UserSession" not in consumer_content


def test_refactor_rename_symbol(tmp_path: Path):
    src_dir = tmp_path / "src" / "commonMain" / "kotlin" / "com" / "pkg"
    src_dir.mkdir(parents=True)
    source_file = src_dir / "OldName.kt"
    source_file.write_text(
        "package com.pkg\n\n"
        "class OldName {\n"
        "    fun doSomething() = 42\n"
        "}\n"
    )

    plan = plan_refactor(
        project_root=tmp_path,
        source_file=source_file,
        target_package="com.pkg",
        rename_symbol="NewName",
    )

    execute_refactor(plan, dry_run=False)

    new_file = src_dir / "NewName.kt"
    assert new_file.exists()
    assert not source_file.exists()
    assert "class NewName" in new_file.read_text(encoding="utf-8")
