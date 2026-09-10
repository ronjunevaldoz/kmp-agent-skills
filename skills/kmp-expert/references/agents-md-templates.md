# Agent scaffold templates — `.claude/AGENTS.md` and `CLAUDE.md`

Part of `kmp-expert`. The literal file bodies `/kmp-setup-agents` writes into a project.

These live in a **skill** reference, not in the command or a plugin-root `assets/`
directory, for a concrete reason: `/kmp-setup-agents` is consumer-facing (README tells
users to run it in any existing KMP project), and `update-consumer-skills.sh
--install-commands` copies a command as a single bare `.md` file. Skills, by contrast,
are always deployed. A template referenced from `assets/` would resolve in this repo and
be missing in every consumer project.

Path when reading this from a consumer project: `.agents/skills/kmp-expert/references/`
(or `.agents/skills/kmp-expert/references/` on a non-Claude client). Path in this repo:
`skills/kmp-expert/references/`. Same dual-path convention `kmp-layout-system` already
uses for its bundled script.

Fill every `<placeholder>` from the detected project before writing — never emit a
placeholder literally.

---

## `.claude/AGENTS.md`

### For APP projects

```markdown
# AGENTS.md — <project name>

This project uses [kmp-agent-skills](https://github.com/ronjunevaldoz/kmp-agent-skills).
Skills are installed in `.agents/skills/`.

## Project overview

<1–2 sentences describing what the app does, its platforms, and group ID>

## Project persona

<1 short paragraph describing the app-specific agent identity>

Examples:
- Todo app: Task Steward — optimize for fast capture, clear prioritization, low-friction completion, and zero clutter.
- Habit app: Coach — keep streaks visible, reduce shame-heavy language, and make progress obvious.
- Finance app: Steward — prioritize clarity, trust, and careful review over flashy automation.

## Skill routing

| Topic | Skill |
|---|---|
| New feature end-to-end | `kmp-feature-scaffold` → `kmp-clean-architecture` → `kmp-mvi` |
| ViewModel / screen state | `kmp-mvi` |
| Navigation | `kmp-navigation` |
| Dependency injection | `kmp-dependency-injection` |
| Code quality / linting | `kmp-code-quality` |
| Unit tests | `kmp-unit-testing` |
| Android CLI / emulator / deploy | `kmp-android-cli` |
| Project docs / onboarding | `kmp-project-docs-maintainer` |
<include only skills detected in Step 2c>
| Auth / login | `kmp-ktor-auth-service` |
| Local database | `kmp-sqldelight-setup` |
| REST API / network | `kmp-network-layer` |
| Key-value settings | `kmp-datastore` |
| Screenshot tests | `kmp-roborazzi` |
| Design system | `kmp-compose-design-system` |
| Architecture audit | `kmp-audit` |
| Harvest consumer lessons | `kmp-audit` (`--harvest` mode via `/kmp-harvest-lessons`) |
</end detected skills>

## Module graph

<list each module group>
| Module | Purpose |
|---|---|
| :composeApp | CMP entry point (Android / iOS / Desktop / Web) |
| :core:common | Shared utilities |
| :feature:auth | Auth feature (domain / data / presenter / ui) |
...

## Commands installed

See `.agents/commands/kmp-*.md` for available commands.
Key commands:
- `/kmp-implement-feature <name>` — plan → implement → validate → review
- `/kmp-run-audit` — architecture audit with per-finding remediation
- `/kmp-harvest-lessons` — collect good patterns to upstream to skills
- `/kmp-verify` — full validation pipeline
- `/kmp-execute-ticket <id>` — implement a GitHub issue end-to-end
- `/kmp-fix-design` — scan and fix design system violations
```

### For LIBRARY projects

```markdown
# AGENTS.md — <library name>

This project uses [kmp-agent-skills](https://github.com/ronjunevaldoz/kmp-agent-skills).
Skills are installed in `.agents/skills/`.

## Project overview

<1–2 sentences: what the library does, target consumers, Maven coordinates>
Group ID: <groupId>   Artifact: <artifactId>   Published to: Maven Central | GitHub Packages

## Skill routing

| Topic | Skill |
|---|---|
| Publishing to Maven Central | `kmp-library-publishing` |
| iOS / SPM distribution | `kmp-xcframework-spm` |
| API surface management | `kmp-library-publishing` (apiCheck / apiDump) |
| Platform-specific implementations | `kmp-expect-actual` |
| Unit / integration tests | `kmp-unit-testing` |
| Code quality (detekt, ktlint) | `kmp-code-quality` |
| CI automation | `kmp-ci-github-actions` |
| Android CLI / emulator / deploy | `kmp-android-cli` |
| Project docs / onboarding | `kmp-project-docs-maintainer` |
| Architecture audit | `kmp-audit` |
| Harvest consumer lessons | `kmp-audit` (`--harvest` mode via `/kmp-harvest-lessons`) |
<add only if detected>
| Screenshot / visual tests | `kmp-roborazzi` |
| BOM / multi-artifact | `kmp-library-publishing` (Step 4) |
| Library mimics a reference API's shape (Modifier/slot DSL) on a custom runtime | `kmp-api-mimicry` |
| Bridges to an existing 3rd-party C/C++ library | `kmp-jni-pro` |
| Authors brand-new first-party C/C++ source (not bridging to an existing library) | `kmp-native-authoring` |
</end>

## Published artifacts

| Artifact | Module |
|---|---|
| <groupId>:<artifactId> | :library |
| <groupId>:<artifactId>-testing | :library-testing (if present) |
| <groupId>:<artifactId>-bom | :bom (if present) |

## API surface rules

- Never remove or rename public symbols without a major version bump
- Run `./gradlew apiDump` after any public API change; commit the `.api` file
- `./gradlew apiCheck` runs in CI and blocks merge if API diff is uncommitted
- Mark internal symbols with `@InternalApi` to exclude from the dump

## Commands installed

See `.agents/commands/kmp-*.md` for available commands.
Key commands:
- `/kmp-run-audit` — architecture audit with per-finding remediation
- `/kmp-harvest-lessons` — collect patterns to upstream to skills
- `/kmp-verify` — full validation pipeline (build + test + apiCheck)
- `/kmp-check-updates` — check for skill updates
```

