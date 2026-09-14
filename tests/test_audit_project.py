from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import REPO_ROOT, load_module

audit_scripts = load_module(
    "audit_project",
    REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_project.py",
)

class AuditProjectTests(unittest.TestCase):
    def test_audit_project_finds_smells(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "auth" / "ui"
            ui_dir.mkdir(parents=True)
            # ViewModel file — triggers state/sharedflow checks but NOT data-import (by design)
            (ui_dir / "AuthViewModel.kt").write_text(
                """
                _state.value = _state.value.copy(isLoading = true)
                val flow = MutableSharedFlow<Int>(replay = 1)
                """.strip(),
                encoding="utf-8",
            )
            # Non-ViewModel UI file — triggers data import check
            (ui_dir / "AuthScreen.kt").write_text(
                "import foo.bar.data.SecretRepo",
                encoding="utf-8",
            )

            findings = audit_scripts.audit_project(root)

            self.assertTrue(any("state copy race" in finding for finding in findings))
            self.assertTrue(any("sharedflow replay effect" in finding for finding in findings))
            self.assertTrue(any("data import in ui" in finding for finding in findings))

    def test_audit_project_finds_network_result_in_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "auth" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "AuthScreen.kt").write_text(
                "val result: NetworkResult<User> = viewModel.state",
                encoding="utf-8",
            )

            findings = audit_scripts.audit_project(root)

            self.assertTrue(any("network result in ui" in finding for finding in findings))

    def test_audit_project_ignores_network_result_outside_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "feature" / "auth" / "data"
            data_dir.mkdir(parents=True)
            (data_dir / "AuthRemoteDataSource.kt").write_text(
                "suspend fun login(): NetworkResult<User>",
                encoding="utf-8",
            )

            findings = audit_scripts.audit_project(root)

            self.assertFalse(any("network result in ui" in finding for finding in findings))

    def test_audit_project_finds_adb_screencap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "androidApp" / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "ScreenshotHelper.kt").write_text(
                'Runtime.getRuntime().exec("adb screencap /sdcard/screen.png")',
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("manual screen capture" in f for f in findings))

    def test_audit_project_finds_playwright(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "androidApp" / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "UITest.kt").write_text(
                "import com.microsoft.playwright.Page",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("manual screen capture" in f for f in findings))

    def test_audit_project_finds_xcrun_simctl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "iosApp" / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "CaptureHelper.kt").write_text(
                'exec("xcrun simctl io booted screenshot screen.png")',
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("manual screen capture" in f for f in findings))

    def test_audit_project_finds_magic_color_in_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "auth" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "AuthScreen.kt").write_text(
                "Box(modifier = Modifier.background(Color(0xFF6200EE)))",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("magic color literal" in f for f in findings))

    def test_audit_project_ignores_magic_color_in_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "core" / "designsystem" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "AppColors.kt").write_text(
                "val primary = Color(0xFF6200EE)",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("magic color literal" in f for f in findings))

    def test_audit_project_ignores_magic_color_outside_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "feature" / "auth" / "data"
            data_dir.mkdir(parents=True)
            (data_dir / "AuthMapper.kt").write_text(
                "val highlight = Color(0xFFFF0000)",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("magic color literal" in f for f in findings))

    def test_audit_project_finds_system_dark_theme_in_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "val isDark = isSystemInDarkTheme()\n"
                "val bg = if (isDark) Color.Black else Color.White",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("system dark theme scatter" in f for f in findings))

    def test_audit_project_finds_hardcoded_spacing_in_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeContent.kt").write_text(
                "Column(modifier = Modifier.padding(16.dp)) { }",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded spacing" in f for f in findings))

    def test_audit_project_finds_hardcoded_spacing_horizontal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeContent.kt").write_text(
                "Row(modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)) { }",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded spacing" in f for f in findings))

    def test_audit_project_ignores_spacing_token_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeContent.kt").write_text(
                "Column(modifier = Modifier.padding(horizontal = AppTheme.spacing.lg)) { }",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded spacing" in f for f in findings))

    def test_audit_project_ignores_zero_dp_padding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeContent.kt").write_text(
                "Column(modifier = Modifier.padding(0.dp)) { }",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded spacing" in f for f in findings))

    def test_audit_project_ignores_hardcoded_spacing_outside_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comp_dir = root / "core" / "designsystem" / "components"
            comp_dir.mkdir(parents=True)
            (comp_dir / "AppTopAppBar.kt").write_text(
                ".padding(horizontal = 4.dp)",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded spacing" in f for f in findings))

    def test_audit_project_ignores_system_dark_theme_in_app_theme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "app" / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "AppTheme.kt").write_text(
                "AppTheme(darkTheme = isSystemInDarkTheme()) { content() }",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("system dark theme scatter" in f for f in findings))

    def test_audit_project_finds_named_color_in_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "Modifier.border(1.dp, Color.Gray)",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("named color in ui" in f for f in findings))

    def test_flags_incomplete_project_owned_agent_scaffold_when_claude_setup_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.gradle.kts").write_text('rootProject.name = "Demo"\n', encoding="utf-8")
            (root / "CLAUDE.md").write_text("--system-prompt-file=.claude/AGENTS.md\n", encoding="utf-8")
            claude = root / ".claude"
            (claude / "commands").mkdir(parents=True)
            (claude / "skills" / "demo").mkdir(parents=True)
            (claude / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
            (claude / "commands" / "kmp-run-audit.md").write_text("# cmd\n", encoding="utf-8")

            findings = audit_scripts.audit_project(root)

            self.assertTrue(
                any("project-owned agent scaffold incomplete" in f for f in findings),
                findings,
            )

    def test_ignores_complete_project_owned_agent_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.gradle.kts").write_text('rootProject.name = "Demo"\n', encoding="utf-8")
            (root / "CLAUDE.md").write_text("--system-prompt-file=.claude/AGENTS.md\n", encoding="utf-8")
            for rel in ("agents", "rules", "hooks", "commands", "skills", "docs/reference"):
                (root / rel).mkdir(parents=True, exist_ok=True)
            (root / "docs" / "reference" / "ai-collaboration.md").write_text("# AI Collaboration\n", encoding="utf-8")
            (root / "docs" / "reference" / "agent-catalog.md").write_text("# Agent Catalog\n", encoding="utf-8")
            claude = root / ".claude"
            (claude / "commands").mkdir(parents=True)
            (claude / "skills" / "demo").mkdir(parents=True)
            (claude / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
            (claude / "commands" / "kmp-run-audit.md").write_text("# cmd\n", encoding="utf-8")

            findings = audit_scripts.audit_project(root)

            self.assertFalse(
                any("project-owned agent scaffold incomplete" in f for f in findings),
                findings,
            )

    def test_audit_project_ignores_named_color_in_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "core" / "designsystem" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "AppColors.kt").write_text(
                "val gray = Color.Gray",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("named color in ui" in f for f in findings))

    def test_audit_project_ignores_named_color_outside_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "feature" / "home" / "domain" / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "HomeUseCase.kt").write_text(
                "val color = Color.Black",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("named color in ui" in f for f in findings))

    def test_audit_project_finds_hardcoded_divider_color(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeContent.kt").write_text(
                "HorizontalDivider(color = Color.LightGray)",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded divider color" in f for f in findings))

    def test_audit_project_ignores_token_divider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeContent.kt").write_text(
                "HorizontalDivider(color = AppTheme.colors.outline)",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded divider color" in f for f in findings))

    def test_audit_project_finds_color_in_composable_outside_ui_path(self) -> None:
        # No /ui/ segment, but the file declares @Composable — content detection catches it.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "composeApp" / "src" / "commonMain" / "kotlin" / "home"
            d.mkdir(parents=True)
            (d / "HomeScreen.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\n"
                "fun HomeScreen() { Modifier.border(1.dp, Color.Gray) }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("named color in ui" in f for f in findings))

    def test_audit_project_ignores_color_in_non_compose_outside_ui(self) -> None:
        # No /ui/ path AND no Compose content — stays skipped (avoids flagging plain constants).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "core" / "util" / "src"
            d.mkdir(parents=True)
            (d / "Constants.kt").write_text(
                "val brandHex = Color.Gray\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("named color in ui" in f for f in findings))


class MultiViewModelScreenTests(unittest.TestCase):
    def test_flags_screen_with_three_or_more_viewmodels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "studio" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "StudioScreen.kt").write_text(
                "val ttiVm = koinViewModel<TextToImageViewModel>()\n"
                "val img2imgVm = koinViewModel<ImageToImageViewModel>()\n"
                "val videoVm = koinViewModel<VideoViewModel>()\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("multi viewmodel screen" in f for f in findings))

    def test_ignores_screen_with_two_viewmodels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "val vm = koinViewModel<HomeViewModel>()\n"
                "val sharedVm = koinViewModel<SharedViewModel>()\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("multi viewmodel screen" in f for f in findings))

    def test_flags_screen_regardless_of_package_path(self) -> None:
        # The detector no longer requires a /ui/ path — a *Screen.kt with 3+ VMs is
        # flagged wherever it lives (projects don't all use the /ui/ module convention).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "composeApp" / "src" / "commonMain" / "kotlin" / "home"
            src_dir.mkdir(parents=True)
            (src_dir / "StudioScreen.kt").write_text(
                "val a = koinViewModel<AViewModel>()\n"
                "val b = koinViewModel<BViewModel>()\n"
                "val c = koinViewModel<CViewModel>()\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("multi viewmodel screen" in f for f in findings))

    def test_ignores_screen_in_build_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "composeApp" / "build" / "generated"
            src_dir.mkdir(parents=True)
            (src_dir / "StudioScreen.kt").write_text(
                "val a = koinViewModel<AViewModel>()\n"
                "val b = koinViewModel<BViewModel>()\n"
                "val c = koinViewModel<CViewModel>()\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("multi viewmodel screen" in f for f in findings))

    def test_flags_non_screen_composable_with_many_vms(self) -> None:
        # Hardening: a Compose file NOT named *Screen (Dashboard) still counts.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "Dashboard.kt").write_text(
                "@Composable\n"
                "fun Dashboard() {\n"
                "    val a = koinViewModel<AViewModel>()\n"
                "    val b = koinViewModel<BViewModel>()\n"
                "    val c = koinViewModel<CViewModel>()\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("multi viewmodel screen" in f for f in findings))


class AuditHardeningTests(unittest.TestCase):
    def test_vm_in_vm_catches_coordinator_without_viewmodel_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "StudioCoordinator.kt").write_text(
                "class StudioCoordinator(\n"
                "    private val tti: TextToImageViewModel,\n"
                ") : MviViewModel<S, I, E>(S()) {\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel in viewmodel" in f for f in findings))

    def test_large_viewmodel_caught_by_content_not_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            body = (
                "import androidx.lifecycle.viewModelScope\n"
                "class HomePresenter : BaseViewModel() {\n"
                + "\n".join(f"    fun op{i}() {{}}" for i in range(200))
                + "\n}\n"
            )
            (d / "HomePresenter.kt").write_text(body, encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel" in f and "HomePresenter" in f for f in findings))

    def test_dto_leak_caught_in_usecase_outside_domain_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "LoginUseCase.kt").write_text(
                "import com.example.data.dto.UserDto\nclass LoginUseCase {}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("dto leak to domain" in f for f in findings))

    def test_data_model_named_file_is_not_treated_as_viewmodel(self) -> None:
        # Guard against over-broad VM detection: a plain data class must not be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            body = (
                "data class UserModel(\n"
                + "\n".join(f"    val field{i}: String," for i in range(200))
                + "\n)\n"
            )
            (d / "UserModel.kt").write_text(body, encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel" in f and "UserModel" in f for f in findings))


class RepositoryInComposableTests(unittest.TestCase):
    def test_flags_repository_injected_and_flow_collected_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "AppRuntime.kt").write_text(
                "@Composable\n"
                "internal fun rememberAppRuntime(): AppRuntime {\n"
                "    val settingsRepository: SettingsRepository = koinInject()\n"
                "    val settings by settingsRepository.settings.collectAsState()\n"
                "    return AppRuntime(settingsRepository)\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("repository in composable" in f for f in findings))

    def test_ignores_repository_forwarded_to_controller(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "GoodRuntime.kt").write_text(
                "@Composable\n"
                "internal fun RememberGoodRuntime() {\n"
                "    val settingsRepository: SettingsRepository = koinInject()\n"
                "    val controller = rememberSettingsController(settingsRepository)\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("repository in composable" in f for f in findings))

    def test_ignores_repository_injected_outside_a_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "SettingsViewModel.kt").write_text(
                "@Composable\n"
                "fun Marker() {}\n"
                "\n"
                "class SettingsViewModel(\n"
                "    private val settingsRepository: SettingsRepository,\n"
                ") : MviViewModel<S, I, E>(S()) {\n"
                "    val settings = settingsRepository.settings.collectAsState()\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("repository in composable" in f for f in findings))


class ViewModelInViewModelTests(unittest.TestCase):
    def test_flags_viewmodel_with_viewmodel_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "studio" / "presenter" / "src"
            d.mkdir(parents=True)
            (d / "StudioCoordinatorViewModel.kt").write_text(
                "class StudioCoordinatorViewModel(\n"
                "    private val tti: TextToImageViewModel,\n"
                "    private val assembler: StudioStateAssembler,\n"
                ") : MviViewModel<S, I, E>(S()) {\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel in viewmodel" in f for f in findings))

    def test_ignores_viewmodel_with_usecase_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "home" / "presenter" / "src"
            d.mkdir(parents=True)
            (d / "HomeViewModel.kt").write_text(
                "class HomeViewModel(\n"
                "    private val generateImage: GenerateImageUseCase,\n"
                "    private val savedStateHandle: SavedStateHandle,\n"
                ") : MviViewModel<S, I, E>(S()) {\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel in viewmodel" in f for f in findings))

    def test_ignores_state_holder_with_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "studio" / "presenter" / "src"
            d.mkdir(parents=True)
            # A plain state holder is not a *ViewModel.kt file and not a ViewModel class
            (d / "TextToImageStateHolder.kt").write_text(
                "class TextToImageStateHolder(\n"
                "    private val scope: CoroutineScope,\n"
                "    private val generateImage: GenerateImageUseCase,\n"
                ") {\n"
                "    fun onIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel in viewmodel" in f for f in findings))

    def test_flags_viewmodel_held_as_injected_property(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "PropCoordinator.kt").write_text(
                "class PropCoordinator : MviViewModel<S, I, E>(S()) {\n"
                "    private val editor: EditorViewModel by inject()\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel in viewmodel" in f for f in findings))

    def test_flags_viewmodel_instantiated_internally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "InstCoordinator.kt").write_text(
                "class InstCoordinator : MviViewModel<S, I, E>(S()) {\n"
                "    private val editor = EditorViewModel()\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel in viewmodel" in f for f in findings))

    def test_flags_viewmodel_via_di_generic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "GenericCoordinator.kt").write_text(
                "class GenericCoordinator : MviViewModel<S, I, E>(S()) {\n"
                "    private val editor by inject<EditorViewModel>()\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel in viewmodel" in f for f in findings))

    def test_ignores_coordinator_holding_state_holder(self) -> None:
        # The valid Option-2 coordinator holds State Holders + use cases — must NOT flag.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "DashboardCoordinatorViewModel.kt").write_text(
                "class DashboardCoordinatorViewModel(\n"
                "    private val saveItem: SaveItemUseCase,\n"
                "    private val assembler: DashboardStateAssembler,\n"
                ") : MviViewModel<S, I, E>(S()) {\n"
                "    private val editor = EditorStateHolder(viewModelScope, saveItem)\n"
                "    override suspend fun handleIntent(intent: I) {}\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel in viewmodel" in f for f in findings))

    def test_ignores_comment_mentioning_viewmodel_in_plain_data_class(self) -> None:
        # Real false positive: a data class with no supertype at all, whose comment
        # happens to say "not the ViewModel" right after a property's type-annotation
        # colon. The old regex read that colon + comment text as if it were the
        # class's own `: ...ViewModel` supertype clause.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "AppRuntime.kt").write_text(
                "internal data class AppRuntime(\n"
                "    val settingsRepository: SettingsRepository,\n"
                "    // A plain callback, not the ViewModel — forwarded to the sub-unit.\n"
                "    val onSessionSettingsChanged: (CueSettings) -> Unit,\n"
                "    val onSelectedNoteChange: (CueNote?) -> Unit,\n"
                ")\n"
                "\n"
                "@Composable\n"
                "internal fun rememberAppRuntime(): AppRuntime {\n"
                "    val sessionViewModel: SessionViewModel = koinViewModel()\n"
                "    return AppRuntime(\n"
                "        settingsRepository = settingsRepository,\n"
                "        onSessionSettingsChanged = sessionViewModel::updateSettings,\n"
                "        onSelectedNoteChange = { selectedNote = it },\n"
                "    )\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel in viewmodel" in f for f in findings))

    def test_ignores_local_val_viewmodel_inside_unrelated_composable(self) -> None:
        # A local `val x: FooViewModel = koinViewModel()` inside a @Composable function
        # body is the correct pattern for obtaining a ViewModel at composition time —
        # it must never be attributed to some other class in the same file as if it
        # were that class's own injected property.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "Screen.kt").write_text(
                "class ScreenStateHolder(private val scope: CoroutineScope) {\n"
                "    fun onIntent(intent: I) {}\n"
                "}\n"
                "\n"
                "@Composable\n"
                "fun Screen() {\n"
                "    val vm: SomeViewModel = koinViewModel()\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel in viewmodel" in f for f in findings))


