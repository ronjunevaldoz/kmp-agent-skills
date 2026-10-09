# Contributing to kmp-agent-skills

Thank you for contributing. This guide covers everything needed to add skills,
fix bugs, run validation, and cut a release.

---

## Contents

- [Prerequisites](#prerequisites)
- [Repo structure](#repo-structure)
- [Adding a new skill](#adding-a-new-skill)
- [Updating an existing skill](#updating-an-existing-skill)
- [Running validation](#running-validation)
- [Commit format](#commit-format)
- [Pull request checklist](#pull-request-checklist)
- [Release process](#release-process)

---

## Prerequisites

| Tool | Minimum version | Purpose |
|---|---|---|
| Python | 3.10 | Audit scripts, release script, tests |
| Git | 2.x | Version control |
| Claude Code | latest | Running skills and commands as an agent |
| Git for Windows | latest | Windows only: the bash that runs hooks and shell-script tests |

On Windows, run `python` where the docs say `python3` (the `python3` there is a Microsoft
Store stub). The tests and `scripts/release.py` run from PowerShell or Git Bash; tests call
Git for Windows' bash directly, since a bare `bash` would start WSL instead.

Install Python dependencies (tests only, no runtime deps):

```bash
pip install pytest
```

---

## Repo structure

```
kmp-agent-skills/
├── agents/              # Pipeline agent definitions (planner, implementer, etc.)
├── commands/            # Slash commands (/kmp-new-project, /kmp-verify, /kmp-audit-screenshots, …)
├── samples/             # E2E test specs (e.g. samples/todo-app.md)
├── scripts/             # Shared scripts (release.py, validate_keyword_routing.py, …)
├── skills/              # One directory per skill
│   └── <skill-name>/
│       ├── SKILL.md     # The skill definition — source of truth
│       └── scripts/     # Optional Python helper scripts for this skill
├── tests/               # Pytest test suite
├── skills.json          # Auto-generated registry — never edit by hand
├── AGENTS.md            # Agent pipeline documentation
├── CHANGELOG.md         # Release history
├── CONTRIBUTING.md      # This file
├── INSTALL.md           # Installation instructions
├── KNOWN_ISSUES.md      # Open issues and workarounds
├── PLAN.md              # Roadmap and shipped skill count
└── RELEASING.md         # Detailed release process
```

---

## Scope boundary

Use this rule before creating anything new:

- `skills/` is for consumer-facing capabilities that downstream projects install.
- `agents/`, `commands/`, and `scripts/` are for repo-internal workflow, validation,
  and maintenance.
- Consumer release notes and per-skill changelog updates belong to
  `agents/changelog.md` and `/kmp-release-notes`, not a new skill.
- If a request is repo-internal, do not scaffold a skill; update the relevant agent,
  command, or repo doc instead.

If the scope is unclear, confirm it before writing files. That keeps consumer skills
and repo maintenance paths separate.

For consumer-facing repos, treat docs organization, `CHANGELOG.md`, and release notes
as a single release surface: keep them in sync as part of the release flow, not as
separate optional updates.

---

## File naming conventions

| Location | Convention | Examples |
|---|---|---|
| Root-level docs | `SCREAMING_CASE.md` | `README.md`, `CHANGELOG.md`, `PLAN.md` |
| `agents/` | `kebab-case.md` | `planner.md`, `changelog.md` |
| `commands/` | `kmp-kebab-case.md` | `kmp-new-project.md`, `kmp-run-audit.md` |
| `docs/` | `kebab-case.md` | `goal-gap-analysis.md` |
| `samples/` | `kebab-case.md` | `todo-app.md` |
| `skills/<name>/` | `SKILL.md` (fixed) | Same reasoning as `README.md` — primary entry file |
| `scripts/` | `snake_case.py` | `release.py`, `generate_release_notes.py` |

**Rule:** root-level files are `SCREAMING_CASE` because GitHub renders them prominently.
Everything inside a subdirectory uses `kebab-case` (or `snake_case` for Python scripts).
`SKILL.md` is the one intentional SCREAMING exception — it is the skill's `README.md` equivalent.

---

## Script paths in consumer commands

Consumer commands run inside other projects, so `skills/...` and `scripts/...` paths don't
exist there. A bash block that runs a bundled script finds it first, in the same block
(each block runs in its own shell):

```bash
for KMP_SKILLS in "${CLAUDE_PLUGIN_ROOT}/skills" skills .agents/skills ~/.agents/skills ~/.claude/skills; do [ -d "$KMP_SKILLS/kmp-audit" ] && break; done
python3 "$KMP_SKILLS/kmp-audit/scripts/audit_project.py" .
```

Probe for the skill the block needs (`kmp-audit` above). Claude Code fills in
`${CLAUDE_PLUGIN_ROOT}` when it loads a plugin command or agent; everywhere else it is empty
and the loop moves on. Top-level `scripts/` aren't deployed with skills, so those use the
`KMP_REPO` loop instead, which finds the plugin or a kmp-agent-skills checkout (see
`commands/kmp-update-skills.md`). Repo-internal commands, listed in README's
"Repo-internal commands" table, keep repo-relative paths so they run your working copy.
`tests/test_docs_governance.py` enforces this.

---

## Adding a new skill

Before you scaffold, make sure the request is truly a consumer-facing skill and not
repo-internal maintenance or consumer changelog work.

### 1. Create the skill directory

```bash
mkdir skills/<skill-name>
```

Skill names use `kebab-case` and are prefixed with `kmp-` for KMP skills.

### 2. Write `SKILL.md`

Every skill file must open with this frontmatter block:

```yaml
---
name: <skill-name>
description: >
  One or two sentence description of what this skill produces.
  Used in the registry and auto-completion.
license: Apache-2.0
last-updated: YYYY-MM-DD
keywords:
    - keyword-one
    - keyword-two
---
```

**Required sections** (in this order):

| Section | Purpose |
|---|---|
| `## When to Use This Skill` | Trigger keywords and when NOT to use it |
| `## Recommendation First` | Default recommended approach and why |
| `## Overview` | What the skill produces (decisions, dependencies) |
| One or more `## Step N:` sections | Concrete implementation steps |
| `## Testing` | How to verify the output (unit tests, audit commands) |
| `## Common Anti-Patterns` | What to avoid and why |
| `## Changelog` | Consumer-facing release notes — date + change table, travels with the skill |

Skills that lack any of these sections will fail the audit script.

### 3. Register the skill in `skills.sh.json`

Add the skill name to the appropriate group in `skills.sh.json`. This file controls
how the skill appears in the `npx skills add` CLI. The release script does not
update this file — you must add it manually before releasing.

### 4. Add a keyword routing entry

Open `skills/kmp-expert/references/skill-invocation-map.md` and add at least one
invocation map row for the new skill, and list it in the `README.md` catalog. This is
tested in CI. `agents/planner.md` reads these; it keeps no routing table of its own.

### 5. Run validation

```bash
python3 skills/kmp-audit/scripts/audit_skills_repo.py .
python3 scripts/scan_skill_issues.py
python3 skills/kmp-expert/scripts/validate_skill_map.py --repo-root .
python3 skills/kmp-expert/scripts/validate_keyword_routing.py --repo-root .
python3 -m pytest tests/ -v
```

All validation commands must pass with zero findings before opening a PR.

---

## Updating an existing skill

- **Content fixes** (anti-patterns, examples, freshness): edit `SKILL.md` directly.
- **Version bumps**: update the `last-updated` frontmatter field and change version
  numbers in the Step sections. Also update `gradle/libs.versions.toml` examples if
  the skill references a version catalog.
- **New section**: add it in the required order. Run the audit after.
- **Rename a skill**: update the directory name, `SKILL.md` `name:` field,
  `skills.sh.json`, and any cross-references in other skills or `AGENTS.md`.

---

## Running validation

```bash
# Architecture audit — checks all skills for required sections and cross-references
python3 skills/kmp-audit/scripts/audit_skills_repo.py .

# Skill issue scan — checks Testing sections, freshness, and required guidance
python3 scripts/scan_skill_issues.py

# Skill map coverage — keeps README and the kmp-expert references synchronized
python3 skills/kmp-expert/scripts/validate_skill_map.py --repo-root .

# Keyword routing coverage — ensures every skill has at least one trigger
python3 skills/kmp-expert/scripts/validate_keyword_routing.py --repo-root .

# Full test suite
python3 -m pytest tests/ -v

# Module graph validator (for KMP project validation, not skills repo)
python3 skills/kmp-audit/scripts/audit_project.py <project-path>
```

All skills-repo validation commands must be clean before a PR is opened or a release is cut.

---

## Commit format

Use the following prefixes. Keep the subject line under 72 characters.

| Prefix | When to use |
|---|---|
| `feat(scope):` | New skill, command, or script |
| `fix(scope):` | Bug fix in a script or incorrect skill content |
| `refine(scope):` | Improving existing skill content, adding examples |
| `enforce(scope):` | Adding a rule or constraint to skill or pipeline |
| `docs:` | README, INSTALL, CONTRIBUTING, RELEASING changes |
| `test:` | Adding or fixing tests |
| `release:` | Do not use manually — reserved for the release script |

**Scope** is the skill name or area, e.g. `feat(scaffold):`, `fix(audit):`, `docs:`.

**Examples:**
```
feat(roborazzi): add visual design audit step with dynamic path resolution
fix(audit-screenshots): resolve output dir from build.gradle.kts
refine(presenter): add koin-core-viewmodel example for KMP ViewModels
enforce(scaffold): mandate kmp-wizard clone as only valid project base
docs: add CONTRIBUTING.md
```

**No `Co-Authored-By` trailer.** Commits in this repo — including ones made by an AI
coding agent — do not carry a `Co-Authored-By: <agent>` trailer. Keep the message to the
subject line (and body if needed) per the format above, nothing appended below it.

---

## Pull request checklist

Before opening a PR, confirm:

- [ ] `audit_skills_repo.py` returns zero findings
- [ ] `scan_skill_issues.py` returns zero issues
- [ ] `validate_skill_map.py` passes
- [ ] `validate_keyword_routing.py` passes
- [ ] `pytest tests/` passes with 0 failures
- [ ] `SKILL.md` frontmatter `last-updated` is set to today's date
- [ ] Any new skill is added to `skills.sh.json`
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]`
- [ ] Commit messages follow the format above

PR title format: same as commit format — `feat(scope): short description`.

---

## Release process

See [`RELEASING.md`](RELEASING.md) for the full release guide.

Quick summary:

```bash
# Dry run first — validates repo gates, tests, and version bump
python3 scripts/release.py --dry-run minor   # or patch / major

# Execute the release
python3 scripts/release.py minor
```

The script does not push. After it completes:

```bash
git push origin main
git push origin v<VERSION>
```

**When to bump:**

| Change | Bump |
|---|---|
| New skill added | `minor` |
| Content fix, script fix, new command | `patch` |
| Breaking change to SKILL.md schema or `skills.json` format | `major` |
