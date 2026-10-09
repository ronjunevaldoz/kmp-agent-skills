from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

auth_service_scripts = load_module(
    "scaffold_auth_service",
    REPO_ROOT / "skills" / "kmp-ktor-auth-service" / "scripts" / "scaffold_auth_service.py",
)

class ScaffoldAuthServiceTests(unittest.TestCase):
    def test_scaffold_auth_service_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            auth_service_scripts.scaffold_auth_service(root, "com.example.server")

            expected = {
                "routes/AuthRoutes.kt",
                "service/AuthService.kt",
                "service/TokenService.kt",
                "model/AuthRequest.kt",
                "model/AuthResponse.kt",
                "model/AuthError.kt",
                "di/AuthModule.kt",
            }
            self.assertTrue(expected.issubset({p.relative_to(root).as_posix() for p in root.rglob("*.kt")}))
            self.assertIn("package com.example.server.auth.model", (root / "model" / "AuthRequest.kt").read_text(encoding="utf-8"))
            self.assertIn("package com.example.server.auth.di", (root / "di" / "AuthModule.kt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
