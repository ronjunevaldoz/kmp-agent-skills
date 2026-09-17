# Skill Invocation Map

Part of `kmp-expert`. Load this file when working on: skill invocation map.

---

When the user asks about one of these topics, invoke the corresponding skill:

| User asks about | Invoke skill |
|---|---|
| "layer contract", "clean architecture", "which layer", ":model vs :api", "internal visibility" | `kmp-clean-architecture` |
| "composition over inheritance", "abstract class in commonMain", "extensible base class", "agent over-abstracting", "requires consumer to extend", "AbstractClassCanBeInterface" | `kmp-clean-architecture` |
| "set up a new KMP project", "create feature module", "6-layer scaffold" | `kmp-feature-scaffold` |
| "presenter module", "ViewModel no Compose", "MVI ViewModel", "UiState UiIntent" | `kmp-presenter-module` |
| "Koin", "dependency injection", "manual modules", "annotated mode" | `kmp-dependency-injection` |
| "coroutine scope", "structured concurrency", "GlobalScope", "Flow operator", "StateFlow vs SharedFlow", "flatMapLatest", "retry backoff", "exception transparency", "catch operator", "runTest", "Turbine flow test", "Mutex", "parallel decomposition", "async awaitAll" | `kmp-coroutines-flow-patterns` |
| "review my KMP project", "audit this repo", "what's wrong with this architecture" | `kmp-audit` |
| "project docs", "consumer docs", "project README", "getting started", "project docs reference", "onboarding docs", "architecture diagram", "library docs", "app docs" | `kmp-project-docs-maintainer` |
| "layout system", "screen wireframe", "SVG wireframe", "draft screen", "document screen layout", "layout doc", "screen layout", "layout-system" | `kmp-layout-system` |
| "write a lesson", "capture lesson", "document a finding", "pattern mismatch", "lesson file" | `kmp-lessons` |
| "harvest lessons", "propose skill amendments", "skill harvester", "harvest findings", "update skills from lessons" | `kmp-skill-harvester` |
| "migrate existing project", "adopt MVI", "LiveData to StateFlow", "migrate to clean architecture", "incremental adoption", "where to start", "brownfield", "refactor architecture", "migration path", "legacy project" | `kmp-migration` |
| "rename symbol", "rename class", "move file", "move class", "move package", "move module", "copy class", "safe delete", "rename skill", "rename command", "package rename", "IntelliJ refactor", "Android Studio refactor", "extract module", "dangling reference" | `kmp-refactor` |
| "repo README", "repo docs", "agent docs", "command docs", "routing text", "skills repo docs" | `docs-maintainer` |
| "wireframes", "screen flows", "layout specs", "design handoff", "component API", "visual direction" | `designer` |
| "release notes", "consumer release notes", "per-skill changelog", "CHANGELOG.md" | `changelog` |
| "logging", "logger wrapper", "logger facade", "kotlin-logging", "KotlinLogging", "Kermit", "log level", "crash reporting", "Crashlytics logging" | `kmp-logging` |
| "token saver", "token-saver", "token saving", "token reduction", "prompt compression", "context compression", "context headroom", "verbose output", "too much output", "caveman", "ponytail", "headroom", "rtk" | `kmp-token-saver` |
| "string.format", "decimalformat", "simpledateformat", "locale formatting", "number formatting", "date formatting", "shared formatter", "kmp formatter" | `kmp-expect-actual` |
| "auth", "authentication", "authorization", "JWT", "sessions", "Ktor RPC" | `kmp-ktor-auth-service` |
| "MongoDB", "database", "collection", "Flow", "change stream", "server-side Kotlin" | `kmp-mongodb-database` |
| "kotlin rpc", "kRPC", "kotlinx rpc", "RPC service", "shared RPC models" | `kmp-kotlin-rpc` |
| "add Ktor", "network layer", "API calls", "token refresh" | `kmp-network-layer` |
| "retry", "exponential backoff", "circuit breaker", "timeout", "rate limiting", "idempotency key", "transient error", "device lost", "backend parity" | `kmp-resilience` |
| "MCP", "Model Context Protocol", "kotlin-sdk", "MCP server", "MCP client", "MCP tool", "expose tool to Claude" | `kmp-mcp-sdk` |
| "local database", "SQLite", "SQLDelight", "offline storage" | `kmp-sqldelight-setup` |
| "CI", "GitHub Actions", "run KMP tests" | `kmp-ci-github-actions` |
| "github issue", "sub-issue", "epic", "ticket spam", "gh issue", "comment flooding", "issue template", "gh sub-issue", "in-place update", "markdown corruption" | `kmp-github-issue-governance` |
| "definition of ready", "definition of done", "DoR", "DoD", "quality gate", "delivery lifecycle", "acceptance criteria", "pr readiness", "readiness checklist", "done checklist", "ui validation", "performance gate" | `kmp-delivery-lifecycle` |
| "android cli", "android-cli", "android init", "android skills add", "create AVD from terminal", "android run apk", "agent-first android", "android studio quail", "render compose preview cli", "build and run android app", "deploy to emulator", "run KMP android target" | `kmp-android-cli` |
| "publish to Maven Central", "Maven publish", "release library", "release project", "cut release", "ship version", "versioning", "semantic versioning", "bump version", "vanniktech", "Sonatype", "git-cliff", "changelog", "GitHub Release", "release pipeline", "GPG signing" | `kmp-release` |
| "dev/staging/prod", "BuildKonfig", "environment config" | `kmp-flavor-environment` |
| "XCFramework", "Swift Package Manager", "SPM", "iOS binary" | `kmp-xcframework-spm` |
| "ImageVector", "vector icon", "vectorize", "SVG to Compose", "PNG to vector", "trace image", "icon from image", "logo vector", "raster to vector", "vtracer", "potrace", "convert image to icon", "compile icon", "app icon vector", "no PNG icons", "icon pipeline", "extract logo", "extract icon" | `kmp-imagevector-generator` |
| "publish KMP library", "Maven Central library", "KMP library publishing", "vanniktech maven publish", "mavenPublishing", "OSSRH", "Sonatype staging", "GitHub Packages library", "binary compatibility", "apiCheck", "apiDump", "api dump", "BOM library", "bill of materials", "distribute KMP library", "library consumers", "artifactId", "groupId", "POM metadata", "GPG signing library", "SNAPSHOT library", "library release checklist" | `kmp-library-publishing` |
| "GitHub Pages", "developer guide", "docs site", "MkDocs", "MkDocs Material", "Dokka HTML", "API reference site", "documentation website", "gh-deploy", "publish developer docs", "library documentation site" | `kmp-docs-site` |
| "expect actual", "platform-specific", "@ObjCName", "iOS interop" | `kmp-expect-actual` |
| "repository", "data layer", "offline-first", "cache", "single source of truth" | `kmp-repository-pattern` |
| "navigation", "screen routing", "NavHost", "deep links", "web routing", "browser fragment", "hash navigation" | `kmp-navigation` |
| "paging", "Paging 3", "PagingSource", "infinite scroll", "load more", "next page", "cursor pagination", "offset pagination", "LazyPagingItems", "paginate" | `kmp-paging` |
| "shared strings", "strings.xml", "stringresource", "hardcoded strings", "localization", "image assets", "fonts" | `kmp-shared-resources` |
| "MVI", "ViewModel state", "one-shot effects", "Screen/Content split" | `kmp-mvi` |
| "design system", "AppTheme", "design tokens", "dark mode", "spacing tokens", "layout consistency", "AppScaffold", "AppTopAppBar", "page title", "top bar", "action button placement" | `kmp-compose-design-system` |
| "update design system", "sync design system", "update components", "sync components", "update AppButton", "design system out of date", "new version of design system", "design system changed", "refresh design system" | `/kmp-update-design-system` |
| "fix design", "fix colors", "fix spacing", "fix typography", "hardcoded color", "hardcoded dp", "design inconsistencies", "wrong colors", "MaterialTheme instead of AppTheme", "nested cards", "redundant surface", "design violations", "design audit project", "fix design system usage", "detekt design rules", "component reimplementation", "token import boundary" | `/kmp-fix-design` |
| "record baselines", "record golden screenshots", "update golden images", "Roborazzi baseline", "screenshot baseline", "update screenshots", "record design screenshots" | `/kmp-record-design-baselines` |
| "visual audit", "audit screenshots", "check visual consistency", "design visual check", "cross-screen consistency", "spacing rhythm", "color contrast audit", "vision audit design" | `/kmp-audit-design-visual` |
| "adaptive layout", "WindowSizeClass", "tablet layout", "desktop layout", "mobile layout", "phone layout", "list detail", "detail split", "split screen", "navigation rail", "Compact Medium Expanded", "responsive UI", "master detail", "multi-pane", "different layout phone tablet", "different layout phone desktop", "screen size breakpoint", "pane layout", "layout per screen size", "layout phone desktop" | `kmp-compose-adaptive-layout` |
| "dialog", "bottom sheet", "toast", "tabs", "TopAppBar", "Checkbox" | `kmp-compose-design-system-extended` |
| "shadcn-compose", "ShadcnButton", "ShadcnTheme", "ShadcnCard", "shadcn ui kotlin", "shadcn compose multiplatform", "ExperimentalFoundationStyleApi", "shadcn kmp" | `kmp-shadcn-compose` |
| "shadcn login form", "shadcn admin layout", "shadcn dashboard", "shadcn data table", "ShadcnField", "ShadcnFieldGroup", "ShadcnTable", "ShadcnSidebar", "shadcn compose form", "admin shell compose multiplatform" | `kmp-shadcn-compose-layouts` |
| "mimic api", "api mimicry", "clone api shape", "inspired by jetpack compose", "custom dsl engine", "from-scratch renderer", "vulkan ui", "metal ui", "port api ergonomics", "reimplement compose-like dsl", "non-compose renderer", "engine-agnostic dsl", "own compiler-free dsl", "api shape porting" | `kmp-api-mimicry` |
| "KotlinPoet", "KSP", "Kotlin Symbol Processing", "annotation processor", "SymbolProcessor", "FileSpec", "TypeSpec", "generate Kotlin source", "compile-time codegen" | `kmp-kotlinpoet` |
| "slot API", "content lambda", "composable parameter", "scoped slot" | `kmp-compose-slot-api` |
| "state hoisting", "hoist state", "controlled component", "where does state go" | `kmp-compose-state-hoisting` |
| "remember vs ViewModel", "rememberSaveable", "state survival", "config change" | `kmp-compose-state-container` |
| "graphicsLayer", "Canvas", "drawWithCache", "workflow node", "custom drawing" | `kmp-compose-graphics-modifiers` |
| "@Preview", "desktop preview", "PDD", "fast UI iteration", "PreviewParameterProvider" | `kmp-compose-preview-driven-development` |
| "unit test", "runTest", "Turbine", "Flow test", "fake repository", ":core:testing" | `kmp-unit-testing` |
| "screenshot test", "Roborazzi", "golden image", "visual regression", "CI diff" | `kmp-roborazzi` |
| "test canvas layout", "canvas screenshot", "layout regression test", "visual accuracy", "pixel-perfect test", "arrangement test", "test node placement", "UI layout verification", "100% accuracy test" | `kmp-roborazzi` |
| "Ktlint", "Detekt", "code quality", "formatting", "architecture rules", "CI gate" | `kmp-code-quality` |
| "benchmark", "microbenchmark", "kotlinx-benchmark", "performance number", "measure performance", "profile this", "@Benchmark", "JMH", "is this faster", "compare performance", "performance regression" | `kmp-benchmark` |
| "web performance", "chrome devtools", "lighthouse", "performance trace", "wasm bundle size", "core web vitals", "network waterfall", "skiko performance", "compose web performance", "first paint", "wasmJs performance" | `kmp-compose-web-performance` |
| "analytics", "event tracking", "track event", "Firebase Analytics", "screen tracking", "AnalyticsTracker", "event schema", "amplitude KMP", "mixpanel KMP" | `kmp-analytics` |
| "form validation", "field validation", "required field", "email validation", "inline error", "submit disabled", "async validation", "FieldState", "ValidationResult" | `kmp-form-validation` |
| "image loading", "Coil", "Coil 3", "AsyncImage", "network image", "image placeholder", "circular image", "avatar image", "image cache", "disk cache" | `kmp-image-loading` |
| "permissions", "runtime permission", "camera permission", "location permission", "permission denied", "PermissionState", "permission rationale", "iOS permission" | `kmp-permissions` |
| "deep linking", "App Links", "Universal Links", "deep link", "AASA", "Digital Asset Links", "intent filter", "route parsing", "notification deep link" | `kmp-deep-linking` |
| "biometric", "fingerprint", "Face ID", "Touch ID", "BiometricPrompt", "LocalAuthentication", "biometric result", "device credential" | `kmp-biometric-auth` |
| "push notifications", "FCM", "APNs", "Firebase Messaging", "push token", "FirebaseMessagingService", "remote notification", "notification tap" | `kmp-push-notifications` |
| "WorkManager", "background work", "background task", "BGTaskScheduler", "BGProcessingTask", "one-time work", "periodic work", "CoroutineWorker", "background sync" | `kmp-workmanager` |
| "feature flags", "feature toggle", "remote config", "Firebase Remote Config", "A/B test", "experiment", "kill switch", "flag evaluation", "FeatureFlagProvider" | `kmp-feature-flags` |
| "accessibility", "a11y", "TalkBack", "VoiceOver", "contentDescription", "semantic role", "screen reader", "touch target", "WCAG", "traversal order", "mergeDescendants" | `kmp-compose-accessibility` |
| "animation", "AnimatedVisibility", "animateContentSize", "Crossfade", "AnimatedContent", "animateFloatAsState", "shared element", "enter transition", "exit transition", "reduced motion", "spring animation" | `kmp-compose-animation` |
| "offline first", "offline-first", "local first", "conflict resolution", "conflict handling", "background sync", "SyncManager", "SyncState" (opt-in — do NOT match on bare "sync", "cache", or "single source of truth"; those route to `repository-pattern`/`sqldelight-setup`) | `kmp-offline-first` |
| "crash reporting", "crashlytics", "firebase crashes", "sentry", "non-fatal", "symbolication", "dSYM", "breadcrumb bridge", "crash handler", "breadcrumb crash" | `kmp-crash-reporting` |
| "DataStore", "Preferences DataStore", "Proto DataStore", "save settings", "persist user prefs", "SharedPreferences migration", "createDataStore", "local key-value store" | `kmp-datastore` |
| "JNI", "JNI bridge", "native bridge", "JNIEnv", "Java_*", "GetStringUTFChars", "jbyteArray", "wrapper.cpp", "vendor C++", "3rd-party C++", "CMake JNI", "NDK", "call C++ from Kotlin/JVM", "native memory leak", "symbol conflict", "C-shim", "header compatibility" | `kmp-jni-pro` |
| "native core", "first-party native code", "author C++ library", "write native code from scratch", "native library scaffold", "public C-ABI header", "native renderer", "custom engine", "native ctest" | `kmp-native-authoring` |
| Disambiguation — "platform-specific code", "iOS implementation", "CPointer", "cinterop", ".def file", "Kotlin/Native" → `kmp-expect-actual` (NOT `kmp-jni-pro`; JNI is JVM-only) | — |
| "privacy policy", "terms and conditions", "terms of service", "GDPR", "CCPA", "data safety", "App Store privacy", "legal docs", "user data disclosure", "consent screen", "privacy screen", "play store legal", "app store compliance" | `kmp-legal-docs` |
| "ProGuard", "R8", "obfuscation", "minification", "keep rules", "proguard-rules.pro", "release build crash", "ClassNotFoundException release", "NoSuchMethodException release", "APK size", "minifyEnabled", "shrinkResources", "Koin keep", "Ktor keep", "SQLDelight keep", "kotlinx.serialization keep" | `kmp-proguard-r8` |
| "certificate pinning", "SSL pinning", "root detection", "jailbreak detection", "freeRASP", "RASP", "secure storage", "encrypted storage", "KSafe", "OWASP Mobile Top 10", "binary stripping", "reverse engineering" | `kmp-security` |
| "in-app purchases", "IAP", "subscriptions", "Play Billing", "StoreKit", "StoreKit 2", "paywall", "premium feature", "purchase flow", "restore purchases", "entitlement", "billing", "unlock premium", "one-time purchase", "auto-renewing subscription" | `kmp-in-app-purchases` |
| "Desktop target", "Compose Desktop", "CMP Desktop", "window management", "system tray", "file picker", "native menu bar", "keyboard shortcut Desktop", "drag and drop Desktop", "packaging Desktop", "distributable", "macOS app", "Windows app", "Linux app", "rememberWindowState", "jpackage", "dmg", "msi" | `kmp-desktop-app` |
| "openrewrite", "rewrite", "rewriteRun", "rewriteDryRun", "ast refactoring", "automated migration", "gradle rewrite", "migrate build.gradle.kts", "libs.versions.toml upgrade", "ktor 3 migration", "bulk dependency update" | `kmp-openrewrite` |

