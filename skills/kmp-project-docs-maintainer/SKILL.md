---
name: kmp-project-docs-maintainer
description: >
  Maintains downstream consumer-facing KMP project documentation only: README,
  GETTING_STARTED, INSTALL, RELEASING, docs/reference pages, onboarding guides,
  architecture notes, and architecture diagrams. Use this skill when project docs need to
  match the actual code, commands, config, folder layout, or app/library structure.
  Does NOT cover consumer release-note generation, per-skill changelogs, or
  skills-repo documentation.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-11'
  references:
    - references/docs-hygiene.md
  keywords:
    - project docs
    - consumer docs
    - README
    - getting started
    - install guide
    - releasing guide
    - docs reference
    - onboarding docs
    - architecture docs
    - architecture diagram
    - docs drift
    - documentation maintainer
    - project documentation
    - repo docs
    - docs sync
    - libraries catalog
    - testing coverage doc
    - docs/libraries.md
    - docs/testing.md
    - docs/demos.md
    - ADR
    - architecture decision record
    - module README
---

## When to Use This Skill

Use this skill when you need to:
- update a project README so it matches the current code, commands, or modules
- refresh onboarding docs such as GETTING_STARTED, INSTALL, or RELEASING
- keep `docs/` and `docs/reference*` content aligned with the project structure
- fix stale links, command names, screenshots, diagrams, or architecture notes
- reconcile docs after a code change, refactor, or release

Do NOT use this skill when:
- you are writing consumer release notes or per-skill changelog tables
- you are maintaining the skills repo's own README, agents, commands, or skill docs
- you are implementing product code instead of updating documentation

If the target is this repository, route to `docs-maintainer` instead.

**Trigger keywords:** project docs, consumer docs, README, getting started, install,
releasing, docs reference, onboarding docs, architecture docs, architecture diagram,
docs drift, documentation maintainer, project documentation, repo docs, library docs,
app docs, clean docs, clean up docs, tidy docs, docs cleanup, update docs, fix docs,
refresh docs, docs out of date, stale docs, docs are wrong, developer friendly docs,
concise docs, clear docs, docs writing style, organize docs, ADR, architecture
decision record, decision log, module README, per-module docs, thinner docs,
scaffold docs.

**Freshness rule:** project docs drift whenever code, commands, config, or folder names
change — re-read the live project README, the touched docs, and the relevant source files
before editing. Re-check docs that mention version numbers, command names, or module
paths after each code change.

---

## Recommendation First

Default to this sequence:
1. Read the live docs and the source files they describe.
2. Update the smallest docs surface that is now stale.
3. Keep terminology, command names, module names, and links consistent across all touched files.
4. Re-run any repo-specific validation or link checks before handing the docs back.

Why:
- project docs are only useful when they match the code people actually run
- stale onboarding or README guidance causes more confusion than missing guidance
- keeping one canonical phrasing across README, onboarding, and reference docs avoids drift

### Architecture Diagram Rule

If the downstream project is an app or a library, include a simple architecture diagram
in the README or `docs/architecture.md` that shows the major modules, layers, or
runtime flow.

Use the diagram to answer "what is the shape of this project?" at a glance: apps show
entry points/feature modules/shared layers; libraries show public API surface, internal
modules, and integration points. Keep it short enough for the README, expand details in
`docs/architecture.md` when needed. Update it whenever a module or release flow changes.

### Writing Style — Clear, Concise, Organized, Developer-Friendly

Docs are for someone about to run a command or make a decision, not someone reading
end to end. Every edit should make the doc easier to act on, not just more complete.

- **Lead with the answer, not the setup.** State the command, decision, or fact first;
  explain why after, only if non-obvious.
- **One idea per section, each short enough to scan.** Needs its own table of contents?
  It's really several sections — split it.
- **Concrete over abstract.** "Run `./gradlew check` before pushing" beats "ensure
  quality gates pass."
- **Cut hedging and filler on sight** — "in order to", "it should be noted that".
- **Organize by what the reader is trying to do, not by build order.** Follow "what a
  new developer needs, in the order they need it."