class HandwrittenImageVectorTests(unittest.TestCase):
    def _builder(self, cmds: int, header: bool = False) -> str:
        lines = "\n".join(f"        lineTo({i}f, {i}f)" for i in range(cmds))
        head = "// GENERATED by convert_image_to_imagevector — do not edit\n" if header else ""
        return (f"{head}val V = ImageVector.Builder(name=\"V\").apply {{\n"
                f"    path {{\n        moveTo(0f, 0f)\n{lines}\n    }}\n}}.build()\n")

    def test_flags_handwritten_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "BadIcon.kt").write_text(self._builder(15), encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("handwritten imagevector" in f for f in findings))

    def test_ignores_generated_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "GenIcon.kt").write_text(self._builder(15, header=True), encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("handwritten imagevector" in f for f in findings))

    def test_ignores_tiny_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "TinyIcon.kt").write_text(self._builder(3), encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("handwritten imagevector" in f for f in findings))


class RasterInCommonMainTests(unittest.TestCase):
    def test_flags_png_in_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "composeApp" / "src" / "commonMain" / "composeResources" / "drawable"
            d.mkdir(parents=True)
            (d / "ic_search.png").write_bytes(b"\x89PNG")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("raster asset in commonMain" in f for f in findings))

    def test_photos_dir_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "composeApp" / "src" / "commonMain" / "composeResources" / "photos"
            d.mkdir(parents=True)
            (d / "hero.jpg").write_bytes(b"\xff\xd8")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raster asset in commonMain" in f for f in findings))

    def test_outside_commonmain_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "composeApp" / "src" / "androidMain" / "res" / "drawable"
            d.mkdir(parents=True)
            (d / "splash.png").write_bytes(b"\x89PNG")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raster asset in commonMain" in f for f in findings))


class EmptyPlatformSourceSetTests(unittest.TestCase):
    def test_flags_directory_with_no_kt_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "auth" / "domain" / "src" / "androidMain" / "kotlin" / "com" / "example"
            d.mkdir(parents=True)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("empty platform source set" in f for f in findings))

    def test_flags_file_with_only_package_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "auth" / "domain" / "src" / "iosMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "Stub.kt").write_text("package com.example.feature.auth.domain\n\n// nothing here yet\n",
                                        encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("empty platform source set" in f for f in findings))

    def test_ignores_common_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "auth" / "domain" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "LoginUseCase.kt").write_text("package com.example\nclass LoginUseCase\n", encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("empty platform source set" in f for f in findings))

    def test_ignores_populated_platform_sourceset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "auth" / "data" / "src" / "androidMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "AndroidHttpEngine.kt").write_text(
                "package com.example\nactual fun httpEngine() = Android.create()\n", encoding="utf-8"
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("empty platform source set" in f for f in findings))


class FocusedStateBorderWidthTests(unittest.TestCase):
    def _write(self, root: Path, filename: str, content: str) -> None:
        d = root / "src" / "commonMain" / "kotlin" / "ui"
        d.mkdir(parents=True, exist_ok=True)
        (d / filename).write_text(content, encoding="utf-8")

    def test_flags_focused_block_animating_border_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "ButtonStyles.kt",
                "internal val buttonInteractionStyle = Style {\n"
                "    focused { animate { borderWidth(2.dp); borderColor(colors.borderFocus) } }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("focused state animates border width" in f for f in findings))

    def test_flags_selected_block_animating_border_bottom_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "ChipStyles.kt",
                "data object Selected : ChipVariant {\n"
                "    override val style = Style {\n"
                "        selected { animate { borderBottomWidth(1.dp); borderColor(colors.borderFocus) } }\n"
                "    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("focused state animates border width" in f for f in findings))

    def test_ignores_focused_block_animating_color_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "ButtonStyles.kt",
                "internal val buttonInteractionStyle = Style {\n"
                "    focused { animate { borderColor(colors.borderFocus) } }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("focused state animates border width" in f for f in findings))

    def test_ignores_border_width_outside_state_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "ButtonStyles.kt",
                "data object Default : ButtonVariant {\n"
                "    override val style = Style {\n"
                "        borderWidth(2.dp)\n"
                "        borderColor(Color.Transparent)\n"
                "        focused { animate { borderColor(colors.borderFocus) } }\n"
                "    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("focused state animates border width" in f for f in findings))


class CombinedOneFilePerXTests(unittest.TestCase):
    _LESSON_FRONTMATTER = (
        "---\nskill: kmp-mvi\ndate: 2026-06-20\n"
        "severity: high\ntype: correction\n---\n\n"
    )

    def test_flags_combined_lesson_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "lessons"
            d.mkdir(parents=True)
            (d / "bad.md").write_text(
                self._LESSON_FRONTMATTER
                + "## What we followed\nA\n\n## What broke / what we discovered\nB\n\n"
                + "## What we followed\nC\n\n## What broke / what we discovered\nD\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("combined lesson file" in f for f in findings))

    def test_ignores_single_lesson_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "lessons"
            d.mkdir(parents=True)
            (d / "good.md").write_text(
                self._LESSON_FRONTMATTER
                + "## What we followed\nA\n\n## What broke / what we discovered\nB\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined lesson file" in f for f in findings))

    def test_flags_combined_layout_screen_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "layout-system"
            d.mkdir(parents=True)
            (d / "bad-screen.md").write_text(
                "# Inbox\n\n## Components\n\n# Contacts\n\n## Components\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("combined layout screen file" in f for f in findings))

    def test_ignores_single_screen_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "layout-system"
            d.mkdir(parents=True)
            (d / "good-screen.md").write_text(
                "# Inbox\n\n## Components\n\n## Variant A\n\nwireframe here\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined layout screen file" in f for f in findings))

    def test_ignores_components_registry_with_multiple_headings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "layout-system"
            d.mkdir(parents=True)
            (d / "_components.md").write_text(
                "# Component Registry\n\n# Another Section\n", encoding="utf-8"
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined layout screen file" in f for f in findings))

    def test_flags_combined_sqldelight_table_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "db"
            d.mkdir(parents=True)
            (d / "Combined.sq").write_text(
                "CREATE TABLE user (\n    id INTEGER PRIMARY KEY\n);\n\n"
                "CREATE TABLE post (\n    id INTEGER PRIMARY KEY\n);\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("combined sqldelight table file" in f for f in findings))

    def test_ignores_single_table_sq_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "db"
            d.mkdir(parents=True)
            (d / "User.sq").write_text(
                "CREATE TABLE user (\n    id INTEGER PRIMARY KEY\n);\n", encoding="utf-8"
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined sqldelight table file" in f for f in findings))


class RawHttpBypassTests(unittest.TestCase):
    _NETWORK_RESULT_KT = (
        "sealed interface NetworkResult<T>\nsuspend fun safeRequest() {}\n"
    )

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_raw_http_when_established_client_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/src/commonMain/kotlin/NetworkResult.kt",
                self._NETWORK_RESULT_KT,
            )
            self._write(
                root, "feature/newserver/src/commonMain/kotlin/RawClient.kt",
                "import java.net.HttpURLConnection\nimport java.net.URL\n"
                "fun fetchFromNewServer() {\n"
                "    val conn = URL(\"http://newserver\").openConnection() as HttpURLConnection\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("raw http bypasses established ktor client" in f for f in findings))

    def test_ignores_raw_http_with_no_established_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/newserver/src/commonMain/kotlin/RawClient.kt",
                "import java.net.HttpURLConnection\nfun fetch() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raw http bypasses established ktor client" in f for f in findings))

    def test_ignores_correct_reuse_of_established_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/src/commonMain/kotlin/NetworkResult.kt",
                self._NETWORK_RESULT_KT,
            )
            self._write(
                root, "feature/newserver/src/commonMain/kotlin/GoodClient.kt",
                "suspend fun fetchFromNewServer(): NetworkResult<String> = safeRequest()\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raw http bypasses established ktor client" in f for f in findings))


class WhatCommentInControlFlowTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_what_comment_before_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "src/commonMain/kotlin/Sample.kt",
                "fun positive(items: List<Int>) {\n"
                "    // Loop through items and print each one\n"
                "    for (item in items) {\n"
                "        println(item)\n"
                "    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("what-comment in control flow" in f for f in findings))

    def test_flags_what_comment_on_same_line_as_conditional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "src/commonMain/kotlin/Sample.kt",
                "fun sameLine(items: List<Int>) {\n"
                "    if (items.isEmpty()) return // Check if items is empty\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("what-comment in control flow" in f for f in findings))

    def test_ignores_why_comment_with_workaround_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "src/commonMain/kotlin/Sample.kt",
                "fun negative(items: List<Int>) {\n"
                "    for (item in items) {\n"
                "        // Skip zero-cost items (workaround for issue #42 pricing div-by-zero)\n"
                "        if (item == 0) continue\n"
                "    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("what-comment in control flow" in f for f in findings))

    def test_ignores_comment_not_attached_to_control_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "src/commonMain/kotlin/Sample.kt",
                "fun helper() {\n"
                "    // Build the cache key from user id and locale\n"
                "    val key = \"$userId:$locale\"\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("what-comment in control flow" in f for f in findings))


class ExtensibleAbstractClassInCommonTests(unittest.TestCase):
    """A real, recurring bug pattern: an agent creates a public abstract class in
    commonMain (e.g. a 'GenericGameApplication') with only abstract members, forcing
    every consumer to subclass it — importing an Android/Spring-style inheritance
    instinct into a context where interface + injection preserves the same flexibility
    without dictating the consumer's app structure. Not scoped to any domain name; the
    smell is the shape (abstract class, only abstract members, in commonMain).
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_pure_template_abstract_class_in_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/game/src/commonMain/kotlin/GenericGameApplication.kt",
                "abstract class GenericGameApplication {\n"
                "    abstract fun onInitialize()\n"
                "    abstract fun onConfigure(): AppConfig\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("extensible abstract class in commonMain" in f for f in findings))

    def test_ignores_abstract_class_with_a_concrete_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/data/src/commonMain/kotlin/BaseRepository.kt",
                "abstract class BaseRepository {\n"
                "    abstract fun fetch(): String\n"
                "    fun cachedFetch(): String {\n"
                "        return fetch()\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("extensible abstract class in commonMain" in f for f in findings))

    def test_ignores_abstract_class_with_no_abstract_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/utils/src/commonMain/kotlin/Utils.kt",
                "abstract class Utils {\n"
                "    fun helper() { println(1) }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("extensible abstract class in commonMain" in f for f in findings))

    def test_ignores_same_shape_outside_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "app/androidApp/src/androidMain/kotlin/BaseActivity.kt",
                "abstract class BaseActivity {\n"
                "    abstract fun onCreateContent()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("extensible abstract class in commonMain" in f for f in findings))


class ModuleLayerViolationTests(unittest.TestCase):
    """A module can declare a wrong-direction Gradle dependency (e.g. :ui directly on
    :data, skipping :presenter) without ever forming a literal cycle — Gradle happily
    builds it, and the existing Detekt import-boundary rules only check file-level
    imports, which can miss a violation declared in build.gradle.kts before any file
    uses it. This detector parses the real Gradle module graph directly.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_ui_depending_directly_on_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/build.gradle.kts",
                "dependencies {\n    implementation(projects.feature.auth.data)\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("module layer-order violation" in f for f in findings))

    def test_flags_data_depending_on_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/data/build.gradle.kts",
                "dependencies {\n    implementation(projects.feature.auth.domain)\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("module layer-order violation" in f for f in findings))

    def test_flags_cross_feature_module_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/build.gradle.kts",
                "dependencies {\n    implementation(projects.feature.payments.api)\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("cross-feature module dependency" in f for f in findings))

    def test_ignores_correctly_layered_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layers = {
                "model": "",
                "api": "implementation(projects.feature.auth.model)",
                "domain": "implementation(projects.feature.auth.api)",
                "data": "implementation(projects.feature.auth.api)\n    implementation(projects.core.network)",
                "presenter": "implementation(projects.feature.auth.domain)",
                "ui": "implementation(projects.feature.auth.presenter)",
            }
            for layer, dep in layers.items():
                self._write(
                    root, f"feature/auth/{layer}/build.gradle.kts",
                    f"dependencies {{\n    {dep}\n}}\n",
                )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("module layer-order violation" in f for f in findings))
            self.assertFalse(any("cross-feature module dependency" in f for f in findings))

    def test_ignores_core_module_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/data/build.gradle.kts",
                "dependencies {\n    implementation(projects.feature.auth.api)\n"
                "    implementation(projects.core.network)\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertEqual(
                [f for f in findings if "layer-order" in f or "cross-feature module" in f], []
            )


class ToggleLayoutStabilityTests(unittest.TestCase):
    def _write(self, root: Path, filename: str, content: str) -> None:
        d = root / "src" / "commonMain" / "kotlin" / "ui"
        d.mkdir(parents=True, exist_ok=True)
        (d / filename).write_text(content, encoding="utf-8")

    def test_flags_icon_swap_between_chevron_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "Trigger.kt",
                "@Composable\nfun Trigger(isExpanded: Boolean) {\n"
                "    if (isExpanded) {\n"
                "        Icon(imageVector = Icons.Default.KeyboardArrowUp, contentDescription = null)\n"
                "    } else {\n"
                "        Icon(imageVector = Icons.Default.KeyboardArrowDown, contentDescription = null)\n"
                "    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("toggle icon swap instead of rotation" in f for f in findings))

    def test_ignores_icon_swap_when_graphics_layer_rotation_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "Trigger.kt",
                "@Composable\nfun Trigger(isExpanded: Boolean) {\n"
                "    val rotation by animateFloatAsState(if (isExpanded) 180f else 0f)\n"
                "    Icon(\n"
                "        imageVector = Icons.Default.KeyboardArrowDown,\n"
                "        contentDescription = null,\n"
                "        modifier = Modifier.graphicsLayer { rotationZ = rotation },\n"
                "    )\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("toggle icon swap instead of rotation" in f for f in findings))

    def test_ignores_single_icon_with_no_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "Trigger.kt",
                "@Composable\nfun Trigger() {\n"
                "    Icon(imageVector = Icons.Default.KeyboardArrowDown, contentDescription = null)\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("toggle icon swap instead of rotation" in f for f in findings))

    def test_flags_bare_conditional_around_composable_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "Collapsible.kt",
                "@Composable\nfun Collapsible(isExpanded: Boolean) {\n"
                "    Column {\n        TriggerRow()\n"
                "        if (isExpanded) {\n            Text(\"content\")\n        }\n    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("bare conditional collapse" in f for f in findings))

    def test_ignores_animated_visibility_wrapped_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "Collapsible.kt",
                "@Composable\nfun Collapsible(isExpanded: Boolean) {\n"
                "    Column {\n        TriggerRow()\n"
                "        AnimatedVisibility(visible = isExpanded) {\n            Text(\"content\")\n        }\n    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("bare conditional collapse" in f for f in findings))

    def test_ignores_bare_conditional_without_composable_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "Toggle.kt",
                "@Composable\nfun Toggle(isExpanded: Boolean) {\n"
                "    if (isExpanded) {\n        println(\"expanded\")\n    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("bare conditional collapse" in f for f in findings))


