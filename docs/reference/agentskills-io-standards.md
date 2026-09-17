# agentskills.io Standards Compliance

Verified against the real spec (`agentskills.io/specification`) and the real reference
validator (`github.com/agentskills/agentskills`, `skills-ref` package) — not assumed.
Agent Skills is the open format Anthropic originally developed; `SKILL.md` in this repo
already follows it. This doc records what was actually checked, how, and what's still open.

## How this was verified

```bash
git clone --depth 1 https://github.com/agentskills/agentskills.git /tmp/agentskills-check
cd /tmp/agentskills-check/skills-ref
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Run against every skill in this repo
cd /path/to/kmp-agent-skills
for d in skills/*/; do skills-ref validate "$d" || echo "FAIL: $d"; done
```

Result as of 2026-07-26: **64/64 pass.** Zero hard-spec violations.

## The spec, in full

### Frontmatter fields

| Field | Required | Constraint |
|---|---|---|
| `name` | Yes | 1-64 chars. Lowercase unicode alphanumeric + hyphens only. No leading/trailing/consecutive hyphen. **Must match the parent directory name.** |
| `description` | Yes | 1-1024 chars, non-empty. What the skill does *and* when to use it. |
| `license` | No | License name or pointer to a bundled license file. |
| `compatibility` | No | Max 500 chars. Environment requirements (product, system packages, network access). Most skills don't need it. |
| `metadata` | No | Arbitrary string→string map. |
| `allowed-tools` | No | Space-separated pre-approved tools. Experimental. |

### Directory structure

```
skill-name/
├── SKILL.md          # Required
├── scripts/           # Optional — executable code
├── references/        # Optional — docs loaded on demand
├── assets/             # Optional — templates, static resources
```

### Progressive disclosure (the load-time budget)

1. **Discovery** (~100 tokens): every skill's `name` + `description` loads at startup.
2. **Activation** (**recommended <5000 tokens / <500 lines**): the full `SKILL.md` body
   loads when a task matches.
3. **Execution** (as needed): `scripts/`/`references/`/`assets/` load only when the
   instructions tell the agent to.

This is the one guideline this repo doesn't fully meet yet — see Known Gaps below.

`kmp-audit`'s `audit_skills_repo.py` enforces the undocumented-directory guard for all
three optional directories — `scripts/`, `references/`, and `assets/` — flagging a skill
that has one of these directories but never mentions it in `SKILL.md`. This repo's
pre-existing `templates/` (4 skills, whole project-scaffolding trees copied verbatim)
predates this doc and isn't part of the spec — a separate, still-unchecked local
convention, not folded into `assets/`.

### Validation

`skills-ref validate ./my-skill` is the official reference check — install instructions
above. It only checks the hard spec (frontmatter), **not** the 500-line guideline; that's
a best-practice, not a validator rule.

## This repo's compliance script

`scripts/scan_skill_issues.py` now checks the full agentskills.io picture, not just this
repo's own internal quality bar:

| Check | Severity | What it catches |
|---|---|---|
| `name_too_long` | HIGH | `name` over 64 chars |
| `name_invalid_format` | HIGH | Uppercase, leading/trailing/double hyphen, non-alphanumeric |
| `name_dir_mismatch` | HIGH | Frontmatter `name` ≠ parent directory name |
| `description_too_long` | HIGH | `description` over the 1024-char hard limit |
| `description_approaching_limit` | LOW | `description` over 800 chars — not a violation, a heads-up |
| `oversized_skill_md` | MEDIUM | `SKILL.md` body over 500 lines — the progressive-disclosure guideline |
| `oversized_reference_md` | MEDIUM | A single `references/*.md` file over 500 lines — same guideline, applied one level down |
| `oversized_command_md` | MEDIUM | A `commands/*.md` slash command over 500 lines — its whole body loads on invocation, same cost the guideline bounds for `SKILL.md` |

Run it: `python3 scripts/scan_skill_issues.py`

These run alongside this repo's own pre-existing quality checks (testing coverage, stale
dates, required sections) in the same report — agentskills.io compliance isn't a separate
gate, it's part of the same one.

## Known gaps

None currently. The 22-skill 500-line-guideline backlog
([KI-008](../../KNOWN_ISSUES.md#ki-008--22-of-64-skillmd-files-exceed-agentskillsios-recommended-500-line-body))
was resolved 2026-08-04 — every skill's detail that belonged in `references/*.md` was
moved there, leaving a pointer stub under the original heading. `kmp-expert` is the one
deliberate exception: its two routing tables stay inline because the validators that
check them (`validate_skill_map.py`, `validate_keyword_routing.py`) read `SKILL.md`
directly, not `references/`.

[`docs/reference/skills-report.md`](skills-report.md) is the live, per-skill view of this
check — regenerated on every release by `scripts/generate_skills_report.py`, sourced from
the same `scan_skill_issues.py` data as the compliance script above.

## Best-practice guidance worth knowing (not enforced, but real)

Full content, re-verified against the live agentskills.io docs on 2026-08-24:
[`docs/reference/skill-best-practices.md`](skill-best-practices.md) — `kmp-refine-skill`
uses it as its qualitative checklist for consumer project-owned skills.

## Related

- `kmp-audit`'s `_detect_project_skill_standards` already enforces a
  version of this 500-line rule (with a `references/` escape hatch) on *consumer
  projects'* own project-owned skills — this doc is this repo holding its own 77 skills
  to the same real standard, not inventing a new one.