---

---

## `CLAUDE.md`

Only written if `CLAUDE.md` does not already exist in the project root — it stays thin
and just bootstraps Claude Code into the generated runtime:

```markdown
### Claude Code Project Profile

### Load skills context on initialization
--system-prompt-file=".claude/AGENTS.md"

### Default flags
--compact
--verbose=false

### Canonical project-owned agent sources
- docs/reference/ai-collaboration.md
- docs/reference/agent-catalog.md
- agents/
- rules/     (optional overlays only)
- hooks/
- commands/
- skills/

### Ignore generated and vendor directories
--ignore="**/build/**"
--ignore="**/.gradle/**"
--ignore="**/vendor/**"
--ignore="**/third_party/**"
```

---

## What to commit vs gitignore under `.claude/` and `.agents/`

Not everything this file's templates write is the same kind of artifact — some of it is a
reproducible mirror, some of it is live, project-specific configuration:

- **Safe to gitignore**: `.claude/skills/`, `.agents/skills/` (bundled `kmp-agent-skills`
  content). These are a pure deployed mirror — `update-consumer-skills.sh` reproduces them
  byte-for-byte from the upstream repo at any time. A missing or stale copy degrades
  gracefully: the agent just lacks a skill file until the next sync.
- **Commit these**: `.claude/AGENTS.md`, `.claude/settings.json`, `.claude/commands/`.
  These are generated once by `/kmp-setup-agents` but are *not* reproducible boilerplate —
  `.claude/AGENTS.md` holds this project's detected skill set and module graph, and may be
  hand-tuned afterward. It is also **live configuration**, not just a reference doc:
  `CLAUDE.md` points `--system-prompt-file` straight at it, so it loads as the actual
  system prompt on every session. Gitignore it and a fresh clone, new teammate, or CI
  runner has *no system prompt at all* until someone remembers to rerun
  `/kmp-setup-agents` — a harder failure than a missing skill file.

Recommended `.gitignore` entries in a consumer project:

```gitignore
.claude/skills/
.agents/skills/
```

Do not add a bare `.claude/` or `.agents/` ignore line — that would also swallow
`AGENTS.md`, `settings.json`, and `commands/`.

**Applying this during `/kmp-setup-agents` Step 7b:** if `.gitignore` doesn't exist,
create it with the entries above. If it exists and already has a **blanket** `.claude/`
or `.agents/` line (exactly that, not a scoped sub-path), replace it with the scoped
form, negating what must stay tracked:

```gitignore
.claude/*
!.claude/AGENTS.md
!.claude/settings.json
!.claude/commands/
.agents/skills/
```

If neither the scoped nor blanket entries exist yet, append the scoped form from above.
If scoped entries are already present in any form, skip — don't duplicate.

---

## Library-specific maintainer agent examples

Referenced from `/kmp-setup-agents`'s "Library-specific maintainer agents" section.
`agents/<name>-maintainer.md` at the project root, deployed to
`.claude/agents/<name>-maintainer.md` — only for a real, ongoing sub-domain the generic
`agents/*.md` roster (`planner`, `implementer`, `reviewer`, `fixer`, ...) doesn't own.

**A library that mimics a reference API's shape** (`kmp-api-mimicry`):

```markdown
# <library name> — UI DSL Maintainer

Owns: keeping the mimicked API shape honest against `MIRROR_MAP.md`.

## When to use
- Adding a new mimicked primitive (a new `*Modifier` function, a new slot composable)
- Reviewing whether a change quietly started claiming real reference-API behavior
  (recomposition, skipping) this library doesn't actually provide

## Checklist
1. Does `MIRROR_MAP.md` have a row for every mimicked primitive touched this session?
2. Does the naming avoid fusing the target runtime's name with the reference API's own
   type name (see `kmp-api-mimicry`'s naming-placeholder guidance)?
3. Does any new doc comment or README line imply real compiler-plugin behavior
   (`@Composable`-compatible, "supports recomposition") that isn't actually true?

Load `kmp-api-mimicry` for the underlying method; this agent only owns
enforcing it stays applied as the library grows.
```

**A library with a first-party native core** (`kmp-native-authoring` +
`kmp-jni-pro`):

```markdown
# <library name> — Native Core Maintainer

Owns: the boundary between this library's own C/C++ core and its JNI/cinterop bridge.

## When to use
- Adding a new native function that needs a Kotlin-side binding
- Reviewing whether JNI glue is being written before the native core's own public
  header API has stabilized (see `kmp-native-authoring`'s handoff point)

## Checklist
1. Is the new native function's public C-ABI signature in `native/include/` before any
   `external fun` is written on the Kotlin side?
2. Does the bridge stay a marshalling-only C-shim, with no reimplemented logic
   (`kmp-jni-pro`'s Phase 0 discovery + EP-1)?
3. Are native-side tests (ctest/gtest) passing independently of the Kotlin test suite?

Load `kmp-native-authoring` for authoring the C/C++ core itself, and
`kmp-jni-pro` for the bridge — this agent owns the boundary between them.
```

Both examples are starting points, not fixed templates — the real checklist should
reflect the project's actual `MIRROR_MAP.md`/native layout, not be copied verbatim.
