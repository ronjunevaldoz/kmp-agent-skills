---
name: kmp-delivery-lifecycle
description: >
  Enforce Definition of Ready (DoR), Definition of Done (DoD), and quality verification
  gates for Kotlin Multiplatform engineering. Use before picking up a task or feature
  to verify prerequisites, during implementation to validate UI and performance constraints,
  and before opening or merging Pull Requests to guarantee release-quality standards.
  Load when opening a PR (gh pr create) that changes UI: it owns the before/after
  screenshot evidence rule for PR bodies and bug issues.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-27'
  keywords:
    - definition of ready
    - definition of done
    - DoR
    - DoD
    - delivery lifecycle
    - acceptance criteria
    - quality gate
    - performance validation
    - ui validation
    - pr readiness
    - verification checklist
    - pull request
    - open a PR
    - gh pr create
    - before/after screenshots
    - visual evidence
---

# KMP Delivery Lifecycle: Definition of Ready (DoR) & Definition of Done (DoD)

## When to Use This Skill

Use this skill when:
- Evaluating an issue or task ticket before writing code to verify it meets the **Definition of Ready (DoR)**
- Specifying verifiable acceptance criteria (Given/When/Then) for complex feature initiatives
- Determining whether a task requires UI layout verification, accessibility audits, or performance benchmarks
- Verifying code against the **Definition of Done (DoD)** before opening or squash-merging a Pull Request
- Opening a PR or filing a bug that changes what users see — Phase 3A.3 before/after evidence is mandatory
- Preventing premature feature sign-off, untested regressions, or unverified multiplatform claims

Do NOT use this skill when:
- Triaging issue hierarchy or avoiding GitHub comment spam (use `kmp-github-issue-governance`)
- Running static code quality rules or Detekt configuration (use `kmp-code-quality`)
- Performing ad-hoc profiling without delivery criteria (use `kmp-benchmark` or `kmp-compose-web-performance`)

**Trigger keywords:** definition of ready, definition of done, DoR, DoD, quality gate, delivery lifecycle, acceptance criteria, pr readiness, readiness checklist, done checklist, ui validation, performance gate, open a PR, pull request, gh pr create, before/after screenshots, visual evidence.

---

## Recommendation First

1. **Never begin coding without a verified Definition of Ready (DoR).**
   An ambiguous ticket produces ambiguous code. If API contracts, target platforms, or acceptance criteria are missing, halt and draft the missing criteria before touching source sets.
2. **Make UI and Performance validation conditional, not optional.**
   - If a change touches `:ui` or composables: Visual Before/After evidence and semantic design token usage are **mandatory**.
   - If a change touches hot loops, rendering shaders, or network pipelines: Allocations and frame timings must be verified against performance budgets.
3. **The Definition of Done (DoD) is binary.**
   There is no "almost done." A task is either 100% verified across all declared platform targets with green CI, or it is in progress.

---

## 1. Phase 1: Definition of Ready (DoR) Gate

Before moving an issue or task from `Todo` to `In Progress`, verify that the work satisfies the DoR checklist:

### DoR Checklist

- [ ] **1. Issue Classification & Hierarchy**:
  - Classify as Epic, Sub-Issue (Task), or Standalone Bug/Feature per `kmp-github-issue-governance`.
  - Child tasks are linked to their parent Epic.
- [ ] **2. Milestone & Version Target (Mandatory)**:
  - Attached to an active GitHub Milestone (e.g. `v0.3.0`, `v3.1.0`).
  - Target SemVer impact declared: `patch` (fix), `minor` (backward-compatible feature), or `major` (breaking change).
- [ ] **3. Target Platform Scope**:
  - Explicitly states which platforms are supported: JVM, Android, iOS (Metal/Simulator), Desktop (Vulkan), or Web (Wasm/WebGPU).
