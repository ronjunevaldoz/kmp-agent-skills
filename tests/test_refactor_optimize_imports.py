# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from scripts.refactor_optimize_imports import plan_optimize_imports, execute_optimize_imports


def test_optimize_imports_removes_unused(tmp_path: Path):
    src_dir = tmp_path / "src" / "commonMain" / "kotlin"
    src_dir.mkdir(parents=True)
    file1 = src_dir / "MyView.kt"
    file1.write_text(
        "package com.app\n\n"
        "import com.app.UsedClass\n"
        "import com.app.UnusedClass\n"
        "import com.app.AnotherUnused\n\n"
        "class MyView(val used: UsedClass)\n"
    )

    plan = plan_optimize_imports(tmp_path)
    assert plan.removed_count == 2
    assert len(plan.affected_files) == 1

    execute_optimize_imports(plan, dry_run=False)

    updated_text = file1.read_text(encoding="utf-8")
    assert "import com.app.UsedClass" in updated_text
    assert "import com.app.UnusedClass" not in updated_text
    assert "import com.app.AnotherUnused" not in updated_text


def test_optimize_imports_preserves_kdoc_and_wildcards(tmp_path: Path):
    src_dir = tmp_path / "src" / "commonMain" / "kotlin"
    src_dir.mkdir(parents=True)
    file1 = src_dir / "Service.kt"
    file1.write_text(
        "package com.app\n\n"
        "import com.wildcard.*\n"
        "import com.kdoc.DocumentedClass\n"
        "import com.unused.DeadClass\n\n"
        "/** See [DocumentedClass] for contract. */\n"
        "class Service\n"
    )

    plan = plan_optimize_imports(tmp_path)
    assert plan.removed_count == 1

    execute_optimize_imports(plan, dry_run=False)

    updated_text = file1.read_text(encoding="utf-8")
    assert "import com.wildcard.*" in updated_text
    assert "import com.kdoc.DocumentedClass" in updated_text
    assert "import com.unused.DeadClass" not in updated_text
