---
description: "Shared plan/implement/validate/review pipeline referenced by /kmp-execute-ticket and /kmp-implement-feature. Not a standalone command."
---

# Feature Delivery Pipeline

Use this shared pipeline after the command-specific intake and before its wrap-up steps.

## Plan

1. Load `agents/planner.md` with the accepted requirements.
2. Map every requirement to a layer, dependency, and test.
3. Show the plan and wait for user approval.

## Implement

1. Load `agents/implementer.md`.
2. Build in order: `:model → :api → :domain → :data → :presenter → :ui`.
3. Add the required Koin wiring and tests with each layer.

## Validate

1. Load `agents/validator.md`.
2. Run the architecture audit, commonMain compilation, and JVM tests.
3. On failure, switch `agents/implementer.md` to targeted-fix mode, load
   `agents/references/targeted-fix-mode.md`, and re-run the failed gate.

Stop and report after two unsuccessful fix cycles.

## Review

1. Load `agents/reviewer.md`.
2. Review boundaries, Koin wiring, MVI contracts, and test coverage.
3. For user-visible behavior, also run runtime QA from
   `agents/references/runtime-qa-mode.md`.
4. Allow one targeted-fix cycle for a review blocker, then re-review.