class DesignSystemPrefixMismatchTests(unittest.TestCase):
    def _write_docs(self, root: Path, prefix: str) -> None:
        d = root / "docs"
        d.mkdir(parents=True, exist_ok=True)
        (d / "design-system.md").write_text(
            f"| Field | Value |\n|---|---|\n| Component prefix | {prefix} |\n",
            encoding="utf-8",
        )

    def _write_component(self, root: Path, filename: str, fn_name: str) -> None:
        d = root / "core" / "designsystem" / "components"
        d.mkdir(parents=True, exist_ok=True)
        (d / filename).write_text(
            f"@Composable\nfun {fn_name}(onClick: () -> Unit) {{}}\n", encoding="utf-8"
        )

    def test_flags_app_named_component_when_prefix_resolved_differently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_docs(root, "GuildBase")
            self._write_component(root, "AppButton.kt", "AppButton")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("design system prefix mismatch" in f for f in findings))

    def test_ignores_consistent_resolved_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_docs(root, "GuildBase")
            self._write_component(root, "GuildBaseButton.kt", "GuildBaseButton")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("design system prefix mismatch" in f for f in findings))

    def test_ignores_when_prefix_genuinely_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_docs(root, "App")
            self._write_component(root, "AppButton.kt", "AppButton")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("design system prefix mismatch" in f for f in findings))

    def test_ignores_when_no_design_system_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_component(root, "AppButton.kt", "AppButton")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("design system prefix mismatch" in f for f in findings))

    def test_ignores_unfilled_template_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_docs(root, "COMPONENT_PREFIX")
            self._write_component(root, "AppButton.kt", "AppButton")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("design system prefix mismatch" in f for f in findings))


class StyleApiComplianceTests(unittest.TestCase):
    def _write(self, root: Path, name: str, content: str) -> None:
        d = root / "app" / "src" / "commonMain" / "kotlin"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(content, encoding="utf-8")

    def test_flags_style_default_with_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Bad.kt",
                "@Composable\nfun BadButton(style: Style = Style { background(Color.Red) }) {}\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("style default with body" in f for f in findings))

    def test_ignores_empty_style_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Good.kt", "@Composable\nfun GoodButton(style: Style = Style) {}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("style default with body" in f for f in findings))

    def test_flags_style_state_wrong_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Bad.kt",
                "fun x() {\n    val styleState = remember { MutableStyleState(i) }\n    styleState.enabled = true\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("style state wrong enabled property" in f for f in findings))

    def test_ignores_correct_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Good.kt",
                "fun x() {\n    val styleState = rememberUpdatedStyleState(i) { it.isEnabled = true }\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("style state wrong enabled property" in f for f in findings))

    def test_flags_style_param_on_screen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Bad.kt", "@Composable\nfun HomeScreen(style: Style = Style) {}\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("style param on screen composable" in f for f in findings))

    def test_ignores_style_param_on_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Good.kt", "@Composable\nfun AppButton(style: Style = Style) {}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("style param on screen composable" in f for f in findings))

    def test_flags_stale_compositionlocal_in_style_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Bad.kt",
                "@Composable\n"
                "fun containerStyle(): Style {\n"
                "    val background = MaterialTheme.colorScheme.background\n"
                "    return Style {\n"
                "        background(background)\n"
                "    }\n"
                "}\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("stale compositionlocal in style function" in f for f in findings))

    def test_ignores_style_scope_extension_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Good.kt",
                "val containerStyle = Style {\n    background(colors.background)\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("stale compositionlocal in style function" in f for f in findings))

    def test_flags_missing_indication_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Bad.kt",
                "val s = Style {\n    pressed { animate { background(Color.Red) } }\n}\n"
                "fun x() {\n    Modifier.clickable(onClick = {})\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("missing indication null with style state" in f for f in findings))

    def test_ignores_when_indication_null_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "Good.kt",
                "val s = Style {\n    pressed { animate { background(Color.Red) } }\n}\n"
                "fun x() {\n    Modifier.clickable(onClick = {}, indication = null)\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("missing indication null with style state" in f for f in findings))


class HardcodedVersionCodeTests(unittest.TestCase):
    def test_flags_literal_version_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "androidApp"
            d.mkdir(parents=True)
            (d / "build.gradle.kts").write_text(
                'plugins { id("com.android.application") }\n'
                "android {\n"
                "    defaultConfig {\n"
                '        applicationId = "com.example.app"\n'
                "        versionCode = 1\n"
                '        versionName = "1.19.1"\n'
                "    }\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded android versioncode" in f for f in findings))

    def test_ignores_derived_formula(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "androidApp"
            d.mkdir(parents=True)
            (d / "build.gradle.kts").write_text(
                'plugins { id("com.android.application") }\n'
                "android {\n"
                "    defaultConfig {\n"
                '        applicationId = "com.example.app"\n'
                "        versionCode = major * 1_000_000 + minor * 1_000 + patch\n"
                "    }\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded android versioncode" in f for f in findings))

    def test_ignores_variable_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "androidApp"
            d.mkdir(parents=True)
            (d / "build.gradle.kts").write_text(
                'plugins { id("com.android.application") }\n'
                "val computedVersionCode = 1_000_002\n"
                "android {\n"
                "    defaultConfig {\n"
                '        applicationId = "com.example.app"\n'
                "        versionCode = computedVersionCode\n"
                "    }\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded android versioncode" in f for f in findings))

    def test_ignores_non_android_app_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "someModule"
            d.mkdir(parents=True)
            (d / "build.gradle.kts").write_text("val versionCode = 1\n", encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded android versioncode" in f for f in findings))


class HasAndCountFilesAlwaysTrueRegressionTests(unittest.TestCase):
    """A severe pre-existing bug found during a full self-audit: _has() tested
    `any(root.rglob(g) for g in globs)` — each item any() saw was a whole generator
    object (from the nested generator expression), and generator objects are always
    truthy regardless of whether they yield anything. _has() therefore returned True
    for every project regardless of whether the file actually existed, silently
    disabling _detect_detekt's HIGH-priority "no Detekt gates" adoption-plan trigger
    and the version-catalog/tests detectors for every project ever audited. No prior
    test caught this because none exercised the genuinely-missing case.
    """

    def test_has_returns_false_when_nothing_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "App.kt").write_text("fun main() {}", encoding="utf-8")
            self.assertFalse(audit_scripts._has(root, "detekt.yml", "detekt.yaml"))

    def test_has_returns_true_when_something_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "detekt.yml").write_text("", encoding="utf-8")
            self.assertTrue(audit_scripts._has(root, "detekt.yml", "detekt.yaml"))

    def test_count_files_returns_zero_when_nothing_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "App.kt").write_text("fun main() {}", encoding="utf-8")
            self.assertEqual(audit_scripts._count_files(root, "*Test.kt", "*Spec.kt"), 0)

    def test_detect_detekt_reports_missing_for_a_clean_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "App.kt").write_text("fun main() {}", encoding="utf-8")
            self.assertEqual(audit_scripts._detect_detekt(root), "missing")

    def test_detect_version_catalog_reports_missing_for_a_clean_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "App.kt").write_text("fun main() {}", encoding="utf-8")
            self.assertEqual(audit_scripts._detect_version_catalog(root), "missing")

    def test_detect_tests_reports_none_for_a_clean_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "App.kt").write_text("fun main() {}", encoding="utf-8")
            self.assertEqual(audit_scripts._detect_tests(root), "none")

    def test_has_ignores_a_deployed_skill_template_libs_versions_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / ".claude" / "skills" / "kmp-feature-scaffold" / "templates" / "gradle"
            d.mkdir(parents=True)
            (d / "libs.versions.toml").write_text('[versions]\nkotlin = "2.4.0"\n', encoding="utf-8")
            self.assertEqual(audit_scripts._detect_version_catalog(root), "missing")

    def test_count_files_ignores_a_deployed_skill_test_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = (
                root / ".claude" / "skills" / "kmp-compose-design-system"
                / "detekt-rules" / "src" / "test" / "kotlin"
            )
            d.mkdir(parents=True)
            (d / "ComponentRegistryRuleTest.kt").write_text("class ComponentRegistryRuleTest", encoding="utf-8")
            self.assertEqual(audit_scripts._detect_tests(root), "none")


