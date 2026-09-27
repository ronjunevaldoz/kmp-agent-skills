---
name: kmp-audit
description: >
  KMP project audit skill for reviewing an existing Kotlin Multiplatform codebase.
  Use this skill to inspect architecture, module boundaries, state handling, repository
  and network layering, Compose patterns, expect/actual usage, shared resources,
  design system usage, test coverage, platform readiness, and the skills repo itself.
  Produces findings, risk levels, and a fix sequence instead of implementation code.
  Pair with kmp-expert to route any follow-up work to the right
  domain skills.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-11'
  keywords:
    - investigation narration comment
    - state the finding not the investigation
    - ponytail comment density
    - too many ponytail comments
    - robotic comment phrase
    - orphaned reference doc
    - no inbound links doc
    - changelog unreleased backlog
    - stale unreleased section
    - formal comment phrasing
    - stepwise what-comments
    - comment-only stub body
    - numbered step comments
    - process narrated in comments
    - duplicate code block
    - repeated code detection
    - clone detection
    - DRY violation
    - builder without build method
    - enum masquerading as sealed
    - enum should be sealed class
    - force unwrap in when branch
    - docs hygiene kebab case
    - SCREAMING_CASE filename
    - docs-hygiene-only
    - audit_skills_repo vs audit_project
    - KMP audit
    - project audit
    - architecture review
    - boundary review
    - architecture drift
    - clean architecture audit
    - module audit
    - state audit
    - repository audit
    - Compose audit
    - expect actual audit
    - KMP review
    - project health check
    - readiness review
    - freshness audit
    - deprecation audit
    - script audit
    - skills repo audit
    - issue draft
    - question draft
    - kmp-agent-skills
    - kmp-skills
    - KMP agent skills
    - skill collection
    - skills index
---

## When to Use This Skill

Use this skill when you need to:
- Review an existing KMP repo for architecture drift or missing boundaries
- Check whether a feature or module is in the right place
- Validate MVI, repository, Compose, and `expect/actual` choices
- Produce a fix order before making code changes
- Compare the project against this collection's recommended KMP patterns
- Audit the skills repo for missing references, examples, scripts, rules, and freshness
- Turn confirmed findings into GitHub issue drafts or question drafts when the user
  wants work items instead of just findings

**Trigger keywords:** audit repo, review architecture, project health, boundary check,
module review, KMP audit, clean architecture review, readiness review, architecture drift,
what is wrong with this project, inspect this repo, audit skills repo, script hygiene,
freshness check, deprecation risk, references audit, governance, CI enforcement,
governance check, enforce skills, compliance, fail on violation, .kmp-skills.

**Freshness rule:** the audit checklist references Compose, MVI, network, and database patterns —
recheck the `kmp-expert` skill map and this collection's PLAN.md before auditing
against a new version baseline.

---

## Recommendation First

Default to **running the bundled scripts first, then reviewing findings manually against the
checklist in this skill**.

Why:
- `audit_project.py` catches mechanical smells (effect replay, state-copy races, UI/data leaks)
  faster than manual review
- scripts produce evidence-backed findings that are easier to convert to issue drafts
- the manual checklist catches architectural problems the scripts cannot detect

Do not skip the scripts and go straight to manual review — you will miss mechanical issues
that automation finds reliably.

---

## Audit Flow

1. Read the project docs first: `AGENTS.md`, `README.md`, architecture notes, and any
   module-specific guidance.
2. Inspect the module graph and dependency direction.
3. Check data flow boundaries: UI, domain, data, network, database, platform code.
4. Check Compose patterns: MVI, state hoisting, slots, state containers, design system.
5. Check multiplatform choices: `expect/actual`, shared resources, platform targets.
6. Report findings with severity, evidence, and the recommended fix order.

This skill does **not** implement fixes by default. It is the review surface that tells
the user and the other skills what to do next.

---

## What to Inspect

### 1) Module boundaries
- UI must not import `:data`
- Domain must not know about DTOs or SQLDelight entities
- Repository interfaces should live in `:api`, implementations in `:data`
- Shared UI primitives should live in the design system, not feature modules
- Run `generate_structure_diagram.py <project_root> --mermaid` to render the actual module
  layout against the canonical App (`feature/*`'s 6 layers) or Library
  (`library`/`library-testing`/`sample`) shape — informational, use it to visually confirm
  a project hasn't drifted before deeper review. Hard layer-order and bare-`:core` gates
  still come from `audit_project.py`'s own findings, not this diagram.
- Nothing new lives directly under `:app:*` for a kmp-wizard-scaffolded project — only
  the four entry points kmp-wizard itself creates (`androidApp`/`desktopApp`/`webApp`/
  `shared`). A new `app/<name>/build.gradle.kts` is a HIGH finding; the content belongs
  in `:feature:*` or `:core:*`.
- kmp-wizard's default demo screen (`class Greeting`, the `compose_multiplatform` logo
  resource) must not survive past scaffolding — a HIGH finding if it's still present.
- Raw Material components are flagged against **whichever** design system a project
  actually has wired — the generated/owned `App*` system, or shadcn-compose's `Shadcn*`
  components. For shadcn-compose specifically, `Scaffold`/`TopAppBar` are never flagged —
  shadcn/ui has no equivalent, keeping them raw is correct, not a bypass.

### 1a) Naming still matches behavior
- `audit_project.py` runs a cheap, non-blocking heuristic (`name-behavior drift`): flags a
  `*ViewModel` whose name shares no word with its own Intent variants. It only catches the
  crudest drift and prints under a separate `HINTS` section — never a BLOCKER.
- On top of that, use actual judgment during review: for each touched class, does the name
  still describe what the body does after this change? A class that quietly grew a second
  responsibility, or was renamed away from its real purpose, is a WARNING even though no
  script can catch it — call it out the same as any other finding.

### 1b) Construction/execution lifecycle coupling
- A class's primary constructor should capture only what it needs for its own
  activation — not every runtime feature variant a caller might eventually want.
  Watch for an infra-role class (a manager, engine, registry, or coordinator by
  *role*, not by name — any class can have this shape, naming it is not a
  reliable signal) whose constructor collects several nullable-default-null or
  Boolean-toggle params representing execution-time feature modes
  (`variantAConfig`, `enableSpecializedBehaviorX`) it doesn't need just to exist.
- No script flags this, deliberately — it's a judgment call about the class's
  *role*, not a countable shape. A legitimate config/state data class can carry
  the exact same param signature and be completely fine; a regex counting
  nullable/Boolean params alone would flag both identically and just become
  false-positive noise to maintain. Ask instead: does this class need to know
  about variant B just to be constructed, or only once execution actually asks
  for it?
- Fix: isolate construction from execution. Collapse the variant params into an
  immutable Specification Key (a small data class describing the requested
  variation) and resolve the actual behavior lazily — a cache keyed on that
  Specification Key, populated on first use — instead of the constructor
  pre-declaring every variation upfront.

### 2) State and MVI
- Screen state should be immutable
- One-shot effects should not be replayed
- Prefer `Screen` / `Content` split for testability
- Check for the wrong state container in ephemeral UI state

### 3) Data layer
- DTOs and entities stay inside `:data`
- NetworkResult should not leak into UI state
- Repositories should own mapping and fetch strategy
- Offline support should be explicit, not accidental

