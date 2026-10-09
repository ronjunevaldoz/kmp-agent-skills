from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

governance_scripts = load_module(
    "governance_check",
    REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "governance_check.py",
)

class GovernanceCheckTests(unittest.TestCase):
    def _project(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / ".kmp-skills").write_text(
            '{"skills_repo": "ronjunevaldoz/kmp-agent-skills", "version": "1.25.11"}',
            encoding="utf-8",
        )
        ui_src = root / "feature" / "auth" / "ui" / "src" / "commonMain" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui"
        ui_src.mkdir(parents=True)
        (ui_src / "LoginContent.kt").write_text(
            "fun LoginContent() { Column { } }", encoding="utf-8"
        )
        (ui_src / "LoginContentPreview.kt").write_text(
            """package com.example.feature.auth.ui.previews

import androidx.compose.runtime.Composable

@MultiDevicePreview
@Composable
fun LoginContentPreview() { LoginContent() }
""",
            encoding="utf-8"
        )
        (ui_src.parent / "previews").mkdir(parents=True, exist_ok=True)
        (ui_src.parent / "previews" / "MultiDevicePreview.kt").write_text(
            """package com.example.feature.auth.ui.previews

import org.jetbrains.compose.ui.tooling.preview.Preview

@Preview(name = "Phone", widthDp = 360, heightDp = 640)
@Preview(name = "Tablet", widthDp = 673, heightDp = 841)
@Preview(name = "Desktop", widthDp = 1280, heightDp = 800)
annotation class MultiDevicePreview
""",
            encoding="utf-8"
        )
        common_test = root / "feature" / "auth" / "ui" / "src" / "commonTest" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui"
        common_test.mkdir(parents=True, exist_ok=True)
        (common_test / "LoginContentTest.kt").write_text(
            """package com.example.feature.auth.ui

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.runComposeUiTest
import kotlin.test.Test

class LoginContentTest {
    @OptIn(ExperimentalTestApi::class)
    @Test
    fun loginContent_displays() = runComposeUiTest {
        setContent { LoginContent() }
    }
}
""",
            encoding="utf-8"
        )
        jvm_previews = root / "feature" / "auth" / "ui" / "src" / "jvmTest" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui" / "previews"
        jvm_previews.mkdir(parents=True, exist_ok=True)
        (jvm_previews / "LoginContentScreenshotTest.kt").write_text(
            """package com.example.feature.auth.ui.previews

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.github.takahirom.roborazzi.captureRoboImage
import com.example.core.designsystem.theme.AppTheme
import kotlin.test.Test

class LoginContentScreenshotTest {
    @Test fun phone_light() {
        captureRoboImage("login_content_phone_light.png") {
            AppTheme {
                Box(modifier = Modifier.size(360.dp, 640.dp)) {}
            }
        }
    }

    @Test fun phone_dark() {
        captureRoboImage("login_content_phone_dark.png") {
            AppTheme(darkTheme = true) {
                Box(modifier = Modifier.size(360.dp, 640.dp)) {}
            }
        }
    }

    @Test fun tablet_light() {
        captureRoboImage("login_content_tablet_light.png") {
            AppTheme {
                Box(modifier = Modifier.size(673.dp, 841.dp)) {}
            }
        }
    }

    @Test fun tablet_dark() {
        captureRoboImage("login_content_tablet_dark.png") {
            AppTheme(darkTheme = true) {
                Box(modifier = Modifier.size(673.dp, 841.dp)) {}
            }
        }
    }

    @Test fun desktop_light() {
        captureRoboImage("login_content_desktop_light.png") {
            AppTheme {
                Box(modifier = Modifier.size(1280.dp, 800.dp)) {}
            }
        }
    }

    @Test fun desktop_dark() {
        captureRoboImage("login_content_desktop_dark.png") {
            AppTheme(darkTheme = true) {
                Box(modifier = Modifier.size(1280.dp, 800.dp)) {}
            }
        }
    }
}
""",
            encoding="utf-8"
        )
        return root

    def test_clean_project_returns_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            findings = (
                governance_scripts.run_scan_violations(root)
                + governance_scripts.run_audit_project(root)
            )
        self.assertEqual(findings, [])

    def test_hardcoded_color_is_high_severity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            (root / "feature" / "auth" / "ui" / "LoginContent.kt").write_text(
                "fun Foo() { Box(Modifier.background(Color(0xFFFF0000))) {} }",
                encoding="utf-8",
            )
            findings = governance_scripts.run_scan_violations(root)
        high = [f for f in findings if f["severity"] == "HIGH"]
        self.assertTrue(len(high) >= 1)

    def test_medium_finding_does_not_fail_on_high_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            ui = root / "feature" / "auth" / "ui" / "src" / "commonMain" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui"
            # layout inconsistency → warning → MEDIUM (audit_project does not flag this)
            (ui / "LoginContent.kt").write_text("fun LoginContent() { Column { } }", encoding="utf-8")
            (ui / "ProfileContent.kt").write_text("fun ProfileContent() { AppCard() { } }", encoding="utf-8")
            (ui / "ProfileContentPreview.kt").write_text(
                """package com.example.feature.auth.ui.previews

import androidx.compose.runtime.Composable

@MultiDevicePreview
@Composable
fun ProfileContentPreview() { ProfileContent() }
""",
                encoding="utf-8",
            )
            (ui.parent / "previews" / "MultiDevicePreview.kt").write_text(
                """package com.example.feature.auth.ui.previews

import org.jetbrains.compose.ui.tooling.preview.Preview

@Preview(name = "Phone", widthDp = 360, heightDp = 640)
@Preview(name = "Tablet", widthDp = 673, heightDp = 841)
@Preview(name = "Desktop", widthDp = 1280, heightDp = 800)
annotation class MultiDevicePreview
""",
                encoding="utf-8",
            )
            common_test = root / "feature" / "auth" / "ui" / "src" / "commonTest" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui"
            common_test.mkdir(parents=True, exist_ok=True)
            (common_test / "ProfileContentTest.kt").write_text(
                """package com.example.feature.auth.ui

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.runComposeUiTest
import kotlin.test.Test

class ProfileContentTest {
    @OptIn(ExperimentalTestApi::class)
    @Test
    fun profileContent_displays() = runComposeUiTest {
        setContent { ProfileContent() }
    }
}
""",
                encoding="utf-8",
            )
            jvm_previews = root / "feature" / "auth" / "ui" / "src" / "jvmTest" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui" / "previews"
            jvm_previews.mkdir(parents=True, exist_ok=True)
            (jvm_previews / "ProfileContentScreenshotTest.kt").write_text(
                """package com.example.feature.auth.ui.previews

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.github.takahirom.roborazzi.captureRoboImage
import com.example.core.designsystem.theme.AppTheme
import kotlin.test.Test

class ProfileContentScreenshotTest {
    @Test fun phone_light() {
        captureRoboImage("profile_content_phone_light.png") {
            AppTheme {
                Box(modifier = Modifier.size(360.dp, 640.dp)) {}
            }
        }
    }

    @Test fun phone_dark() {
        captureRoboImage("profile_content_phone_dark.png") {
            AppTheme(darkTheme = true) {
                Box(modifier = Modifier.size(360.dp, 640.dp)) {}
            }
        }
    }

    @Test fun tablet_light() {
        captureRoboImage("profile_content_tablet_light.png") {
            AppTheme {
                Box(modifier = Modifier.size(673.dp, 841.dp)) {}
            }
        }
    }

    @Test fun tablet_dark() {
        captureRoboImage("profile_content_tablet_dark.png") {
            AppTheme(darkTheme = true) {
                Box(modifier = Modifier.size(673.dp, 841.dp)) {}
            }
        }
    }

    @Test fun desktop_light() {
        captureRoboImage("profile_content_desktop_light.png") {
            AppTheme {
                Box(modifier = Modifier.size(1280.dp, 800.dp)) {}
            }
        }
    }

    @Test fun desktop_dark() {
        captureRoboImage("profile_content_desktop_dark.png") {
            AppTheme(darkTheme = true) {
                Box(modifier = Modifier.size(1280.dp, 800.dp)) {}
            }
        }
    }
}
""",
                encoding="utf-8",
            )
            findings = (
                governance_scripts.run_scan_violations(root)
                + governance_scripts.run_audit_project(root)
            )
        threshold = governance_scripts.SEVERITY_RANK["HIGH"]
        failing = [f for f in findings if governance_scripts.SEVERITY_RANK.get(f["severity"], 0) >= threshold]
        self.assertEqual(failing, [])

    def test_docs_hygiene_flags_oversized_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "architecture.md").write_text(
                "\n".join(f"line {i}" for i in range(200)), encoding="utf-8"
            )
            findings = governance_scripts.run_docs_hygiene(root)
        self.assertTrue(any(
            f["source"] == "docs_hygiene" and "architecture.md" in f["file"] for f in findings
        ))

    def test_docs_hygiene_clean_docs_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "architecture.md").write_text("Short doc.\n", encoding="utf-8")
            # linked from README so the orphaned-reference-doc check doesn't fire
            (root / "README.md").write_text("See [architecture.md](docs/architecture.md).\n", encoding="utf-8")
            findings = governance_scripts.run_docs_hygiene(root)
        self.assertEqual(findings, [])

    def test_docs_hygiene_is_medium_and_does_not_fail_high_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "architecture.md").write_text(
                "\n".join(f"line {i}" for i in range(200)), encoding="utf-8"
            )
            findings = governance_scripts.run_docs_hygiene(root)
        self.assertTrue(all(f["severity"] == "MEDIUM" for f in findings))
        threshold = governance_scripts.SEVERITY_RANK["HIGH"]
        failing = [f for f in findings if governance_scripts.SEVERITY_RANK.get(f["severity"], 0) >= threshold]
        self.assertEqual(failing, [])

    def test_reads_kmm_skills_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".kmp-skills").write_text(
                '{"skills_repo": "ronjunevaldoz/kmp-agent-skills", "version": "1.24.1"}',
                encoding="utf-8",
            )
            version = governance_scripts.read_skills_version(root)
        self.assertEqual(version, "1.24.1")

    def test_missing_kmm_skills_file_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            version = governance_scripts.read_skills_version(Path(tmp))
        self.assertIsNone(version)

    def test_missing_kmm_skills_file_fails_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            (root / ".kmp-skills").unlink()
            findings = governance_scripts.validate_skills_version_pin(root)
        self.assertEqual(findings[0]["type"], "missing_version_pin")
        self.assertEqual(findings[0]["severity"], "HIGH")

    def test_branch_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            (root / ".kmp-skills").write_text(
                '{"skills_repo": "ronjunevaldoz/kmp-agent-skills", "version": "main"}',
                encoding="utf-8",
            )
            findings = governance_scripts.validate_skills_version_pin(root)
        self.assertEqual(findings[0]["type"], "mutable_version_pin")
        self.assertEqual(findings[0]["severity"], "HIGH")

    def test_tag_version_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            (root / ".kmp-skills").write_text(
                '{"skills_repo": "ronjunevaldoz/kmp-agent-skills", "version": "v1.25.11"}',
                encoding="utf-8",
            )
            findings = governance_scripts.validate_skills_version_pin(root)
        self.assertEqual(findings, [])

    def test_cli_exit_0_on_clean_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            script = REPO_ROOT / "skills/kmp-audit/scripts/governance_check.py"
            result = subprocess.run(
                [sys.executable, str(script), str(root)],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 0)

    def test_cli_exit_1_on_unpinned_skills_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            (root / ".kmp-skills").write_text(
                '{"skills_repo": "ronjunevaldoz/kmp-agent-skills", "version": "main"}',
                encoding="utf-8",
            )
            script = REPO_ROOT / "skills/kmp-audit/scripts/governance_check.py"
            result = subprocess.run(
                [sys.executable, str(script), str(root)],
                capture_output=True,
                text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 1)

    def test_cli_exit_2_on_missing_root(self) -> None:
        script = REPO_ROOT / "skills/kmp-audit/scripts/governance_check.py"
        result = subprocess.run(
            [sys.executable, str(script), "/nonexistent/path/xyz"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_json_output_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp)
            script = REPO_ROOT / "skills/kmp-audit/scripts/governance_check.py"
            result = subprocess.run(
                [sys.executable, str(script), str(root), "--json"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIsInstance(parsed, list)


if __name__ == "__main__":
    unittest.main()
