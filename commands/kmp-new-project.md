---
description: "Scaffold a complete KMP project from a natural language description."
argument-hint: "[arguments]"
---

# /kmp-new-project $ARGUMENTS

**KMP Agent Skills** — scaffold a complete KMP project from a natural language description.

`$ARGUMENTS` is optional:
- Omitted: the command asks what the app does before proceeding
- Plain description: `build a todo app in kmm`
- A path to a sample spec: `samples/todo-app.md`
- Append `--dry-run` anywhere in the description to run intake, inference, and planning
  through Step 4's F-03 architecture diagram, then print the resulting module structure
  and stop — no `git clone`, no file writes. Re-run without `--dry-run` to actually
  scaffold once the preview looks right. Strip `--dry-run` from the text before treating
  the rest as the app description.

This command drives the full pipeline end-to-end across 11 steps:
intake → infer → **plan (compact MVP + delivery slices, gated approval, persisted to `PLAN.md`)** → scaffold → infrastructure → design system → screen layouts + previews → features → verify → agent setup → summary.
Any assumptions made are printed before implementation begins.

For every gated decision below (plan confirmation, design token draft, component
library choice, sprint review, etc.), use the `AskUserQuestion` tool to present the
choice — not a printed block the user replies to in free text. Each such point below
still shows the *content* of the options; render them as `AskUserQuestion` options
rather than plain prose.

---

## Pipeline — 11 steps across 5 phases

Each phase lives in `kmp-expert`'s `references/`. **Load one phase at a time**, in order,
when the pipeline reaches it — not all of them up front. That is the whole point of the
split: a 1000-line procedure loaded on invocation crowds out the context the actual
scaffolding work needs.

| Phase | Steps | Reference file | Gate before moving on |
|---|---|---|---|
| 1. Intake and plan | 1-3 | `references/new-project-phase-1-intake-and-plan.md` | User confirms the plan; it is written to `PLAN.md` |
| 2. Foundation | 4-5 | `references/new-project-phase-2-foundation.md` | `./gradlew help` is `BUILD SUCCESSFUL` |
| 3. Design system | 6-7 | `references/new-project-phase-3-design-system.md` | **[App] only** — Library skips to Phase 4 |
| 4. Features | 8 | `references/new-project-phase-4-features.md` | Each sprint reviewed before the next starts |
| 5. Verify and handoff | 9-11 | `references/new-project-phase-5-verify-and-handoff.md` | `/kmp-verify` passes before the summary prints |

Paths are `skills/kmp-expert/references/...` in this repo. `/kmp-new-project` is
repo-internal — `/kmp-setup-agents` Step 6 deliberately excludes it from consumer
installs — so it always runs somewhere this collection's own `skills/` tree is present.

If `--dry-run` was set in Step 1, stop at the end of Phase 2's F-03 architecture diagram:
print the resulting module structure and stop, before any `git clone` or file write.

---

## Notes

- **[App]** Always generate `Content` composables (pure state, no ViewModel) — they are
  what Roborazzi tests inject. Never screenshot a `Screen` directly.
- **[App]** Every screen needs `AppScaffold` + `AppTopAppBar`. The visual audit will
  catch missing chrome.
- **[App]** Roborazzi golden images must be recorded and committed:
  `./gradlew recordRoborazziJvm` — run this before Step 9.
- **[Library]** Design the public API signature before the implementation — `explicitApi()`
  (wired in Step 4) makes every visibility choice deliberate from the first line instead
  of a retrofit; changing a signature after `apiDump` has run means a real `apiCheck`
  failure, not just a style nit.
- This command is the consumer-facing entry point. For E2E testing the skills themselves,
  use a spec from `samples/` as the `$ARGUMENTS` input in a clean sandbox directory.