- **Prefer a table over a paragraph when comparing options** (see Fix Maturity Lanes,
  Project Doc Change Checklist below) — scanning a row beats prose.
- **Every code example must be real and runnable, not pseudocode** — copy-pasting it
  should work, or it isn't worth including.
- **Mermaid only where prose/a table can't show the shape** — module dependency
  graphs, sequence/flow diagrams. `kmp-audit`'s `generate_structure_diagram.py --mermaid`
  already generates the module-graph case — don't hand-draw one. **Code snippets** go
  wherever a real API/interface is described (Reference, Task, Module README). **ADRs
  need neither** — link out to the Reference doc instead.

**For deeper AI-tell removal**, verified real and actively maintained:
[`conorbronsdon/avoid-ai-writing`](https://github.com/conorbronsdon/avoid-ai-writing) —
a 62-category tiered detector (em dashes, hollow intensifiers, promotional inflation).
`npx skills add conorbronsdon/avoid-ai-writing` for a `docs/`/README prose pass; this
skill's own `_detect_hedging_language` stays scoped to its narrower phrase list.

### Default Docs Topology

If a downstream project does not already have a clear docs layout, use this structure as
the default. Keep the top-level docs visible, then branch active work into purpose-built
folders:

```text
docs/
├── tasks.md
├── roadmap.md
├── architecture.md
├── deployment.md
├── libraries.md
├── testing.md
├── reference/
├── mvp/
│   └── 0-mvp/
│       ├── 0-mvp.md
│       └── 0-phase/
│           ├── 0-phase.md
│           └── tasks/
│               ├── 0-task.md
│               └── 1-task.md
└── bugs/
    └── 0-bug.md
```

Use it like this:
- `docs/tasks.md` — single source of truth for current work, active decisions, and links
  into active plan or bug lanes
- `docs/roadmap.md` — consolidated planning, including integration and project planning
- `docs/architecture.md` — system design, kept as the stable long-form architecture doc
- `docs/deployment.md` — consolidated deployment and publishing flow
- `docs/libraries.md` — catalog of every library this project publishes: name, Maven
  coordinate, current version, publish status (stable/SNAPSHOT), link to its README.
  Cross-referenced from `kmp-library-publishing`'s release checklist so
  a release has somewhere durable to point to, instead of nowhere
- `docs/testing.md` — overview/index of test coverage: which modules have unit tests vs.
  Roborazzi screenshot coverage, where goldens live, how to run the full suite locally.
  Doesn't duplicate `kmp-unit-testing`/`kmp-roborazzi`'s
  content — answers "what's actually covered" at a glance, the same relationship
  `deployment.md` already has to the CI/release skills
- `docs/reference/` — searchable technical audits, model setup notes, and deep references
- `docs/mvp/` — structured MVP planning records, phase notes, and task breakdowns
- `docs/bugs/` — active bug threads; start with one file (`0-bug.md`) and add a folder only
  if the bug lane needs multiple files
- `docs/demos.md` — **conditional, not default.** Only add this if the project has a
  runnable demo/sample/catalog app module. A project with no demo module should not have
  this file at all — don't scaffold a demos page (or a demo module) just to have one

Use the active lanes like this:
- `docs/mvp/0-mvp/0-mvp.md` — the current MVP summary
- `docs/mvp/0-mvp/0-phase/0-phase.md` — the current phase plan
- `docs/mvp/0-mvp/0-phase/tasks/0-task.md` and `1-task.md` — individual task notes
- `docs/bugs/0-bug.md` — the active bug note for a single tracked issue

If the project needs chronological task history as well, keep `docs/tasks/` as the
archive lane for dated phase notes and pointers, but do not force every active doc there.

### Reference Doc Starter Templates

Root `README.md`, `docs/architecture.md`, and `docs/reference/<topic>.md` starter
templates — full content in `references/docs-hygiene.md`'s "Reference Doc Starter
Templates" section.

### Fix Maturity Lanes

Use one of these lanes for every fix note in `docs/tasks/`:

| Lane | Meaning | Where it lives |
|---|---|---|
| Dev | Investigating, changing fast, or not yet validated | `docs/tasks/` |
| Beta | Tested enough to share, but still under observation | `docs/tasks/` with a `beta` marker |
| Stable | Accepted and durable enough for the wider project | `docs/architecture.md`, `docs/deployment.md`, or `docs/reference/` |

Lifecycle rules:
- keep dev fixes in the dated task notes while they are still moving
- mark beta fixes clearly in `docs/tasks.md` or the dated note so they do not get mistaken for final guidance
- once a fix becomes stable, promote the final guidance into durable docs and leave the task note as history
- if a stable fix later regresses, open a new dated task note instead of rewriting history

Rules:
- make `docs/tasks.md` the primary entrypoint for day-to-day updates
- treat the layout as agile-friendly: backlog/current work lives in `docs/tasks.md`, execution
  history lives in dated task notes, and stable decisions graduate into architecture/docs
- put detailed phase history, approvals, and dated execution notes in `docs/tasks/`
- use `docs/mvp/` for the numbered MVP/phase/task tree when the project wants a visible
  planning hierarchy instead of flat task notes
- use `docs/bugs/0-bug.md` for a single active bug thread; only create `docs/bugs/0-bug/`
  when that bug needs multiple related files
- when a task is complete, rename its status suffix to `-done` and move it into
  `docs/tasks/<parent>/archive/`, keeping a short index line or backlink in `docs/tasks.md`
- use the `<NN>-<slug>-<status>.md` convention (see `docs-hygiene.md`'s Naming Convention
  section) — status lives in the filename, the date lives inside the file content
- if a note is still needed for current work, keep it in `docs/tasks/<parent>/`; if it is
  done but still relevant to search, move it to `docs/tasks/<parent>/archive/`
- if a note contains durable design or operating guidance, promote that guidance into
  `docs/architecture.md`, `docs/deployment.md`, or `docs/reference/` instead of leaving
  it only in task logs
- consolidate overlapping planning or deployment docs instead of duplicating them
- keep `docs/reference/` out of the main flow; it supports the core docs, it does not replace them
- link from README or onboarding docs to `docs/tasks.md` if the project has a lot of moving parts
- if older task files exist at the root, consolidate them into `docs/tasks/` and leave a pointer
  from `docs/tasks.md` instead of keeping parallel task indexes

### Project Doc Change Checklist

| Change | Update |
|---|---|
| New module, command, or phase | README, onboarding docs, `docs/tasks.md`, and any `docs/reference*` page that mentions it |
| Renamed command or path | Every docs mention, code sample, and navigation link |
| Architecture shift | README plus the affected reference pages, diagrams, and architecture notes |
| Release or setup change | RELEASING, INSTALL, and any onboarding checklist that relies on it |

## Project Doc Workflow

### 1) Read the current sources

Always inspect the live files first:
- the docs files you expect to change
- the code or config that those docs describe
- any linked reference docs that those files depend on

### 2) Edit the docs

Keep the docs narrow and accurate:
- prefer one canonical description over repeated paraphrases
- update examples to match the current repo shape
- remove references to deleted files, commands, or options
- if the user asks to "write a doc in docs", classify it first:
  - durable project guidance → `docs/architecture.md`, `docs/deployment.md`, or `docs/reference/`
  - current planning / MVP work → `docs/tasks.md` or `docs/mvp/0-mvp/0-phase/`
  - active bug tracking → `docs/bugs/0-bug.md` (or a `docs/bugs/0-bug/` folder only if the bug lane needs multiple files)
  - if the path is ambiguous, choose the narrowest durable home and explain the placement

### 2a) Use the default task template

When creating a new downstream project, start `docs/tasks.md` with this structure:

```markdown
# Tasks

## Current Objective

## Active Phase

## Open Questions

## Fix Lanes

- Dev:
- Beta:
- Stable:

## Task Log

| Task | Status | Parent |
|---|---|---|
| [01-plan](tasks/my-feature/01-plan-doing.md) | doing | my-feature |
| [02-build](tasks/my-feature/02-build-todo.md) | todo | my-feature |

## Archive Index

- [my-feature](tasks/my-feature/archive/)
```

A table, not a bullet list — the whole point is reading every active task's status in
one place without opening each file. Every active (non-archive) task file under
`docs/tasks/<parent>/` needs a row here; `kmp-audit`'s `--docs-hygiene-only` flags a
task file with no matching row (see `docs-hygiene.md`'s Hygiene Limits). Update the
row's **Status** column and the link's target filename together — the filename is the
source of truth for status (per the naming convention), this table is just a rolled-up
index of it, not a second place to track status independently.

### 2b) Use `<NN>-<slug>-<status>.md` task filenames

Full convention (parent folder, numbering, status vocabulary, date-in-content) lives in
`docs-hygiene.md`'s Naming Convention section — don't re-derive it here. Short version:
short, action-first slugs (`plan`, `build`, `change-request`, `approval`, `retro`) under
one parent folder per feature/project, e.g. `tasks/my-feature/01-plan-doing.md`.

Keep the slug focused on the phase or decision, not the whole feature name — the parent
folder already carries that.

### 2c) Promote or archive

When a task is finished:
- rename its status suffix to `-done` and move it to `docs/tasks/<parent>/archive/`
- promote stable guidance into `architecture.md`, `deployment.md`, or `reference/`
- leave a backlink in `docs/tasks.md` so the current work page still points to the history
- keep `doing`/`blocked` tasks in the active task trail until they either stabilize or are discarded

### 3) Validate

Use the project's own checks when the docs mention build steps, commands, or generated
output. For pure text edits, verify links and filenames by inspection.

If the docs live in this skills repo, also run:

```bash
python3 scripts/scan_skill_issues.py
python3 skills/kmp-audit/scripts/audit_skills_repo.py .
```

## Testing

Use this validation matrix for project docs:

| Case | Expected |
|---|---|
| README mentions a module or command | The referenced file or command exists |
| `docs/tasks/` updates | `docs/tasks.md` links to the dated record and the dated record has a date-stamped filename |
| `docs/tasks/archive/` updates | Completed notes retain date-stamped filenames and `docs/tasks.md` still points to them |
| Task history becomes dense | The oldest active notes move to `docs/tasks/archive/` and durable guidance moves to architecture/reference docs |
| Dev/Beta/Stable fix lanes | Lane markers stay visible until a fix is promoted into durable docs |
| `docs/reference*` updates | Links resolve and match the code or configuration it documents |
| Onboarding docs change | The setup steps match the current project workflow |
| Release/setup docs change | Version numbers, paths, and commands reflect the current repo |
| Benchmark or performance comparison tables | Write the canonical table in `docs/reference/benchmark-matrix.md` (or the nearest durable `docs/reference/` page), and keep task-note summaries short with a link back |
| `docs/libraries.md` updates | Every listed Maven coordinate/version matches what's actually published (cross-check `gradle.properties`/`libs.versions.toml`, not just what the page claims) |
| `docs/testing.md` updates | Every module claimed to have coverage actually has test files under it — don't list a module as covered because it should be |
| `docs/demos.md` present | A real demo/sample/catalog module exists at the path the page references — this file should not exist at all if there's no demo module |

## Doc Classification and Hygiene

Read `references/docs-hygiene.md` before any clean-up task. It covers:
- Classification (Reference / Task / Non-doc, plus the Decision/ADR lane) with examples
- `docs/` root vs `docs/reference/` placement rule
- Reference Doc Starter Templates: root README.md, architecture.md, reference/<topic>.md
- Decision lane (ADR): one-decision-per-file, immutable once Accepted, starter template
- Clean-up sequence (classify → check references → update links → move → consolidate → validate)
- Consolidation rule for task files scattered at the `docs/` root
- Naming convention (kebab-case; snake_case is flagged by the audit script)
- Hygiene limits table (line limits, lesson backlog, stale lessons, non-doc files, ADR shape)
- Lesson lifecycle and hygiene check commands

---

## Per-Module README.md

A different concern from everything above — this lives *inside* a module
directory (`:feature:auth/README.md`, `:core:network/README.md`), not under
`docs/` at all, and no other skill currently owns it.

**Not every module needs one.** A thin leaf module (`:model`, `:api`) with a
handful of self-explanatory files doesn't need a README duplicating what the
code already says — that's the same "will a reader gain something a file
listing wouldn't already tell them" test as everything else in this skill.
Add one when a module has:
- non-obvious setup or wiring steps a newcomer wouldn't guess from the files alone
- a public API surface other modules actually depend on
- a role that isn't obvious from its name and the 6-layer contract alone

**Starter template** — `:module-path/README.md`:

```markdown
# :feature:auth:presenter

What this module owns — one or two sentences, not a re-explanation of the
6-layer contract (`kmp-clean-architecture` already covers that).

## Public API

The types/functions other modules actually consume from here. Skip internals
— if it's not `internal` or `public` on purpose for cross-module use, it
doesn't belong in this list.

## Depends on

`:feature:auth:domain`, `:core:mvi` — only the direct deps a reader would
need to know before touching this module, not the full transitive graph.

## Gotchas

Anything a newcomer would get wrong without being told. Skip this section
entirely if there isn't a real one — an empty "nothing to note here" section
is worse than no section.
```

Keep it short — a module README ballooning past a page is the same drift
this skill's `docs/` line caps exist to prevent, just uncapped because it
lives outside `docs/` and the mechanical check doesn't reach it yet (see
`kmp-clean-architecture`/`kmp-feature-scaffold` for the module-boundary rules
this README should stay consistent with, not restate).

---

## Common Anti-Patterns

- Leaving a stale command name in README or onboarding docs after a rename.
- Updating one doc page and forgetting the linked reference page that explains it.
- Copying code snippets that no longer compile or run.
- Burying the command/decision a reader needs three paragraphs deep instead of leading with it — see Writing Style above.
- Writing a paragraph to compare options a table would show at a glance.
- Mixing consumer release-note content into general project docs.
- Scaffolding `docs/demos.md` (or a demo module) when the project has no runnable demo app — this page is conditional, not part of the default topology.
- Reusing this skill's internal `docs/` folder as the source for a public GitHub Pages developer guide — see `kmp-docs-site`, which uses a separate `website/` folder specifically to avoid leaking task notes/roadmap to a public site.

## Related Skills

- `kmp-audit` — catches doc drift when the docs repo or consumer project needs a health check; `_detect_hedging_language` is the mechanical enforcement for the Writing Style rule's hedge-phrase check above (the other 6 rules stay judgment calls — not mechanically detectable without real false-positive risk).
- `kmp-release` — use when project docs need to explain versioning or publishing flow.
- `kmp-legal-docs` — use when the docs are specifically about privacy, terms, or compliance.
- `kmp-library-publishing` — owns the Maven Central pipeline `docs/libraries.md` catalogs; its release checklist should point here.
- `kmp-unit-testing` / `kmp-roborazzi` — own the actual test coverage `docs/testing.md` indexes; this page doesn't duplicate their content.
- `kmp-docs-site` — the public, GitHub-Pages-deployed developer guide for a published library; a separate concern from this skill's internal `docs/` — never share the same source folder.
- `kmp-clean-architecture` — owns the 6-layer module contract a per-module README should stay consistent with, not restate.

## Output Style

When asked to update project docs, respond in this order:
1. files changed
2. source-of-truth files consulted
3. validations run
4. follow-up docs that should be updated next

Keep the response focused on the project's docs surface and the source files it mirrors.

## KDoc vs Ground-Truth Docs Boundary, Code Examples & Linking Policy

Never duplicate architectural explanations across source code and markdown documentation.
Full tables (KDoc/Ground-Truth/Decisions boundary + anti-patterns; Code Examples/Internal
Links/Issue Links/External Spec Links policy) live in `references/docs-hygiene.md`.

---

## Developer-Friendly Vibe-to-Plan Template (Real-World Analogies)

When drafting task plans from conversational instructions, use the **Vibe Plan Template** located in `references/vibe-plan-template.md`.

Every task plan must provide:
1. **Real-World Analogy**: a scenario (e.g. *The Chef & Waiter* for Domain vs Presenter) readers grasp instantly.
2. **Before vs After Snippets**: what callers did before vs the clean, idiomatic API after.
3. **4-Stage Progression**: `:model` → `:domain` → `:presenter` → `:ui`.
4. **Verification Commands**: explicit Gradle / Roborazzi test commands.

---

## Consumer README Standards (Root, Docs, and Module)

Consumer projects follow a clean 3-tier README hierarchy documented in `references/readme-templates.md`:
1. **Root `README.md`**: Project entrance, quickstart commands, high-level architecture links, license.
2. **`docs/README.md`**: High-density self-healed sitemap generated by `heal_docs.py`.
3. **Per-Module `README.md`**: Colocated inside public/core modules documenting exports and platform targets.

---

## Changelog

| Date | Change |
|---|---|
| 2026-09-11 | Updated docs hygiene rules: documented recursive non-doc file checks, asset/image isolation to `docs/assets/` or `docs/images/`, canonical top-level `docs/` subdirectories enforcement, and archive historical task exemption. |
| 2026-08-29 | Trimmed `SKILL.md` under 500 lines per agentskills.io progressive disclosure. Moved KDoc vs Ground-Truth Docs Boundary and Code Examples & Linking Policy tables into `references/docs-hygiene.md`. Tightened Writing Style bullets and Vibe-to-Plan Template steps. |
| 2026-08-26 | Cross-referenced `conorbronsdon/avoid-ai-writing` in the Writing Style section — user asked whether the tool was useful to us. Verified real via `gh api` before recommending it: 3264 stars, actively maintained, a 62-category/112-word tiered AI-tell detector with a real test suite and honest cited false-positive caveats (Stanford *Patterns* 2023, BFI Working Paper 2025). Cited rather than reimplemented — its scope is far deeper than this skill's own `_detect_hedging_language`, which stays scoped to its existing narrow KDoc/code-comment phrase list rather than duplicating a 112-word catalog. |
| 2026-08-23 | Added an 8th Writing Style rule: when to use Mermaid vs a code snippet vs neither, per doc kind — user asked directly which doc kinds should use which. Mermaid only for module graphs/sequence flows a table or list genuinely can't show (points at `kmp-audit`'s existing `generate_structure_diagram.py --mermaid` for the module-graph case rather than re-deriving one by hand); code snippets wherever a real API/interface is being described (Reference, Task, Module README); ADRs need neither — link out to the Reference doc instead of duplicating a diagram/snippet inside the decision record. |
| 2026-08-23 | Added Reference Doc Starter Templates (root `README.md`, `docs/architecture.md`, `docs/reference/<topic>.md`) — user asked to see a template for every doc kind; Task, ADR, and Module README already had one, these three primary Reference docs didn't. Lives in `references/docs-hygiene.md`, moved there after adding it directly to `SKILL.md` pushed it to 548 lines. |
| 2026-08-23 | Added the Decision lane (ADR) and Per-Module README.md. User asked us to research why a real consumer project's `docs/` had grown to 141 files / 29,650 lines — `kmp-audit --docs-hygiene-only` found 118 real violations there, including a 1,578-line `decision-log.md` and a 714-line findings file, both trying to be Architecture Decision Records built as one growing log instead of one-file-per-decision. Verified the real, widely-adopted ADR pattern (Michael Nygard, 2011; ThoughtWorks Radar ADOPT) before writing: one decision per file, ~1 page, immutable once `Accepted`, superseded by a new numbered file rather than edited. Added `docs/decisions/NNNN-slug.md` with a starter template, plus two mechanical checks in `kmp-audit` (filename shape, `**Status:**` line presence). Separately, user asked whether per-module `README.md` was a different concern — confirmed yes (code-colocated, not under `docs/`, zero prior coverage anywhere) and added a Per-Module README.md section with its own starter template, explicitly out of `docs/`'s line-cap enforcement since it lives outside that tree. |
| 2026-08-23 | Upgraded `docs/tasks.md`'s Task Log template from a bullet list to an explicit `\| Task \| Status \| Parent \|` table — user wanted to read every task's status without opening each file one by one. `kmp-audit`'s `_check_docs_hygiene` now flags an active task file with no matching row in `docs/tasks.md`, so the table can't silently drift from what's actually on disk. |
| 2026-08-22 | Task filename convention changed at the user's request: `docs/tasks/YYYY-MM-DD-slug.md` → `docs/tasks/<parent>/<NN>-<slug>-<status>.md` (status one of `todo`/`doing`/`blocked`/`done`, resets numbering per parent folder). Status now lives in the filename instead of a `status:` field in content — the whole point is reading status without opening the file. The date moved the other direction: out of the filename, into a `**Date:** YYYY-MM-DD` line in the content. Rewrote `docs-hygiene.md`'s Naming Convention, Consolidation Rule, and Delete vs Archive sections; updated `kmp-audit`'s `_check_docs_hygiene` to validate the new shape and flag a missing Date line instead of grepping for `status: done`. Migrated this repo's own 3 archived task docs (`docs/tasks/archive/*.md`) into the new convention under a `skills-repo` parent. |
| 2026-08-21 | Added an "orphaned reference doc" row to the Hygiene Limits table — a user asked for the audit to flag stale/rename/delete candidates directly instead of leaving it to a human grep. Backed by `kmp-audit`'s new `_check_orphaned_reference_docs`: a `docs/`-root or `docs/reference/*.md` file with zero inbound links anywhere in the repo gets flagged for review, not auto-deleted — automates the grep this doc's own Delete vs Archive section already told a human to do by hand. |
| 2026-08-18 | Clarified `references/docs-hygiene.md`'s "Running the hygiene check" — a filed issue (kmp-agent-skills#6) claimed the documented command only resolves inside this skills repo; verified live against a real consumer project and disproved that (works standalone). The genuine confusion was the script's name — `audit_skills_repo.py` sounds skills-repo-only despite its `--docs-hygiene-only` path being generic. Added a one-line note plus an explicit "don't use `audit_project.py` here" pointer, since that's the script that actually has no hygiene checks. See `kmp-audit`'s changelog for the real bug the same investigation turned up (SCREAMING_CASE filenames weren't being caught). |
| 2026-08-17 | Cross-referenced `kmp-audit`'s new `_detect_hedging_language` — the Writing Style rule's hedge-phrase check now has real mechanical backing, not just prose guidance a reader has to self-police. |
| 2026-08-15 | Added "Writing Style — Clear, Concise, Organized, Developer-Friendly": real gap — this skill governed doc *structure* (topology, hygiene, classification) but had nothing about doc *prose quality*. 7 concrete rules (lead with the answer, one idea per section, concrete over abstract, cut hedging, organize by reader intent not build order, table over paragraph for comparisons, every example must be real and runnable). 2 new anti-patterns. |
| 2026-08-04 | Added a "Delete vs Archive" section to `references/docs-hygiene.md` — real gap: the only prior guidance was a blanket "Never delete — archive," but that only made sense for the Consolidation Rule's task-kind files. Git history already preserves every version regardless of delete/archive, so the actual test is whether a human should be able to browse the old content again without going to git log — archive covers that case (task/bug resolution history); a fully-superseded reference doc, a `docs/` copy of a file already moved to its real home, or a leftover pre-rename file has nothing left to browse to and should just be deleted. Also registered `MIRROR_MAP.md` (from `kmp-api-mimicry`) as a named classification example. |
| 2026-07-11 | Added `docs/libraries.md` (Maven coordinate/version/publish-status catalog, cross-referenced from `library-publishing`) and `docs/testing.md` (test coverage index, cross-referenced from `unit-testing`/`roborazzi`) to the default topology — closing a real gap where "libraries" only had architecture-diagram guidance and "tests"/"demos" had nothing. `docs/demos.md` added as explicitly **conditional**, not default — only when a real demo module exists. Cross-referenced the new `kmp-docs-site` skill (public GitHub Pages developer guide) and drew an explicit boundary: never share this skill's internal `docs/` folder as that site's source. 2 new anti-patterns, 3 new validation-matrix rows. |
| 2026-06-27 | Extracted classification + hygiene into `references/docs-hygiene.md`. Added cleanup-intent trigger keywords. |
| 2026-06-24 | Initial release — consumer-facing project docs workflow, default topology (`docs/tasks.md`, `roadmap.md`, `architecture.md`, `deployment.md`, `reference/`), fix maturity lanes, task lifecycle and archive policy, and architecture diagrams. |
