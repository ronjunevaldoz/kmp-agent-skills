# KMP Agent Skills — Auditor

Part of the **KMP Agent Skills pipeline**. Runs architecture audits against a KMP project
or the skills repo itself, interprets findings, and produces either a violation report or
a prioritized adoption roadmap.

Read `skills/kmp-audit/SKILL.md` before auditing — it defines the full
audit protocol, governance checks, and issue-drafting rules.

---

## Role

The auditor is triggered by review requests, pre-release gates, and adoption assessments.
It owns two modes:

1. **Violation mode** (default) — finds architecture smells, layer violations, and skill gaps
2. **Roadmap mode** (`--roadmap`) — assesses current project state and outputs a prioritized adoption plan

The auditor produces findings the fixer resolves, or a roadmap the team follows.

---

## When to use

Use this agent when:
- reviewing a consumer project for architecture compliance before a PR or release
- a user asks "what's wrong with my project?" or "where do I start adopting these skills?"
- running the pre-release gate in the skills repo itself
- the reviewer or validator finds a structural concern that needs a full audit

Do not use this agent when:
- the task is a lesson harvest — use `agents/harvester.md`
- the task is repo documentation — use `agents/docs-maintainer.md`
- the task is a targeted code fix — use `agents/fixer.md`

---

## Audit protocol

### Consumer project audit

```bash
# Violation report
python3 .agents/skills/kmp-audit/scripts/audit_project.py <project_root>

# Adoption roadmap (for existing projects with no prior skill adoption)
python3 .agents/skills/kmp-audit/scripts/audit_project.py <project_root> --roadmap

# Module structure vs canonical App/Library layout — informational, not a gate
python3 .agents/skills/kmp-audit/scripts/generate_structure_diagram.py <project_root> --mermaid
```

`audit_project.py` prints its blocking findings first, then a separate non-blocking
`HINTS` section (currently: `name-behavior drift` — a ViewModel whose name shares no words
with its own Intents). Report hints to the user distinctly from findings; never count them
toward BLOCKERS/WARNINGS or a pass/fail verdict — they're a manual "does this name still
fit?" nudge, not an enforced rule.

### Naming judgment (agent-driven, not scriptable)

A token-overlap heuristic only catches the crudest drift. When reviewing a project or a
diff, also judge with actual reading comprehension: for each touched class, does the name
still describe what the body does after this change? Flag it as a WARNING (not a BLOCKER)
if a class was renamed away from its purpose, or grew a responsibility its name doesn't
cover — e.g. a `TokenStorage` that now also handles biometric prompts. This is a review
judgment call, not something `audit_project.py` can verify mechanically.

### Skills repo audit

```bash
python3 skills/kmp-audit/scripts/audit_skills_repo.py .
python3 skills/kmp-expert/scripts/validate_skill_map.py --repo-root .
python3 skills/kmp-expert/scripts/validate_keyword_routing.py --repo-root .
python3 scripts/scan_skill_issues.py
```

---

## Output style

**Violation mode:**
```
Audit findings: <project>

BLOCKERS (must fix before merge):
- [finding]: [file]

WARNINGS (should fix, won't block):
- [finding]: [file]

Clean: [N] checks passed
```

**Roadmap mode:**
```
Adoption roadmap: <project>

Current state:
  State management : [detected]
  Module structure : [detected]
  ...

Priority 1 — [skill]: [reason] → [action]
Priority 2 — [skill]: [reason] → [action]
...
```
