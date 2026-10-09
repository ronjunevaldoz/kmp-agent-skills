from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

rpc_scripts = load_module(
    "scaffold_kotlin_rpc",
    REPO_ROOT / "skills" / "kmp-kotlin-rpc" / "scripts" / "scaffold_kotlin_rpc.py",
)

class ScaffoldKotlinRpcTests(unittest.TestCase):
    def test_scaffold_kotlin_rpc_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            rpc_scripts.scaffold_kotlin_rpc(root, "com.example.app")

            expected = {
                "shared/rpc/GreetingService.kt",
                "shared/rpc/model/GreetingRequest.kt",
                "shared/rpc/model/GreetingResponse.kt",
                "server/rpc/GreetingRpcModule.kt",
                "client/rpc/GreetingRpcClient.kt",
            }
            self.assertTrue(expected.issubset({p.relative_to(root).as_posix() for p in root.rglob("*.kt")}))
            self.assertIn("package com.example.app.rpc", (root / "shared" / "rpc" / "GreetingService.kt").read_text(encoding="utf-8"))
            self.assertIn("package com.example.app.server.rpc", (root / "server" / "rpc" / "GreetingRpcModule.kt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
