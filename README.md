# kmp-agent-skills

[![skills.sh](https://skills.sh/b/ronjunevaldoz/kmp-agent-skills)](https://skills.sh/ronjunevaldoz/kmp-agent-skills)
[![Agent Skills spec](https://img.shields.io/badge/Agent%20Skills-spec%20compliant-brightgreen)](docs/reference/agentskills-io-standards.md)
[![License](https://img.shields.io/github/license/ronjunevaldoz/kmp-agent-skills)](LICENSE)
[![Repo size](https://img.shields.io/github/repo-size/ronjunevaldoz/kmp-agent-skills)](https://github.com/ronjunevaldoz/kmp-agent-skills)
[![Last commit](https://img.shields.io/github/last-commit/ronjunevaldoz/kmp-agent-skills)](https://github.com/ronjunevaldoz/kmp-agent-skills)

Created and maintained by [Ron Valdoz](https://github.com/ronjunevaldoz).

AI agent skills for **Kotlin Multiplatform (KMP)** development — clean module boundaries,
version catalogs, build-logic convention plugins, and explicit review loops before code is generated.

Built on the open [Agent Skills](https://agentskills.io) format. All 74 skills verified
against the real [`skills-ref`](https://github.com/agentskills/agentskills) reference
validator — see [`docs/reference/agentskills-io-standards.md`](docs/reference/agentskills-io-standards.md)
for what was checked and how.

---

## Main Use Cases

### Start a new KMP project

Run `/kmp-new-project` with a natural language description. The agent asks for your group ID, project
name, and what the app does — then scaffolds a full multi-module KMP project with clean architecture,
a design system, and a ready-to-use `.agents/` agent setup.

```
/kmp-new-project "A shopping app with auth, product listing, and orders"
```

The 9-step pipeline handles everything: module graph → clean-arch layers → Koin/Ktor/SQLDelight
wiring → design system → feature scaffolds → `AGENTS.md` tailored to your modules.

### Set up agents in an existing project

Run `/kmp-setup-agents` in any existing KMP project. It reads your `settings.gradle.kts` and
`libs.versions.toml`, then generates a custom `AGENTS.md` routing table based on the libraries
and feature modules it finds.

```
/kmp-setup-agents
```

Writes: `AGENTS.md` (tailored skill routing), all consumer
commands (`kmp-*.md`), deployed skills, and a `settings.json` Bash allowlist.

### Cross-agent repo policy

Downstream repos should keep canonical collaboration policy in:

- [`docs/reference/ai-collaboration.md`](docs/reference/ai-collaboration.md)
- [`docs/reference/agent-catalog.md`](docs/reference/agent-catalog.md)

Use `docs/*` for stable project design and ownership rules, and `skills/*` for
repo-local agent execution guidance. Keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`
thin and pointer-based instead of turning them into the only source of truth.

### Audit an existing project

```
/kmp-run-audit
```

Runs `audit_project.py` across your project and produces per-finding remediation steps using
the relevant skill. Catches architecture boundary violations, missing Koin bindings, layer leaks,
hardcoded colors, and Material theme usage. See [`kmp-audit`](skills/kmp-audit/) for what it checks.

---

## Quick Start

```bash
npx skills add ronjunevaldoz/kmp-agent-skills
```

Then in Claude Code:

1. **New project** → `/kmp-new-project <description>`
2. **Existing project** → `/kmp-setup-agents`
3. **Audit** → `/kmp-run-audit`
4. **Implement a feature** → `/kmp-implement-feature <name>`

**Start here:** not sure which skill to use? Ask `kmp-expert` — it routes you
to the smallest relevant skill set.

---

## Key Features

### Auto-reporting — consumer side
Every consumer project running `/kmp-run-audit` or `/kmp-harvest-lessons` can now surface
issues back to this repo without leaving the terminal:

- `/kmp-run-audit` **Step 7**: detects when a finding points to a *skill gap* (not just bad
  consumer code) and prompts `[y] Submit / [n] Skip / [v] View draft` — submits via `gh` or
  falls back to a browser URL
- `/kmp-harvest-lessons` **Step 6**: after every harvest, each positive pattern that the
  skills don't yet teach triggers the same interactive prompt to file an improvement proposal
- Both flows use `draft_issue.py --submit --repo ronjunevaldoz/kmp-agent-skills`

**Who runs it:** the consumer (any project using kmp-agent-skills).
**Where it goes:** issues land in this repo's GitHub Issues for the skills team to act on.

### Smart versioning — skills-repo side
`scripts/release.py` now has an `auto` bump mode that reads conventional commits and picks
the right tier — no more guessing or accumulating patch releases when a `feat` was shipped:

```bash
python3 scripts/release.py auto           # detects major / minor / patch
python3 scripts/release.py auto --dry-run # preview first
```

| Commit type | Bump |
|---|---|
| `feat!` or `BREAKING CHANGE` | major |
| `feat` | minor |
| `fix`, `chore`, `docs`, `refactor` | patch |

**Who runs it:** only the kmp-agent-skills maintainer when cutting a release.

---

## Skills

74 skills covering the full KMP stack. Load the smallest set that answers the request.
Health at a glance (size, freshness, known issues) without reading every `SKILL.md`:
[`docs/reference/skills-report.md`](docs/reference/skills-report.md).

| Category | Count | Covers |
|---|---|---|
| Foundation | 8 | Module structure, clean architecture, DI, CI, Android CLI |
| Infrastructure | 15 | Auth, networking, resilience, MCP, database, publishing, JNI, codegen |
| Patterns | 22 | MVI, navigation, offline-first, notifications, IAP, security, and more |
| UI System | 13 | Design system, state hoisting, animation, adaptive layout |
| Testing & Quality | 6 | Unit tests, screenshot tests, lint/static analysis, web performance |
| Meta | 10 | Routing, audit, migration, docs, release, refactor |

<details>
<summary>Full skill list (click to expand)</summary>

### Foundation
- [`feature-scaffold`](skills/kmp-feature-scaffold/) — 6-layer module structure, build-logic, TOML catalog, Koin
- [`clean-architecture`](skills/kmp-clean-architecture/) — layer contract, `:model` vs `:api`, `internal` rules
- [`presenter-module`](skills/kmp-presenter-module/) — pure-Kotlin ViewModel, MVI contracts, no Compose dep
- [`dependency-injection`](skills/kmp-dependency-injection/) — Koin wiring and scopes
- [`coroutines-flow-patterns`](skills/kmp-coroutines-flow-patterns/) — structured concurrency, Flow/StateFlow/SharedFlow selection, exception transparency, testing
- [`flavor-environment`](skills/kmp-flavor-environment/) — BuildKonfig, secrets, env setup
- [`ci-github-actions`](skills/kmp-ci-github-actions/) — CI matrix and release workflow
- [`android-cli`](skills/kmp-android-cli/) — Google's `android` CLI: emulator, build/deploy, SDK installs, agent bootstrap

### Infrastructure
- [`ktor-auth-service`](skills/kmp-ktor-auth-service/) — auth service, bearer/JWT, sessions
- [`network-layer`](skills/kmp-network-layer/) — Ktor client, auth refresh, result mapping
- [`resilience`](skills/kmp-resilience/) — retry/backoff/jitter, timeout, circuit breaker, rate limiting, idempotency keys
- [`mcp-sdk`](skills/kmp-mcp-sdk/) — Model Context Protocol via `modelcontextprotocol/kotlin-sdk`: MCP server/client, transport selection
- [`sqldelight-setup`](skills/kmp-sqldelight-setup/) — SQLDelight schema, drivers, migrations
- [`datastore`](skills/kmp-datastore/) — Preferences DataStore + Proto DataStore
- [`xcframework-spm`](skills/kmp-xcframework-spm/) — XCFramework and SPM export
- [`library-publishing`](skills/kmp-library-publishing/) — Maven Central, GitHub Packages, BOM, binary-compat-validator, GPG signing
- [`docs-site`](skills/kmp-docs-site/) — GitHub Pages developer guide, MkDocs Material, Dokka HTML API reference, compiler-verified code examples
- [`api-mimicry`](skills/kmp-api-mimicry/) — mimic a reference API's shape (Modifier chains, slot DSLs) for a from-scratch library on a non-standard runtime
- [`kotlinpoet`](skills/kmp-kotlinpoet/) — author a custom KSP annotation processor with KotlinPoet, FileSpec/TypeSpec builders, kotlinpoet-ksp interop
- [`mongodb-database`](skills/kmp-mongodb-database/) — MongoDB coroutine driver and repositories
- [`kotlin-rpc`](skills/kmp-kotlin-rpc/) — Kotlin RPC boundaries and scaffolding
- [`jni-pro`](skills/kmp-jni-pro/) — JVM JNI bridge to native C/C++
- [`native-authoring`](skills/kmp-native-authoring/) — author brand-new first-party C/C++ source for a native core, before any JNI bridge exists

### Patterns
- [`mvi`](skills/kmp-mvi/) — State / Intent / Effect, Channel effects, MviViewModel base
- [`expect-actual`](skills/kmp-expect-actual/) — platform-specific implementations
- [`repository-pattern`](skills/kmp-repository-pattern/) — repository boundary, fetch strategy
- [`navigation`](skills/kmp-navigation/) — type-safe navigation, auth gate
- [`deep-linking`](skills/kmp-deep-linking/) — App Links, Universal Links, URI schemes
- [`offline-first`](skills/kmp-offline-first/) — SyncState, optimistic updates, conflict resolution
- [`paging`](skills/kmp-paging/) — Paging 3, PagingSource, RemoteMediator
- [`logging`](skills/kmp-logging/) — logger wrapper, kotlin-logging or Kermit
- [`crash-reporting`](skills/kmp-crash-reporting/) — Crashlytics + Sentry, dSYM symbolication
- [`analytics`](skills/kmp-analytics/) — sealed AnalyticsEvent, Firebase/Amplitude
- [`feature-flags`](skills/kmp-feature-flags/) — FeatureFlag enum, Remote Config, A/B variants
- [`form-validation`](skills/kmp-form-validation/) — ValidationResult, FieldState, submit gating
- [`permissions`](skills/kmp-permissions/) — PermissionState, expect/actual PermissionController
- [`push-notifications`](skills/kmp-push-notifications/) — FCM + APNs, PushToken expect/actual
- [`workmanager`](skills/kmp-workmanager/) — CoroutineWorker, BGTaskScheduler
- [`biometric-auth`](skills/kmp-biometric-auth/) — BiometricResult, expect/actual BiometricAuthenticator
- [`image-loading`](skills/kmp-image-loading/) — Coil 3, AsyncImage, image cache
- [`shared-resources`](skills/kmp-shared-resources/) — shared resources and localization
- [`in-app-purchases`](skills/kmp-in-app-purchases/) — Play Billing + StoreKit 2, PurchaseState, MVI paywall
- [`proguard-r8`](skills/kmp-proguard-r8/) — R8 keep rules for KMP libraries, release build validation
- [`security`](skills/kmp-security/) — certificate pinning, root/jailbreak detection (freeRASP), encrypted storage (KSafe), iOS binary stripping, OWASP Mobile Top 10 map
- [`desktop-app`](skills/kmp-desktop-app/) — window management, tray, file picker, packaging

### UI System
- [`design-system`](skills/kmp-compose-design-system/) — tokens and core components
- [`design-system-extended`](skills/kmp-compose-design-system-extended/) — bottom sheet, dialog, snackbar, skeleton
- [`shadcn-compose`](skills/kmp-shadcn-compose/) — published library alternative to `design-system` — 70+ components, real experimental-API dependency risk
- [`shadcn-compose-layouts`](skills/kmp-shadcn-compose-layouts/) — composes shadcn-compose components into login forms, generic forms, data tables, and admin/dashboard shells, plus an audit script for hand-rolled patterns that should migrate to them
- [`compose-state-hoisting`](skills/kmp-compose-state-hoisting/) — hoisting rules, `@Stable`, `@Immutable`
- [`compose-state-container`](skills/kmp-compose-state-container/) — `remember` vs `ViewModel`, `rememberUpdatedState`
- [`compose-animation`](skills/kmp-compose-animation/) — AnimatedVisibility, Crossfade, shared elements
- [`compose-slot-api`](skills/kmp-compose-slot-api/) — slot-based component APIs, CompositionLocal
- [`adaptive-layout`](skills/kmp-compose-adaptive-layout/) — WindowSizeClass, list-detail split
- [`graphics-modifiers`](skills/kmp-compose-graphics-modifiers/) — Canvas, graphicsLayer
- [`preview-driven-development`](skills/kmp-compose-preview-driven-development/) — Desktop-first `@Preview` workflow, PDD cycle
- [`layout-system`](skills/kmp-layout-system/) — SVG wireframe docs per screen + slot-grid layout contracts
- [`imagevector-generator`](skills/kmp-imagevector-generator/) — raster/SVG → compiled Kotlin ImageVector; no hand-written paths, no PNG icons

### Testing & Quality
- [`unit-testing`](skills/kmp-unit-testing/) — `runTest`, Turbine, fake-over-mock
- [`roborazzi`](skills/kmp-roborazzi/) — screenshot tests from `@Preview` on JVM
- [`code-quality`](skills/kmp-code-quality/) — Ktlint + Detekt, CI gates
- [`accessibility`](skills/kmp-compose-accessibility/) — semantic roles, contentDescription, WCAG
- [`benchmark`](skills/kmp-benchmark/) — kotlinx-benchmark setup, @Benchmark conventions, per-target registration
- [`compose-web-performance`](skills/kmp-compose-web-performance/) — live browser profiling for the Web/Wasm target via chrome-devtools-mcp (traces, Lighthouse, network waterfall)

### Meta
- [`expert`](skills/kmp-expert/) — skill routing and build order
- [`audit`](skills/kmp-audit/) — repo review, fix sequencing, CI governance gate
- [`migration`](skills/kmp-migration/) — MVVM→MVI, monolith→multi-module, incremental adoption
- [`refactor`](skills/kmp-refactor/) — rename/move/copy/delete: textual sweep vs IDE refactor, module-move checklist, safe-delete checks
- [`project-docs-maintainer`](skills/kmp-project-docs-maintainer/) — consumer-facing project docs and onboarding
- [`legal-docs`](skills/kmp-legal-docs/) — privacy policy, terms, GDPR, data-safety labels
- [`lessons`](skills/kmp-lessons/) — structured lesson files for pattern mismatches
- [`skill-harvester`](skills/kmp-skill-harvester/) — reads lessons, proposes skill amendments
- [`token-saver`](skills/kmp-token-saver/) — terse replies, output compression, and smallest-correct-solution checks
- [`release`](skills/kmp-release/) — versioning, Maven Central, git-cliff, GitHub Release

</details>

---

## Commands

All commands are `kmp-` prefixed so they don't collide with your own command namespace.

### Consumer commands — install these in your project

| Command | What it does |
|---|---|
| `/kmp-new-project <description>` | Scaffold a full KMP project from a description |
| `/kmp-setup-agents [path]` | Initialize `.agents/` agent setup in an existing project |
| `/kmp-implement-feature <name>` | Plan → Implement → Validate → Review a feature |
| `/kmp-execute-ticket <id>` | Implement a GitHub Issue end-to-end |
| `/kmp-run-audit [path]` | Architecture audit with per-finding remediation + auto skill-gap reporting |
| `/kmp-harvest-lessons [path]` | Collect positive patterns from consumer project; auto-propose GitHub issues |
| `/kmp-audit-adaptive [path]` | Adaptive layout coverage + redundant title check across Compact/Medium/Expanded |
| `/kmp-verify [path]` | Full pipeline: build, tests, audit, screenshots, design |
| `/kmp-review-changes` | Review git diff against 6-layer rules and anti-patterns |
| `/kmp-generate-palette <name=#HEX ...>` | Generate `AppColors.kt` + Compose palette preview from N brand seed colors |
| `/kmp-vectorize <image>` | Compile a raster/SVG into a Kotlin `ImageVector` — replaces PNG icons and hand-written paths |
| `/kmp-fix-design [path]` | Scan and fix design system violations |
| `/kmp-migrate-to-shadcn [path]` | Migrate a project from the owned design-system to shadcn-compose, file-by-file with confirmation |
| `/kmp-clean-comments [path]` | Refactor documentation by architectural level (class/function/extension/inline) |
| `/kmp-update-design-system [path]` | Pull latest design system components |
| `/kmp-record-design-baselines [path]` | Record Roborazzi golden PNGs |
| `/kmp-audit-screenshots [path]` | Vision audit of screenshot goldens |
| `/kmp-audit-design-visual [path]` | Cross-screen visual consistency check |
| `/kmp-update-skills` | Pull latest skills and re-deploy to `.agents/skills/` |
| `/kmp-check-updates` | Check for a newer version of kmp-agent-skills |
| `/kmp-report-skill-issue` | File a structured skill bug report |
| `/kmp-refine-skill <name>` | Refine a project-owned skill against agentskills.io's real qualitative best practices (description phrasing, gotchas, scoping) |
| `/kmp-heal-docs [path]` | Self-heal project documentation sitemap (`docs/README.md`), verify link hygiene, and archive stale tasks |

### Repo-internal commands

| Command | What it does |
|---|---|
| `/kmp-new-skill <name>` | Scaffold a new skill with all required sections |
| `/kmp-modify-skill <name>` | Safely edit an existing skill |
| `/kmp-summarize-issues` | Scan all skills for quality gaps |
| `/kmp-submit-issue` | File a structured GitHub issue |
| `/kmp-maintain-docs [scope]` | Reconcile repo docs and routing text |
| `/kmp-release-notes` | Draft release notes for a version bump |
| `/kmp-setup-hooks` | Install git hooks for architecture hygiene |
| `/kmp-sync-local-skills` | Sync this repo release into local Claude / Codex / Gemini skill bundles on this Mac |

---

## Installation

### 🚀 Recommended: Global Machine-Wide Install (Zero Git Bloat)
Install once to make all 74 skills available across all your KMP projects (Claude Code, Gemini CLI, Codex, Cursor):

```bash
# Sync latest released skills globally (~/.claude, ~/.gemini, ~/.codex, ~/.agents)
bash scripts/sync-local-assistant-skills.sh
```

### 📦 Project-Level Installation & Provenance Lockfile
For team repositories, cherry-pick only the relevant architectural skills and track upstream versioning with `.agents/skills.lock`:

```bash
# Generate provenance lockfile
python3 skills/kmp-project-docs-maintainer/scripts/generate_skills_lock.py --project path/to/your-project
```

See [INSTALL.md](INSTALL.md) for full setup instructions and [Framework vs App Boundary Guide](docs/reference/framework-vs-app-boundary.md).

---

## Versions

| Library | Version |
|---|---|
| AGP | 9.2.0 |
| Kotlin | 2.4.0 |
| Compose Multiplatform | 1.11.1 |
| Coroutines | 1.11.0 |
| AndroidX Lifecycle | 2.11.0 |
| Navigation Compose | 2.9.2 |
| Koin | 4.2.2 |
| Ktor | 3.5.0 |
| SQLDelight | 2.3.2 |
| Roborazzi | 1.64.0 |

Full compatibility table: [`docs/reference/compatibility-matrix.md`](docs/reference/compatibility-matrix.md)

---

## Docs tasks

Before routing any docs request, classify it as repo-internal or downstream consumer.
Repo docs stay with `docs-maintainer`; downstream project docs go to `project-docs-maintainer`.

---

## Roadmap

See [PLAN.md](PLAN.md) for full scope and priority details.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for skill authoring, commit format, and PR checklist.

## References

- [Kotlin/kotlin-agent-skills](https://github.com/Kotlin/kotlin-agent-skills) — official Kotlin agent skills
- [android/skills](https://github.com/android/skills) — official Android agent skills
- [Kotlin/kmp-wizard](https://github.com/Kotlin/kmp-wizard) — AGP 9 KMP project templates

## Support

- ⭐ Star this repo
- 💬 Share feedback via issues
- 💰 [Support via donation](FUNDING.md)

## License

Apache-2.0 — see [LICENSE](LICENSE)
