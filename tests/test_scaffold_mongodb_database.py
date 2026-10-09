from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

mongodb_scripts = load_module(
    "scaffold_mongodb_database",
    REPO_ROOT / "skills" / "kmp-mongodb-database" / "scripts" / "scaffold_mongodb_database.py",
)

class ScaffoldMongoDatabaseTests(unittest.TestCase):
    def test_scaffold_mongodb_database_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            mongodb_scripts.scaffold_mongodb_database(root, "com.example.server")

            expected = {
                "MongoClientFactory.kt",
                "di/DatabaseModule.kt",
                "user/data/UserDocument.kt",
                "user/repository/UserRepository.kt",
                "user/repository/UserRepositoryImpl.kt",
            }
            self.assertTrue(expected.issubset({p.relative_to(root).as_posix() for p in root.rglob("*.kt")}))
            self.assertIn("package com.example.server.database", (root / "MongoClientFactory.kt").read_text(encoding="utf-8"))
            self.assertIn("package com.example.server.user.repository", (root / "user" / "repository" / "UserRepository.kt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
