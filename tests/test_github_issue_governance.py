# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
Tests for kmp-github-issue-governance skill and payload validation scripts.
"""
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, load_module

SKILL_DIR = REPO_ROOT / "skills" / "kmp-github-issue-governance"
SCRIPTS_DIR = SKILL_DIR / "scripts"

validate_payload_module = load_module(
    "validate_issue_payload",
    SCRIPTS_DIR / "validate_issue_payload.py",
)


class TestValidateIssuePayload(unittest.TestCase):

    def test_check_escaped_newlines_detects_literal_escape(self) -> None:
        corrupt_text = "Audit refresh: still PARTIAL.\\n\\nThe freshly built Web/Wasm distribution..."
        errors = validate_payload_module.check_escaped_newlines(corrupt_text)
        self.assertTrue(len(errors) > 0)
        self.assertIn("literal '\\n'", errors[0])

    def test_check_escaped_newlines_passes_clean_multiline(self) -> None:
        clean_text = "Audit refresh: still PARTIAL.\n\nThe freshly built Web/Wasm distribution..."
        errors = validate_payload_module.check_escaped_newlines(clean_text)
        self.assertEqual(errors, [])

    def test_check_markdown_fences_detects_unclosed_block(self) -> None:
        bad_fence = "Here is some code:\n```kotlin\nval x = 1\n"
        errors = validate_payload_module.check_markdown_fences(bad_fence)
        self.assertTrue(any("Unmatched code block fences" in e for e in errors))

    def test_check_markdown_fences_detects_unclosed_inline_tick(self) -> None:
        bad_tick = "Fixed on `refactor/studio-authoring-boundaries branch without closing tick."
        errors = validate_payload_module.check_markdown_fences(bad_tick)
        self.assertTrue(any("Unmatched inline backticks" in e for e in errors))

    def test_check_markdown_fences_passes_balanced_markdown(self) -> None:
        clean = "Fixed on `refactor/studio` branch.\n\n```kotlin\nval x = `escaped`\n```\nAll good."
        errors = validate_payload_module.check_markdown_fences(clean)
        self.assertEqual(errors, [])

    def test_check_template_sections_task_passes_when_all_present(self) -> None:
        content = """# task: Isolate Game play session

## Parent Issue
Belongs to #39.

## Task Description
Separate Scene3D world from Game play runtime.

## Acceptance Criteria
- Desktop and Web pass.
"""
        errors = validate_payload_module.check_template_sections(content, "task")
        self.assertEqual(errors, [])

    def test_check_template_sections_task_fails_when_missing_section(self) -> None:
        content = """# task: Isolate Game play session

## Task Description
Missing parent and acceptance.
"""
        errors = validate_payload_module.check_template_sections(content, "task")
        self.assertTrue(len(errors) >= 2)
        self.assertTrue(any("Parent" in e for e in errors))
        self.assertTrue(any("Acceptance" in e for e in errors))

    def test_validate_payload_combined(self) -> None:
        valid_payload = """# feat: Epic (#39)

## Objective & Scope
Deliver full workflow.

## Planned Tracks
- [ ] Task 1

## Acceptance Criteria
All tests pass.
"""
        errors = validate_payload_module.validate_payload(valid_payload, "epic")
        self.assertEqual(errors, [])


class TestSkillMetadata(unittest.TestCase):

    def test_skill_files_exist(self) -> None:
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())
        self.assertTrue((SKILL_DIR / "references" / "epic-vs-subissue-matrix.md").is_file())
        self.assertTrue((SKILL_DIR / "references" / "shell-safe-gh-cli.md").is_file())
        self.assertTrue((SCRIPTS_DIR / "validate_issue_payload.py").is_file())
        self.assertTrue((SCRIPTS_DIR / "gh_sub_issue.py").is_file())

    def test_skill_frontmatter(self) -> None:
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: kmp-github-issue-governance", content)
        self.assertIn("keywords:", content)
        self.assertIn("sub-issue", content)
        self.assertIn("epic", content)


if __name__ == "__main__":
    unittest.main()
