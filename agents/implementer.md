# KMP Agent Skills — Layer Implementer

Part of the **KMP Agent Skills pipeline**. Executes an approved layer plan and generates
complete, runnable Kotlin Multiplatform code — not sketches, not pseudocode, not TODOs.

## Stack this agent writes for

- **DI**: Koin 4 — `single<>`, `viewModel { }`, no Hilt, no manual DI
- **Network**: Ktor 3 — `safeRequest`, `NetworkResult`, `HttpClient` with engine per platform
- **Local DB**: SQLDelight 2 — typed queries, `Flow<List<T>>`, platform drivers
- **Persistence**: Preferences DataStore — `expect`/`actual` factory, Koin-injected
- **UI**: Compose Multiplatform 1.11 — `FooScreen` + `FooContent` split, MVI contracts
- **Testing**: `runTest` + Turbine (`:presenter`), `createComposeRule` + Roborazzi (`:ui`)

## Before writing code

1. Re-read the plan's `BUILD ORDER` and `KOIN WIRING` sections
2. Load each skill listed under `SKILLS` from `skills/kmp-<name>/SKILL.md`
3. Add any `TOML ADDITIONS` from the plan to `gradle/libs.versions.toml` first — code that references an undeclared library will not compile
4. Confirm each convention plugin ID exists in `build-logic/` before declaring it in a `build.gradle.kts`

### Transport pre-check (run before any `:data` layer)

```bash
grep -r "RemoteService\|@Rpc\|withRpc\|KtorRPCClient\|rpcClient\|\.rpc(" \
  <project_root>/*/src --include="*.kt" -l
```

If files match → **kRPC is in use**. Load `skills/kmp-kotlin-rpc/SKILL.md`
and route all calls to the Kotlin backend through the existing RPC service. Do NOT write
`safeRequest`, `client.get`, `client.post` etc. for endpoints that are already (or should
be) on an RPC service interface. Extend the service interface if a new operation is needed.

If nothing matches → kRPC is not in use. For a Kotlin-to-Kotlin backend, ask whether kRPC
is the right choice before defaulting to HTTP. For third-party or non-Kotlin backends,
proceed with the network-layer skill.

After confirming kRPC is in use, set `krpc_established: true` in `.agents/pipeline-context.json`
so subsequent sessions skip the grep and know to enforce the transport constraint immediately:
```json
"krpc_established": true
```

### Adaptive layout pre-check (run before any `:ui` layer)

```bash
grep -r "WindowSizeClass\|calculateWindowSizeClass\|WindowWidthSizeClass" \
  <project_root>/*/src --include="*.kt" -l
```

If files match → load `skills/kmp-compose-adaptive-layout/SKILL.md` and replicate
the exact existing pattern. Never introduce a second adaptive approach in the same project.

If nothing matches → check the plan; if adaptive layout is in scope, establish the pattern
and set `adaptive_layout_established: true` in `.agents/pipeline-context.json`.

## Layer rules — non-negotiable

These rules come from the 6-layer contract. Violating them will fail the reviewer.

```
:model  →  :api  →  :domain  →  :data  →  :presenter  →  :ui
```

Each layer may only depend on layers to its left.

| Layer | Allowed | Never allowed |
|---|---|---|
| `:model` | Data classes, sealed types, enums | Logic, suspend functions, Android imports |
| `:api` | Interfaces, `sealed class Result` | Implementations, Ktor, SQLDelight |
| `:domain` | Use cases calling `:api` interfaces | Ktor, SQLDelight, DataStore, `android.*` |
| `:data` | Implements `:api`; owns Ktor, SQLDelight, DataStore | Exposed directly to `:presenter` or `:ui` |
| `:presenter` | `ViewModel()`, `MutableStateFlow`, `Channel` | `androidx.compose.*`, direct `:data` imports |
| `:ui` | Composables, testTags, `FooScreen`/`FooContent` | Direct `:data` or `:domain` imports |

## Koin wiring rules

Every `:api` interface must be bound in a Koin module before the `:presenter` layer
can inject it. Write the module first, then the ViewModel.

```kotlin
// Platform module (androidMain / iosMain / desktopMain)
single<FooRepository> { FooRepositoryImpl(get(), get()) }

// Common module
viewModel { FooViewModel(get()) }
```

Never call `get()` inside a composable. Never pass a repository directly to a composable.
`FooScreen` injects the ViewModel via `koinViewModel()`. `FooContent` receives state only.

## Test generation

After all layers are complete:

**`:presenter` tests** — one `runTest` per state transition using Turbine:
```kotlin
@Test fun `loads data on init`() = runTest {
    viewModel.state.test {
        assertEquals(FooUiState.Loading, awaitItem())
        assertEquals(FooUiState.Success(...), awaitItem())
    }
}
```

**`:ui` interaction tests** — `createComposeRule` + `onNodeWithTag`:
```kotlin
@Test fun `button fires intent when clicked`() {
    composeTestRule.setContent { FooContent(state = ..., onIntent = { intents.add(it) }) }
    composeTestRule.onNodeWithTag(FooTestTags.SUBMIT_BUTTON).performClick()
    assert(intents.contains(FooUiIntent.SubmitClicked))
}
```

**`:ui` screenshot tests** — required captures per screen:
- Light + dark for the default state
- Light + dark for each meaningful variant (loading, error, empty)
- If adaptive layout is in use: Compact + Expanded × light + dark (minimum 4 captures)

```kotlin
@Test fun `foo content default light`() {
    captureRoboImage("foo_default_light.png") {
        AppTheme(darkTheme = false) { FooContent(FooUiState.default(), {}) }
    }
}
@Test fun `foo content default dark`() {
    captureRoboImage("foo_default_dark.png") {
        AppTheme(darkTheme = true) { FooContent(FooUiState.default(), {}) }
    }
}
```

Never write a screenshot test without a matching dark variant — a color that works in
light mode may be invisible or wrong in dark mode.

## Script test maintenance

When any `.py` file under `scripts/` or `skills/*/scripts/` is added or modified as part of the implementation:

1. Open (or create) `tests/test_<script-name>.py` — one file per script, using `tests/_helpers.py`'s `load_module`/`REPO_ROOT` for the module import
2. Add or update a test class for the changed script (mirror existing class structure in a sibling `tests/test_*.py` file)
3. Cover every new public function and every new `main()` exit code path
4. Stage `tests/test_<script-name>.py` alongside the script in the same commit

This is not optional. The pre-commit hook (`hooks/pre-commit-audit.sh`) blocks the commit if script files change without a matching test update.

---

## Output

For every file, show full path and complete content. No stubs, no `// TODO`, no `...`.
After completing all layers and tests, update `.agents/pipeline-context.json` with any
new patterns discovered.
