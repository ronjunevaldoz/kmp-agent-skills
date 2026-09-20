from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

expert_scripts = load_module(
    "validate_skill_map",
    REPO_ROOT / "skills" / "kmp-expert" / "scripts" / "validate_skill_map.py",
)

class ValidateSkillMapTests(unittest.TestCase):
    def test_validate_skill_map_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                """
                kmp-a
                kmp-b
                kmp-expert
                3 skills covering the stack.
                """.strip(),
                encoding="utf-8",
            )
            (root / "docs" / "reference").mkdir(parents=True)
            (root / "docs" / "reference" / "agentskills-io-standards.md").write_text(
                "3 skills verified.\n", encoding="utf-8",
            )
            skills_dir = root / "skills"
            for name in ("kmp-a", "kmp-b", "kmp-expert"):
                (skills_dir / name).mkdir(parents=True)
                (skills_dir / name / "SKILL.md").write_text(
                    "## The 3 Skills and What They Own\n"
                    "kmp-a\n"
                    "kmp-b\n"
                    "kmp-expert\n",
                    encoding="utf-8",
                )

            self.assertEqual(expert_scripts.validate_skill_map(root), [])

    def test_validate_skill_map_flags_stale_count_phrase_in_readme(self) -> None:
        # Reproduces the real bug: README.md said "68 skills" while the repo had 69 —
        # every individual skill *name* still appeared in README (a separate check),
        # so only a dedicated count-phrase check catches a stale summary line.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "kmp-a\nkmp-b\nkmp-expert\n2 skills covering the stack.\n",
                encoding="utf-8",
            )
            skills_dir = root / "skills"
            for name in ("kmp-a", "kmp-b", "kmp-expert"):
                (skills_dir / name).mkdir(parents=True)
                (skills_dir / name / "SKILL.md").write_text(
                    "## The 3 Skills and What They Own\nkmp-a\nkmp-b\nkmp-expert\n",
                    encoding="utf-8",
                )
            errors = expert_scripts.validate_skill_map(root)
            self.assertTrue(any("README.md is missing the current count phrase" in e for e in errors))

    def test_validate_skill_map_does_not_false_positive_on_unrelated_historical_count(self) -> None:
        # agentskills-io-standards.md legitimately mentions a different, historical
        # number (e.g. "the 22-skill backlog was resolved...") alongside the current
        # count — the check must not treat that unrelated number as needing to match.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "kmp-a\nkmp-b\nkmp-expert\n3 skills covering the stack.\n",
                encoding="utf-8",
            )
            (root / "docs" / "reference").mkdir(parents=True)
            (root / "docs" / "reference" / "agentskills-io-standards.md").write_text(
                "3 skills verified. The 22-skill backlog was resolved on 2026-08-04.\n",
                encoding="utf-8",
            )
            skills_dir = root / "skills"
            for name in ("kmp-a", "kmp-b", "kmp-expert"):
                (skills_dir / name).mkdir(parents=True)
                (skills_dir / name / "SKILL.md").write_text(
                    "## The 3 Skills and What They Own\nkmp-a\nkmp-b\nkmp-expert\n",
                    encoding="utf-8",
                )
            self.assertEqual(expert_scripts.validate_skill_map(root), [])

    def test_validate_skill_map_reports_missing_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("kmp-a", encoding="utf-8")
            skills_dir = root / "skills"
            (skills_dir / "kmp-a").mkdir(parents=True)
            (skills_dir / "kmp-a" / "SKILL.md").write_text(
                "## The 1 Skills and What They Own\nkmp-a\n",
                encoding="utf-8",
            )
            (skills_dir / "kmp-expert").mkdir(parents=True)
            (skills_dir / "kmp-expert" / "SKILL.md").write_text(
                "## The 1 Skills and What They Own\nkmp-a\n",
                encoding="utf-8",
            )
            errors = expert_scripts.validate_skill_map(root)
            self.assertTrue(any("declares 1 skills but repo has 2 skill folders" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
