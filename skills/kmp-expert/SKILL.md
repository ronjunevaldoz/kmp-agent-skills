---
name: kmp-expert
description: >
  Route Kotlin Multiplatform project or feature work to the smallest relevant skills and
  sequence them. Use for skill selection, build-order decisions, or adoption-roadmap routing;
  use the audit skill for project findings.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-27'
  keywords:
    - KMP expert
    - orchestrator
    - skill sequencing
    - dependency graph
    - project setup order
    - KMP architecture
    - Kotlin Multiplatform expert
    - what skill should I use
    - skill map
    - meta-skill
    - feature assembly
    - KMP decision tree
    - audit
    - project review
    - architecture review
    - issue draft
    - question draft
    - kmp-agent-skills
    - kmp-skills
    - KMP agent skills
    - skill collection
    - skills index
---

# KMP Skill Router

This skill's public ID remains `kmp-expert` for compatibility. Agents are named by role;
skills are named by reusable capability. Keep skill folder/frontmatter IDs stable and improve
their short descriptions or display labels instead of renaming installed skills.

## When to Use This Skill

Use this skill when you need to:
- Start a new KMP project and don't know which skills to invoke or in what order
- Start a new KMP project from the Kotlin/kmp-wizard baseline and don't know which
  skills to invoke or in what order
- Add a new full feature to an existing KMP project (network + DB + UI + navigation)
- Decide which skill answers a specific question ("where do I put this?", "which pattern fits?")
- Route an existing KMP project into the audit skill before making changes
- Convert confirmed audit findings into GitHub issue drafts or question drafts before
  fixing if the user wants repo tracking
- Get a high-level roadmap before diving into implementation

**Do NOT use this skill, or route to any skill in this collection, when the request
names a different stack** (React, Swift/SwiftUI native-only, Flutter, plain Android
Views, a backend framework unrelated to Ktor/kRPC, etc.) or no stack at all with no
Kotlin/KMP signal anywhere in the request. This collection is Kotlin Multiplatform +
Compose Multiplatform + Koin + Ktor specific — nothing here applies to "build a React
tic-tac-toe app" or similarly unrelated requests, even if the task shape sounds generic
(a UI component, a state machine, a build pipeline). If the stack is genuinely
ambiguous, ask which stack before assuming KMP.

**Branch recommendation:** use `Kotlin/kmp-wizard` `all-targets` by default for new
full-stack KMP projects. Use `all-frontends-shared` only if you want to omit the server.

**Build-logic rule:** route plugin and dependency versions through `build-logic/`
convention plugins and `gradle/libs.versions.toml`; do not scatter version strings
across module build files when creating or updating KMP projects.

**Trigger keywords:** where do I start KMP, full KMP setup, new KMP feature, which skill,
skill order, KMP architecture decision, KMP expert, KMP project plan, which pattern KMP,
KMP checklist, review my KMP project, custom agent for project, custom command for project,
project-specific agent, project-specific command, project-specific skill.

**Freshness rule:** recheck the Skill Invocation Map and dependency graph entries whenever
a new skill is added or removed — the routing table and skill count must stay in sync with
the actual `skills/` directories. Run `python3 skills/kmp-expert/scripts/validate_skill_map.py --repo-root .`
after any skill addition.

---

## Recommendation First

Default to **reading the current skill list and dependency graph before recommending anything**.

Why:
- the skill collection grows; a recommendation based on a stale skill list misroutes work
- the dependency graph in this skill defines the correct build order — skipping foundation skills
  causes downstream failures
- routing to the wrong skill wastes a context window on the wrong patterns

Use this skill as an entry point for open-ended KMP questions. Then hand off to the specific skill.
Do not implement — route and explain.

## Priority Ladder

When more than one skill could apply, rank them instead of enabling everything.

