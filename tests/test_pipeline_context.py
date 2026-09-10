from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

class PipelineContextFlagTests(unittest.TestCase):
    """KI-005 — krpc_established round-trip contract.

    These tests verify that the three files involved in the round-trip
    (pipeline-context.json, implementer.md, reviewer.md) all reference the flag.
    If any file is edited and the reference is removed, the test fails immediately
    rather than silently regressing to re-running the grep every session.
    """

    def _pipeline_context(self) -> dict:
        path = REPO_ROOT / ".agents" / "pipeline-context.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_pipeline_context_has_krpc_established_key(self) -> None:
        ctx = self._pipeline_context()
        self.assertIn("krpc_established", ctx, (
            "pipeline-context.json is missing the 'krpc_established' key. "
            "Add it back as false — it is set to true by the implementer after "
            "confirming kRPC is active."
        ))

    def test_pipeline_context_krpc_established_is_bool(self) -> None:
        ctx = self._pipeline_context()
        self.assertIsInstance(ctx.get("krpc_established"), bool, (
            "'krpc_established' must be a bool (true/false), not a string or null."
        ))

    def test_implementer_sets_krpc_established(self) -> None:
        text = (REPO_ROOT / "agents" / "implementer.md").read_text(encoding="utf-8")
        self.assertIn("krpc_established", text, (
            "agents/implementer.md no longer references 'krpc_established'. "
            "The implementer must set this flag to true in pipeline-context.json "
            "after confirming kRPC is active, so subsequent sessions skip the grep."
        ))

    def test_reviewer_reads_krpc_established(self) -> None:
        text = (REPO_ROOT / "agents" / "reviewer.md").read_text(encoding="utf-8")
        self.assertIn("krpc_established", text, (
            "agents/reviewer.md no longer references 'krpc_established'. "
            "The reviewer must read this flag before running the transport grep "
            "(Check 9) to avoid redundant work in sessions after the flag is set."
        ))


if __name__ == "__main__":
    unittest.main()