class DeployedSkillsBundleExclusionTests(unittest.TestCase):
    """A real bug: a consumer project with skills deployed to .claude/skills/ got a
    'hardcoded android versioncode' false positive from kmp-feature-scaffold's
    own templates/androidApp/build.gradle.kts (versionCode = 1 is a legitimate scaffold
    placeholder, not the user's real app config). _EXCLUDED_DIRS now excludes deployed
    agent skills bundle directories entirely.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_ignores_scaffold_template_under_claude_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                ".claude/skills/kmp-feature-scaffold/templates/androidApp/build.gradle.kts",
                'plugins { id("com.android.application") }\n'
                "android {\n    defaultConfig {\n"
                '        applicationId = "com.example.app"\n'
                "        versionCode = 1\n    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded android versioncode" in f for f in findings))

    def test_still_flags_real_project_code_alongside_deployed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                ".claude/skills/kmp-feature-scaffold/templates/androidApp/build.gradle.kts",
                "android {\n    defaultConfig {\n        versionCode = 1\n    }\n}\n",
            )
            self._write(
                root,
                "app/shared/src/commonMain/kotlin/App.kt",
                "val Ink = androidx.compose.ui.graphics.Color(0xFFE9EDF7)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded android versioncode" in f for f in findings))
            self.assertTrue(any("magic color literal" in f for f in findings))

    def test_ignores_content_under_codex_and_cursor_and_continue_skills(self) -> None:
        for agent_dir in (".codex", ".cursor", ".continue"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._write(
                    root,
                    f"{agent_dir}/skills/kmp-feature-scaffold/templates/androidApp/build.gradle.kts",
                    "android {\n    defaultConfig {\n        versionCode = 1\n    }\n}\n",
                )
                findings = audit_scripts.audit_project(root)
                self.assertFalse(
                    any("hardcoded android versioncode" in f for f in findings),
                    f"false positive under {agent_dir}/skills/",
                )

    def test_mvi_placement_ignores_deployed_skill_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                ".claude/skills/kmp-mvi/templates/MviViewModel.kt",
                "abstract class MviViewModel<State, Intent, Effect>",
            )
            findings = audit_scripts._detect_mvi_placement(root)
            self.assertEqual(findings, [])

    def test_design_system_wiring_ignores_deployed_skill_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                ".claude/skills/kmp-compose-design-system/templates/AppTheme.kt",
                "@Composable\nfun AppTheme(content: @Composable () -> Unit) {\n"
                "    MaterialTheme(content = content)\n}\n",
            )
            findings = audit_scripts._detect_design_system_wiring(root)
            self.assertEqual(findings, [])


class LayoutGuardrailTests(unittest.TestCase):
    def test_flags_arbitrary_weight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "S.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable fun S() { Box(Modifier.weight(0.37f)) }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("raw weight literal" in f for f in findings))

    def test_ignores_simple_fractions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "S.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable fun S() { Row { Box(Modifier.weight(1f)); Box(Modifier.weight(1.5f)) } }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raw weight literal" in f for f in findings))

    def test_flags_partial_breakpoint_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "P.kt").write_text(
                "fun p(w: WindowSizeClass) { when (w.widthSizeClass) { WindowWidthSizeClass.Compact -> a() } }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("breakpoint branch missing" in f for f in findings))

    def test_full_coverage_and_else_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "F.kt").write_text(
                "fun f(w: WindowSizeClass) { when (w.widthSizeClass) {\n"
                "    WindowWidthSizeClass.Compact -> a()\n"
                "    WindowWidthSizeClass.Medium -> b()\n"
                "    WindowWidthSizeClass.Expanded -> c()\n"
                "} }\n",
                encoding="utf-8",
            )
            (d / "E.kt").write_text(
                "fun e(w: WindowSizeClass) { when (w.widthSizeClass) {\n"
                "    WindowWidthSizeClass.Compact -> a()\n"
                "    else -> b()\n"
                "} }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("breakpoint branch missing" in f for f in findings))


class FixedWidthOverflowTests(unittest.TestCase):
    def test_flags_large_fixed_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "S.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun S() { Box(Modifier.width(400.dp)) }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("fixed width overflow" in f for f in findings))

    def test_flags_required_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "S.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun S() { Card(Modifier.requiredWidth(300.dp)) }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("fixed width overflow" in f for f in findings))

    def test_ignores_small_and_responsive_widths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "S.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun S() { Box(Modifier.width(48.dp).fillMaxWidth()) }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("fixed width overflow" in f for f in findings))


class RawComponentBypassTests(unittest.TestCase):
    def _ds_marker(self, d: Path) -> None:
        # A file that establishes the project HAS a design system.
        (d / "AppButton.kt").write_text(
            "import androidx.compose.runtime.Composable\n"
            "@Composable\nfun AppButton(onClick: () -> Unit) { BasicText(\"x\") }\n",
            encoding="utf-8",
        )

    def test_flags_raw_components_when_design_system_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            self._ds_marker(d)
            (d / "HomeScreen.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\n"
                "fun HomeScreen() {\n"
                "    Scaffold {\n"
                "        Button(onClick = {}) { Text(\"Save\") }\n"
                "        Card { Text(\"hi\") }\n"
                "    }\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("raw component bypass" in f for f in findings))

    def test_ignores_app_wrapper_definition_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            self._ds_marker(d)
            # AppCard.kt defines a wrapper and legitimately uses a raw Card internally
            (d / "AppCard.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun AppCard(content: @Composable () -> Unit) { Card { content() } }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("AppCard.kt" in f and "raw component bypass" in f for f in findings))

    def test_ignores_screen_using_app_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            self._ds_marker(d)
            (d / "GoodScreen.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun GoodScreen() { AppScaffold { AppButton(onClick = {}) {} } }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("GoodScreen.kt" in f and "raw component bypass" in f for f in findings))

    def test_ignores_project_without_design_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            # No App* / AppTheme anywhere — raw Material is the project's choice.
            (d / "HomeScreen.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun HomeScreen() { Scaffold { Button(onClick = {}) {} } }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raw component bypass" in f for f in findings))


class ShadcnRawComponentBypassTests(unittest.TestCase):
    def _shadcn_marker(self, d: Path) -> None:
        (d / "ShadcnButton.kt").write_text(
            "import androidx.compose.runtime.Composable\n"
            "@Composable\nfun ShadcnButton(onClick: () -> Unit) { Button(onClick) { } }\n",
            encoding="utf-8",
        )

    def test_flags_raw_button_and_card_in_shadcn_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            self._shadcn_marker(d)
            (d / "HomeScreen.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\n"
                "fun HomeScreen() {\n"
                "    Button(onClick = {}) { Text(\"Save\") }\n"
                "    Card { Text(\"hi\") }\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(
                any("raw component bypass" in f and "ShadcnButton" in f for f in findings)
            )

    def test_does_not_flag_scaffold_or_topappbar_in_shadcn_project(self) -> None:
        # shadcn/ui has no Scaffold/TopAppBar concept — /kmp-migrate-to-shadcn's own
        # mapping table says keep raw Compose Scaffold/TopAppBar; flagging it would be wrong.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            self._shadcn_marker(d)
            (d / "HomeScreen.kt").write_text(
                "import androidx.compose.runtime.Composable\n"
                "@Composable\n"
                "fun HomeScreen() { Scaffold(topBar = { TopAppBar(title = {}) }) { } }\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("raw component bypass" in f for f in findings))

    def test_ignores_shadcn_wrapper_definition_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            self._shadcn_marker(d)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("ShadcnButton.kt" in f and "raw component bypass" in f for f in findings))


class LeftoverWizardDemoCodeTests(unittest.TestCase):
    def test_flags_greeting_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "shared" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "Greeting.kt").write_text(
                "class Greeting {\n    fun greet(): String = \"Hello\"\n}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("leftover wizard demo code" in f for f in findings))

    def test_flags_compose_multiplatform_resource_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "shared" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "App.kt").write_text(
                "import kotlinproject.app.shared.generated.resources.compose_multiplatform\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("leftover wizard demo code" in f for f in findings))

    def test_ignores_project_with_no_demo_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "shared" / "src" / "commonMain" / "kotlin"
            d.mkdir(parents=True)
            (d / "App.kt").write_text(
                "@Composable\nfun App() { AppTheme { } }\n", encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("leftover wizard demo code" in f for f in findings))


class FindingEvidenceTests(unittest.TestCase):
    def test_findings_include_file_line_and_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "HomeScreen.kt").write_text(
                "@Composable\n"
                "fun HomeScreen() {\n"
                "    HorizontalDivider(color = Color.Gray)\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            divider = next(f for f in findings if "hardcoded divider color" in f)
            # file:line anchor present
            self.assertIn("HomeScreen.kt:3", divider)
            # matched source line included as evidence
            self.assertIn("HorizontalDivider(color = Color.Gray)", divider)
            # severity tag preserved for release-gate parsing
            self.assertTrue(any("[HIGH]" in f or "[MEDIUM]" in f or ":" in f for f in findings))


class RepositoryLeakTests(unittest.TestCase):
    def test_flags_interface_returning_dto(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "user" / "api" / "src"
            d.mkdir(parents=True)
            (d / "UserRepository.kt").write_text(
                "interface UserRepository {\n"
                "    suspend fun getUser(id: String): UserDto\n"
                "    fun observeUsers(): Flow<List<UserEntity>>\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("repository leaks data type" in f for f in findings))

    def test_ignores_interface_with_domain_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "product" / "api" / "src"
            d.mkdir(parents=True)
            (d / "ProductRepository.kt").write_text(
                "interface ProductRepository {\n"
                "    suspend fun getProduct(id: String): Product\n"
                "    fun observeProducts(): Flow<List<Product>>\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("repository leaks data type" in f for f in findings))

    def test_ignores_repository_impl_using_dto_internally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "product" / "data" / "src"
            d.mkdir(parents=True)
            (d / "ProductRepositoryImpl.kt").write_text(
                "class ProductRepositoryImpl(private val api: ProductApi) : ProductRepository {\n"
                "    override suspend fun getProduct(id: String): Product {\n"
                "        val dto: ProductDto = api.fetch(id)\n"
                "        return dto.toDomain()\n"
                "    }\n"
                "}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("repository leaks data type" in f for f in findings))

    def test_flags_entity_import_in_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "user" / "domain" / "src"
            d.mkdir(parents=True)
            (d / "GetUser.kt").write_text(
                "import com.example.data.entity.UserEntity\nclass GetUser {}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("dto leak to domain" in f for f in findings))


class StringNavigationTests(unittest.TestCase):
    def test_flags_string_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "AppNavHost.kt").write_text(
                'NavHost(navController, startDestination = "home") {\n'
                '    composable("home") { HomeScreen() }\n'
                '    composable(route = "detail/{id}") { DetailScreen() }\n'
                '}\n'
                'fun go() { navController.navigate("home") }\n',
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("string navigation" in f for f in findings))

    def test_ignores_type_safe_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "AppNavHost.kt").write_text(
                'NavHost(navController, startDestination = HomeRoute) {\n'
                '    composable<HomeRoute> { HomeScreen() }\n'
                '    composable<DetailRoute> { DetailScreen() }\n'
                '}\n'
                'fun go() { navController.navigate(HomeRoute) }\n',
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("string navigation" in f for f in findings))

    def test_ignores_deep_link_uri_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "app" / "src" / "main" / "kotlin"
            d.mkdir(parents=True)
            (d / "DeepLink.kt").write_text(
                'fun open() { navController.navigate("myapp://detail/42") }\n',
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("string navigation" in f for f in findings))


class ViewModelAsComposableParamTests(unittest.TestCase):
    def test_flags_composable_with_required_viewmodel_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "home" / "ui" / "src"
            d.mkdir(parents=True)
            (d / "HomeScreen.kt").write_text(
                "@Composable\n"
                "fun HomeScreen(studioVm: StudioViewModel, healthVm: HealthViewModel) {}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel as composable param" in f for f in findings))

    def test_ignores_defaulted_koinviewmodel_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "home" / "ui" / "src"
            d.mkdir(parents=True)
            (d / "HomeScreen.kt").write_text(
                "@Composable\n"
                "fun HomeScreen(vm: HomeViewModel = koinViewModel()) {}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel as composable param" in f for f in findings))

    def test_ignores_content_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "feature" / "home" / "ui" / "src"
            d.mkdir(parents=True)
            (d / "HomeContent.kt").write_text(
                "@Composable\n"
                "fun HomeContent(state: FooState, onIntent: (FooIntent) -> Unit) {}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel as composable param" in f for f in findings))

    def test_flags_outside_ui_path(self) -> None:
        # No /ui/ segment — common when a project does not use the layered module convention.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "composeApp" / "src" / "commonMain" / "kotlin" / "home"
            d.mkdir(parents=True)
            (d / "HomeScreen.kt").write_text(
                "@Composable\n"
                "fun HomeScreen(studioVm: StudioViewModel) {}\n",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel as composable param" in f for f in findings))


class GodComposableTests(unittest.TestCase):
    def test_flags_screen_with_many_launched_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "studio" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            body = "\n".join(f"LaunchedEffect(key{i}) {{ doThing() }}" for i in range(6))
            (ui_dir / "HomeScreen.kt").write_text(body, encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god composable" in f for f in findings))

    def test_flags_screen_with_many_effect_collects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "studio" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            body = "\n".join(f"vm{i}.effect.collect {{ relay() }}" for i in range(3))
            (ui_dir / "HomeScreen.kt").write_text(body, encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god composable" in f for f in findings))

    def test_high_severity_for_extreme_orchestration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "studio" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            body = "\n".join(f"LaunchedEffect(key{i}) {{ x() }}" for i in range(9))
            (ui_dir / "HomeScreen.kt").write_text(body, encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god composable [HIGH]" in f for f in findings))

    def test_ignores_screen_with_one_launched_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "LaunchedEffect(vm) { vm.effect.collect { } }",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god composable" in f for f in findings))


class RedundantTitleTests(unittest.TestCase):
    def test_flags_screen_with_topbar_and_heading_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "fun HomeScreen() {\n"
                "  AppScaffold(topBar = { AppTopAppBar(title = \"Home\") }) {\n"
                "    AppText(\"Home\", style = AppTextStyle.HeadlineLarge)\n"
                "  }\n"
                "}",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("redundant screen title" in f for f in findings))

    def test_ignores_screen_with_only_topbar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "fun HomeScreen() {\n"
                "  AppScaffold(topBar = { AppTopAppBar(title = \"Home\") }) {\n"
                "    AppText(\"Welcome back\", style = AppTextStyle.BodyLarge)\n"
                "  }\n"
                "}",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("redundant screen title" in f for f in findings))

    def test_ignores_non_screen_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeViewModel.kt").write_text(
                "fun HomeViewModel() {\n"
                "  AppScaffold(topBar = { AppTopAppBar(title = \"Home\") }) {\n"
                "    AppText(\"Home\", style = AppTextStyle.H1)\n"
                "  }\n"
                "}",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("redundant screen title" in f for f in findings))


class AdaptiveCoverageTests(unittest.TestCase):
    def test_flags_screen_missing_windowsizeclass_when_project_uses_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            # One file that uses WindowSizeClass (triggers the check)
            (ui_dir / "AppRoot.kt").write_text(
                "val wsc: WindowSizeClass = calculateWindowSizeClass()",
                encoding="utf-8",
            )
            # Screen that doesn't receive it
            (ui_dir / "HomeScreen.kt").write_text(
                "fun HomeScreen(onBack: () -> Unit) {}",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("adaptive coverage" in f for f in findings))

    def test_ignores_project_without_windowsizeclass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "HomeScreen.kt").write_text(
                "fun HomeScreen(onBack: () -> Unit) {}",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("adaptive coverage" in f for f in findings))

    def test_ignores_screen_that_has_windowsizeclass_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "feature" / "home" / "ui" / "src"
            ui_dir.mkdir(parents=True)
            (ui_dir / "AppRoot.kt").write_text(
                "val wsc: WindowSizeClass = calculateWindowSizeClass()",
                encoding="utf-8",
            )
            (ui_dir / "HomeScreen.kt").write_text(
                "fun HomeScreen(windowSizeClass: WindowSizeClass, onBack: () -> Unit) {}",
                encoding="utf-8",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("adaptive coverage" in f for f in findings))


class HarvestProjectTests(unittest.TestCase):
    """Tests for --harvest mode and _detect_positive_patterns."""

    def test_harvest_returns_findings_and_lessons_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = audit_scripts.harvest_project(root)
            self.assertIn("project", result)
            self.assertIn("findings", result)
            self.assertIn("lessons", result)
            self.assertIsInstance(result["findings"], list)
            self.assertIsInstance(result["lessons"], list)

    def test_harvest_detects_local_app_dark_theme_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AppTheme.kt").write_text(
                "val LocalAppDarkTheme = compositionLocalOf<Boolean?> { null }\n"
                "fun isDark(): Boolean = LocalAppDarkTheme.current ?: isSystemInDarkTheme()\n",
                encoding="utf-8",
            )
            lessons = audit_scripts._detect_positive_patterns(root)
            patterns = [l["pattern"] for l in lessons]
            self.assertTrue(
                any("LocalAppDarkTheme" in p for p in patterns),
                f"Expected LocalAppDarkTheme lesson, got: {patterns}",
            )

    def test_harvest_detects_undo_window_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "FooViewModel.kt").write_text(
                "private const val UNDO_WINDOW_MS = 4500L\n"
                "private var undoJob: Job? = null\n",
                encoding="utf-8",
            )
            lessons = audit_scripts._detect_positive_patterns(root)
            patterns = [l["pattern"] for l in lessons]
            self.assertTrue(
                any("undo" in p.lower() for p in patterns),
                f"Expected undo-window lesson, got: {patterns}",
            )

    def test_harvest_detects_build_logic_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_logic = root / "build-logic" / "convention"
            build_logic.mkdir(parents=True)
            (build_logic / "build.gradle.kts").write_text("plugins { `kotlin-dsl` }", encoding="utf-8")
            lessons = audit_scripts._detect_positive_patterns(root)
            patterns = [l["pattern"] for l in lessons]
            self.assertTrue(
                any("build-logic" in p.lower() for p in patterns),
                f"Expected build-logic lesson, got: {patterns}",
            )

    def test_harvest_cli_outputs_json(self) -> None:
        import subprocess, json as _json
        with tempfile.TemporaryDirectory() as tmp:
            audit_script = REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_project.py"
            result = subprocess.run(
                ["python3", str(audit_script), "--harvest", tmp],
                capture_output=True,
                text=True,
            )
            self.assertIn(result.returncode, (0, 1), "harvest should exit 0 or 1 only")
            parsed = _json.loads(result.stdout)
            self.assertIn("findings", parsed)
            self.assertIn("lessons", parsed)

    def test_harvest_detects_full_claude_scaffold_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CLAUDE.md").write_text("--system-prompt-file=.claude/AGENTS.md\n", encoding="utf-8")
            for rel in ("agents", "rules", "hooks", "commands", "skills", "docs/reference"):
                (root / rel).mkdir(parents=True, exist_ok=True)
            (root / "docs" / "reference" / "ai-collaboration.md").write_text("# AI Collaboration\n", encoding="utf-8")
            (root / "docs" / "reference" / "agent-catalog.md").write_text("# Agent Catalog\n", encoding="utf-8")
            claude = root / ".claude"
            (claude / "commands").mkdir(parents=True)
            (claude / "skills" / "demo").mkdir(parents=True)
            (claude / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")

            lessons = audit_scripts._detect_positive_patterns(root)
            patterns = [lesson["pattern"] for lesson in lessons]

            self.assertTrue(
                any("Full Claude scaffold" in pattern for pattern in patterns),
                patterns,
            )


class HardcodedBaseUrlTests(unittest.TestCase):
    """Library-first requires configurability — a base URL baked in as a string
    literal builds and runs fine today, then becomes tech debt the moment a second
    environment or a library consumer needs a different endpoint.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_hardcoded_https_url_in_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/src/commonMain/kotlin/ApiConfig.kt",
                'val BASE_URL = "https://api.example.com/v1"\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded base URL" in f for f in findings))

    def test_ignores_url_routed_through_buildkonfig(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/src/commonMain/kotlin/ApiConfig.kt",
                'val BASE_URL = BuildKonfig.API_BASE_URL\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded base URL" in f for f in findings))

    def test_ignores_hardcoded_url_outside_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/src/androidMain/kotlin/ApiConfig.kt",
                'val BASE_URL = "https://api.example.com/v1"\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded base URL" in f for f in findings))

    def test_ignores_hardcoded_url_in_test_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/src/commonTest/kotlin/ApiConfigTest.kt",
                'val BASE_URL = "https://api.example.com/v1"\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded base URL" in f for f in findings))


class ProjectSkillStandardsTests(unittest.TestCase):
    """A project-owned skill at <project root>/skills/<skill-name>/ should meet the
    real skill anatomy (verified against anthropic-skills:skill-creator's own
    documented convention): SKILL.md required, opening YAML frontmatter with name
    and description, body under ~500 lines unless a references/ dir exists.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_skill_folder_missing_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "my-skill").mkdir(parents=True)
            (root / "skills" / "my-skill" / "notes.md").write_text("stub", encoding="utf-8")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill missing SKILL.md" in f for f in findings))

    def test_flags_missing_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "skills/my-skill/SKILL.md", "# My Skill\n\nNo frontmatter here.\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill missing frontmatter" in f for f in findings))

    def test_flags_frontmatter_missing_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "skills/my-skill/SKILL.md",
                "---\ndescription: Does a thing.\n---\n\nBody text.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("frontmatter missing name" in f for f in findings))

    def test_flags_frontmatter_missing_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "skills/my-skill/SKILL.md",
                "---\nname: my-skill\n---\n\nBody text.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("frontmatter missing description" in f for f in findings))

    def test_flags_body_over_500_lines_without_references_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = "\n".join(f"line {i}" for i in range(600))
            self._write(
                root, "skills/my-skill/SKILL.md",
                f"---\nname: my-skill\ndescription: Does a thing.\n---\n\n{body}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("exceeds 500-line guideline" in f for f in findings))

    def test_ignores_long_body_with_references_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = "\n".join(f"line {i}" for i in range(600))
            self._write(
                root, "skills/my-skill/SKILL.md",
                f"---\nname: my-skill\ndescription: Does a thing.\n---\n\n{body}\n",
            )
            (root / "skills" / "my-skill" / "references").mkdir(parents=True)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("exceeds 500-line guideline" in f for f in findings))

    def test_compliant_skill_has_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_text = "---\nname: my-skill\ndescription: Does a thing.\n---\n\nShort body.\n"
            self._write(root, "skills/my-skill/SKILL.md", skill_text)
            self._write(root, ".claude/skills/my-skill/SKILL.md", skill_text)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any(f.startswith("project skill") for f in findings))

    def test_flags_skill_name_dir_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_text = "---\nname: other-name\ndescription: Does a thing.\n---\n\nBody.\n"
            self._write(root, "skills/my-skill/SKILL.md", skill_text)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill name directory mismatch" in f for f in findings))

    def test_flags_skill_name_invalid_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_text = "---\nname: My_Skill\ndescription: Does a thing.\n---\n\nBody.\n"
            self._write(root, "skills/My_Skill/SKILL.md", skill_text)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill name invalid format" in f for f in findings))

    def test_flags_skill_micro_scoped_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_text = "---\nname: fix-login-error\ndescription: Fixes login.\n---\n\nBody.\n"
            self._write(root, "skills/fix-login-error/SKILL.md", skill_text)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill micro-scoped / too specific" in f for f in findings))

    def test_flags_skill_description_exceeds_1024_chars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            long_desc = "a" * 1050
            skill_text = f"---\nname: my-skill\ndescription: {long_desc}\n---\n\nBody.\n"
            self._write(root, "skills/my-skill/SKILL.md", skill_text)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill description exceeds 1024 chars" in f for f in findings))

    def test_no_skills_dir_returns_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any(f.startswith("project skill") for f in findings))

    def test_flags_project_skill_missing_deployed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "skills/my-skill/SKILL.md",
                "---\nname: my-skill\ndescription: Does a thing.\n---\n\nShort body.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill not deployed" in f for f in findings))

    def test_flags_project_skill_deployment_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "skills/my-skill/SKILL.md",
                "---\nname: my-skill\ndescription: Source copy.\n---\n\nSource body.\n",
            )
            self._write(
                root, ".claude/skills/my-skill/SKILL.md",
                "---\nname: my-skill\ndescription: Deployed copy.\n---\n\nOld body.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project skill deployment drift" in f for f in findings))

    def test_ignores_project_skill_when_deployed_copy_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_text = "---\nname: my-skill\ndescription: Does a thing.\n---\n\nShort body.\n"
            self._write(root, "skills/my-skill/SKILL.md", skill_text)
            self._write(root, ".claude/skills/my-skill/SKILL.md", skill_text)
            self._write(root, "skills/my-skill/references/usage.md", "# usage\n")
            self._write(root, ".claude/skills/my-skill/references/usage.md", "# usage\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("project skill not deployed" in f for f in findings))
            self.assertFalse(any("project skill deployment drift" in f for f in findings))


class WhatCommentInControlFlowTests(unittest.TestCase):
    """This detector shipped with no tests at all. An audit of the comment surface found
    it reported findings against lines containing no comment: it located comments with a
    plain `line.find("//")`, which also matches the `//` inside a URL string literal, so
    `val base = "https://build.example.com"` next to an `if` was reported as "this //
    comment narrates what the block does".
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def _findings(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "feature/x/src/commonMain/kotlin/F.kt", source)
            return [f for f in audit_scripts.audit_project(root)
                    if "what-comment in control flow" in f]

    def test_flags_what_narration_above_a_loop(self) -> None:
        self.assertTrue(self._findings(
            "fun a() {\n    // Loop through items\n    for (i in x) { p(i) }\n}\n"))

    def test_ignores_a_genuine_why_comment(self) -> None:
        self.assertFalse(self._findings(
            "fun b() {\n    // Workaround: driver rejects batches over 64\n"
            "    for (i in x) { p(i) }\n}\n"))

    def test_ignores_a_url_string_literal_in_a_conditional(self) -> None:
        # No comment on this line at all — the `//` belongs to `https://`.
        self.assertFalse(self._findings(
            'fun c() {\n    if (link == "https://get.myapp.io/share") { open() }\n}\n'))

    def test_ignores_a_url_assigned_above_a_conditional(self) -> None:
        self.assertFalse(self._findings(
            'fun d() {\n    val base = "https://build.example.com/v1"\n'
            '    if (base.isEmpty()) { p() }\n}\n'))

    def test_still_flags_a_real_comment_that_follows_a_url_string(self) -> None:
        # The string-literal skip must not swallow a genuine trailing comment.
        self.assertTrue(self._findings(
            'fun e() {\n    if (u == "https://a.io") { p() }  // check if ready\n}\n'))

    def test_handles_an_escaped_quote_before_the_comment(self) -> None:
        self.assertTrue(self._findings(
            'fun f() {\n    val s = "a\\"b"\n    if (s.isEmpty()) { p() }  // build the list\n}\n'))


class LongStackedCommentBlockTests(unittest.TestCase):
    """kmp-code-quality's own rule says a // block growing past ~4
    lines should split off to docs/reference/ — documented but never mechanically
    checked anywhere until this detector. Verified against a real false-positive
    risk: a license/copyright header at the top of a file is also a long stacked //
    block, but isn't the same problem this rule targets.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_five_line_comment_block_with_no_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Foo.kt",
                "fun a() {}\n\n"
                "// line one\n// line two\n// line three\n// line four\n// line five\n"
                "fun b() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("long stacked comment block" in f for f in findings))

    def test_ignores_block_with_docs_reference_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Foo.kt",
                "fun a() {}\n\n"
                "// line one\n// line two\n// line three\n// line four\n"
                "// Full rationale: docs/reference/foo.md\n"
                "fun b() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("long stacked comment block" in f for f in findings))

    def test_ignores_short_comment_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Foo.kt",
                "fun a() {}\n\n// line one\n// line two\nfun b() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("long stacked comment block" in f for f in findings))

    def test_ignores_leading_license_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Foo.kt",
                "// Copyright (c) Example Corp\n"
                "// Licensed under the Apache License, Version 2.0\n"
                "// you may not use this file except in compliance with the License.\n"
                "// You may obtain a copy of the License at\n"
                "// http://www.apache.org/licenses/LICENSE-2.0\n"
                "package com.example.x\n\n"
                "fun a() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("long stacked comment block" in f for f in findings))

    def test_ignores_genuine_why_explanation(self) -> None:
        # Real false-positive class: dense native/graphics pipeline code (Vulkan/
        # WebGPU/OpenGL) legitimately needs a long inline WHY explanation — moving it
        # to docs/reference/ would separate the reasoning from the exact code it
        # explains. 2+ causal/justifying signal words exempt the block.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "backend/vulkan/src/commonMain/kotlin/Vulkan.kt",
                "fun a() {}\n\n"
                "// The image layout transition must happen before the render pass begins,\n"
                "// because the driver assumes a specific layout at pass start on some\n"
                "// hardware. This is a workaround for a non-obvious constraint not\n"
                "// documented in the Vulkan spec itself, only observed empirically.\n"
                "fun transitionImage() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("long stacked comment block" in f for f in findings))

    def test_still_flags_lazy_narration_with_no_why_signal(self) -> None:
        # A block with zero/one causal signal words should still be flagged — the
        # WHY-exemption requires 2+ distinct signal words, not just one incidental
        # word, so this doesn't silently swallow the real anti-pattern.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "backend/vulkan/src/commonMain/kotlin/Vulkan.kt",
                "fun a() {}\n\n"
                "// Create the buffer.\n"
                "// Bind the memory.\n"
                "// Map the pointer.\n"
                "// Copy the data.\n"
                "// Unmap the pointer.\n"
                "fun uploadBuffer() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("long stacked comment block" in f for f in findings))


class JustificationCommentAboveSingleStatementTests(unittest.TestCase):
    """A 3+ line comment block justifying one Gradle dependency line — even a real,
    WHY-shaped reason doesn't need a paragraph to add one line. Distinct from the
    long-stacked-comment-block check above: this is short enough (often 3-4 lines) to
    duck under that check's 5-line threshold, and WHY-shaped enough to duck its
    WHY-signal exemption too. Confirmed real: a user reported an agent-written comment
    of this exact shape and asked for a mechanical backstop.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_justification_comment_above_single_dependency_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/build.gradle.kts",
                "// Dispatchers.setMain(Dispatchers.Default) is needed because SuggestedCueViewModel uses\n"
                "// androidx.lifecycle.viewModelScope, which resolves Dispatchers.Main via ServiceLoader --\n"
                "// absent on plain JVM outside Android/Compose. kotlinx-coroutines-test's setMain accepts any\n"
                "// real CoroutineDispatcher, not just TestDispatchers, so this isn't test-only despite the name.\n"
                "    implementation(libs.kotlinx.coroutinesTest)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(
                any("justification comment above single statement" in f for f in findings)
            )

    def test_ignores_short_comment_above_dependency_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/build.gradle.kts",
                "// pinned for CVE-2026-1234\n"
                "    implementation(libs.foo)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(
                any("justification comment above single statement" in f for f in findings)
            )

    def test_ignores_comment_block_above_a_block_opener(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/build.gradle.kts",
                "// line one\n// line two\n// line three\n"
                "dependencies {\n"
                "    implementation(libs.foo)\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(
                any("justification comment above single statement" in f for f in findings)
            )

    def test_ignores_kotlin_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/src/commonMain/kotlin/Foo.kt",
                "// line one\n// line two\n// line three\n"
                "fun implementation() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(
                any("justification comment above single statement" in f for f in findings)
            )