- [ ] **4. Architectural Layer Boundary**:
  - Identifies which of the 6 layers are touched (`:model`, `:api`, `:domain`, `:data`, `:presenter`, `:ui`).
  - Identifies whether new Koin dependencies or database migrations (`SQLDelight`) are required.
- [ ] **5. State Machine & Contract (for UI / Features)**:
  - MVI Contract defined: `UiState` (explicit Empty, Loading, Content, Error states), `UiIntent`, and `UiEffect`.
- [ ] **6. Testable Acceptance Criteria**:
  - Defined in Given / When / Then format.
  - Test strategy identified: JVM Unit test (`runTest` + Turbine), Compose screenshot (`Roborazzi`), or headless integration test.

---

## 2. Phase 2: Implementation Quality Gates

During implementation, enforce this collection's non-negotiable architectural boundaries:

1. **Layer Dependency Rules**:
   - `:presenter` must NOT import Compose runtime or UI libraries (JVM testable).
   - `:ui` depends only on `:presenter` and design system tokens.
   - ViewModels never take another ViewModel as constructor param or property.
2. **Zero-Warning Code Quality**:
   - Run Detekt and compiler checks: `./gradlew detekt check`
   - No `@Suppress` annotations without a documented, verified rationale.

---

## 3. Phase 3: UI & Performance Validation Gates (Conditional)

When a task touches visual presentation, user interaction, or performance-critical paths, enforce these specialized validation gates:

### A. UI & Visual Validation Gate (Trigger: Touches `:ui`, Composables, Shaders)

1. **Semantic Design Tokens**:
   - Zero raw hex colors (`Color(0xFF...)`) or hardcoded DP margins.
   - All colors resolved via `AppTheme.colors.*` and spacing via `AppTheme.dimensions.*`.
2. **Accessibility (a11y)**:
   - Minimum tap target of 48×48 dp for interactive controls.
   - Every icon or image has a meaningful `contentDescription` or is marked decorative.
3. **Visual Evidence** (every PR and bug issue that changes what users see):
   - **Source:** committed Roborazzi goldens (`kmp-roborazzi`). Before = snapshot at the
     merge-base with the target branch; After = snapshot at the PR head. Do not "attach"
     screenshots — `gh` and the REST API cannot upload attachments to PR bodies or comments.
   - **Stale base:** if a golden was already stale at the base, make the branch's first commit
     a re-record on the base with no code change and use that commit as Before.
   - **Links:** SHA-pinned `https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true` inside
     an HTML `<table>` with `<img width=...>` — phone ~360, desktop ~420. Push first; unpushed
     SHAs 404. Never branch-pinned URLs: they break once the branch is deleted.
   - **Generate it:** `python3 <skills-root>/kmp-roborazzi/scripts/pr_visual_evidence.py > /tmp/visual.md`
     (base defaults to merge-base with `origin/main`; `--base`, `--glob`, `--target`, `--repo`
     override). Modified/renamed → Before | After row; new-only and removed snapshots get their
     own sections; long lists fold into `<details>`. Include the output in the `--body-file`.
   - **Private repos:** images render only for signed-in members; public repos render for everyone.
   - **No visual change:** write one line instead, e.g. `No before/after: server-only`.

### B. Performance Validation Gate (Trigger: Touches Render Loops, Canvas, Flow Chains, Wasm)

1. **Allocation & Composition Health**:
   - Zero object allocations inside `drawBehind`, `drawWithCache`, or per-frame render passes.
   - State reads hoisted to phase boundaries (`Modifier.graphicsLayer { ... }` instead of recomposing whole containers).
2. **WebGPU / Wasm Budgets**:
   - Wasm bundle payload growth within project thresholds (`kmp-compose-web-performance`).
   - Clean first-paint under 1.5s on headless Chrome.
3. **Microbenchmarks**:
   - Critical path algorithms (parsers, serializers, matrix math) must run `kotlinx-benchmark` without regression against baseline.

---

## 4. Phase 4: Definition of Done (DoD) Gate

Before submitting a Pull Request for review or marking a ticket complete:

