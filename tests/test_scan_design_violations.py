from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

scan_design_violations_scripts = load_module(
    "scan_design_violations",
    REPO_ROOT / "skills" / "kmp-compose-design-system" / "scripts" / "scan_design_violations.py",
)
scaffold_preview_coverage_scripts = load_module(
    "scaffold_preview_coverage",
    REPO_ROOT / "skills" / "kmp-compose-design-system" / "scripts" / "scaffold_preview_coverage.py",
)

class ScanDesignViolationsTests(unittest.TestCase):
    """Tests for scan_design_violations.py."""

    def _write_kt(self, tmp: str, name: str, content: str) -> Path:
        path = Path(tmp) / "feature" / "auth" / "ui" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _scan(self, tmp: str, content: str, name: str = "AuthContent.kt") -> list[dict]:
        path = self._write_kt(tmp, name, content)
        return scan_design_violations_scripts.scan_file(path)

    # ── hardcoded_color ──────────────────────────────────────────────────────

    def test_flags_hardcoded_hex_color(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "val c = Color(0xFF1A73E8)\n")
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_color", types)

    def test_flags_hardcoded_rgb_float_color(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "val c = Color(0.1f, 0.5f, 0.9f)\n")
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_color", types)

    def test_allows_named_color_constants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "val c = Color.Transparent\nval d = Color.White\n")
        types = [f["type"] for f in findings]
        self.assertNotIn("hardcoded_color", types)

    # ── hardcoded_dp ─────────────────────────────────────────────────────────

    def test_flags_hardcoded_padding_dp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "Modifier.padding(16.dp)\n")
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_dp", types)

    def test_flags_hardcoded_height_dp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "Modifier.height(48.dp)\n")
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_dp", types)

    def test_flags_spacer_with_hardcoded_dp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(
                tmp,
                "Spacer(modifier = Modifier.height(8.dp))\n",
            )
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_dp", types)

    def test_allows_zero_and_one_dp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(
                tmp,
                "Modifier.padding(0.dp)\nModifier.height(1.dp)\n",
            )
        types = [f["type"] for f in findings]
        self.assertNotIn("hardcoded_dp", types)

    # ── material_theme ───────────────────────────────────────────────────────

    def test_flags_material_theme_colors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "MaterialTheme.colors.primary\n")
        types = [f["type"] for f in findings]
        self.assertIn("material_theme", types)

    def test_flags_material_theme_typography(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "style = MaterialTheme.typography.bodyMedium\n")
        types = [f["type"] for f in findings]
        self.assertIn("material_theme", types)

    def test_allows_apptheme_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "val t = appTheme\nt.colors.primary\n")
        types = [f["type"] for f in findings]
        self.assertNotIn("material_theme", types)

    # ── direct_textstyle ─────────────────────────────────────────────────────

    def test_flags_direct_textstyle_construction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "val s = TextStyle(fontSize = 16.sp)\n")
        types = [f["type"] for f in findings]
        self.assertIn("direct_textstyle", types)

    def test_allows_apptextstyle_enum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "val s = AppTextStyle.BodyMedium\n")
        types = [f["type"] for f in findings]
        self.assertNotIn("direct_textstyle", types)

    # ── hardcoded_string ────────────────────────────────────────────────────

    def test_flags_hardcoded_text_in_text_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "Text(\"Continue\")\n")
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_string", types)

    def test_flags_hardcoded_content_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "Icon(contentDescription = \"Back\")\n")
        types = [f["type"] for f in findings]
        self.assertIn("hardcoded_string", types)

    def test_allows_state_driven_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "Text(text = state.title)\n")
        types = [f["type"] for f in findings]
        self.assertNotIn("hardcoded_string", types)

    def test_allows_string_resource_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(tmp, "Text(stringResource(Res.string.continue_label))\n")
        types = [f["type"] for f in findings]
        self.assertNotIn("hardcoded_string", types)

    # ── nested_container ─────────────────────────────────────────────────────

    def test_flags_nested_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(
                tmp,
                "@Composable\nfun Foo() {\n  Card {\n    Card {\n    }\n  }\n}\n",
            )
        types = [f["type"] for f in findings]
        self.assertIn("nested_container", types)

    def test_flags_nested_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(
                tmp,
                "@Composable\nfun Foo() {\n  Surface {\n    Surface {\n    }\n  }\n}\n",
            )
        types = [f["type"] for f in findings]
        self.assertIn("nested_container", types)

    def test_allows_single_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(
                tmp,
                "@Composable\nfun Foo() {\n  Card {\n    Text(text = state.title)\n  }\n}\n",
            )
        types = [f["type"] for f in findings]
        self.assertNotIn("nested_container", types)
        self.assertNotIn("hardcoded_string", types)

    # ── skip rules ───────────────────────────────────────────────────────────

    def test_skips_styles_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ButtonStyles.kt"
            path.write_text("val c = Color(0xFF1A73E8)\n", encoding="utf-8")
            findings = scan_design_violations_scripts.scan_file.__wrapped__ if hasattr(
                scan_design_violations_scripts.scan_file, "__wrapped__"
            ) else None
            # Use scan() with should_skip — it must skip ButtonStyles.kt
            result = scan_design_violations_scripts.scan(Path(tmp))
        # ButtonStyles.kt is in _SKIP_NAME_SUFFIXES → no findings
        self.assertEqual(result, [])

    def test_skips_designsystem_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ds_dir = Path(tmp) / "core" / "designsystem"
            ds_dir.mkdir(parents=True)
            (ds_dir / "AppButton.kt").write_text(
                "val c = Color(0xFF1A73E8)\n", encoding="utf-8"
            )
            result = scan_design_violations_scripts.scan(Path(tmp))
        self.assertEqual(result, [])

    def test_preview_coverage_flags_missing_preview_and_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "feature" / "auth" / "ui" / "src" / "commonMain" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui" / "LoginContent.kt"
            content.parent.mkdir(parents=True, exist_ok=True)
            content.write_text(
                """package com.example.feature.auth.ui

import androidx.compose.runtime.Composable

@Composable
fun LoginContent(
    state: LoginUiState,
    onIntent: (LoginIntent) -> Unit,
) {}
""",
                encoding="utf-8",
            )
            findings = scan_design_violations_scripts.scan(root)
        types = [f["type"] for f in findings]
        self.assertIn("preview_coverage", types)
        self.assertTrue(any("Missing preview stub" in f["message"] for f in findings))
        self.assertTrue(any("Missing Roborazzi screenshot test" in f["message"] for f in findings))
        self.assertTrue(any("Missing UI interaction test" in f["message"] for f in findings))

    def test_preview_coverage_accepts_multi_device_preview_and_roborazzi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "feature" / "auth" / "ui" / "src"
            common = base / "commonMain" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui"
            previews = common / "previews"
            tests = base / "jvmTest" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui" / "previews"
            common_test = base / "commonTest" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui"
            previews.mkdir(parents=True, exist_ok=True)
            tests.mkdir(parents=True, exist_ok=True)
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
        setContent { LoginContent(state = LoginUiState(), onIntent = {}) }
    }
}
""",
                encoding="utf-8",
            )

            (common / "LoginContent.kt").write_text(
                """package com.example.feature.auth.ui