class DestructiveReadAccessorTests(unittest.TestCase):
    """A getter/consume function that clears the field it just read breaks the moment a
    second caller reads it in the same tick/request — the real bug found (and fixed) in
    awaken's Input.consumeTypedText()/consumeEditActions().
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_clear_call_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Input.kt",
                "class Input {\n"
                "    private val typedText = StringBuilder()\n"
                "    fun consumeTypedText(): String {\n"
                "        val value = typedText.toString()\n"
                "        typedText.clear()\n"
                "        return value\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("destructive read accessor" in f for f in findings))

    def test_flags_zero_assignment_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Input.kt",
                "class Input {\n"
                "    var scrollDeltaY: Float = 0f\n"
                "    fun consumeScrollDeltaY(): Float {\n"
                "        val delta = scrollDeltaY\n"
                "        scrollDeltaY = 0f\n"
                "        return delta\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("destructive read accessor" in f for f in findings))

    def test_ignores_snapshot_that_clears_a_different_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Input.kt",
                "class Input {\n"
                "    var scrollDeltaY: Float = 0f\n"
                "    var pointerX: Float = 0f\n"
                "    fun snapshot(): Float {\n"
                "        val delta = scrollDeltaY\n"
                "        pointerX = 0f\n"
                "        return delta\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("destructive read accessor" in f for f in findings))

    def test_ignores_read_without_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/x/src/commonMain/kotlin/Input.kt",
                "class Input {\n"
                "    var scrollDeltaY: Float = 0f\n"
                "    fun peekScrollDeltaY(): Float {\n"
                "        val delta = scrollDeltaY\n"
                "        log(delta)\n"
                "        return delta\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("destructive read accessor" in f for f in findings))


class ValueClassOpportunityTests(unittest.TestCase):
    """kmp-clean-architecture's Typed Domain IDs rule: nothing stops
    getOrder(userId, orderId) from compiling when both are raw String. This is an
    opportunity nudge, not a misuse flag.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_two_raw_id_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/Orders.kt",
                "fun getOrder(userId: String, orderId: String): Order = TODO()\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("value class opportunity" in f for f in findings))

    def test_ignores_single_id_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/Orders.kt",
                "fun getOrder(orderId: String): Order = TODO()\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("value class opportunity" in f for f in findings))

    def test_ignores_non_id_string_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/Orders.kt",
                "fun search(query: String, filter: String): List<Order> = TODO()\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("value class opportunity" in f for f in findings))

    def test_flags_long_id_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/Orders.kt",
                "fun link(userId: Long, orderId: Long): Unit = TODO()\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("value class opportunity" in f for f in findings))


class ContextParameterOpportunityTests(unittest.TestCase):
    """kmp-dependency-injection's Context Parameters section: a value
    threaded through many function signatures in the same file is a candidate for
    context(...) instead of an explicit parameter on every function.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_param_repeated_five_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = "\n".join(
                f"fun step{i}(logger: Logger, x: Int): Unit = TODO()" for i in range(5)
            )
            self._write(root, "feature/x/src/commonMain/kotlin/Steps.kt", body + "\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("context parameter opportunity" in f for f in findings))

    def test_ignores_param_repeated_four_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = "\n".join(
                f"fun step{i}(logger: Logger, x: Int): Unit = TODO()" for i in range(4)
            )
            self._write(root, "feature/x/src/commonMain/kotlin/Steps.kt", body + "\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("context parameter opportunity" in f for f in findings))

    def test_ignores_differing_types_for_same_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = "\n".join(
                f"fun step{i}(logger: Logger{i % 2}): Unit = TODO()" for i in range(6)
            )
            self._write(root, "feature/x/src/commonMain/kotlin/Steps.kt", body + "\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("context parameter opportunity" in f for f in findings))


class GodClassTests(unittest.TestCase):
    """God-object detection existed for exactly two file types — ViewModel size and
    god composable — nothing caught a repository/use-case/manager class accumulating
    too many responsibilities. _detect_god_class is the repo-wide backstop.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def _big_class(self, name: str, fun_count: int, filler_lines_per_fun: int = 25) -> str:
        funs = []
        for i in range(fun_count):
            body = "\n".join(f"        val x{j} = {j}" for j in range(filler_lines_per_fun))
            funs.append(f"    fun op{i}(): Int {{\n{body}\n        return x0\n    }}")
        return f"class {name} {{\n" + "\n".join(funs) + "\n}\n"

    def test_flags_large_plain_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderManager.kt",
                self._big_class("OrderManager", fun_count=16),
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god class" in f for f in findings))

    def test_ignores_small_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderMapper.kt",
                "class OrderMapper {\n    fun toDomain(dto: OrderDto): Order = TODO()\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god class" in f for f in findings))

    def test_ignores_data_class_regardless_of_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            props = "\n".join(f"    val field{i}: Int = {i}," for i in range(500))
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderState.kt",
                f"data class OrderState(\n{props}\n)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god class" in f for f in findings))

    def test_ignores_viewmodel_already_covered_by_viewmodel_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = self._big_class("OrderViewModel", fun_count=16).replace(
                "class OrderViewModel {", "class OrderViewModel : ViewModel() {"
            )
            self._write(root, "feature/orders/src/commonMain/kotlin/OrderViewModel.kt", content)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god class" in f for f in findings))
            self.assertTrue(any("viewmodel" in f.lower() for f in findings))