### DoD Checklist

- [ ] **1. Build & Test Verification**:
  - 100% tests pass across all target platform source sets (`./gradlew check`).
  - No broken or skipped tests without linked tracking issues.
- [ ] **2. Architecture Audit**:
  - `python3 skills/kmp-audit/scripts/audit_project.py .` passes with zero critical/high findings.
- [ ] **3. Visual & Diagnostic Evidence in the PR Body**:
  - PR body contains the Phase 3A.3 Before/After table (or the one-line "No before/after: <reason>"), or diagnostic test logs per `kmp-github-issue-governance`.
- [ ] **4. Milestone & Release Target Alignment**:
  - Pull Request is assigned to the matching GitHub Milestone (`gh pr edit <pr> --milestone "<milestone>"`).
  - Commit types match the target version bump (`feat` -> minor, `fix` -> patch, `BREAKING CHANGE` -> major).
- [ ] **5. Documentation & Changelog**:
  - Public API symbols documented with KDoc.
  - Commits follow Conventional Commit format (`feat(...)`, `fix(...)`, `chore(...)`).
  - `docs/` or module README updated if contracts changed.
- [ ] **6. In-Place Ticket Updates**:
  - Issue task checkboxes marked complete (`- [x]`) in the GitHub issue description.
  - Closing keyword (`Closes #123`) included in PR description.

---

## 5. Parallel Execution: Multi-Tasking with Git Worktrees

When working on multiple issues, sub-issues, or PR reviews simultaneously on a single device, **use `git worktree` instead of stash-and-switch branch churn**. Worktrees share the `.git` database but provide isolated working directories and build outputs.

### Branch Naming Conventions (Mandatory)

Always prefix branch names with the conventional type and target GitHub issue ID:

```text
<type>/<issue-id>-<short-description>
```

| Type | When | Example |
|---|---|---|
| `feat/` | New features, sub-tasks, capability additions | `feat/102-camera-hud` |
| `fix/` | Bug fixes, rendering defects, regressions | `fix/104-gizmo-wireframe` |
| `chore/` | Housekeeping, dependency bumps, agent setups | `chore/28-standardize-agents` |
| `refactor/` | Restructuring without behavior change | `refactor/55-scene-hierarchy` |
| `docs/` | Documentation additions or sync | `docs/88-kmp-openrewrite` |

*Why this is enforced:* GitHub automatically connects branches containing `#<id>` or `<id>-` to the issue in project boards, and worktree directories (`../worktrees/feat-102-camera-hud`) become self-describing and collision-free.

### KMP Worktree Setup Recipe

Always allocate worktrees outside the primary git root (or under a gitignored directory like `.worktrees/`) to prevent recursive audit loops and tooling confusion:

```bash
# 1. Create a worktree for a specific task branch (branch: feat/102-camera-hud)
git worktree add ../my-project-worktrees/feat-102-camera-hud -b feat/102-camera-hud

# 2. MANDATORY for KMP: Copy local.properties
# (local.properties is gitignored; Android SDK and NDK paths are required to compile)
cp local.properties ../my-project-worktrees/feat-102-camera-hud/local.properties

# 3. Enter and work in total isolation
cd ../my-project-worktrees/feat-102-camera-hud
./gradlew check
```

### Worktree Cleanup (Zero Disk Waste)

After the Pull Request is merged into `main`:

```bash
# 1. Return to primary repository root
cd /path/to/primary/repo

# 2. Prune and delete the worktree directory
git worktree remove ../my-project-worktrees/feat-102-camera-hud

# 3. Delete the local feature branch once merged
git branch -d feat/102-camera-hud
```

### Operational Worktree Rules
1. **Never commit inside `.worktrees/` inside the repo without adding it to `.gitignore`**:
   Orphaned worktrees checked into the working tree duplicate audit violations and waste disk space.
2. **Always copy `local.properties` immediately**:
   A worktree without `local.properties` will fail on the first Android or NDK compilation step with `SDK location not found`.
