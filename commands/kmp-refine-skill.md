# /kmp-refine-skill $ARGUMENTS

**KMP Agent Skills** — refine a *project-owned* skill (one your own project authored
under its own `skills/<name>/`) against agentskills.io's real qualitative best
practices. Complements, not duplicates, `kmp-audit`'s mechanical
`_detect_project_skill_standards` check (frontmatter presence, 500-line cap) — this
command is about whether the skill is *good*, not just structurally valid.

Skill path: **$ARGUMENTS** (e.g. `awake-render-vulkan` → `skills/awake-render-vulkan/SKILL.md`)

---

## Step 1 — Mechanical baseline first

```bash
python3 ~/.agents/skills/kmp-audit/scripts/audit_project.py .
```

Fix any `project skill missing SKILL.md` / `missing frontmatter` / `missing name` /
`missing description` / `exceeds 500-line guideline` findings before continuing — this
command's checklist assumes those basics already pass.

---

## Step 2 — Qualitative checklist

Full source for every row: `docs/reference/skill-best-practices.md` (re-verified against
the live agentskills.io docs, not assumed) — read it before starting the review, don't
work from memory of this table alone.

| Check | Look for | Real failure shape |
|---|---|---|
| Description phrasing | "Use this skill when..." not "This skill does..." | Descriptive phrasing doesn't tell the agent *when* to act |
| Description explicitness | Names contexts where it applies even without exact keyword match | A skill that only triggers when the user says the exact domain word |
| Coherent unit scope | Not so narrow it forces multiple skills to load per task, not so broad it's hard to activate precisely | Either symptom is a real scoping problem, not a wording fix |
| Moderate detail | Concise stepwise guidance + one working example | Exhaustive edge-case coverage the agent can't extract signal from |
| Specificity calibration | Fragile/sequenced operations get exact prescriptive commands; flexible tasks get freedom + the *why* | One register applied to the whole file regardless of fragility |
| Procedures over declarations | Teaches a reusable method | A one-off specific answer that only covers the exact case it was written for |
| Gotchas section | Concrete corrections ("the `users` table uses soft deletes...") | Generic advice ("handle errors appropriately") — not a real gotcha |
| Output templates | A concrete template for structured output | Prose description of a format instead of a template to pattern-match against |
| Progressive disclosure pointers | "Load `references/x.md` when Y happens" | A bare "see references/ for details" with no trigger condition |
| Reference depth | `references/*.md` files are one level deep from `SKILL.md` | `a.md` pointing to `b.md` pointing to `c.md` |

For each row, read the target `SKILL.md` (and its `references/*.md` if any) and note a
pass/fail with the specific line/section that fails, same evidence-first standard as any
other audit finding in this collection — don't flag a row without quoting what's wrong.

---

## Step 3 — Trigger-rate testing (defer to `skill-creator`, don't reimplement)

Whether the description actually triggers on the right prompts — and stays quiet on
near-misses — is testable, not guessable, but this command does not reimplement that
loop. If `anthropic-skills:skill-creator` is available in the current session, hand off
to it: it automates the full eval loop (labeled `eval_queries.json`, train/validation
split, 3 runs per query for trigger-rate under nondeterminism, description-improvement
proposals, an HTML report). If it isn't available, tell the user it exists and where
(`github.com/anthropics/skills/tree/main/skills/skill-creator`) rather than hand-rolling
a thinner eval script here.

---

## Step 4 — Present findings and apply on confirmation

```
─────────────────────────────────────────────
SKILL REFINEMENT: <skill-name>
Check:     <checklist row>
Evidence:  <quoted line/section from the target SKILL.md>
Suggested: <concrete rewrite, not just "improve this">
─────────────────────────────────────────────
Apply this change?
[y] Apply   [n] Skip   [a] Apply all remaining
─────────────────────────────────────────────
```

Apply only on confirmation, one finding at a time unless the user picks `[a]`. After
applying any change, bump the target skill's own `last-updated` field if it has one —
same discipline `kmp-modify-skill` applies to this repo's own skills.

Do not touch mechanical baseline items already covered by Step 1's script output — this
command's edits are scoped to the qualitative checklist only.