import androidx.compose.runtime.Composable

@Composable
fun LoginContent(
    state: LoginUiState,
    onIntent: (LoginIntent) -> Unit,
) {}
""",
                encoding="utf-8",
            )
            (previews / "MultiDevicePreview.kt").write_text(
                """package com.example.feature.auth.ui.previews

import org.jetbrains.compose.ui.tooling.preview.Preview

@Preview(name = "Phone", widthDp = 360, heightDp = 640)
@Preview(name = "Tablet", widthDp = 673, heightDp = 841)
@Preview(name = "Desktop", widthDp = 1280, heightDp = 800)
annotation class MultiDevicePreview
""",
                encoding="utf-8",
            )
            (previews / "LoginContentPreview.kt").write_text(
                """package com.example.feature.auth.ui.previews

import androidx.compose.runtime.Composable

@MultiDevicePreview
@Composable
fun LoginContentPreview() {}
""",
                encoding="utf-8",
            )
            (tests / "LoginContentScreenshotTest.kt").write_text(
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
                encoding="utf-8",
            )
            findings = scan_design_violations_scripts.scan(root)
        self.assertFalse(any(f["type"] == "preview_coverage" for f in findings))

    def test_scaffold_preview_coverage_creates_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "feature" / "auth" / "ui" / "src" / "commonMain" / "kotlin" / "com" / "example" / "feature" / "auth" / "ui" / "LoginContent.kt"
            content.parent.mkdir(parents=True, exist_ok=True)
            content.write_text(
                """package com.example.feature.auth.ui