3. **Prune stale worktrees periodically**:
   Run `git worktree prune` to clean up dangling references.

---

## Output Template: PR Delivery Gate Checklist

Include this markdown block in PR descriptions to prove verification:

```markdown
### Delivery Gates Verification

#### Definition of Ready (DoR)
- [x] Clear acceptance criteria and target platforms identified
- [x] Architecture layer boundaries respected

#### UI & Performance Gates
- [x] Design system tokens used (no hardcoded colors/dp)
- [x] Before/After table from committed goldens in PR body (or "No before/after: <reason>")
- [x] Zero per-frame allocations in render/draw paths

#### Definition of Done (DoD)
- [x] All unit, flow, and screenshot tests pass across active platforms
- [x] Detekt and code quality clean
- [x] Documentation & conventional commits verified
```

---

## Common Anti-Patterns

| Mistake | Fix |
|---|---|
| Picking up an unclarified ticket with no acceptance criteria | Halt and document the Given/When/Then criteria before writing code (DoR Gate). |
| Marking a task done when only the JVM target tests pass | Execute `./gradlew check` across all declared targets (Desktop, Wasm, iOS, Android). |
| Leaving an issue or PR unassigned to a Milestone | Bind to the active milestone using `gh issue edit --milestone` or `gh pr edit --milestone`. |
| Merging visual changes without side-by-side evidence | Generate the Before vs After table from committed goldens with `kmp-roborazzi/scripts/pr_visual_evidence.py` and put it in the PR body (Phase 3A.3). |
| Promising "screenshots attached" from an agent via `gh` | `gh`/REST cannot upload attachments — use SHA-pinned blob links to committed snapshots. |
| Over-abstracting performance gates for pure data/model changes | Only enforce allocation & render gates when touching `:ui`, shaders, or collections. |

---

## Testing

Validate adherence to delivery gates across repositories:
- `@Test` pre-commit and CI verification workflows to ensure PR templates require DoR/DoD blocks.
- `runTest` on GitHub Actions status checks to enforce zero failing gates before merge.

---

## Output Style

1. State the ticket's DoR assessment (Ready vs Blocked) clearly at the top.
2. List any missing platform targets or acceptance criteria before beginning code.
3. Emit a concise, checkable verification block in the final response and PR description.

---

## Related Skills

- `kmp-github-issue-governance` — issue decomposition, anti-spam comment policy, PR visual evidence
- `kmp-roborazzi` — committed goldens and `scripts/pr_visual_evidence.py` for the Phase 3A.3 table
- `kmp-clean-architecture` — 6-layer contract and module boundaries
- `kmp-code-quality` — Detekt, Ktlint, and compiler warning gates
- `kmp-compose-design-system` — semantic tokens, themes, and UI components
- `kmp-benchmark` — microbenchmarking with `kotlinx-benchmark`
- `kmp-compose-web-performance` — Wasm bundle size, DevTools, and first-paint metrics

**Freshness rule:** recheck GitHub CLI and PR template capabilities before amending DoR/DoD checklists, as milestone and sub-issue API structures evolve.

---

## Changelog

| Date | Change |
|---|---|
| 2026-09-27 | Rewrote Phase 3A.3 Visual Evidence as an agent-executable recipe: committed goldens at merge-base vs PR head, SHA-pinned blob links, `kmp-roborazzi/scripts/pr_visual_evidence.py`, private-repo note, and the one-line "No before/after" rule. Dropped the "screenshots attached" instruction — `gh`/REST cannot upload attachments, and UI PRs shipped without evidence. Added PR keywords so the gate loads at PR time. |
| 2026-09-18 | Added Section 5 Git Worktree Parallel Execution runbook with mandatory `<type>/<issue-id>-<description>` branch naming conventions. |
| 2026-09-18 | Initial release — codified Definition of Ready (DoR), Definition of Done (DoD), milestone/version binding, conditional UI validation, and performance gates. |
