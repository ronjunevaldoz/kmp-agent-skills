# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from scripts.refactor_rename_package import plan_package_rename, execute_package_rename


def test_refactor_rename_entire_package_tree(tmp_path: Path):
    # Setup multiple files in old package and subpackage
    pkg1_dir = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "com" / "old" / "auth"
    pkg1_dir.mkdir(parents=True)
    file1 = pkg1_dir / "User.kt"
    file1.write_text(
        "package com.old.auth\n\n"
        "/** Reference: [com.old.auth.User] */\n"
        "data class User(val id: String)\n"
    )

    pkg2_dir = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "com" / "old" / "auth" / "internal"
    pkg2_dir.mkdir(parents=True)
    file2 = pkg2_dir / "TokenStore.kt"
    file2.write_text(
        "package com.old.auth.internal\n\n"
        "class TokenStore\n"
    )

    # Setup consumer file
    consumer_dir = tmp_path / "feature" / "src" / "commonMain" / "kotlin" / "com" / "app"
    consumer_dir.mkdir(parents=True)
    consumer_file = consumer_dir / "App.kt"
    consumer_file.write_text(
        "package com.app\n\n"
        "import com.old.auth.User\n"
        "import com.old.auth.internal.TokenStore\n\n"
        "class App(val user: User, val tokens: TokenStore)\n"
    )

    # 1. Plan Package Rename
    plan = plan_package_rename(
        project_root=tmp_path,
        old_package="com.old.auth",
        new_package="io.github.new.security",
    )

    assert len(plan.moved_files) == 2
    assert len(plan.modified_files) == 3

    # 2. Dry run check
    execute_package_rename(plan, dry_run=True)
    assert file1.exists()
    assert file2.exists()

    # 3. Execute
    execute_package_rename(plan, dry_run=False)

    # Old files moved
    assert not file1.exists()
    assert not file2.exists()

    expected_file1 = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "io" / "github" / "new" / "security" / "User.kt"
    expected_file2 = tmp_path / "core" / "src" / "commonMain" / "kotlin" / "io" / "github" / "new" / "security" / "internal" / "TokenStore.kt"
    assert expected_file1.exists()
    assert expected_file2.exists()

    assert "package io.github.new.security" in expected_file1.read_text(encoding="utf-8")
    assert "[io.github.new.security.User]" in expected_file1.read_text(encoding="utf-8")
    assert "package io.github.new.security.internal" in expected_file2.read_text(encoding="utf-8")

    # Consumer imports updated
    consumer_text = consumer_file.read_text(encoding="utf-8")
    assert "import io.github.new.security.User" in consumer_text
    assert "import io.github.new.security.internal.TokenStore" in consumer_text
    assert "com.old.auth" not in consumer_text