1. Contract and scaffold skills first: `clean-architecture`, `feature-scaffold`, `presenter-module`
2. Foundation and project plumbing next: `dependency-injection`, `flavor-environment`, `ci-github-actions`, `logging`
3. Core infrastructure after the foundation is clear: `network-layer`, `sqldelight-setup`, `datastore`, `logging`, `kotlin-rpc`, `ktor-auth-service`, `mongodb-database`, `xcframework-spm`
4. Feature building blocks after the data and platform shape is known: `navigation`, `mvi`, `repository-pattern`, `shared-resources`, `paging`, `analytics`, `form-validation`, `image-loading`, `permissions`, `deep-linking`, `biometric-auth`, `push-notifications`, `workmanager`, `feature-flags`, `crash-reporting`
5. UI, testing, quality, docs, and release last: `design-system`, `design-system-extended`, `adaptive-layout`, `compose-*`, `preview-driven-development`, `unit-testing`, `roborazzi`, `code-quality`, `accessibility`, `project-docs-maintainer`, `audit`, `release`

Load the earliest tier that answers the request, then add lower tiers only when the task genuinely needs them.

## Model Routing

Route subagents by work type, not by habit.

Use the strongest available reasoning model for:
- ambiguous planning
- complex architecture decisions
- performance investigations
- benchmark-topping work
- root-cause analysis on hard failures
- final review of claims, numbers, and tradeoffs

Use a cheaper or faster model for:
- mechanical implementation after the plan is clear
- repetitive file generation
- straightforward wiring
- bulk edits with no design decision

Use a precision-focused strong model for:
- validation
- review
- anything where an incorrect conclusion would be expensive to unwind

If a task is both complex and high-impact, escalate the planning and review stages first;
keep the implementation stage on the smallest model that can still follow the plan cleanly.

---

## Required vs Optional Skills

Full content: `references/required-vs-optional-skills.md`.

## Routing Precedence

When a request could fit more than one surface, use this order:

1. Repo README, `docs/`, agent docs, command docs, or routing text -> `docs-maintainer`
2. Downstream project README, onboarding docs, or reference docs -> `project-docs-maintainer`
3. Wireframes, screen flows, layout specs, design handoff, or component API direction -> `designer`
4. Consumer release notes, `CHANGELOG.md`, or per-skill changelog tables -> `changelog`
5. Project release, versioning, or publishing flow -> `release`
6. Navigation structure -> `navigation`; external URL handling -> `deep-linking`

If the request still spans two surfaces after that, route the earlier-layer owner first and name the follow-up skill explicitly.

### Docs Scope Guard

Before routing docs work, classify the target:
- repo-internal docs, agents, commands, or routing text -> `docs-maintainer`
- downstream consumer docs -> `project-docs-maintainer`

If the user has not said which one they mean, resolve the scope before editing.

---

## Freshness Rule

At the start of every session, treat the repo files in front of you as the source of
truth. Re-read the current `README.md` and the relevant `skills/*/SKILL.md` files before
recommending an approach. Do not rely on a previous session's skill list or remembered
versions when the local repo can be checked directly.

---

## The 77 Skills and What They Own

The complete catalog is maintained in [`README.md`](../../README.md); the task-to-skill
routes live in [`references/skill-invocation-map.md`](references/skill-invocation-map.md).
Keep that mapping canonical instead of copying the full skill inventory into agents.

## Dependency Graph

Full content: `references/dependency-graph.md`.

## Build Order for a New Project

Full content: `references/build-order.md`.

## Feature Slice Checklist

Full content: `references/feature-slice-checklist.md`.

## Decision Trees

Full content: `references/decision-trees.md`.

## Common Anti-Patterns

Load [`references/common-anti-patterns.md`](references/common-anti-patterns.md) when planning or
reviewing a feature that touches those patterns.

---

## Skill Invocation Map

Full content: `references/skill-invocation-map.md`.

---

## Quick Health Check for Existing Projects

Full content: `references/quick-health-check.md`.

## Docs-First Rule

Before coding a feature, check the official docs and the project docs:

- verify official Android / Compose guidance first
- prefer standard APIs over custom wrappers unless the docs force a custom path
- record the decision in the project docs before implementation

