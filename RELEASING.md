# Release Guide

This document is the authoritative source for releasing kmp-agent-skills.
It is written for both humans and AI agents — any agent that touches this
repo should read this before making release-related changes.

---

## Contents

- [When to release](#when-to-release)
- [Versioning rules](#versioning-rules)
- [Release process](#release-process)
- [Manual checklist](#manual-checklist-if-the-script-is-unavailable)
- [Pushing to remote](#pushing-to-remote)
- [After release](#after-release)
- [Rules for agents](#rules-for-agents)

---

## When to release

| Change | Release? | Bump |
|---|---|---|
| New skill added | Yes | `minor` |
| Existing skill improved (content, freshness, anti-patterns) | Yes, batch with other changes | `patch` |
| Bug fix in a script (`validate_module_graph.py`, etc.) | Yes | `patch` |
| Test added or fixed | Yes | `patch` |
| Architecture breaking change (new required SKILL.md section, changed frontmatter schema) | Yes | `major` |
| README / INSTALL.md / RELEASING.md typo fix | Only if batched with other changes | `patch` |
| Work-in-progress commits (mid-session changes) | No | — |

**Do not release after every single commit.** Batch related changes into one release.
The right moment is: the work is done, tests pass, audit is clean, and the change is worth
a tag so downstream users and registries can pin a known-good version.

---

## Versioning rules

This repo uses **semver** (`MAJOR.MINOR.PATCH`).

| Component | Bump when |
|---|---|
| `MAJOR` | A required SKILL.md section is added or renamed (breaks agents that validate skill structure), or the `skills.json` schema changes in a backwards-incompatible way |
| `MINOR` | One or more new skills are added |
| `PATCH` | Content improvements, freshness updates, script fixes, test additions — no new skills, no structure changes |

Current version is always in `skills.json` → `"version"`.

---

## Release process

### One command

```bash
# Validate only — nothing is written
python3 scripts/release.py --dry-run minor

# Execute the release
python3 scripts/release.py minor   # or patch / major
```

The script does the following automatically:

1. **Verify git working tree is clean** — uncommitted changes abort the release
2. **Run `audit_skills_repo.py`** — must return zero findings
3. **Run `scan_skill_issues.py`** — must report zero issues
4. **Run `validate_skill_map.py`** — README and the kmp-expert references must match
5. **Run `validate_keyword_routing.py`** — every skill must have routing coverage
6. **Run pytest** — must be 100% passing
7. **Bump the version** in `skills.json` (semver, based on the argument)
8. **Regenerate all skill entries** in `skills.json` from `SKILL.md` frontmatter
9. **Update shipped skill count** in `PLAN.md`
10. **Stage `skills.json`, `PLAN.md`, and `CHANGELOG.md`**
11. **Create a commit**: `Release vX.Y.Z`
12. **Create an annotated git tag**: `vX.Y.Z`
13. **Create a GitHub Release** via `gh` if available
14. **Print push instructions** — does **not** push automatically

### Script output

A successful release looks like:

```
kmp-agent-skills release — bump: minor

✅  Working tree is clean
✅  Audit clean — zero findings
✅  All tests pass (12 passed)
    Version: 1.0.0 → 1.1.0
✅  skills.json updated — version 1.1.0, 31 skills
✅  PLAN.md updated — Shipped Skills (31)
✅  Committed and tagged v1.1.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Release v1.1.0 ready.

  Push when confirmed:
    git push origin main
    git push origin v1.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Manual checklist (if the script is unavailable)

If `scripts/release.py` cannot be run, follow these steps exactly:

```bash
# 1. Verify clean tree
git status   # must show nothing to commit

# 2. Audit — must print nothing (zero findings)
python3 skills/kmp-audit/scripts/audit_skills_repo.py .

# 3. Skill issue scan — must report zero issues
python3 scripts/scan_skill_issues.py

# 4. Skill map validation — must pass
python3 skills/kmp-expert/scripts/validate_skill_map.py --repo-root .

# 5. Keyword routing validation — must pass
python3 skills/kmp-expert/scripts/validate_keyword_routing.py --repo-root .

# 6. Tests — must show N passed, 0 failed
python3 -m pytest tests/ -v

# 7. Bump version and regenerate skills.json manually
#    Edit skills.json "version" field, then re-run the extraction:
python3 - << 'PYEOF'
import json, re
from pathlib import Path
skills_dir = Path("skills")
skills = []
for skill_dir in sorted(skills_dir.iterdir()):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        continue
    text = skill_md.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        continue
    fm = fm_match.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    license_ = re.search(r"^license:\s*(.+)$", fm, re.MULTILINE)
    last_updated = re.search(r"last-updated:\s*['\"]?(.+?)['\"]?\s*$", fm, re.MULTILINE)
    desc_match = re.search(r"^description:\s*>\n((?:  .+\n?)+)", fm, re.MULTILINE)
    if desc_match:
        desc = " ".join(l.strip() for l in desc_match.group(1).splitlines())
    else:
        dm2 = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        desc = dm2.group(1).strip() if dm2 else ""
    kw_block = re.search(r"keywords:\n((?:    - .+\n?)+)", fm)
    keywords = [re.sub(r"^\s*-\s*", "", l).strip()
                for l in (kw_block.group(1).splitlines() if kw_block else []) if l.strip()]
    trigger_match = re.search(r"\*\*Trigger keywords:\*\*\s*(.+?)(?=\n\n|\n\*\*)", text, re.DOTALL)
    triggers = []
    if trigger_match:
        raw = trigger_match.group(1).replace("\n", " ")
        triggers = [t.strip().strip(".") for t in raw.split(",") if t.strip()]
    sd = skill_dir / "scripts"
    scripts = [p.name for p in sorted(sd.glob("*.py"))] if sd.exists() else []
    skills.append({"name": name.group(1).strip() if name else skill_dir.name,
                   "path": f"skills/{skill_dir.name}", "description": desc,
                   "license": license_.group(1).strip() if license_ else "Apache-2.0",
                   "last_updated": last_updated.group(1).strip() if last_updated else "",
                   "keywords": keywords, "triggers": triggers, "scripts": scripts})
# Read existing version (already bumped manually)
existing = json.loads(Path("skills.json").read_text())
Path("skills.json").write_text(json.dumps({"version": existing["version"], "skills": skills}, indent=2) + "\n")
print(f"skills.json regenerated — {len(skills)} skills")
PYEOF

# 5. Update PLAN.md shipped count
#    Find the line "## Shipped Skills (N)" and update N to match the skill count

# 6. Stage and commit
git add skills.json PLAN.md
git commit -m "Release vX.Y.Z"

# 7. Tag
git tag -a vX.Y.Z -m "Release vX.Y.Z — N skills"
```

---

## Pushing to remote

The script **never pushes automatically**. Always confirm with the user before pushing:

```bash
git push origin main
git push origin vX.Y.Z
```

Both commands are required. Pushing the tag without the commit (or vice versa) leaves
the registry in an inconsistent state.

---

## After release

Once pushed:

1. **Verify the tag is visible on GitHub**: `https://github.com/ronjunevaldoz/kmp-agent-skills/releases`
2. **Submit to skills.sh** (if not yet submitted): point the registry to the repo and the new tag
3. **Update downstream projects**: projects that pinned a previous tag can upgrade by pulling
   the new `skills.json` and re-copying the updated skill directories

---

## Rules for agents

These rules apply to any AI agent (Claude, Codex, Gemini, Cursor, etc.) that is asked
to perform a release:

1. **Run `--dry-run` first.** Always validate before executing.
   ```bash
   python3 scripts/release.py --dry-run <bump>
   ```

2. **Never push without explicit user confirmation.** The script deliberately stops before
   `git push`. Ask the user: *"Release vX.Y.Z is tagged locally. Should I push?"*

3. **Never force-push tags.** If a tag already exists at the target version, stop and
   report the conflict to the user. Do not `--force` overwrite a published tag.

4. **Never bump `major` without confirming the breaking change with the user.** A major
   bump means downstream agents and projects that depend on the current skill structure
   will need to update. Confirm the impact before proceeding.

5. **The release commit message must be exactly**: `Release vX.Y.Z` (no trailing period,
   no extra lines in the subject). The script enforces this. Do not deviate.

6. **`skills.json` is always regenerated from source.** Never hand-edit `skills.json`
   entries. The script extracts them from `SKILL.md` frontmatter. Manual edits will be
   overwritten on the next release.

7. **`skills.sh.json` must be kept in sync manually.** When adding a new skill, add its
   name to the appropriate grouping in `skills.sh.json` before running the release script.
   This file controls how skills.sh and the `npx skills add` CLI organize and display
   the skills. The release script does not touch it.

7. **All gates must pass before tagging.** If audit finds issues or tests fail, fix them
   and commit before re-running the release script. Do not skip or suppress failures.