### 4) Multiplatform code
- Prefer shared code in `commonMain`
- Prefer a pure `commonMain` implementation before abstractions; only split to an
  interface or `expect/actual` when shared code cannot express the behavior cleanly
- Use `expect/actual` only when platform behavior is genuinely different
- Flag JVM-only utilities in `commonMain` such as `String.format`, `DecimalFormat`, or
  `SimpleDateFormat`; keep the shared API in common code and move the implementation to
  the platform that owns it
- Check platform target coverage against the product goal
- Distinguish `expect`/`actual` naming conventions from platform-exclusive files:
  - `Name.<platform>.kt` is reserved strictly for `actual` declarations matching an `expect` in `commonMain` (e.g. `FrameLoop.desktop.kt`)
  - Platform-exclusive files (`Main.kt`, `MainActivity.kt`, target-only engines/helpers like `WebGpuEngine.kt`, and platform interface implementations) must use standard `Name.kt`
  - Do NOT flag the coexistence of both naming styles as a divergence or split when each adheres to its proper category; flag only true inconsistencies (e.g. an `actual` missing its platform suffix while sibling actuals have it, or a platform-only file falsely suffixed with `.<platform>.kt`)

### 4b) Library project structure (gated on vanniktech-mavenPublish being applied)
- `explicitApi()` present somewhere — without it, every internal type Kotlin defaults
  to public leaks into the published API surface (kmp-library-publishing Step 3)
- A binary-compatibility-validator plugin or committed `.api` file present — without
  it, a public API change ships unreviewed and can break consumers silently (Step 5)
- Once split into 2+ published modules, a `build-logic/` convention plugin actually
  applied — 2+ modules each hand-rolling the same vanniktech/explicitApi config is
  real, growing duplication (Step 1a). A single `:library` module needs none of this —
  `build-logic/` adds nothing until the multi-module split happens

### 5) Design system
- Verify tokens, palette rules, and typography are consistent
- Check whether components use the right pattern for the repo's chosen UI system
- Flag hardcoded colors, sizes, and text styles
- Flag hardcoded user-facing strings in Compose; route to `kmp-shared-resources`
  and require `values/strings.xml` / `stringResource()` instead
- Require a preview stub for each `*Content.kt` in a feature `ui/` module so the
  preview workflow stays part of the scaffold, not a manual afterthought
- **Layout pattern consistency** — every `*Content.kt` in the same feature `ui/` dir must use the same top-level layout pattern (flat `Column`/`LazyColumn`, card-sectioned `AppCard`, or tabbed `TabRow`+`HorizontalPager`); mixed patterns are a `layout_inconsistency` violation. Run `scan_design_violations.py <project_root>` — it detects this cross-screen.

### 6) Native / JNI boundary (only if `*-jni.cpp`, `*-wrapper.cpp`, or `CMakeLists.txt` exist)
- 3rd-party C++ (`vendor/`, `third_party/`, submodules, `FetchContent`) is **read-only** —
  flag ANY edit to a vendored `.cpp`/`.h`. Hand off to `kmp-jni-pro`.
- Every opaque native handle stored as a Kotlin `Long` has a matching `dispose()`/`close()`
  → JNI `_free`. Flag any `_create` with no `_free` (memory leak).
- Every `GetStringUTFChars`/`Get*ArrayElements` has a release on all exit paths.
- JNI bridge contains type-conversion only — flag native logic or reimplemented library
  algorithms (route to `kmp-jni-pro` Phase 0 discovery).
- Complex headers (templates, `std::function`, overloads, exceptions) are wrapped via a
  flat `extern "C"` C-shim, not mapped directly. Full gate: `kmp-jni-pro`.

### 8) Agent & consumer setup
- **`CLAUDE.md` missing** → HIGH — no `--system-prompt-file` configured; skills context never loads
- **`.claude/AGENTS.md` missing** → HIGH — agent has no skill routing, feature table, or module map; run `/kmp-setup-agents`
- **`.agents/commands/` missing or empty** → MEDIUM — consumer commands (`/kmp-run-audit`, `/kmp-implement-feature`, `/kmp-verify`) not installed
- **`.agents/skills/` missing or empty** → MEDIUM — skills not deployed; trigger keywords won't activate skill content
- **Project-owned Claude scaffold incomplete** → MEDIUM — if a project already has `CLAUDE.md`/`.claude/`, it should also keep `agents/`, `rules/`, `hooks/`, `commands/`, `skills/`, `docs/reference/ai-collaboration.md`, and `docs/reference/agent-catalog.md` in the repo root so project-specific agent work is versioned outside runtime-only files
- **Project-owned custom skill not deployed or stale** → MEDIUM — every `skills/<name>/SKILL.md` must be copied into `.agents/skills/<name>/` after edits; missing or drifted deployed copies mean agents load outdated behavior. `_detect_project_skill_standards` only checks mechanical validity (frontmatter, line cap) — run `/kmp-refine-skill <name>` for the qualitative pass (description phrasing, gotchas quality, scoping) once the mechanical check is clean
- **Project agent file missing frontmatter, `name`, or `description`** → HIGH — `agents/<name>.md` needs a `---` frontmatter block with both fields to be usable
- **Project agent's `model:` is a tier name, not a real id** → HIGH — `flagship-coding`/`balanced-coding`/`fast-utility`/`precision-review` are provider-neutral catalog labels, not resolvable model ids; look up the real id in `docs/reference/agent-catalog.md`'s Mapping Rule table
- **Codex subagent TOML missing `name`/`description`/`developer_instructions`** → HIGH — all three are required by Codex CLI's own real subagent format
- **Project agent not deployed or stale** → MEDIUM — every `agents/<name>.md` must be copied into `.claude/agents/<name>.md` after edits, same discipline as skills
- **`AGENTS.md` covers only one surface of a multi-surface project** → MEDIUM — e.g., engine-only AGENTS.md in a project that also has Studio/UI modules; the active development surface has no routing
- **`MviViewModel` base class defined in a feature module** → MEDIUM — should live in `:shared:core` or `:core:mvi` so future features can extend it without cross-feature imports
- **Theme composable wraps `MaterialTheme`** → MEDIUM — blocks custom token ownership and `StyleScope` integration; use `CompositionLocalProvider` with `AppTheme` instead
- **`darkTheme = false` hardcoded in theme composable** → MEDIUM — system dark mode never applied; replace with `isSystemInDarkTheme()` default
- **Multiple parallel token files** (`*Tokens.kt`, `*ColorTokens.kt`) with different types (e.g., `ULong` constants vs `Color` values) → LOW — two token systems with no shared access pattern; consolidate under a single `AppColors` data class

### 7) Skills repo hygiene
- Ensure every skill has `name`, `description`, and `metadata.last-updated`
- Ensure trigger guidance is explicit enough to fire in practice
- Prefer references for fast-moving topics and keep examples only when they clarify
- Check that scripts are deterministic and covered by tests when practical — this repo's
  convention is explicit `python3 scripts/x.py` / `bash scripts/x.sh` invocation, not `./x.py`,
  so the executable bit itself is not a hygiene signal here
- Flag skills that depend on fast-moving libraries without a freshness note or docs link
- Flag scripts that encode assumptions about deprecated or unstable APIs
- Ensure new-project scaffold guidance names the `Kotlin/kmp-wizard` `all-targets`
  branch when the goal is Android, iOS, Web, Desktop, and Server
- Ensure KMP projects route plugin and dependency versions through `build-logic/`
  convention plugins and `gradle/libs.versions.toml` instead of scattering versions
  across module build files
