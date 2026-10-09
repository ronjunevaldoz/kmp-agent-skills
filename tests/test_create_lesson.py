from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

create_lesson_scripts = load_module(
    "create_lesson",
    REPO_ROOT / "skills" / "kmp-lessons" / "scripts" / "create_lesson.py",
)

class CreateLessonTests(unittest.TestCase):
    def _run(self, root: Path, title: str, **kw) -> int:
        import argparse
        args = argparse.Namespace(
            skill=kw.get("skill", "kmp-mvi"),
            type=kw.get("type", "correction"),
            severity=kw.get("severity", "high"),
            title=title,
            followed=kw.get("followed"), broke=kw.get("broke"), correct=kw.get("correct"),
            evidence=kw.get("evidence"), proposed=kw.get("proposed"),
            root=root, date=kw.get("date", "2026-06-30"),
        )
        # Render + write the way main() does, without argparse/CLI.
        date = args.date
        lessons_dir = root / "docs" / "lessons"
        lessons_dir.mkdir(parents=True, exist_ok=True)
        path = create_lesson_scripts.unique_path(lessons_dir, date, create_lesson_scripts.slugify(title))
        path.write_text(create_lesson_scripts.render(args, date), encoding="utf-8")
        return path

    def test_each_call_creates_a_separate_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run(root, "Effect replayed on nav back")
            self._run(root, "No nested graph guidance", skill="kmp-navigation", type="gap", severity="medium")
            files = sorted((root / "docs" / "lessons").glob("*.md"))
            self.assertEqual(len(files), 2)

    def test_duplicate_title_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p1 = self._run(root, "Same title")
            p2 = self._run(root, "Same title")
            self.assertNotEqual(p1, p2)
            self.assertEqual(len(list((root / "docs" / "lessons").glob("*.md"))), 2)

    def test_file_has_required_frontmatter_and_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = self._run(root, "Effect replay", evidence="Foo.kt:10")
            text = p.read_text(encoding="utf-8")
            for token in ("skill:", "date:", "severity:", "type:",
                          "## What we followed", "## Correct pattern", "## Evidence"):
                self.assertIn(token, text)

    def test_slug_and_date_in_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = self._run(root, "Effect Replayed!! On Nav Back")
            self.assertEqual(p.name, "2026-06-30-effect-replayed-on-nav-back.md")


if __name__ == "__main__":
    unittest.main()