import androidx.compose.runtime.Composable

@Composable
fun LoginContent(
    state: LoginUiState,
    onIntent: (LoginIntent) -> Unit,
) {}
""",
                encoding="utf-8",
            )

            created = scaffold_preview_coverage_scripts.scaffold_preview_coverage(root)

            self.assertTrue(any(path.endswith("LoginContentPreview.kt") for path in created))
            self.assertTrue(any(path.endswith("LoginContentScreenshotTest.kt") for path in created))
            self.assertTrue(any(path.endswith("MultiDevicePreview.kt") for path in created))
            self.assertTrue(any(path.endswith("LoginContentTest.kt") for path in created))

    def test_clean_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._scan(
                tmp,
                "@Composable\nfun AuthContent(state: AuthUiState) {\n"
                "  val t = appTheme\n"
                "  Card {\n"
                "    AppText(text = state.title, style = AppTextStyle.BodyMedium)\n"
                "    Modifier.padding(t.spacing.lg)\n"
                "  }\n"
                "}\n",
            )
        self.assertEqual(findings, [])

    # ── CLI exit codes ────────────────────────────────────────────────────────

    def test_cli_exit_0_on_clean_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "skills" / "kmp-compose-design-system"
                     / "scripts" / "scan_design_violations.py"),
                 tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0)

    def test_cli_exit_1_on_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Foo.kt").write_text("val c = Color(0xFF1A73E8)\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "skills" / "kmp-compose-design-system"
                     / "scripts" / "scan_design_violations.py"),
                 tmp],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 1)

    def test_cli_exit_2_on_missing_root(self) -> None:
        result = subprocess.run(
            [sys.executable,
             str(REPO_ROOT / "skills" / "kmp-compose-design-system"
                 / "scripts" / "scan_design_violations.py"),
             "/nonexistent/path/that/does/not/exist"],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_json_output_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Foo.kt").write_text("val c = Color(0xFF1A73E8)\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "skills" / "kmp-compose-design-system"
                     / "scripts" / "scan_design_violations.py"),
                 tmp, "--json"],
                capture_output=True,
                text=True, encoding="utf-8",
            )
        parsed = json.loads(result.stdout)
        self.assertIsInstance(parsed, list)
        self.assertGreater(len(parsed), 0)
        self.assertIn("type", parsed[0])
        self.assertIn("line", parsed[0])
        self.assertIn("file", parsed[0])


class ScanDesignViolationsDeployedSkillsExclusionTests(unittest.TestCase):
    """The same false-positive class found in kmp-audit's
    audit_project.py (deployed skill reference/template content scanned as if it were
    the consumer's own source) also existed here: _SKIP_DIR_FRAGMENTS only knew about
    designsystem/design_system/theme, so a real project with skills deployed to
    .claude/skills/ would get a hardcoded_color violation from this skill's own
    detekt-rules/src/test/kotlin/.../HardcodedColorRuleTest.kt (which legitimately
    contains a Color(0x...) literal to test the rule against). Worse than the
    read-only audit case since /fix-design uses this scanner to auto-fix violations.
    """

    def test_ignores_deployed_skill_detekt_rule_test_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = (
                root / ".claude" / "skills" / "kmp-compose-design-system"
                / "detekt-rules" / "src" / "test" / "kotlin"
            )
            d.mkdir(parents=True)
            (d / "HardcodedColorRuleTest.kt").write_text(
                "class HardcodedColorRuleTest {\n    val bad = Color(0xFFAABBCC)\n}\n",
                encoding="utf-8",
            )
            findings = scan_design_violations_scripts.scan(root)
            self.assertEqual(findings, [])

    def test_still_flags_real_project_code_alongside_deployed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = (
                root / ".claude" / "skills" / "kmp-compose-design-system"
                / "detekt-rules" / "src" / "test" / "kotlin"
            )
            d.mkdir(parents=True)
            (d / "HardcodedColorRuleTest.kt").write_text(
                "val bad = Color(0xFFAABBCC)\n", encoding="utf-8"
            )
            real = root / "app" / "shared" / "src" / "commonMain" / "kotlin"
            real.mkdir(parents=True)
            (real / "App.kt").write_text("val Ink = Color(0xFFE9EDF7)\n", encoding="utf-8")

            findings = scan_design_violations_scripts.scan(root)
            self.assertFalse(any(".claude" in f["file"] for f in findings))
            self.assertTrue(any("App.kt" in f["file"] for f in findings))


class LayoutConsistencyTests(unittest.TestCase):
    """Tests for scan_layout_consistency() in scan_design_violations.py."""

    def _make_ui_dir(self, tmp: str, feature: str = "auth") -> Path:
        ui_dir = Path(tmp) / "feature" / feature / "ui"
        ui_dir.mkdir(parents=True, exist_ok=True)
        return ui_dir

    def _write_content(self, ui_dir: Path, name: str, body: str) -> Path:
        path = ui_dir / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_flat_screens_are_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ui = self._make_ui_dir(tmp)
            self._write_content(ui, "ListContent.kt", "fun ListContent() { Column { } }")
            self._write_content(ui, "DetailContent.kt", "fun DetailContent() { Column { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        self.assertEqual(findings, [])

    def test_card_screens_are_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ui = self._make_ui_dir(tmp)
            self._write_content(ui, "ProfileContent.kt", "fun ProfileContent() { AppCard() { } }")
            self._write_content(ui, "SettingsContent.kt", "fun SettingsContent() { AppCard() { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        self.assertEqual(findings, [])

    def test_mixed_card_and_flat_flags_minority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ui = self._make_ui_dir(tmp)
            self._write_content(ui, "ListContent.kt", "fun ListContent() { Column { } }")
            self._write_content(ui, "DetailContent.kt", "fun DetailContent() { Column { } }")
            self._write_content(ui, "ProfileContent.kt", "fun ProfileContent() { AppCard() { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        types = [f["type"] for f in findings]
        self.assertIn("layout_inconsistency", types)
        # Only the minority (card) is flagged, not the majority (flat x2)
        flagged = [f["file"] for f in findings if f["type"] == "layout_inconsistency"]
        self.assertTrue(any("ProfileContent" in p for p in flagged))
        self.assertFalse(any("ListContent" in p for p in flagged))

    def test_tabbed_screen_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ui = self._make_ui_dir(tmp)
            self._write_content(ui, "OverviewContent.kt", "fun OverviewContent() { Column { TabRow() } }")
            self._write_content(ui, "ListContent.kt", "fun ListContent() { Column { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        types = [f["type"] for f in findings]
        self.assertIn("layout_inconsistency", types)

    def test_mixed_layout_suggests_matching_shadcn_pattern_with_risk_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ui = self._make_ui_dir(tmp)
            self._write_content(ui, "OverviewContent.kt", "fun OverviewContent() { Column { TabRow() } }")
            self._write_content(ui, "SecondContent.kt", "fun SecondContent() { Column { TabRow() } }")
            self._write_content(ui, "ListContent.kt", "fun ListContent() { Column { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        messages = " ".join(f["message"] for f in findings if f["type"] == "layout_inconsistency")
        self.assertIn("ShadcnTabsList", messages)
        self.assertIn("kmp-shadcn-compose", messages)
        self.assertIn("experimental-API risk", messages)

    def test_single_content_file_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ui = self._make_ui_dir(tmp)
            self._write_content(ui, "AuthContent.kt", "fun AuthContent() { AppCard() { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        self.assertEqual(findings, [])

    def test_different_features_checked_independently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            auth_ui = self._make_ui_dir(tmp, "auth")
            home_ui = self._make_ui_dir(tmp, "home")
            # auth uses flat — consistent within itself
            self._write_content(auth_ui, "LoginContent.kt", "fun LoginContent() { Column { } }")
            self._write_content(auth_ui, "RegisterContent.kt", "fun RegisterContent() { Column { } }")
            # home uses card — consistent within itself
            self._write_content(home_ui, "FeedContent.kt", "fun FeedContent() { AppCard() { } }")
            self._write_content(home_ui, "ProfileContent.kt", "fun ProfileContent() { AppCard() { } }")
            findings = scan_design_violations_scripts.scan_layout_consistency(Path(tmp))
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