- Run `scripts/check_redundancy.py` to flag skill pairs and agent pairs with heavy
  keyword/vocabulary overlap — a heuristic scan, not a verdict; read both before acting

---

## Output Format

When auditing, return:
- `Findings` first, ordered by severity
- `Evidence` for each finding, with file paths when available
- `Recommended fix order`
- `Skills to use next`
- `Optional issue drafts` when the user wants findings turned into GitHub-ready work items

Keep implementation advice short and actionable. If a finding maps cleanly to an existing skill,
name that skill so the follow-up path is obvious.

## From Finding to Issue

If the user wants repo work items, convert each confirmed finding into one of two things:
- a **GitHub issue draft** when the problem is actionable and should be tracked
- a **question draft** when the finding needs product or architecture confirmation first

Ask before creating any issue draft. Do not auto-file issues from an audit without
explicit confirmation from the user.

Every draft should include:
- a title following the format `[category] short problem description` — see categories below
- the evidence that triggered it (file path, line, or script output)
- the recommended fix or follow-up skill
- an attribution footer such as `Suggested by kmp-audit`

### Issue Title Format

Use `[category] short problem description`. Keep titles under 72 characters.
The description names the symptom, not the fix.

| Category | Use for |
|---|---|
| `[arch]` | Layer boundary violations, wrong module placement |
| `[mvi]` | Effect replay, state copy race, wrong state container |
| `[presenter]` | ViewModel has Compose import, wrong scope, missing test |
| `[data]` | Pass-through repository, DTO escaping layer, no cache |
| `[ui]` | Stateless composable violates, missing Preview stub, design drift |
| `[di]` | Koin module scope wrong, missing factory/viewModel registration |
| `[build]` | Convention plugin misconfiguration, version drift |
| `[test]` | Missing test coverage, mock instead of fake, wrong scope |

**Examples:**
```
[arch] DTO from :data escapes to :feature:todo:ui
[mvi] Effect replayed on recomposition in TodoListScreen
[presenter] ViewModel imports Compose in :feature:todo:presenter
[data] Repository is pass-through — no local cache
[ui] AddTodoContent missing Preview stub for error state
[di] TodoListViewModel registered as factory instead of viewModel
```

## References

Full implementation content lives in `references/*.md`: `governance-ci-enforcement`.
Load it under the Governance & CI Enforcement pointer above, not standalone.

---

## Common Anti-Patterns

- reporting findings before reading `AGENTS.md` and `README.md` — misses project-specific constraints
- producing implementation code during an audit instead of findings + fix order — audit and implement are separate steps
- auto-filing issues without user confirmation — always ask before creating GitHub issue drafts
- mapping every finding to the same skill — route each finding to the most specific applicable skill
- flagging style preferences as architecture violations — only flag boundary or correctness problems

An audit should produce findings that are actionable. If a finding doesn't map to a specific skill or fix, reclassify it as a question draft.

---

## Governance & CI Enforcement

Wiring a consumer project's CI to run the governance check automatically — the
`.kmp-skills` version file, the reusable workflow, what it scans, the `fail_on`
threshold guide, and running it locally before pushing.

Full content: [references/governance-ci-enforcement.md](references/governance-ci-enforcement.md).

---

## Bundled Script

- `scripts/governance_check.py` — CI enforcement orchestrator. Runs both scanners, reads
  `.kmp-skills` for version pinning, fails on missing or mutable pins, and exits non-zero
  on findings at or above the threshold.
  Used by the reusable workflow at `.github/workflows/kmp-audit.yml`.
- `scripts/classify_declarations.py` — classifies every Kotlin declaration as
  `core`/`sugar`/`helper`/`sample-local`/`deprecated`, per `kmp-code-quality`'s Code
  categorization table. A classifier, not a smell detector: `_detect_god_utils_file`
  asks a filename question, this asks what role a declaration plays in the API surface.
  Three categories are exactly decidable (`@Deprecated`, sample path, visibility);
  `sugar` is a conservative heuristic carrying a `confidence` field. Also flags a
  `@Deprecated` with no `ReplaceWith` and a public declaration in a sample module.
  `--json` for machine output, `--strict` to exit 1 on those problems.
- `scripts/audit_project.py` — runs a lightweight scan for common KMP architecture
  smells such as effect replay bugs, state copy races, and obvious UI/data boundary leaks.
  Supports three modes:
  - default — prints `FINDINGS:` list, exits 1 if any found
  - `--roadmap` — prints a prioritized adoption plan
  - `--harvest` — prints JSON `{ findings, lessons }` where `lessons` are positive patterns
    the consumer does right that could be upstreamed to skills (run `/kmp-harvest-lessons`)
- `scripts/validate_module_graph.py` — checks an existing project’s feature module layout and
  requires a preview stub for each `*Content.kt` in `:feature:*:ui`.
- `scripts/audit_skills_repo.py` — checks the skills repo for metadata, freshness, scripts,
  and documentation gaps.
- `scripts/draft_issue.py` — renders a GitHub-ready issue or question draft with an
  attribution footer.

---

## Related Skills

- `docs/reference/compatibility-matrix.md` — version compatibility table and conflict zones; check before bumping any library
- `kmp-expert` — use before running the audit; the expert skill identifies which domain skills apply and what build order to follow
- `kmp-clean-architecture` — defines the 6-layer boundary rules the audit script enforces
- `kmp-mvi` — most `state copy race` and `sharedflow replay effect` findings require this skill to fix correctly
- `kmp-roborazzi` — replacement for `manual screen capture` findings
- `kmp-compose-design-system` — replacement for `magic color literal` and `hardcoded spacing` findings
- `kmp-jni-pro` — owns every native/JNI finding (3rd-party C++ immutability, opaque-handle cleanup, C-shim wrapping); hand off section 6 findings here
- `kmp-code-quality` — owns the comment/KDoc convention `what-comment in control flow` findings are checked against; `/kmp-clean-comments` applies the fix

---

## Output Style

When asked to audit a project or the skills repo, respond in this order:
1. run the bundled scripts and report any automated findings
2. work through the manual checklist sections (module boundaries, state, data layer, etc.)
3. findings ordered by severity (critical → high → medium → low)
4. evidence for each finding (file paths, grep output, or line references)
5. recommended fix order
6. skills to use next

Ask before converting findings to issue drafts. Keep implementation advice minimal — this skill routes work, it doesn't implement it.

---

## Changelog