class RunBlockingInSharedCodeTests(unittest.TestCase):
    """runBlocking blocks the calling thread — often the main thread on Android/iOS —
    a real correctness hazard anywhere in shared business logic outside a CLI entry point.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_runblocking_in_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderRepository.kt",
                "class OrderRepository {\n"
                "    fun getOrderSync(id: String): Order = runBlocking { fetch(id) }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("runBlocking in shared code" in f for f in findings))

    def test_ignores_runblocking_in_main_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "app/src/commonMain/kotlin/Main.kt",
                "fun main() {\n"
                "    runBlocking { startApp() }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("runBlocking in shared code" in f for f in findings))

    def test_ignores_runblocking_outside_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/androidMain/kotlin/OrderRepository.kt",
                "class OrderRepository {\n"
                "    fun getOrderSync(id: String): Order = runBlocking { fetch(id) }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("runBlocking in shared code" in f for f in findings))


class KoinCircularDependencyTests(unittest.TestCase):
    """Only detects explicitly-typed single<A>/factory<A>/scoped<A> bindings whose
    body references get<B>() — narrow scope keeps false positives near zero.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_two_node_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "app/src/commonMain/kotlin/AppModule.kt",
                "val appModule = module {\n"
                "    single<A> { AImpl(get<B>()) }\n"
                "    single<B> { BImpl(get<A>()) }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("koin circular dependency" in f for f in findings))

    def test_ignores_acyclic_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "app/src/commonMain/kotlin/AppModule.kt",
                "val appModule = module {\n"
                "    single<A> { AImpl(get<B>()) }\n"
                "    single<B> { BImpl(get<C>()) }\n"
                "    single<C> { CImpl() }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("koin circular dependency" in f for f in findings))

    def test_flags_three_node_cycle_across_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "app/src/commonMain/kotlin/ModuleOne.kt",
                "val moduleOne = module {\n"
                "    single<A> { AImpl(get<B>()) }\n"
                "}\n",
            )
            self._write(
                root, "app/src/commonMain/kotlin/ModuleTwo.kt",
                "val moduleTwo = module {\n"
                "    single<B> { BImpl(get<C>()) }\n"
                "    single<C> { CImpl(get<A>()) }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("koin circular dependency" in f for f in findings))


class ComposeUnstableCollectionParamTests(unittest.TestCase):
    """Raw List/Map/Set params on a @Composable are unstable to the Compose compiler,
    forcing recomposition even when contents haven't changed.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_raw_list_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderListScreen.kt",
                "@Composable\n"
                "fun OrderListContent(orders: List<Order>) {\n"
                "    Column {}\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("compose unstable collection param" in f for f in findings))

    def test_ignores_immutable_list_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderListScreen.kt",
                "@Composable\n"
                "fun OrderListContent(orders: ImmutableList<Order>) {\n"
                "    Column {}\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("compose unstable collection param" in f for f in findings))

    def test_ignores_non_composable_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderMapper.kt",
                "fun mapOrders(orders: List<OrderDto>): List<Order> = TODO()\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("compose unstable collection param" in f for f in findings))


class LibraryProjectStructureTests(unittest.TestCase):
    """kmp-library-publishing conformance — gated on vanniktech-mavenPublish actually
    being applied, the one unambiguous 'this is a published library' signal."""

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def _vanniktech_module(self, explicit_api: bool = False) -> str:
        api_line = "kotlin { explicitApi() }\n" if explicit_api else ""
        return (
            "plugins {\n"
            "    id(\"org.jetbrains.kotlin.multiplatform\")\n"
            "    id(\"com.vanniktech.maven.publish\")\n"
            "}\n"
            f"{api_line}"
            "mavenPublishing {\n"
            "    coordinates(\"io.github.me\", \"mylib\", \"0.1.0\")\n"
            "}\n"
        )

    def test_flags_missing_binary_compat_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "library/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("library missing binary-compat validator" in f for f in findings))

    def test_ignores_binary_compat_validator_when_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "library/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            self._write(
                root, "build.gradle.kts",
                'plugins { id("org.jetbrains.kotlinx.binary-compatibility-validator") }\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("library missing binary-compat validator" in f for f in findings))

    def test_flags_missing_explicit_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "library/build.gradle.kts", self._vanniktech_module(explicit_api=False))
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("library missing explicitApi()" in f for f in findings))

    def test_ignores_explicit_api_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "library/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("library missing explicitApi()" in f for f in findings))

    def test_ignores_non_library_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/network/build.gradle.kts",
                'plugins { id("org.jetbrains.kotlin.multiplatform") }\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any(
                f.startswith("library missing") or "library multi-module" in f
                for f in findings
            ))

    def test_single_module_library_not_flagged_for_build_logic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "library/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("library multi-module missing build-logic" in f for f in findings))

    def test_flags_multimodule_missing_build_logic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "mylib-core/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            self._write(root, "mylib-compose/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("library multi-module missing build-logic" in f for f in findings))

    def test_ignores_multimodule_with_build_logic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "mylib-core/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            self._write(root, "mylib-compose/build.gradle.kts", self._vanniktech_module(explicit_api=True))
            self._write(root, "build-logic/build.gradle.kts", "plugins { `kotlin-dsl` }\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("library multi-module missing build-logic" in f for f in findings))


class UndocumentedPublicApiTests(unittest.TestCase):
    """Gated on explicitApi() — once 'public' is a deliberate choice under that
    compiler mode, an undocumented one is a real gap for a library's consumers.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def _enable_explicit_api(self, root: Path) -> None:
        self._write(root, "library/build.gradle.kts", "kotlin {\n    explicitApi()\n}\n")

    def test_flags_undocumented_public_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._enable_explicit_api(root)
            self._write(
                root, "library/src/commonMain/kotlin/RetryPolicy.kt",
                "public class RetryPolicy(public val maxAttempts: Int)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("undocumented public api" in f for f in findings))

    def test_ignores_documented_public_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._enable_explicit_api(root)
            self._write(
                root, "library/src/commonMain/kotlin/RetryPolicy.kt",
                "/**\n"
                " * Controls retry behavior for transient network failures.\n"
                " */\n"
                "public class RetryPolicy(public val maxAttempts: Int)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("undocumented public api" in f for f in findings))

    def test_flags_undocumented_public_property(self) -> None:
        # A public property is as much published surface as a function under
        # explicitApi() — binary-compatibility-validator tracks it either way — but this
        # detector matched only class/interface/object/fun, and kmp-code-quality's Detekt
        # block enabled only UndocumentedPublicClass/Function. A public `val` was covered
        # by neither, while the doc claimed "every public declaration".
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._enable_explicit_api(root)
            self._write(
                root, "library/src/commonMain/kotlin/Config.kt",
                "public val defaultTimeoutMs: Long = 30_000\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("undocumented public api" in f for f in findings))

    def test_ignores_documented_public_property(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._enable_explicit_api(root)
            self._write(
                root, "library/src/commonMain/kotlin/Config.kt",
                "/** Default request timeout applied when none is set per-call. */\n"
                "public val defaultTimeoutMs: Long = 30_000\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("undocumented public api" in f for f in findings))

    def test_ignores_project_without_explicit_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "app/src/commonMain/kotlin/RetryPolicy.kt",
                "public class RetryPolicy(public val maxAttempts: Int)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("undocumented public api" in f for f in findings))


class CombinedComponentFileTests(unittest.TestCase):
    """kmp-compose-design-system's own generated templates always put one
    component per file — never stated as a rule, never mechanically checked for a
    real project's own component files, until now.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_three_components_in_one_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/designsystem/components/Overlays.kt",
                "@Composable\nfun AppDialog() {}\n"
                "@Composable\nfun AppSheet() {}\n"
                "@Composable\nfun AppTooltip() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("combined component file" in f for f in findings))

    def test_ignores_two_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/designsystem/components/Overlays.kt",
                "@Composable\nfun AppDialog() {}\n"
                "@Composable\nfun AppSheet() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined component file" in f for f in findings))

    def test_ignores_screen_content_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/designsystem/components/OrderScreen.kt",
                "@Composable\nfun OrderScreen() {}\n"
                "@Composable\nfun OrderContent() {}\n"
                "@Composable\nfun OrderScreenPreview() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined component file" in f for f in findings))

    def test_ignores_outside_designsystem_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/Widgets.kt",
                "@Composable\nfun WidgetOne() {}\n"
                "@Composable\nfun WidgetTwo() {}\n"
                "@Composable\nfun WidgetThree() {}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined component file" in f for f in findings))


class CombinedStyleFileTests(unittest.TestCase):
    """Same bundling problem as combined component files, one directory over —
    styles/ButtonStyles.kt should hold exactly ButtonVariant, not every variant.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_two_variant_types_in_one_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/designsystem/styles/AllStyles.kt",
                "sealed class ButtonVariant\nsealed class CardVariant\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("combined style file" in f for f in findings))

    def test_ignores_single_variant_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/designsystem/styles/ButtonStyles.kt",
                "sealed class ButtonVariant\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined style file" in f for f in findings))

    def test_ignores_outside_styles_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/designsystem/other/AllStyles.kt",
                "sealed class ButtonVariant\nsealed class CardVariant\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("combined style file" in f for f in findings))


class ViewModelTooManyIntentsTests(unittest.TestCase):
    """_detect_viewmodel_size only measures lines — a terse ViewModel handling 20+
    Intent variants in short when-branches can dodge that threshold.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def _intent_block(self, count: int) -> str:
        variants = "\n".join(f"    data object Action{i} : Intent" for i in range(count))
        return f"sealed interface Intent {{\n{variants}\n}}\n"

    def test_flags_fifteen_plus_intents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel : ViewModel() {\n}\n" + self._intent_block(16),
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel too many intents" in f for f in findings))

    def test_ignores_few_intents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel : ViewModel() {\n}\n" + self._intent_block(4),
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel too many intents" in f for f in findings))


class ViewModelMultipleStateFlowsTests(unittest.TestCase):
    """MVI's contract is one State per screen — exposing state1/state2/state3 as
    separate public StateFlows is often the same god-ViewModel smell wearing a
    different shape.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_multiple_exposed_stateflows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel : ViewModel() {\n"
                "    val state: StateFlow<ChatState> = TODO()\n"
                "    val projectState: StateFlow<ProjectState> = TODO()\n"
                "    val sessionState: StateFlow<SessionState> = TODO()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel multiple stateflows" in f for f in findings))

    def test_ignores_single_state_and_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel : ViewModel() {\n"
                "    val state: StateFlow<ChatState> = TODO()\n"
                "    val effect: Flow<ChatEffect> = TODO()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel multiple stateflows" in f for f in findings))

    def test_ignores_one_extra_stateflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel : ViewModel() {\n"
                "    val state: StateFlow<ChatState> = TODO()\n"
                "    val validationState: StateFlow<Boolean> = TODO()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel multiple stateflows" in f for f in findings))


class ViewModelInjectsRepositoryTests(unittest.TestCase):
    """kmp-mvi's own changelog calls the ViewModel-depends-only-on-
    :domain rule 'bright-line and mechanically checkable' — it wasn't actually checked.
    _detect_module_layer_violation can't catch it either since presenter -> api is an
    allowed module-level edge; this is a file-level constructor-param check instead.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_repository_in_constructor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel(\n"
                "    private val chatRepository: ChatRepository,\n"
                ") : ViewModel() {\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("viewmodel injects repository" in f for f in findings))

    def test_ignores_usecase_in_constructor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/presenter/src/commonMain/kotlin/ChatViewModel.kt",
                "class ChatViewModel(\n"
                "    private val sendMessageUseCase: SendMessageUseCase,\n"
                ") : ViewModel() {\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel injects repository" in f for f in findings))

    def test_ignores_repository_in_non_viewmodel_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/chat/domain/src/commonMain/kotlin/SendMessageUseCase.kt",
                "class SendMessageUseCase(\n"
                "    private val chatRepository: ChatRepository,\n"
                ") {\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("viewmodel injects repository" in f for f in findings))


class BareCoreModuleTests(unittest.TestCase):
    """:core must be a folder GROUP of separate modules (:core:model, :core:api, ...),
    mirroring :feature:*'s own shape — never a module in its own right.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_bare_core_build_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/build.gradle.kts", "plugins {\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("bare core module" in f for f in findings))

    def test_ignores_split_core_submodules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/model/build.gradle.kts", "plugins {\n}\n")
            self._write(root, "core/api/build.gradle.kts", "plugins {\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("bare core module" in f for f in findings))

    def test_ignores_when_no_core_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "feature/auth/model/build.gradle.kts", "plugins {\n}\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("bare core module" in f for f in findings))


class MixedDesignSystemUsageTests(unittest.TestCase):
    """kmp-shadcn-compose says "Never combine with
    kmp-compose-design-system" - documented but never mechanically checked.
    Scoped to both theme wrappers coexisting (ShadcnTheme(/AppTheme() rather than
    individual App*-prefixed component names, to avoid a false positive on an
    unrelated real identifier like AppConfig(...) or AppDatabase(...).
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_both_theme_wrappers_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/a/src/commonMain/kotlin/A.kt",
                "@Composable\nfun A() { ShadcnTheme { } }\n",
            )
            self._write(
                root, "feature/b/src/commonMain/kotlin/B.kt",
                "@Composable\nfun B() { AppTheme { } }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("mixed component library usage" in f for f in findings))

    def test_ignores_shadcn_theme_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/a/src/commonMain/kotlin/A.kt",
                "@Composable\nfun A() { ShadcnTheme { } }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("mixed component library usage" in f for f in findings))

    def test_ignores_app_theme_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/a/src/commonMain/kotlin/A.kt",
                "@Composable\nfun A() { AppTheme { } }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("mixed component library usage" in f for f in findings))

    def test_ignores_unrelated_app_prefixed_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/a/src/commonMain/kotlin/A.kt",
                "@Composable\nfun A() {\n    ShadcnTheme { }\n"
                "    val config = AppConfig()\n    val db = AppDatabase()\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("mixed component library usage" in f for f in findings))


class AgentFileStandardsTests(unittest.TestCase):
    """No detector existed for the standards of project-owned agent files themselves
    (agents/*.md, .codex/agents/*.toml) — only whether setup artifacts exist at all.
    Also catches the exact real bug found in docs/reference/agent-catalog.md this same
    session: a tier name written into model: instead of a real, resolvable model id.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_agent_md_missing_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "agents/reviewer.md", "# Reviewer\n\nNo frontmatter.\n")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent missing frontmatter" in f for f in findings))

    def test_flags_agent_md_missing_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "agents/reviewer.md",
                "---\ndescription: Reviews code.\n---\n\nBody.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("frontmatter missing name" in f for f in findings))

    def test_flags_agent_md_missing_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "agents/reviewer.md",
                "---\nname: reviewer\n---\n\nBody.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("frontmatter missing description" in f for f in findings))

    def test_flags_tier_name_used_as_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "agents/reviewer.md",
                "---\nname: reviewer\ndescription: Reviews code.\n"
                "model: balanced-coding\n---\n\nBody.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent uses tier name as model" in f for f in findings))

    def test_ignores_real_model_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "agents/reviewer.md",
                "---\nname: reviewer\ndescription: Reviews code.\n"
                "model: sonnet\n---\n\nBody.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("project agent uses tier name as model" in f for f in findings))

    def test_compliant_agent_md_has_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "---\nname: reviewer\ndescription: Reviews code.\n---\n\nBody.\n"
            self._write(root, "agents/reviewer.md", content)
            self._write(root, ".claude/agents/reviewer.md", content)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any(f.startswith("project agent") for f in findings))

    def test_flags_agent_redundant_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "---\nname: reviewer-agent\ndescription: Reviews code.\n---\n\nBody.\n"
            self._write(root, "agents/reviewer-agent.md", content)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent redundant suffix" in f for f in findings))

    def test_flags_agent_action_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "---\nname: fix-bugs\ndescription: Fixes bugs.\n---\n\nBody.\n"
            self._write(root, "agents/fix-bugs.md", content)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent action-named" in f for f in findings))

    def test_flags_agent_model_prefixed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "---\nname: claude-reviewer\ndescription: Reviews code.\n---\n\nBody.\n"
            self._write(root, "agents/claude-reviewer.md", content)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent model-prefixed" in f for f in findings))

    def test_flags_agent_name_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "---\nname: custom-reviewer\ndescription: Reviews code.\n---\n\nBody.\n"
            self._write(root, "agents/reviewer.md", content)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent name mismatch" in f for f in findings))

    def test_flags_codex_toml_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, ".codex/agents/reviewer.toml",
                'name = "reviewer"\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("codex agent missing required field" in f for f in findings))

    def test_ignores_compliant_codex_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, ".codex/agents/reviewer.toml",
                'name = "reviewer"\n'
                'description = "Reviews code."\n'
                'developer_instructions = """\nReview the diff.\n"""\n',
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("codex agent missing required field" in f for f in findings))

    def test_flags_agent_not_deployed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "agents/reviewer.md",
                "---\nname: reviewer\ndescription: Reviews code.\n---\n\nBody.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent not deployed" in f for f in findings))

    def test_flags_agent_deployment_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "agents/reviewer.md",
                "---\nname: reviewer\ndescription: Reviews code.\n---\n\nBody.\n",
            )
            self._write(
                root, ".claude/agents/reviewer.md",
                "---\nname: reviewer\ndescription: Reviews code.\n---\n\nStale body.\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent deployment drift" in f for f in findings))

    def test_ignores_synced_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "---\nname: reviewer\ndescription: Reviews code.\n---\n\nBody.\n"
            self._write(root, "agents/reviewer.md", content)
            self._write(root, ".claude/agents/reviewer.md", content)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any(f.startswith("project agent") for f in findings))

    def test_flags_tier_name_in_deployed_agent_with_no_canonical_source(self) -> None:
        """Reproduces the real bug found in a consumer project (`awaken`): the real
        agent files lived under a project skill (`skills/awake/agents/`), symlinked
        into `.claude/agents/` — never at the canonical `agents/` path this detector
        used to require. 10 files had `model: balanced-coding`/`flagship-coding`
        (tier-name literals) and produced a real "invalid model" error at runtime,
        completely outside the old detector's scan."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "skills/awake/agents/engineer.md",
                "---\nname: engineer\ndescription: Builds features.\n"
                "model: balanced-coding\n---\n\nBody.\n",
            )
            (root / ".claude").mkdir(parents=True, exist_ok=True)
            (root / ".claude" / "agents").symlink_to(
                root / "skills" / "awake" / "agents", target_is_directory=True
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("project agent uses tier name as model" in f for f in findings))

    def test_does_not_double_report_a_tier_name_present_in_both_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = (
                "---\nname: reviewer\ndescription: Reviews code.\n"
                "model: balanced-coding\n---\n\nBody.\n"
            )
            self._write(root, "agents/reviewer.md", content)
            self._write(root, ".claude/agents/reviewer.md", content)
            findings = audit_scripts.audit_project(root)
            hits = [f for f in findings if "project agent uses tier name as model" in f]
            self.assertEqual(len(hits), 1)


class ObjectCreationInLoopTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_ctor_inside_for_loop_not_using_loop_var(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Formatter.kt",
                "fun formatAll(items: List<Long>): List<String> {\n"
                "    val results = mutableListOf<String>()\n"
                "    for (item in items) {\n"
                "        val fmt = SimpleDateFormat(\"yyyy-MM-dd\")\n"
                "        results.add(fmt.format(item))\n"
                "    }\n"
                "    return results\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("object creation in loop" in f for f in findings))

    def test_ignores_ctor_hoisted_before_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Formatter.kt",
                "fun formatAll(items: List<Long>): List<String> {\n"
                "    val fmt = SimpleDateFormat(\"yyyy-MM-dd\")\n"
                "    val results = mutableListOf<String>()\n"
                "    for (item in items) {\n"
                "        results.add(fmt.format(item))\n"
                "    }\n"
                "    return results\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("object creation in loop" in f for f in findings))

    def test_ignores_ctor_that_depends_on_loop_variable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Formatter.kt",
                "fun perItem(codes: List<String>) {\n"
                "    for (code in codes) {\n"
                "        val fmt = SimpleDateFormat(code)\n"
                "        println(fmt)\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("object creation in loop" in f for f in findings))


class ContextLeakInSingletonTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_context_in_companion_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/AppContextHolder.kt",
                "class AppContextHolder {\n"
                "    companion object {\n"
                "        var appContext: Context? = null\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("context leak in singleton" in f for f in findings))

    def test_flags_activity_in_object_singleton(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/BadSingleton.kt",
                "object BadSingleton {\n    var activity: Activity? = null\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("context leak in singleton" in f for f in findings))

    def test_ignores_application_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/SafeHolder.kt",
                "class SafeHolder {\n"
                "    companion object {\n"
                "        lateinit var applicationContext: Application\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("context leak in singleton" in f for f in findings))

    def test_ignores_context_outside_singleton_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Screen.kt",
                "class Screen {\n    var context: Context? = null\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("context leak in singleton" in f for f in findings))


class PublicMutableCollectionTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_public_mutable_list_property(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Repo.kt",
                "class ItemStore {\n    val items: MutableList<String> = mutableListOf()\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("public mutable collection exposure" in f for f in findings))

    def test_flags_public_function_returning_mutable_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Repo.kt",
                "class ItemStore {\n"
                "    private val items = mutableListOf<String>()\n"
                "    fun getRaw(): MutableList<String> = items\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("public mutable collection exposure" in f for f in findings))

    def test_ignores_private_mutable_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Repo.kt",
                "class ItemStore {\n    private val cache: MutableMap<String, Int> = mutableMapOf()\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("public mutable collection exposure" in f for f in findings))

    def test_ignores_read_only_return_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Repo.kt",
                "class ItemStore {\n"
                "    private val items = mutableListOf<String>()\n"
                "    fun getAll(): List<String> = items\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("public mutable collection exposure" in f for f in findings))


class HardcodedUiStringTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_hardcoded_text_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun AuthScreen() { Text(\"Welcome back\") }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded ui string" in f and "Welcome back" in f for f in findings))

    def test_flags_hardcoded_content_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun AuthScreen() { Icon(imageVector = X, contentDescription = \"Close dialog\") }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("hardcoded ui string" in f and "Close dialog" in f for f in findings))

    def test_ignores_string_resource_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun AuthScreen() { Text(stringResource(Res.string.hello)) }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded ui string" in f for f in findings))

    def test_ignores_numeric_only_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun AuthScreen() { Text(\"42\") }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded ui string" in f for f in findings))

    def test_ignores_preview_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/ScreenPreview.kt",
                "import androidx.compose.runtime.Composable\n"
                "@Composable\nfun AuthScreenPreview() { Text(\"Welcome back\") }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("hardcoded ui string" in f for f in findings))


class KotlinReflectInCommonTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_full_reflection_import_in_commonmain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Reflecty.kt",
                "import kotlin.reflect.full.memberProperties\n"
                "fun x() { Foo::class.memberProperties }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("kotlin-reflect in commonMain" in f for f in findings))

    def test_ignores_kclass_literal_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Plain.kt",
                "fun x(): KClass<*> = Foo::class\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("kotlin-reflect in commonMain" in f for f in findings))

    def test_ignores_reflection_in_jvm_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/jvmMain/kotlin/Reflecty.kt",
                "import kotlin.reflect.full.memberProperties\n"
                "fun x() { Foo::class.memberProperties }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("kotlin-reflect in commonMain" in f for f in findings))


class GodUtilsFileTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_utils_file_with_many_unrelated_functions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(
                [f"fun String.f{i}() = this" for i in range(4)]
                + [f"fun Int.g{i}() = this" for i in range(4)]
                + [f"fun h{i}() = Unit" for i in range(4)]
            )
            self._write(root, "core/AppUtils.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god utils file" in f for f in findings))

    def test_ignores_single_receiver_extension_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(f"fun String.f{i}() = this" for i in range(12))
            self._write(root, "core/StringUtils.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god utils file" in f for f in findings))

    def test_flags_god_extensions_file(self) -> None:
        # kmp-code-quality's rule names Utils.kt/Helpers.kt/Extensions.kt, but the
        # filename regex covered only the first two — a god AppExtensions.kt sailed
        # through the very check written to catch it.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(
                [f"fun String.f{i}() = this" for i in range(4)]
                + [f"fun Int.g{i}() = this" for i in range(4)]
                + [f"fun List<String>.h{i}() = this" for i in range(4)]
            )
            self._write(root, "core/AppExtensions.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god utils file" in f for f in findings))

    def test_flags_utils_file_written_with_explicit_visibility(self) -> None:
        # The top-level-fun regex was `^fun\\s+`, so any visibility modifier hid the
        # function from it. Under explicitApi() every top-level fun is `public fun`, so
        # this detector silently found nothing in exactly the library projects where
        # API hygiene matters most.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(
                [f"public fun String.f{i}() = this" for i in range(4)]
                + [f"public fun Int.g{i}() = this" for i in range(4)]
                + [f"internal fun List<String>.h{i}() = this" for i in range(4)]
            )
            self._write(root, "core/AppUtils.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("god utils file" in f for f in findings))

    def test_ignores_recommended_single_receiver_extensions_file(self) -> None:
        # StringExtensions.kt is the shape the rule *recommends*; adding `Extensions` to
        # the filename regex must not start flagging it. The 3-receiver-type threshold
        # is what keeps it safe.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(f"public fun String.f{i}() = this" for i in range(12))
            self._write(root, "core/StringExtensions.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god utils file" in f for f in findings))

    def test_ignores_non_utils_named_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(
                [f"fun String.f{i}() = this" for i in range(4)]
                + [f"fun Int.g{i}() = this" for i in range(4)]
                + [f"fun h{i}() = Unit" for i in range(4)]
            )
            self._write(root, "core/AuthRepository.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god utils file" in f for f in findings))

    def test_ignores_small_utils_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            funcs = "\n\n".join(
                [f"fun String.f{i}() = this" for i in range(2)]
                + [f"fun Int.g{i}() = this" for i in range(2)]
            )
            self._write(root, "core/AppUtils.kt", funcs)
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("god utils file" in f for f in findings))


class InlineUnnamedRegexTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_inline_regex_in_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Validate.kt",
                "fun check(s: String) = Regex(\"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}$\").matches(s)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("inline unnamed regex" in f for f in findings))

    def test_ignores_named_val_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Validate.kt",
                "private val EMAIL_RE = Regex(\"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}$\")\n"
                "fun check(s: String) = EMAIL_RE.matches(s)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("inline unnamed regex" in f for f in findings))

    def test_ignores_short_inline_regex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/Validate.kt", "fun ok(s: String) = Regex(\"a\").matches(s)\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("inline unnamed regex" in f for f in findings))


class AgentsSkillsCrossClientTests(unittest.TestCase):
    def _base_claude_setup(self, root: Path) -> Path:
        (root / "settings.gradle.kts").write_text("", encoding="utf-8")
        (root / "CLAUDE.md").write_text("", encoding="utf-8")
        claude = root / ".claude"
        (claude / "commands").mkdir(parents=True)
        (claude / "commands" / "x.md").write_text("", encoding="utf-8")
        (claude / "AGENTS.md").write_text("", encoding="utf-8")
        skill_dir = claude / "skills" / "kmp-mvi"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("", encoding="utf-8")
        return claude

    def test_flags_missing_agents_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            findings = audit_scripts._detect_agent_setup(root)
            self.assertTrue(any(".agents/skills/ missing or empty" in f for f in findings))

    def test_warns_redundant_when_claude_skills_mirror_matches_agents_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            agents_skill = root / ".agents" / "skills" / "kmp-mvi"
            agents_skill.mkdir(parents=True)
            (agents_skill / "SKILL.md").write_text("", encoding="utf-8")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertFalse(any(".agents/skills/" in f and "missing" in f for f in findings))
            self.assertFalse(any("drifted" in f for f in findings))
            self.assertTrue(any("redundant repo-local .claude/skills/ mirror" in f for f in findings))

    def test_flags_drift_between_claude_and_agents_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude = self._base_claude_setup(root)
            agents_skill = root / ".agents" / "skills" / "kmp-mvi"
            agents_skill.mkdir(parents=True)
            (agents_skill / "SKILL.md").write_text("", encoding="utf-8")
            # Extra skill only in .claude/skills/ — a real drift.
            extra = claude / "skills" / "kmp-audit"
            extra.mkdir(parents=True)
            (extra / "SKILL.md").write_text("", encoding="utf-8")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertTrue(any("drifted" in f for f in findings))

    def test_flags_bundled_skill_name_under_project_root_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            agents_skill = root / ".agents" / "skills" / "kmp-mvi"
            agents_skill.mkdir(parents=True)
            (agents_skill / "SKILL.md").write_text("", encoding="utf-8")
            bundled_looking = root / "skills" / "kmp-fake"
            bundled_looking.mkdir(parents=True)
            (bundled_looking / "SKILL.md").write_text("", encoding="utf-8")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertTrue(
                any("bundled-looking skill name" in f and "kmp-fake" in f for f in findings)
            )

    def test_ignores_genuine_custom_skill_under_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            agents_skill = root / ".agents" / "skills" / "kmp-mvi"
            agents_skill.mkdir(parents=True)
            (agents_skill / "SKILL.md").write_text("", encoding="utf-8")
            custom = root / "skills" / "my-app-custom-widget"
            custom.mkdir(parents=True)
            (custom / "SKILL.md").write_text("", encoding="utf-8")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertFalse(any("bundled-looking skill name" in f for f in findings))


class AgentSetupGitignoredTests(unittest.TestCase):
    """A `.claude/AGENTS.md` that exists locally but is gitignored looks identical to a
    correctly committed one to every filesystem-only check — it only breaks for whoever
    clones next. Reproduces the real bug found in a consumer project (`awaken`): the
    file was present and current on the author's machine, and both `--dry-run` and this
    audit reported nothing wrong, because nothing checked git-tracking status."""

    def _base_claude_setup(self, root: Path) -> Path:
        (root / "settings.gradle.kts").write_text("", encoding="utf-8")
        (root / "CLAUDE.md").write_text("", encoding="utf-8")
        claude = root / ".claude"
        (claude / "commands").mkdir(parents=True)
        (claude / "commands" / "x.md").write_text("", encoding="utf-8")
        (claude / "AGENTS.md").write_text("", encoding="utf-8")
        (claude / "settings.json").write_text("{}", encoding="utf-8")
        skill_dir = claude / "skills" / "kmp-mvi"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("", encoding="utf-8")
        agents_skill = root / ".agents" / "skills" / "kmp-mvi"
        agents_skill.mkdir(parents=True)
        (agents_skill / "SKILL.md").write_text("", encoding="utf-8")
        return claude

    def _git_init(self, root: Path, gitignore: str) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / ".gitignore").write_text(gitignore, encoding="utf-8")

    def test_flags_gitignored_agents_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            self._git_init(root, ".claude/\n")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertTrue(
                any("AGENTS.md exists but is gitignored" in f for f in findings)
            )

    def test_flags_gitignored_commands_and_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            self._git_init(root, ".claude/\n")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertTrue(
                any("commands/ exists but is gitignored" in f for f in findings)
            )
            self.assertFalse(any("settings.json exists but is gitignored" in f for f in findings))

    def test_ignores_when_only_skills_mirror_is_gitignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            self._git_init(root, ".claude/skills/\n.agents/skills/\n")
            findings = audit_scripts._detect_agent_setup(root)
            self.assertFalse(any("gitignored" in f for f in findings))

    def test_ignores_outside_a_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._base_claude_setup(root)
            # No `git init` — a plain checkout-less directory should never be flagged.
            findings = audit_scripts._detect_agent_setup(root)
            self.assertFalse(any("gitignored" in f for f in findings))


class PartialParamDocumentationTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_partial_param_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/Login.kt",
                "/**\n"
                " * Logs a user in.\n"
                " * @param email The user email address.\n"
                " */\n"
                "fun login(email: String, password: String, rememberMe: Boolean): Result<User> { TODO() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("partial param documentation" in f for f in findings))

    def test_ignores_fully_documented_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/Login.kt",
                "/**\n"
                " * Fully documented.\n"
                " * @param email The email.\n"
                " * @param password The password.\n"
                " */\n"
                "fun login(email: String, password: String): Result<User> { TODO() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("partial param documentation" in f for f in findings))

    def test_ignores_zero_param_detail_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/Login.kt",
                "/** Plain summary, no param detail at all. */\n"
                "fun login(email: String, password: String): Result<User> { TODO() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("partial param documentation" in f for f in findings))

    def test_ignores_single_param_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/Login.kt",
                "/**\n"
                " * Logs a user in.\n"
                " * @param email The user email address.\n"
                " */\n"
                "fun login(email: String): Result<User> { TODO() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("partial param documentation" in f for f in findings))

    def test_covers_inline_bracket_references_too(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/Login.kt",
                "/**\n"
                " * Uses [email] to authenticate.\n"
                " */\n"
                "fun login(email: String, password: String, rememberMe: Boolean): Result<User> { TODO() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("partial param documentation" in f for f in findings))

    def test_ignores_full_inline_bracket_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/domain/Login.kt",
                "/**\n"
                " * Uses [email] and [password] to authenticate, ignoring [rememberMe].\n"
                " */\n"
                "fun login(email: String, password: String, rememberMe: Boolean): Result<User> { TODO() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("partial param documentation" in f for f in findings))


class LowercaseUnitComposableTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_lowercase_unit_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "@Composable\nfun appButton(onClick: () -> Unit) { Text(\"x\") }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("lowercase unit composable" in f and "appButton" in f for f in findings))

    def test_ignores_pascalcase_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "@Composable\nfun AppButton(onClick: () -> Unit) { Text(\"x\") }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("lowercase unit composable" in f for f in findings))

    def test_ignores_composable_with_explicit_return_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "@Composable\nfun rememberScrollState(): ScrollState { return ScrollState() }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("lowercase unit composable" in f for f in findings))

    def test_flags_private_lowercase_composable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/Screen.kt",
                "@Composable\nprivate fun homeContent(state: State) { }\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("lowercase unit composable" in f and "homeContent" in f for f in findings))


class UnauthorizedAppSubmoduleTests(unittest.TestCase):
    def _touch(self, root: Path, rel_path: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    def test_flags_new_module_under_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._touch(root, "app/newFeature/build.gradle.kts")
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("unauthorized app submodule" in f for f in findings))

    def test_ignores_known_kmp_wizard_entry_points(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("androidApp", "desktopApp", "webApp", "shared"):
                self._touch(root, f"app/{name}/build.gradle.kts")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("unauthorized app submodule" in f for f in findings))

    def test_ignores_unrelated_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._touch(root, "core/common/build.gradle.kts")
            self._touch(root, "feature/auth/ui/build.gradle.kts")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("unauthorized app submodule" in f for f in findings))


class NameBehaviorDriftTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_viewmodel_name_with_no_overlap_with_its_intents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/AuthContract.kt",
                """
                object AuthContract {
                    sealed interface Intent {
                        data object LogoutClicked : Intent
                        data object RefreshTapped : Intent
                    }
                }
                """,
            )
            self._write(root, "feature/auth/ui/AuthViewModel.kt", "class AuthViewModel {}")

            hints = audit_scripts._detect_name_behavior_drift(root)
            self.assertTrue(any("name-behavior drift" in h for h in hints))

    def test_does_not_flag_viewmodel_name_that_overlaps_its_intents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/login/ui/LoginContract.kt",
                """
                object LoginContract {
                    sealed interface Intent {
                        data object LoginClicked : Intent
                        data class EmailChanged(val v: String) : Intent
                    }
                }
                """,
            )
            self._write(root, "feature/login/ui/LoginViewModel.kt", "class LoginViewModel {}")

            hints = audit_scripts._detect_name_behavior_drift(root)
            self.assertFalse(hints)

    def test_does_not_flag_with_fewer_than_two_intents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/AuthContract.kt",
                """
                object AuthContract {
                    sealed interface Intent {
                        data object RefreshTapped : Intent
                    }
                }
                """,
            )
            self._write(root, "feature/auth/ui/AuthViewModel.kt", "class AuthViewModel {}")

            hints = audit_scripts._detect_name_behavior_drift(root)
            self.assertFalse(hints)

    def test_hints_are_excluded_from_blocking_audit_project_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/ui/AuthContract.kt",
                """
                object AuthContract {
                    sealed interface Intent {
                        data object LogoutClicked : Intent
                        data object RefreshTapped : Intent
                    }
                }
                """,
            )
            self._write(root, "feature/auth/ui/AuthViewModel.kt", "class AuthViewModel {}")

            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("name-behavior drift" in f for f in findings))


class VagueClassNameSuffixTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_manager_suffix_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/SyncManager.kt", "class SyncManager(val x: Int) { }\n")
            hints = audit_scripts._detect_vague_class_name_suffix(root)
            self.assertTrue(any("SyncManager" in h for h in hints))

    def test_flags_helper_suffix_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/ConfigHelper.kt", "object ConfigHelper { }\n")
            hints = audit_scripts._detect_vague_class_name_suffix(root)
            self.assertTrue(any("ConfigHelper" in h for h in hints))

    def test_ignores_data_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/UserData.kt", "data class UserData(val id: String)\n")
            hints = audit_scripts._detect_vague_class_name_suffix(root)
            self.assertFalse(hints)

    def test_ignores_enum_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/InfoType.kt", "enum class InfoType { A, B }\n")
            hints = audit_scripts._detect_vague_class_name_suffix(root)
            self.assertFalse(hints)

    def test_ignores_coordinator_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "feature/auth/AuthCoordinator.kt", "class AuthCoordinator { }\n")
            hints = audit_scripts._detect_vague_class_name_suffix(root)
            self.assertFalse(hints)

    def test_hints_are_excluded_from_blocking_audit_project_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/SyncManager.kt", "class SyncManager(val x: Int) { }\n")
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("vague class name suffix" in f for f in findings))


class EmptyCatchBlockTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_fully_empty_catch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Sample.kt",
                "fun a() {\n    try {\n        risky()\n    } catch (e: Exception) {\n    }\n}\n",
            )
            hints = audit_scripts._detect_empty_catch_block(root)
            self.assertTrue(any("patch not root-cause fix" in h for h in hints))

    def test_flags_log_only_catch_and_notes_todo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Sample.kt",
                "fun c() {\n"
                "    try {\n        risky()\n    } catch (e: Exception) {\n"
                "        // TODO: handle this properly\n"
                "        Log.e(\"tag\", \"failed\", e)\n"
                "    }\n"
                "}\n",
            )
            hints = audit_scripts._detect_empty_catch_block(root)
            self.assertTrue(any("TODO/FIXME" in h for h in hints))

    def test_ignores_catch_with_real_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Sample.kt",
                "fun d() {\n"
                "    try {\n        risky()\n    } catch (e: IOException) {\n"
                "        retryWithBackoff()\n        logFailure(e)\n"
                "    }\n"
                "}\n",
            )
            hints = audit_scripts._detect_empty_catch_block(root)
            self.assertFalse(hints)

    def test_hints_are_excluded_from_blocking_audit_project_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Sample.kt",
                "fun a() {\n    try {\n        risky()\n    } catch (e: Exception) {\n    }\n}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("patch not root-cause fix" in f for f in findings))


class UnjustifiedSuppressTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_suppress_with_no_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "core/Sample.kt", "@Suppress(\"MagicNumber\")\nfun e() = 42\n")
            hints = audit_scripts._detect_unjustified_suppress(root)
            self.assertTrue(any("patch not root-cause fix" in h for h in hints))

    def test_ignores_suppress_with_comment_above(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Sample.kt",
                "// Detekt false positive: threshold is intentionally 42 for the checksum spec\n"
                "@Suppress(\"MagicNumber\")\nfun f() = 42\n",
            )
            hints = audit_scripts._detect_unjustified_suppress(root)
            self.assertFalse(hints)

    def test_ignores_suppress_with_trailing_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "core/Sample.kt",
                "@Suppress(\"MagicNumber\") // checksum spec requires exactly 42\nfun g() = 42\n",
            )
            hints = audit_scripts._detect_unjustified_suppress(root)
            self.assertFalse(hints)


class HedgingLanguageTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_flags_hedge_phrase_in_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "README.md",
                "In order to build the project, run the build command.\n",
            )
            findings = audit_scripts._detect_hedging_language(root)
            self.assertTrue(any("hedging language" in f and "README.md:1" in f for f in findings))

    def test_flags_hedge_phrase_in_docs_subdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "docs/architecture.md",
                "# Architecture\n\nIt should be noted that modules follow the 6-layer contract.\n",
            )
            findings = audit_scripts._detect_hedging_language(root)
            self.assertTrue(any("It should be noted that" in f for f in findings))

    def test_ignores_hedge_phrase_inside_code_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "README.md",
                "# Demo\n\n```text\nIn order to reproduce, do X.\n```\n",
            )
            findings = audit_scripts._detect_hedging_language(root)
            self.assertFalse(findings)

    def test_ignores_archived_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "docs/tasks/archive/2026-01-01-plan.md",
                "In order to migrate, we did X.\n",
            )
            findings = audit_scripts._detect_hedging_language(root)
            self.assertFalse(findings)

    def test_clean_docs_produce_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "README.md", "Run `./gradlew build` to build.\n")
            findings = audit_scripts._detect_hedging_language(root)
            self.assertFalse(findings)


class EnumMasqueradingAsSealedTests(unittest.TestCase):
    """kmp-code-quality's Enum vs sealed class vs factory rule: an enum whose `when`
    forces a `!!` in a branch likely needed variant-specific data it has nowhere to
    carry — a nudge toward sealed class/interface, not a certain misuse claim.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_enum_when_with_force_unwrap_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/state/src/commonMain/kotlin/State.kt",
                "enum class RequestState { IDLE, LOADING, LOADED, FAILED }\n\n"
                "fun render(state: RequestState, data: List<Item>?, error: String?) = when (state) {\n"
                "    RequestState.LOADED -> renderList(data!!)\n"
                "    RequestState.FAILED -> renderError(error!!)\n"
                "    else -> renderSpinner()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("enum masquerading as sealed" in f for f in findings))

    def test_ignores_sealed_class_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/state/src/commonMain/kotlin/State.kt",
                "sealed interface RequestState {\n"
                "    data object Idle : RequestState\n"
                "    data class Loaded(val data: List<Item>) : RequestState\n"
                "}\n\n"
                "fun render(state: RequestState) = when (state) {\n"
                "    is RequestState.Loaded -> renderList(state.data)\n"
                "    else -> renderSpinner()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("enum masquerading as sealed" in f for f in findings))

    def test_ignores_enum_when_without_force_unwrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/state/src/commonMain/kotlin/State.kt",
                "enum class Direction { NORTH, SOUTH, EAST, WEST }\n\n"
                "fun label(direction: Direction) = when (direction) {\n"
                "    Direction.NORTH -> \"N\"\n"
                "    Direction.SOUTH -> \"S\"\n"
                "    else -> \"?\"\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("enum masquerading as sealed" in f for f in findings))


class BuilderWithoutBuildMethodTests(unittest.TestCase):
    """kmp-code-quality's Splitting a god class rule: a *Builder-named class with no
    build() method is a real name/shape mismatch, not a judgment call.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_builder_with_no_build_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/net/src/commonMain/kotlin/RequestBuilder.kt",
                "package test\n\n"
                "class RequestBuilder {\n"
                "    fun url(value: String): RequestBuilder { return this }\n"
                "    fun send(): Request = Request()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("builder without build()" in f and "RequestBuilder.kt:3" in f for f in findings))

    def test_ignores_builder_with_build_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/net/src/commonMain/kotlin/RequestBuilder.kt",
                "package test\n\n"
                "class RequestBuilder {\n"
                "    fun url(value: String): RequestBuilder { return this }\n"
                "    fun build(): Request = Request()\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("builder without build()" in f for f in findings))


class DuplicateCodeBlockTests(unittest.TestCase):
    """Real gap surfaced by a user question: nothing caught repeated code. File-scoped,
    literal-line matching only — deliberately the narrow, safe version.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_two_functions_sharing_five_identical_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OrderService.kt",
                "class OrderService {\n"
                "    fun placeOrder(userId: String, cartId: String): Result {\n"
                "        val user = fetchUser(userId)\n"
                "        val cart = fetchCart(cartId)\n"
                "        val inventory = checkInventory(cart.items)\n"
                "        val totalPrice = calculateTotal(cart.items)\n"
                "        val discount = applyDiscount(user, totalPrice)\n"
                "        return Result.Success(discount)\n"
                "    }\n\n"
                "    fun previewOrder(userId: String, cartId: String): Result {\n"
                "        val user = fetchUser(userId)\n"
                "        val cart = fetchCart(cartId)\n"
                "        val inventory = checkInventory(cart.items)\n"
                "        val totalPrice = calculateTotal(cart.items)\n"
                "        val discount = applyDiscount(user, totalPrice)\n"
                "        return Result.Preview(discount)\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any(
                "duplicate code block" in f and "placeOrder" in f and "previewOrder" in f
                for f in findings
            ))

    def test_ignores_functions_sharing_fewer_than_five_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/SmallService.kt",
                "class SmallService {\n"
                "    fun a(): Int {\n"
                "        val computed = compute()\n"
                "        val adjusted = adjust(computed)\n"
                "        return adjusted\n"
                "    }\n\n"
                "    fun b(): Int {\n"
                "        val computed = compute()\n"
                "        val adjusted = adjust(computed)\n"
                "        return adjusted + 1\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("duplicate code block" in f for f in findings))

    def test_ignores_single_function_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/orders/src/commonMain/kotlin/OnlyOne.kt",
                "class OnlyOne {\n"
                "    fun run(): Int {\n"
                "        val computed = compute()\n"
                "        val adjusted = adjust(computed)\n"
                "        return adjusted\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("duplicate code block" in f for f in findings))


class StepwiseWhatCommentsTests(unittest.TestCase):
    """kmp-code-quality's 'a process never gets one // per step' rule."""

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_interleaved_numbered_step_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/LoginFlow.kt",
                "class LoginFlow {\n"
                "    fun run() {\n"
                "        // 1. validate the form\n"
                "        validate()\n"
                "        // 2. then log in\n"
                "        login()\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("stepwise what-comments" in f for f in findings))

    def test_ignores_single_numbered_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Ok.kt",
                "class Ok {\n"
                "    fun run() {\n"
                "        // 1. only one step here, no repetition\n"
                "        validate()\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("stepwise what-comments" in f for f in findings))

    def test_ignores_real_why_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Ok2.kt",
                "class Ok2 {\n"
                "    fun run() {\n"
                "        // Global lock, not per-account — fine at current throughput\n"
                "        validate()\n"
                "        login()\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("stepwise what-comments" in f for f in findings))


class CommentOnlyStubBodyTests(unittest.TestCase):
    """kmp-code-quality's stub-body rule: a checklist of // comments standing in for
    an unimplemented function isn't documentation.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_comment_only_checklist_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/render/src/commonMain/kotlin/Renderer.kt",
                "class Renderer {\n"
                "    fun recordCommand() {\n"
                "        // Begin Shadow Render Pass\n"
                "        // Bind basic shadow-casting pipeline\n"
                "        // Render mesh positions only\n"
                "        // End Render Pass\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("comment-only stub body" in f for f in findings))

    def test_ignores_single_todo_comment_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/render/src/commonMain/kotlin/Renderer.kt",
                "class Renderer {\n"
                "    fun recordCommand() {\n"
                "        // TODO: github.com/org/repo/issues/123 - implement shadow pass\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("comment-only stub body" in f for f in findings))

    def test_ignores_body_with_real_statements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/render/src/commonMain/kotlin/Renderer.kt",
                "class Renderer {\n"
                "    fun recordCommand() {\n"
                "        // Begin Shadow Render Pass\n"
                "        beginPass()\n"
                "    }\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("comment-only stub body" in f for f in findings))


class RoboticCommentPhraseTests(unittest.TestCase):
    """kmp-code-quality's Comment & KDoc Conventions: a comment that translates code
    into textbook prose isn't how a developer would explain it to a teammate.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_robotic_line_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Email.kt",
                "package test\n\n"
                "// This function is responsible for validating the email\n"
                "fun isValidEmail(email: String): Boolean = EMAIL_REGEX.matches(email)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("robotic comment phrasing" in f and "Email.kt:3" in f for f in findings))

    def test_flags_robotic_kdoc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Preferences.kt",
                "package test\n\n"
                "/**\n"
                " * This class is used to store user preferences.\n"
                " */\n"
                "class Preferences\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("robotic comment phrasing" in f for f in findings))

    def test_ignores_real_why_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/auth/src/commonMain/kotlin/Cache.kt",
                "package test\n\n"
                "fun ok(): Boolean {\n"
                "    // Cache miss is expected on cold start, not a bug\n"
                "    return true\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("robotic comment phrasing" in f for f in findings))


class PonytailCommentDensityTests(unittest.TestCase):
    """Real case found: 40 legitimate ponytail: ceiling comments added across one
    work session, spread thin (max 2 in any one file) — a per-file threshold
    would have caught none of it. Project-wide total is the real signal.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_when_total_exceeds_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(21):
                self._write(
                    root, f"feature/f{i}/src/commonMain/kotlin/File{i}.kt",
                    f"// ponytail: ceiling {i}, upgrade path {i}\nclass File{i}\n",
                )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("ponytail comment density" in f and "21 " in f for f in findings))

    def test_ignores_when_under_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(5):
                self._write(
                    root, f"feature/f{i}/src/commonMain/kotlin/File{i}.kt",
                    f"// ponytail: ceiling {i}, upgrade path {i}\nclass File{i}\n",
                )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("ponytail comment density" in f for f in findings))


class InvestigationNarrationCommentTests(unittest.TestCase):
    """kmp-code-quality's 'state the finding, not the investigation' rule: a
    comment recounting the debugging process isn't what a reader needs.
    """

    def _write(self, root: Path, rel_path: str, content: str) -> None:
        d = (root / rel_path).parent
        d.mkdir(parents=True, exist_ok=True)
        (root / rel_path).write_text(content, encoding="utf-8")

    def test_flags_investigation_narration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/cache/src/commonMain/kotlin/Cache.kt",
                "package test\n\n"
                "// Investigated: checked retry logic, turned out the root cause was a\n"
                "// stale cache entry.\n"
                "class ExpiringCache(ttl: Int)\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertTrue(any("investigation narration comment" in f for f in findings))

    def test_ignores_todo_with_tracked_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/cache/src/commonMain/kotlin/Cache.kt",
                "package test\n\n"
                "fun ok() {\n"
                "    // TODO: github.com/org/repo/issues/123 - revisit retry backoff\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("investigation narration comment" in f for f in findings))

    def test_ignores_real_why_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "feature/cache/src/commonMain/kotlin/Cache.kt",
                "package test\n\n"
                "fun ok() {\n"
                "    // 30s TTL -- a longer cache silently served stale data across a reconnect.\n"
                "}\n",
            )
            findings = audit_scripts.audit_project(root)
            self.assertFalse(any("investigation narration comment" in f for f in findings))


class MisplacedGithubAutomationTests(unittest.TestCase):
    def test_flags_misplaced_gh_scripts_in_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools_dir = root / "tools"
            tools_dir.mkdir(parents=True)
            (tools_dir / "gh-sub-issue.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            (tools_dir / "gh_sub_issue.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            (tools_dir / "create_issue.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            (tools_dir / "pr_validator.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            findings = audit_scripts._detect_misplaced_github_automation(root)
            self.assertEqual(len(findings), 4)
            self.assertTrue(all("misplaced GitHub automation script" in f for f in findings))

    def test_ignores_standard_verification_and_analysis_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools_dir = root / "tools"
            tools_dir.mkdir(parents=True)
            (tools_dir / "loc_survey.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            (tools_dir / "verify_agent_skills_sync.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            (tools_dir / "test_verify_detekt_baselines.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            (tools_dir / "check_template_consumer.sh").write_text("#!/bin/bash\n", encoding="utf-8")

            findings = audit_scripts._detect_misplaced_github_automation(root)
            self.assertEqual(len(findings), 0)

    def test_ignores_scripts_in_github_scripts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gh_scripts = root / ".github" / "scripts"
            gh_scripts.mkdir(parents=True)
            (gh_scripts / "gh-sub-issue.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            (gh_scripts / "gh_sub_issue.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            findings = audit_scripts._detect_misplaced_github_automation(root)
            self.assertEqual(len(findings), 0)


if __name__ == "__main__":
    unittest.main()