Use this when the user asks to audit or extend an existing project:

1. Read the project architecture docs
2. Confirm the module boundary
3. Check whether the feature belongs in an existing pattern skill
4. Only then write code or a new skill

**Skill naming rule:** if step 3 reveals no existing skill covers the domain, propose the new
skill by its full name: `kmp-<topic>`. Never suggest a bare topic name
without the `kmp-` prefix. Then route to `/kmp-new-skill kmp-<topic>`.

## Project-Specific Commands/Agents/Skills — Source of Truth

Full content: `references/project-specific-source-of-truth.md`.

## Recommendation Format

When recommending an approach, always present it in this order:

1. Recommend the default first.
2. Show the relevant project structure.
3. Show a small code snippet.
4. Explain why that path is preferred.
5. Mention the main alternative only after the default is clear.

Use this format when the user asks what to build next, which pattern to use, or how a
skill should be applied. Keep the snippet small and directly tied to the structure.

## Naming Rule

Use neutral names by default. Prefix only when the prefix adds clarity at the boundary.

- Shared design-system primitives may use an `App` prefix: `AppButton`, `AppCard`,
  `AppText`, `AppIcon`.
- Feature-local UI should usually stay plain: `UsersScreen`, `UsersList`, `GraphSurface`.
- Layout and state types should be descriptive, not branded: `ViewportState`,
  `LayoutMode`, `Breakpoint`, `SelectionState`.
- Avoid repeating the layer in the name: prefer `Toolbar` over `GraphUiToolbar`,
  `Canvas` over `GraphUiCanvas`, unless a collision actually exists.

If a name feels noisy, remove the prefix first. Add a prefix only when the codebase
already has multiple same-named concepts or the component is part of a shared library.

## Bundled Script

- `scripts/validate_skill_map.py` — checks that the README and expert map still list
  the current skill folders and that the declared skill count matches the repo.

---

## References

Full implementation content lives in `references/*.md`: `dependency-graph`,
`build-order`, `feature-slice-checklist`, `decision-trees`, `quick-health-check`,
`required-vs-optional-skills`, `project-specific-source-of-truth`, `skill-invocation-map`,
`changelog`. Load the specific file named in the pointer under its matching heading
above, not all of them.

Two reference groups back a *command*, not a heading here — orchestration is this skill's:

- `references/agents-md-templates.md` — the `.claude/AGENTS.md` and `CLAUDE.md` bodies
  `/kmp-setup-agents` writes. Here, not in the command, because a command reaches a
  consumer as a single bare `.md` while skills are always deployed.
- `references/new-project-phase-1..5-*.md` — the five phases of `/kmp-new-project`; the
  command is just the index and gates. **Load one phase at a time**, or the split is moot.

The 70 Skills table stays inline above — `validate_skill_map.py` reads it directly. The
Skill Invocation Map moved to `references/skill-invocation-map.md` once it grew past the
line cap; `validate_skill_map.py` and `validate_keyword_routing.py` both follow the
pointer rather than requiring it to stay inline.

---

## Related Skills

- `kmp-audit` — run this after every feature to verify no architecture smells were introduced
- `kmp-project-docs-maintainer` — use this when a downstream project's README, onboarding, or reference docs drift from the actual code
- `kmp-clean-architecture` — the 6-layer contract that all skill routing assumes
- `kmp-feature-scaffold` — establishes the module structure before any feature skills are loaded
- `kmp-dependency-injection` — every feature plan must include Koin wiring; load this if the plan references bindings

---

## Output Style

When asked for a KMP recommendation, routing decision, or anti-pattern check, respond in this order:
1. recommendation (name the skill and the default choice)
2. the decision rule or dependency graph node that applies
3. why that skill or pattern fits
4. skills to use next (if the task spans multiple domains)

Keep the response concise — this skill routes to other skills, not implements. Name the exact skill to invoke for follow-up work.

---

## Changelog

Full content: `references/changelog.md`.
