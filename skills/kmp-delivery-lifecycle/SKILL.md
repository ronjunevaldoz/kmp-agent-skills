---
name: kmp-delivery-lifecycle
description: >
  Enforce Definition of Ready (DoR), Definition of Done (DoD), and quality verification
  gates for Kotlin Multiplatform engineering. Use before picking up a task or feature
  to verify prerequisites, during implementation to validate UI and performance constraints,
  and before opening or merging Pull Requests to guarantee release-quality standards.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-18'
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
---

# KMP Delivery Lifecycle: Definition of Ready (DoR) & Definition of Done (DoD)

## When to Use This Skill

Use this skill when:
- Evaluating an issue or task ticket before writing code to verify it meets the **Definition of Ready (DoR)**
- Specifying verifiable acceptance criteria (Given/When/Then) for complex feature initiatives
- Determining whether a task requires UI layout verification, accessibility audits, or performance benchmarks
- Verifying code against the **Definition of Done (DoD)** before opening or squash-merging a Pull Request
- Preventing premature feature sign-off, untested regressions, or unverified multiplatform claims

Do NOT use this skill when:
- Triaging issue hierarchy or avoiding GitHub comment spam (use `kmp-github-issue-governance`)
- Running static code quality rules or Detekt configuration (use `kmp-code-quality`)
- Performing ad-hoc profiling without delivery criteria (use `kmp-benchmark` or `kmp-compose-web-performance`)

**Trigger keywords:** definition of ready, definition of done, DoR, DoD, quality gate, delivery lifecycle, acceptance criteria, pr readiness, readiness checklist, done checklist, ui validation, performance gate.

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
3. **Visual Evidence**:
   - Side-by-side **Before vs After table** (fixed 380px width) or collapsible `<details>` block with real device/simulator screenshots attached to the PR.

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
- [ ] **3. Visual & Diagnostic Evidence Attached**:
  - PR contains Before/After screenshots or diagnostic test logs per `kmp-github-issue-governance`.
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

## Output Template: PR Delivery Gate Checklist

Include this markdown block in PR descriptions to prove verification:

```markdown
### Delivery Gates Verification

#### Definition of Ready (DoR)
- [x] Clear acceptance criteria and target platforms identified
- [x] Architecture layer boundaries respected

#### UI & Performance Gates
- [x] Design system tokens used (no hardcoded colors/dp)
- [x] Before/After visual evidence attached
- [x] Zero per-frame allocations in render/draw paths

#### Definition of Done (DoD)
- [x] All unit, flow, and screenshot tests pass across active platforms
- [x] Detekt and code quality clean
- [x] Documentation & conventional commits verified
```

---

## Related Skills

- `kmp-github-issue-governance` — issue decomposition, anti-spam comment policy, PR visual evidence
- `kmp-clean-architecture` — 6-layer contract and module boundaries
- `kmp-code-quality` — Detekt, Ktlint, and compiler warning gates
- `kmp-compose-design-system` — semantic tokens, themes, and UI components
- `kmp-benchmark` — microbenchmarking with `kotlinx-benchmark`
- `kmp-compose-web-performance` — Wasm bundle size, DevTools, and first-paint metrics
