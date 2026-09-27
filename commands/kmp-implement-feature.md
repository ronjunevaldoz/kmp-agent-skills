# /kmp-implement-feature $ARGUMENTS

**KMP Agent Skills** — build a new KMP feature end-to-end, layer by layer, with the full
Koin 4 / Ktor 3 / SQLDelight 2 / CMP 1.11 stack wired correctly from the start.

Feature name: **$ARGUMENTS**

---

## Phase 0 — Skills freshness check

```bash
python3 scripts/check_updates.py
```

| Exit | Action |
|---|---|
| `0` | Skills are current — proceed to Phase 1 |
| `1` | Updates available — display the output, ask the user: **Pull now / Skip / View diff** (see `commands/kmp-check-updates.md`). Do not pull automatically. After the choice is made, proceed to Phase 1. |
| `2` | Remote unreachable — print `⚠️ Running with local skills (offline)` and proceed to Phase 1. |

---

## Phases 1–4 — Shared delivery pipeline

Follow [Feature Delivery Pipeline](references/feature-delivery-pipeline.md). During planning,
inspect `build-logic/`, `gradle/libs.versions.toml`, and existing `feature/$ARGUMENTS/` modules.
Every implementation file must be complete and runnable; do not leave stubs or `// TODO` markers.

---

## Phase 5 — Wrap up

Before committing, check whether any `.py` script was added or modified during implementation:

```bash
git diff --name-only HEAD | grep -E '^(scripts/|skills/.*/scripts/).*\.py$' || true
```

If any scripts changed → ensure the matching `tests/test_<script-name>.py` is staged in the same commit (tests are one file per script under `tests/`). The pre-commit hook blocks otherwise.

Update `.agents/pipeline-context.json` with patterns learned during this feature,
then commit it so the next session inherits the context:

```bash
git add .agents/pipeline-context.json
git commit -m "chore(pipeline): update context after $ARGUMENTS"
```

Only commit if the file actually changed. Skip if all values are unchanged.

Report:
```
Feature:        $ARGUMENTS
Layers built:   <list>
Files created:  <N>
Tests written:  <N> unit + <N> UI
Validation:     PASS (ktlint: PASS | NOT CONFIGURED)
Review:         APPROVE
Pipeline ctx:   committed | unchanged
```

---

## Phase 6 — Proactive issue tracking

After the report, scan this session for patterns worth tracking:

1. **Recurring blockers** — any `[BLOCKER_TYPE]` that appeared in 2+ files
2. **LOW-confidence fixes** — anything the fixer marked LOW and the user resolved manually
3. **Skill gaps discovered** — any guidance the implementer had to invent because no skill covered it

For each item found, prompt:
```
Found <N> item(s) worth tracking as GitHub issues:
  · [<TYPE>] seen in <N> files — may indicate a skill gap in <skill-name>

Create GitHub issues for these? /submit-issue is ready to pre-fill each one.
  [y] Yes — open /submit-issue for each item in turn
  [n] No  — end session
```

Skip this phase if the session had zero blockers and no LOW fixes.