| Date | Change |
|---|---|
| 2026-09-11 | Added expect/actual vs platform-exclusive file naming check under Section 4 (Multiplatform code) — distinguish `Name.<platform>.kt` (reserved strictly for `actual` declarations matching an `expect`) from standard `Name.kt` (platform-exclusive files, target entry points, DI modules). Clarify that coexistence of both styles across a codebase is intentional and must not be flagged as a naming divergence. |
| 2026-08-30 | Added `_check_changelog_unreleased_backlog` to `audit_skills_repo.py` — user asked whether docs healing scoped `CHANGELOG.md`'s growth, and it deliberately doesn't (`kmp-project-docs-maintainer`'s scope explicitly excludes release notes). Real gap found in that investigation: `git-cliff`'s `## [Unreleased]` section (`kmp-release`'s own convention) only flushes into a dated version section on an actual `--tag` release run, and nothing previously flagged a project that just never cuts one — it silently accumulates forever. Flags once `[Unreleased]` exceeds 20 bullet entries, static filename/heading scan only, no git dependency, consistent with every other check in this file. Wired into both `--docs-hygiene-only` and the full audit. 4 new tests. |
| 2026-08-24 | Cross-referenced the new `/kmp-refine-skill` command from the "Project-owned custom skill" finding — `_detect_project_skill_standards` only checks mechanical validity (frontmatter, line cap); the new command owns the qualitative pass (description phrasing, gotchas quality, scoping) re-verified against the real, current agentskills.io best-practices docs. |
| 2026-08-24 | Wired `audit_skills_repo.py --docs-hygiene-only` into `governance_check.py` as a 3rd real check (MEDIUM severity, doesn't fail the default HIGH threshold). Root cause found while investigating "how do we keep consumer docs from going stale like awaken did": a consumer project's local pre-commit hook is a one-time fork of this repo's own hook script — `update-consumer-skills.sh` never re-syncs `hooks/` — so the local copy silently drifts, verified live on a real project whose forked hook still referenced an issue this repo had already resolved and never ran the docs-hygiene check at all. CI has no such staleness problem — it checks out this repo fresh, pinned to `skills_ref`, every run — so that's the actual enforcement point, not the local hook. Also fixed `governance-ci-enforcement.md`'s scanner table, which claimed a `validate_module_graph.py` check that was never actually wired into the script — a real doc/script drift caught in the same pass. Smoke-tested against a real 141-file/29,650-line consumer `docs/` tree — 119 real findings, including catching `docs/decisions/D10-codegen-derisk-findings.md` predating the ADR naming convention. 3 new tests. |
| 2026-08-23 | Added a `docs/tasks.md` index-drift check to `_check_docs_hygiene` — user wanted a task-status list so they don't have to open every task file one by one. `docs/tasks.md`'s Task Log table already existed as a convention but nothing enforced it stayed in sync; now an active (non-archive) task file with no matching mention in `docs/tasks.md` is flagged. Upgraded the Task Log template from a bullet list to an explicit `| Task | Status | Parent |` table in `kmp-project-docs-maintainer`. 3 new tests. |
| 2026-08-22 | Added the `assets/` undocumented-directory guard to `audit_skills_repo.py`, mirroring the existing `scripts/`/`references/` checks — user compared this repo's structure against the real agentskills.io spec (which `docs/reference/agentskills-io-standards.md` already documents as including `assets/`) and asked for it to be enforced the same way. No skill currently has an `assets/` folder, so this is preventive, not a fix for an existing violation. Noted `templates/` (4 skills, pre-existing) is a separate local convention, not part of the spec, and deliberately not folded into this check. 2 new tests. |
| 2026-08-22 | Added "1b) Construction/execution lifecycle coupling" — user supplied a full architectural rule spec ("Predictive Interface Over-Configuration": an infra manager/engine/registry class whose constructor hoards nullable/toggle params for runtime feature variants instead of resolving them lazily via a Specification Key). Initially planned a mechanical regex detector scoped to manager-suffixed class names; user pushed back twice — any class name can have this shape (name is not a reliable signal), and a name-agnostic structural heuristic (param count + has-a-function) would just be false-positive noise to maintain, real maintenance debt for a smell that's fundamentally about the class's *role*, not a countable shape. Added as a judgment-only inspection item instead, same treatment as 1a's naming-drift check — no script backs this one, deliberately. Extracted "Governance & CI Enforcement" into `references/governance-ci-enforcement.md` (first references/ split for this skill) to stay under the 500-line cap after the addition. |
| 2026-08-22 | Rewrote the docs/tasks/ hygiene check for `kmp-project-docs-maintainer`'s new task naming convention (user-requested): `docs/tasks/<parent>/<NN>-<slug>-<status>.md`, status one of `todo`/`doing`/`blocked`/`done` in the filename instead of a `status:` field in content. Replaced the `status:\s*(done\|completed\|closed)` content regex with `_TASK_FILE_RE` filename validation; added a missing-`**Date:**`-line check (the date moved out of the filename into the content); added a check for loose `.md` files sitting directly in `docs/tasks/` instead of under a parent folder. Also fixed `_check_naming_conventions`'s generic kebab-case scan, which would have false-positived on the new `NN-slug-status` filenames (they don't match the old `YYYY-MM-DD-` optional prefix) — now skips `docs/tasks/` entirely, since that path owns its own stricter check. 6 new tests. |
| 2026-08-22 | Added `_detect_investigation_narration_comment` — mechanical backing for `kmp-code-quality`'s new "state the finding, not the investigation" rule. Fixed phrase list ("investigated", "turned out to be", "root cause was", "steps to reproduce") in `//`/KDoc comments; `TODO`/`FIXME` naturally exempt since neither appears in the phrase list. Extracted `_iter_kt_comment_lines` as a shared helper — this detector and `_detect_robotic_comment_phrase` were duplicating the same KDoc-block-state scan. 3 new tests. |
| 2026-08-22 | Added `_detect_ponytail_comment_density` — real case found live: a ponytail-mode session added 40 legitimate `ponytail:` ceiling comments (each individually correct, states a real limitation + upgrade path) across one work session, spread thin across many files (max 2 in any one file), reading as noise in aggregate even though no single instance was wrong. A per-file threshold would have caught none of it — project-wide total (20+) is the actual signal. Non-blocking: a real ceiling stays valid regardless of count, this is a backlog-review nudge. 2 new tests. |
| 2026-08-21 | Widened `_detect_hedging_language` to also match the comment-specific robotic-phrase list ("is responsible for", "this class is used to") that previously only applied to `.kt` comments via `_detect_robotic_comment_phrase` — docs deserve the same "does this read like a textbook" bar as code. Also added `_check_orphaned_reference_docs` to `audit_skills_repo.py` — flags a `docs/`-root or `docs/reference/*.md` file with zero inbound links from anywhere else in the repo. Automates the grep `docs-hygiene.md` already tells a human to do by hand before deleting a reference doc; stays a review nudge, not a deletion verdict, since a fresh doc nothing points to yet isn't necessarily stale. Both wired into `--docs-hygiene-only`, the consumer-facing path. 5 new tests. |
| 2026-08-19 | Added `_detect_robotic_comment_phrase` — mechanical backing for `kmp-code-quality`'s new "write it like you'd explain it to a teammate" rule. Scans `//` and KDoc comments in `.kt` files for formal/robotic phrasing: comment-specific openers ("is responsible for", "this class is used to") plus the existing docs-hedging phrase list ("in order to," "it should be noted that"). Distinct scope from `_detect_hedging_language` (markdown docs) — this one walks Kotlin source, tracking KDoc block state and reusing `_line_comment_index` to avoid the URL-in-string false positive already fixed for the control-flow WHAT-comment detector. 3 new tests. |
| 2026-08-19 | Added `_detect_stepwise_what_comments` and `_detect_comment_only_stub_body` — mechanical backing for `kmp-code-quality`'s new "a process never gets one `//` per step" rule. First flags a numbered/step-prefixed `//` comment repeated 2+ times, each directly above its own statement (narrower than the broader WHAT-verb list, to avoid catching a single legitimate WHY comment that starts with a verb). Second flags a function body containing 2+ `//` lines and zero real statements — an unimplemented checklist standing in for code. Found and fixed a false positive during verification: the stub-body check initially fired on a *single* `TODO:` line too, which is the rule's own recommended fix — now requires 2+ comment lines. 6 new tests. |
| 2026-08-19 | Added `_detect_duplicate_code_block` — a user asked why a class using repetitive code wasn't caught; verified it genuinely wasn't (no detector in this file targets code duplication, and Detekt itself has no clone-detection ruleset by default). Deliberately narrow and safe: file-scoped (misses cross-file duplication, the costlier case) and literal-line matching (misses copy-paste with renamed variables — real clone detection needs token normalization, not attempted here). Flags 2+ functions in one file sharing 5+ identical consecutive statement lines via a brace-depth function-body scan + line-shingle intersection. 3 new tests. |
| 2026-08-19 | Added `_detect_builder_without_build_method` — mechanical check for `kmp-code-quality`'s new "Splitting a god class" rule: a `*Builder`-named class/interface/object with no `build()` method anywhere in the file is a real name/shape mismatch (the reader-expected chained-calls-ending-in-build() shape isn't there), not a fuzzy judgment call, so it's a plain finding rather than folded into the non-blocking vague-suffix hint. Fixing this detector's own regex surfaced a real pre-existing line-number bug shared with `_detect_vague_class_name_suffix` — `\s+` in the modifier-prefix group slurps across blank lines, so a class preceded by `package x\n\n` reports the `package` line instead of the actual `class` line. Fixed for the new regex (`[^\S\n]+` instead of `\s+`); flagged the sibling regex's identical bug as a separate follow-up rather than expanding this change's scope. 2 new tests. |
| 2026-09-11 | Expanded docs-hygiene auditing in `audit_skills_repo.py`: recursive non-doc and asset leakage detection (flags misplaced binary/asset files outside `docs/assets/` or `docs/images/`), canonical top-level `docs/` subdirectories enforcement, and fixed false positives for historical task notes in archive directories. 7 new regression tests. |
| 2026-08-18 | Added `_detect_enum_masquerading_as_sealed` — mechanical nudge for `kmp-code-quality`'s new "Enum vs sealed class vs factory" rule. Heuristic (same window-scan technique as `_detect_destructive_read_accessor`, not a real type-checker): a `when` referencing an enum's variants 2+ times, with a `!!` force-unwrap inside the same window, signals a branch needed data the enum has nowhere to carry. Verified it fires on the doc's own before-example and stays silent on the sealed-class fix. 3 new tests. |
| 2026-08-18 | Fixed `_check_docs_hygiene`'s kebab-case check in `audit_skills_repo.py` — `_SNAKE_CASE_RE` only matched lowercase `snake_case`, so a `SCREAMING_CASE.md` file in a consumer's `docs/` (a real violation, `kmp-project-docs-maintainer`'s docs-hygiene rule requires kebab-case everywhere under `docs/`) went unflagged. Found live: ran `--docs-hygiene-only` against a real downstream project (verifying a filed issue's premise), the run correctly caught stale lessons and an unarchived done task but missed two genuinely SCREAMING_CASE filenames. Regex now case-insensitive; kebab suggestion lowercases. Also added a doc-clarity note to `docs-hygiene.md` — the issue's actual root cause was conflating `audit_project.py` (no hygiene checks, correctly) with the script `docs-hygiene.md` actually documents (`audit_skills_repo.py --docs-hygiene-only`, which already worked standalone against any project despite its skills-repo-sounding name). 3 new tests. |
| 2026-08-17 | Added `_detect_hedging_language` — mechanical enforcement for `kmp-project-docs-maintainer`'s new Writing Style rule, which until now was pure judgment with no detector backing it. Scoped honestly: only the hedge-phrase rule is regex-detectable with low false-positive risk (a fixed, real phrase list — "in order to", "it should be noted that", etc.); the other 6 Writing Style rules (buried lead, table vs paragraph, real-example) need actual judgment and aren't claimed here. Scans root-level named docs + `docs/**/*.md`, skips fenced code blocks and `docs/*/archive/` (frozen history, not something this rule should churn). 5 tests. |
| 2026-08-07 | Fixed `classify_declarations.py` classifying local variables as API surface — a `var last = null` inside a method body came back as `core`. Real code is mostly function bodies, so this buried the actual declarations in noise (the worked before/after example added to `kmp-code-quality` is what surfaced it). Now tracks brace depth and skips `fun` block bodies; a class body is deliberately *not* skipped, since its members are exactly what the classifier exists to read. 2 new tests. |
| 2026-08-07 | Added `scripts/classify_declarations.py` — a **classifier** for `kmp-code-quality`'s core/sugar/helper/sample-local/deprecated taxonomy, which until now had no mechanical backing at all (the doc said so). Distinct from `_detect_god_utils_file`, which asks a filename question ("is this called Utils.kt and is it a grab-bag?"); this asks the taxonomy's real question per declaration: what role does it play in the API surface? Reads the doc's own "Kotlin mechanism" column literally — `@Deprecated`, sample path, and visibility keyword are exactly decidable; `sugar` is a conservative heuristic (public + single-expression body that delegates) carrying a `confidence` field; `core` is the residual. Also flags two things the categories imply but nothing checked: a `@Deprecated` with no `ReplaceWith` (no migration path = dead code, not a deprecation) and a public declaration inside a sample module. 11 tests. |
| 2026-08-07 | Fixed three real gaps in `_detect_god_utils_file`, found auditing what mechanically backs `kmp-code-quality`'s core/helper/sugar categorization. (1) The filename regex was `(Utils|Helpers)$` while the rule it enforces names **three** files — a god `AppExtensions.kt` sailed through the check written to catch it. (2) The top-level-fun regex was `^fun\s+`, so any visibility modifier hid the function: under `explicitApi()` — which every library this collection scaffolds turns on — every top-level fun is `public fun`, so the detector found zero functions and silently never fired in exactly the projects where API hygiene matters most. (3) A generic receiver (`fun List<String>.foo()`) failed to parse at all, so it counted toward neither the function total nor receiver diversity; type arguments are now consumed but not captured, so `List<String>` and `List<Int>` count as one receiver type. Verified the *recommended* shape (`StringExtensions.kt`, single receiver) still doesn't fire. 3 new tests. |
| 2026-08-07 | Comment-surface audit, three real fixes. (1) `_detect_what_comment_in_control_flow` reported findings against lines with **no comment on them**: it located comments with a plain `line.find("//")`, which also matches the `//` inside a URL string literal, so `val base = "https://build.example.com"` next to an `if` was reported as "this // comment narrates what the block does". Added `_line_comment_index()`, which skips quoted literals (honouring backslash escapes) — verified the two false positives go silent while a genuine comment *following* a URL string still fires. (2) That detector had **zero tests** despite shipping months ago; added 6. (3) Widened `_PUBLIC_DECL_RE` to match `val`/`var` — a public property is published surface under `explicitApi()` that `binary-compatibility-validator` tracks, but neither this detector nor `kmp-code-quality`'s Detekt block covered it, while the doc claimed "every public declaration". 2 new tests. |
| 2026-08-04 | Added `_detect_justification_comment_above_single_statement` — flags a 3+ line `//` comment block directly above one single-line Gradle dependency declaration. Distinct from `_detect_long_stacked_comment_block`: short enough (often 3-4 lines) to duck that check's 5-line threshold, and WHY-shaped enough to duck its WHY-signal exemption too — a real gap, since a user reported an agent-written comment of exactly this shape justifying a single `implementation(...)` line. See `kmp-code-quality`'s Comment & KDoc Conventions for the "genuine WHY vs justification trail" distinction this backs mechanically. 4 new regression tests. |
| 2026-08-03 | Fixed `_detect_long_stacked_comment_block`: it flagged any 5+ line `//` block by raw line count alone, with no way to tell lazy WHAT-narration (the real anti-pattern) apart from a genuine WHY explanation. Real gap surfaced auditing a consumer project's native rendering backends (Vulkan/WebGPU/OpenGL) — 108 of its 475 findings were this one check, mostly on legitimately dense GPU-pipeline WHY commentary that shouldn't be exiled to `docs/reference/` away from the code it explains. Added a WHY-signal heuristic (2+ causal/justifying words — "because", "workaround", "driver", "constraint", etc.) that exempts a block reading as genuine WHY; a block with 0-1 signal words is still flagged. 2 new regression tests. |
| 2026-08-03 | **Correction**: the 2026-07-20 entry below claims `kmp-code-quality`'s `CouplingBetweenObjects` is a real Detekt rule — verified directly against Detekt's own `default-detekt-config.yml` and confirmed it does not exist (no `coupling:` rule set in Detekt at all; that's a PMD/Java rule concept, fabricated into this repo in error). `_detect_god_class` remains this collection's only signal for cross-class coupling/fan-out — a heuristic, not backed by a real AST-based Detekt rule as previously claimed. See `kmp-code-quality`'s own correction entry for the full detail. |
| 2026-08-03 | Added library project structure conformance, gated on vanniktech-mavenPublish actually being applied (the one unambiguous "this is a published library" signal — a plain internal KMP module never applies it): `_detect_library_missing_explicit_api`, `_detect_library_missing_binary_compat_validator`, and `_detect_library_multimodule_missing_build_logic` (counts published modules to classify single- vs multi-module structure — a single `:library` module is correctly never flagged for missing build-logic, per kmp-library-publishing Step 1a's own "adds nothing until the split happens" guidance). Real gap: nothing previously checked whether a library project actually followed kmp-library-publishing's own documented setup. 8 new regression tests. |
| 2026-08-02 | Added two "patch not root-cause fix" hints (same non-blocking tier as `name-behavior drift`/`vague class name suffix`): `_detect_empty_catch_block` (empty or log-only catch, no real recovery) and `_detect_unjustified_suppress` (`@Suppress` with no nearby comment explaining why). Both note a nearby `TODO`/`FIXME` in the finding text as corroborating evidence when present. Verified first that Detekt's own `ForbiddenComment` rule already flags `TODO:`/`FIXME:`/`STOPSHIP:` by default — no separate TODO detector needed. 7 new regression tests. |
| 2026-08-02 | Added `_detect_context_leak_in_singleton` — the classic Android memory leak, a `companion object`/singleton caching a `Context`/`Activity` reference. Applies to both App and Library projects with no project-type gating (a KMP library's Android `actual` implementation is exactly as leak-prone as an app). Fixed a real bug found during testing: the first version required the *property name* to contain "context," missing `Activity`-named properties even though the type check would have caught them — the type annotation is the real signal, not the name. Correctly exempts `applicationContext`/`Application` (safe to hold long-term). 4 new regression tests. |
| 2026-08-01 | Added two performance/encapsulation detectors from a Kotlin performance-killer survey: `_detect_object_creation_in_loop` (a known-expensive constructor built inside a `for`/`while` body with no dependency on the loop variable — verified against Detekt's own Performance ruleset first, which doesn't cover this) and `_detect_public_mutable_collection` (a public `Mutable*` property/return type — distinct from the Compose-only unstable-collection-param check, this is an encapsulation concern). 7 new regression tests. |
| 2026-08-01 | Added `_detect_vague_class_name_suffix` — a non-blocking hint (same channel as `name-behavior drift`) flagging `Manager`/`Processor`/`Helper`/`Info`/`Data` class-name suffixes, a well-known Clean Code naming smell. Deliberately kept out of blocking findings: this repo's own `offline-first` skill ships a legitimate, well-scoped `SyncManager` interface, so a pure regex can't reliably judge vagueness for every case — nudge only. Excludes `data class`/`enum class` declarations (self-documenting). 6 new regression tests. |
| 2026-08-01 | Added `_detect_hardcoded_ui_string` — real gap: this skill's own "What to Inspect" checklist has said "flag hardcoded user-facing strings, route to `kmp-shared-resources`" since the beginning, but unlike every other "hardcoded X" (colors, spacing, divider color, base URL, Android versionCode), strings were never mechanically checked. Flags a literal in a `Text`/`AppText`/`ShadcnText` call or `contentDescription`, skipping numeric/punctuation-only literals and `Preview` files. 5 new regression tests. |
| 2026-07-31 | Added three detectors from a Kotlin/KMP library-hygiene survey: `_detect_kotlin_reflect_in_common` (full reflection in `commonMain` — `kotlin-reflect` is JVM-primary, limited/absent on Native/JS), `_detect_god_utils_file` (a `*Utils.kt`/`*Helpers.kt` file with 10+ top-level functions spanning 3+ distinct receiver types), and `_detect_inline_unnamed_regex` (a `Regex(...)`/`.toRegex()` built inline inside an expression instead of bound to a named `val`). Also added an Alpha-stability caveat to `_detect_compose_unstable_collection_param`'s `kotlinx.collections.immutable` suggestion — verified against the library's own repo. 13 new regression tests. |
| 2026-07-31 | Extended `_detect_agent_setup` with three real gaps found in a user-submitted review: `.agents/skills/` missing/empty when a Claude scaffold exists (MEDIUM — other agentskills.io clients see no skills), drift between `.claude/skills/` and `.agents/skills/`'s actual skill-name sets (MEDIUM), and a bundled-looking skill name (`kmp-*`/`jni-*` prefix) present under project-root `skills/` (HIGH — that path is for project-owned custom skills only). Fixed the same gaps at the source: `update-consumer-skills.sh` now prefers `.agents/skills` in auto-detection and mirrors project-owned custom skills there too (previously only bundled skills were mirrored), `INSTALL.md`'s manual/Gemini install paths were Claude-only, and `docs/reference/ai-collaboration.md`/`kmp-expert`'s canonical layout diagrams never mentioned `.agents/` at all. 5 new regression tests. |
| 2026-07-31 | Added `_detect_partial_param_documentation` — user-reported real gap: a KDoc block that documents 1 of a function's several parameters reads as complete but isn't, and nothing caught it. Coverage must be all-or-nothing (every parameter addressed via `@param`/inline `[name]`, or none — a plain summary is still valid). Caught and fixed a real bug while building it: the new regex was silently overwritten by an unrelated pre-existing `_FUN_SIGNATURE_RE` with the same module-level name, defined later in the file — Python's top-to-bottom execution means the second definition wins with no error, and the detector matched nothing until renamed. Swept the rest of the file for other name collisions (none found). 6 new regression tests. |
| 2026-07-31 | Added `_detect_lowercase_unit_composable` — the real, official [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide) requires a `@Composable` function returning `Unit` to be PascalCase (a UI node, read as a noun), never camelCase like a verb; this repo's own generated `App*`/`Shadcn*` components already followed the rule by convention but nothing checked it mechanically or stated it as a naming rule. Excludes composables with an explicit return type (factory functions like `rememberScrollState()`, correctly camelCase). 4 new regression tests. |
| 2026-07-31 | Added `_detect_leftover_wizard_demo_code` — kmp-wizard's real `all-targets` template ships a working demo screen (`class Greeting`, a `compose_multiplatform` logo resource) that must be deleted once real feature work starts; left in place it's dead sample code shipping to production. Extended `_detect_raw_component_bypass` to also fire for shadcn-compose projects (`ShadcnTheme`/`Shadcn*` marker), using a narrower, separately-verified component map (`Button`/`Card`/`TextField`/`AlertDialog`/`ModalBottomSheet` only — `Scaffold`/`TopAppBar` deliberately excluded since shadcn/ui has no equivalent, per `/kmp-migrate-to-shadcn`'s own mapping table; flagging them would have been wrong). Previously this detector only recognized the generated/owned `App*` system, so a shadcn-compose project got zero raw-component enforcement. 7 new regression tests. |
| 2026-07-31 | Added `_detect_unauthorized_app_submodule` — kmp-wizard's real `all-targets` template (verified against the live repo) nests exactly four modules under `app/`: `androidApp`/`desktopApp`/`webApp`/`shared`. A new module dropped directly under `app/<name>/` duplicates `:core:*`/`:feature:*`'s job and blurs the entry-point boundary kmp-wizard itself draws. 3 new regression tests. |
| 2026-07-31 | Added `generate_structure_diagram.py` — renders actual App/Library module structure (markdown tree + Mermaid) against the canonical layout, so a developer can visually verify a project hasn't drifted; informational only, wired into `/kmp-verify` as an optional Step 1a. Added `_detect_name_behavior_drift` — a non-blocking heuristic flagging a `*ViewModel` whose name shares no word with its own Intent variants; deliberately kept out of `audit_project()`'s blocking findings and surfaced through a separate `HINTS` section in `main()`, since a token-overlap check has real false-positive risk. Real gaps — no structure-visualization tool existed, and naming drift had zero mechanical or documented check. 7 new regression tests. |
| 2026-07-26 | Added `_detect_bare_core_module` — `_detect_module_layer_violation`'s module-path regex only ever matched `feature/<name>/<layer>`, so it never applied to `:core` at all; a monolithic `core/build.gradle.kts` (instead of split `:core:model`/`:core:api`/etc. submodules, per `kmp-clean-architecture`'s own ":core" vs ":feature" Split table) went completely uncaught. 3 new regression tests. |
| 2026-07-26 | Added `_detect_viewmodel_injects_repository` — `kmp-mvi`'s own changelog called the ViewModel-depends-only-on-`:domain` rule mechanically checkable, but it wasn't; `_detect_module_layer_violation` can't catch it since `presenter -> api` is an allowed module-level edge for other reasons. File-level check instead: a `*ViewModel`'s constructor param typed `*Repository`. 3 new regression tests. |
| 2026-07-26 | Added three more detectors following the same session's gap survey: `_detect_combined_style_file` (2+ `*Variant` sealed types bundled in one `styles/` file — the same problem as combined component files, one directory over), `_detect_viewmodel_too_many_intents` (15+ `Intent` variants — a god-ViewModel signal `_detect_viewmodel_size`'s line count alone can miss), and `_detect_viewmodel_multiple_stateflows` (2+ exposed `StateFlow` properties beyond `state` — MVI's one-State-per-screen rule broken a different way). 8 new regression tests. |
| 2026-07-26 | Added `_detect_combined_component_file` — a user asked why the collection would introduce component-file bloat; found that `kmp-compose-design-system`'s own generated templates already follow one-component-per-file by convention, but nothing stated or checked that rule for a real project. Flags 3+ top-level components in one `designsystem`/`components/` file, excluding Preview functions and Screen/Content pairs. 4 new regression tests. |
| 2026-07-20 | Added `_detect_undocumented_public_api` — flags a `public class`/`interface`/`object`/`fun` with no preceding KDoc block, gated on the project already using `explicitApi()`/`explicitApiWarning()` (without it, "public" isn't a deliberate-enough signal to check — most app code is public by Kotlin's own default). Backs `kmp-library-publishing`'s new KDoc coverage rule. 3 new regression tests. |
| 2026-07-20 | Added three more anti-pattern detectors from a user-requested gap survey: `_detect_runblocking_in_shared_code` (runBlocking in commonMain outside a `fun main()` entry point — blocks the calling thread, often the main thread on Android/iOS), `_detect_koin_circular_dependency` (a cycle among explicitly-typed `single<A>`/`factory<A>`/`scoped<A>` Koin bindings — narrowed to explicit type args to keep false positives near zero, since a plain `get()` with no type argument can't be resolved to a dependency graph without also parsing the constructor it's injected into), and `_detect_compose_unstable_collection_param` (raw `List`/`Map`/`Set` composable parameters, which the Compose compiler treats as unstable). 9 new regression tests. |
| 2026-07-20 | Added `_detect_god_class` — repo-wide god-object detection, not scoped to ViewModel/Composable. A plain class (excludes data/sealed/enum/value/annotation classes, and files already covered by the ViewModel-size/god-composable detectors) past 400 lines and 15 functions is flagged. Real gap: `kmp-code-quality`'s new `LargeClass`/`TooManyFunctions`/`CouplingBetweenObjects` Detekt rules are the precise version; this is the heuristic backstop for a project that hasn't wired that config yet. 4 new regression tests. |
| 2026-07-20 | Added a new detector category — pattern-adoption *opportunities*, distinct from misuse anti-patterns and from `_detect_positive_patterns`' upstream-candidate scanning. `_detect_value_class_opportunity` flags 2+ raw String/Long ID parameters in one function signature (kmp-clean-architecture's Typed Domain IDs rule). `_detect_context_parameter_opportunity` flags a parameter repeated across 5+ signatures in the same file (kmp-dependency-injection's Context Parameters section). Both LOW severity, both nudges rather than findings — real gap: this collection had anti-pattern detection and positive-pattern harvesting, but nothing that says "your code shape suggests a pattern you don't have yet." 7 new regression tests. |
| 2026-07-19 | Added `_detect_destructive_read_accessor` — real gap found while comparing this repo's own guidance against a separate KMP project's commit history: a `consume*()`/getter that clears the field it just read before returning, breaking silently for a second caller in the same tick/request (the exact bug fixed in that project's `Input.consumeTypedText()`/`consumeEditActions()`). Heuristic matches the 3-line "read field into local, clear same field, return local" shape. Backs `kmp-code-quality`'s new "Side-Effect-Free Accessors" section. 4 new regression tests. |
| 2026-07-17 | Added `_detect_agent_file_standards`/`_detect_agent_deployment_drift` — real gap: only whether agent *setup artifacts* existed was checked, never whether individual agent files themselves were valid. Mirrors the skill-standards/deployment-drift pattern for `agents/*.md` (frontmatter with `name`/`description`; flags a tier name like `balanced-coding` written into `model:` instead of a real id — the exact bug found and fixed in `docs/reference/agent-catalog.md` this same session) and `.codex/agents/*.toml` (Codex's real required fields: `name`/`description`/`developer_instructions`). Caught a real bug before shipping: `.codex` is normally in `_EXCLUDED_DIRS` to keep other detectors from scanning deployed bundle templates as real code, which silently filtered out this detector's own `.codex/agents/` scan — its exact target directory; fixed by not applying that exclusion here, since inspecting `.codex/agents/` is this detector's whole purpose. 11 new regression tests. |
| 2026-07-17 | Added `_detect_mixed_design_system_usage` — flags a project calling both `ShadcnTheme(...)` and `AppTheme(...)` in real source, mechanically enforcing the "never combine `kmp-shadcn-compose` and `kmp-compose-design-system`" rule that was documented but never checked. Scoped to the two theme wrappers rather than individual `App*` component names, to avoid a false positive on an unrelated real identifier (`AppConfig(...)`, `AppDatabase(...)`). Caught a real bug before shipping: the first regex only matched a parenthesized call (`AppTheme(`), missing the common parenthesis-free trailing-lambda call (`AppTheme { ... }`) both wrappers support since every other param is defaulted. 4 new regression tests. |
| 2026-07-15 | Expanded agent-setup auditing to cover the full Claude scaffold contract, not just runtime files: project-owned `agents/`, `rules/`, `hooks/`, `commands/`, `skills/`, plus `docs/reference/ai-collaboration.md`, are now part of the expected consumer setup whenever Claude bootstrap files exist. |
| 2026-07-14 | Added `_detect_long_stacked_comment_block` — flags 5+ consecutive `//` lines with no `docs/reference/` pointer, mechanically enforcing `kmp-code-quality`'s "grows past ~4 lines, split to docs/reference/" rule, which was documented but never checked anywhere. Real gap surfaced by a user report of still seeing long stacked `//` blocks after the skill shipped — traced to the rule existing only in prose, no Detekt config, no audit detector. Excludes a leading license/copyright header (checked all-blank-before-block, not just line 0) to avoid a real false-positive on a common Kotlin file convention. 4 new regression tests. |
| 2026-07-14 | Added `_detect_project_skill_standards` — checks every project-owned `skills/<name>/` folder against the real skill anatomy (verified against `anthropic-skills:skill-creator`'s own documented convention, not assumed): SKILL.md must exist, must open with `---`-delimited YAML frontmatter containing `name` and `description`, and the body should stay under ~500 lines unless a `references/` subdirectory exists for progressive disclosure. Cross-referenced from `kmp-expert`'s "Project-Specific Commands/Agents/Skills — Source of Truth" section. Scoped to a consumer project's own top-level `skills/`, never this repo's own — confirmed the reusable `kmp-audit.yml` GitHub Actions workflow this feeds is `workflow_call`-only, invoked by consumer projects auditing their own root, never by this repo against itself. 8 new regression tests. |
| 2026-07-11 | Added `_detect_module_layer_violation` — parses every module's `build.gradle.kts` for `projects.*` references and flags a wrong-direction dependency (e.g. `:ui` directly on `:data`, skipping `:presenter`) or a cross-feature module dependency, checked against `kmp-clean-architecture`'s 6-layer contract. Closes a real gap: a literal cycle can't happen silently (Gradle refuses to build one), but a one-way wrong-direction dependency can exist at the Gradle level before any file imports the forbidden package — earlier than the existing file-level Detekt import rules can react. 5 new regression tests (3 violation types, a valid full graph, a core-module dependency correctly ignored). |
| 2026-07-11 | Added `_detect_extensible_abstract_class_in_common` — flags a public `abstract class` in `commonMain` with only abstract members (Detekt's real `UnnecessaryAbstractClass` shape, scoped here specifically to `commonMain` since that's where the anti-pattern costs KMP's sharing advantage). Backstop for projects without Detekt's rule configured yet. Cross-referenced to `kmp-clean-architecture`'s new "Composition Over Inheritance" section, which explains the full rationale. 4 new regression tests, including a scope-boundary test confirming the same shape in `androidMain` is correctly ignored. |
| 2026-07-11 | Fixed a real false-positive bug found in a consumer project: `_EXCLUDED_DIRS` had no entry for deployed agent skills bundle directories (`.claude/`, `.codex/`, `.cursor/`, `.continue/`, `.github/copilot/`), so `audit_project.py` scanned this collection's own reference templates as if they were the consumer's real source — flagging `kmp-feature-scaffold`'s own `templates/androidApp/build.gradle.kts` placeholder `versionCode = 1` as a real app's hardcoded version code. Added `.claude`, `.codex`, `.cursor`, `.continue`, `copilot` to `_EXCLUDED_DIRS`. A full self-audit stress test (running `audit_project.py` against this repo, and systematically checking every detector for a missing exclusion check) surfaced two more gaps in the same family: `_detect_mvi_placement` and `_detect_design_system_wiring` used raw `rglob` with no exclusion at all, and the shared `_read_all`/`_has`/`_count_files` helpers (used by `_detect_state_mgmt`, `_detect_di`, `_detect_detekt`, `_detect_version_catalog`, `_detect_tests`, `_detect_positive_patterns`) had the same gap — fixed once at the shared-helper level. Also found a much more severe, unrelated pre-existing bug while fixing this: `_has()` tested `any(root.rglob(g) for g in globs)`, where each item `any()` saw was a whole generator object from the nested generator expression — generator objects are always truthy regardless of whether they yield anything, so `_has()` returned `True` for every project unconditionally, silently disabling `_detect_detekt`'s HIGH-priority "no Detekt gates" adoption-plan trigger (and the version-catalog/tests detectors) for every project ever audited. No prior test caught it because none exercised the genuinely-missing case. Fixed by iterating actual matched paths instead of testing the generator's own truthiness. 13 new regression tests, verified against synthetic reproductions of both bug classes before fixing. |
| 2026-07-10 | Added `_detect_what_comment_in_control_flow` — a regex heuristic flagging `//` comments that narrate WHAT a loop/conditional does (action-verb opener, no WHY-marker) instead of WHY, per `kmp-code-quality`'s "By architectural level" rule. LOW severity (heuristic, human review). New `/kmp-clean-comments` command applies the fix across all four documentation levels (class/function/extension/inline), not just this detector's inline-block slice. |
| 2026-06-29 | Added section 8 (Agent & Consumer Setup) to audit checklist. Added three new detectors to `audit_project.py`: `_detect_agent_setup` (missing AGENTS.md, commands, skills, CLAUDE.md, single-surface AGENTS.md in multi-surface project), `_detect_mvi_placement` (MviViewModel in feature module instead of shared/core), `_detect_design_system_wiring` (MaterialTheme wrapping, hardcoded darkTheme=false, parallel ULong token files). |
| 2026-06-24 | Added a skills-version pin guard to governance: `.kmp-skills` must exist and must point at a release tag, not `main` or another mutable ref. |
| 2026-06-23 | Added "Governance & CI Enforcement" section: governance_check.py, reusable workflow, .kmp-skills version file, threshold guide. |
| 2026-06-22 | Added "Native / JNI boundary" inspection section (#6): 3rd-party C++ immutability, opaque-handle cleanup, acquire/release pairing, C-shim wrapping — closes the cross-skill enforcement gap for the immutability rule. Hands off to kmp-jni-pro. |
| 2026-06-21 | GitHub issue title format defined: `[category] short description`. Category table added with 8 categories (`[arch]`, `[mvi]`, `[presenter]`, `[data]`, `[ui]`, `[di]`, `[build]`, `[test]`). |
| 2026-06-18 | Initial release — architecture audit checklist, `audit_project.py`, `audit_skills_repo.py`, `draft_issue.py`. |
