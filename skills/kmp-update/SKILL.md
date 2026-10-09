---
name: kmp-update
description: >
  Update kmp-agent-skills to the latest upstream release across machine-wide assistant
  bundles or consumer projects. Check for version drift, sync installed skills
  (~/.gemini/config/plugins/kmp-agent-skills, ~/.gemini/skills, ~/.agents/skills,
  ~/.claude/skills, ~/.codex/skills), update consumer .agents/skills, regenerate
  skills lockfiles, and run post-update verification audits.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-10-09'
  references: []
  keywords:
    - update skills
    - check updates
    - sync skills
    - kmp-update
    - kmp-update-skills
    - kmp-check-updates
    - upgrade skills
    - skills drift
    - sync-local-assistant-skills
    - update-consumer-skills
---

# `kmp-update` — Upstream Skill Synchronization & Drift Remediation

## When to Use This Skill

Use this skill when:
- Checking whether the active skills collection is behind upstream `origin/main` on [github.com/ronjunevaldoz/kmp-agent-skills](https://github.com/ronjunevaldoz/kmp-agent-skills).
- Syncing global machine-wide assistant skill bundles across Antigravity, Gemini CLI, Claude Code, Codex, and Cursor (`~/.gemini/config/plugins/kmp-agent-skills`, `~/.gemini/skills`, `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`).
- Updating vendored `.agents/skills/` in a downstream consumer project and regenerating `.agents/skills.lock`.
- Auditing skills drift after new KMP releases or git pull operations.

Do NOT use this skill when:
- Upgrading Gradle dependencies or libraries inside Kotlin source code (use `kmp-openrewrite` instead).
- Scaffolding a new feature module (use `kmp-feature-scaffold` instead).

**Trigger keywords:** update skills, check updates, sync skills, kmp-update, kmp-update-skills, kmp-check-updates, upgrade skills, skills drift, sync-local-assistant-skills, update-consumer-skills, refresh skills, latest skills release.

**Freshness rule:** recheck upstream release tags (`git fetch origin --tags`) before declaring a collection current; do not rely on local cached commit timestamps alone.

---

## Recommendation First

**Default to machine-wide assistant sync unless explicitly operating on a project-local vendored directory:**

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
# 1. Check if updates exist
python3 "$KMP_REPO/scripts/check_updates.py"

# 2. Sync all local assistant skill runtimes
bash "$KMP_REPO/scripts/sync-local-assistant-skills.sh"
```

The first line finds the scripts in the Claude Code plugin or a kmp-agent-skills checkout; they
are not deployed with the skills themselves. Run each block in one shell.

In Antigravity, slash commands are populated directly by active skills. Invoking `/kmp-update` in the chat canvas triggers this runbook.

---

## Phase 1 — Drift & Upstream Check

To verify if local skills are current relative to upstream:

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
python3 "$KMP_REPO/scripts/check_updates.py"
```

- **Exit 0**: Skills are up to date.
- **Exit 1**: Updates are available. Inspect the list of changed skills and commits.
- **Exit 2**: Offline or unable to reach remote, or the scripts are the Claude Code plugin (update
  it with `claude plugin update kmp-agent-skills@kmp-agent-skills`). Continue with local cache and warn user.

To check the installed version in a specific target directory:

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
bash "$KMP_REPO/scripts/check-installed-skills-version.sh" ~/.gemini/skills
```

---

## Phase 2 — Machine-Wide Global Sync

To update all assistant bundles across the current machine:

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
bash "$KMP_REPO/scripts/sync-local-assistant-skills.sh"
```

This synchronizes the latest release to:
- `~/.gemini/config/plugins/kmp-agent-skills/` (Antigravity plugin manifest + skills)
- `~/.gemini/skills/` and `~/.gemini/commands/` (Gemini CLI)
- `~/.agents/skills/` and `~/.agents/commands/` (Cross-client convention)
- `~/.claude/skills/` and `~/.claude/commands/` (Claude Code), skipped when the kmp-agent-skills
  Claude Code plugin is installed; update the plugin with `claude plugin update kmp-agent-skills@kmp-agent-skills`
- `~/.codex/skills/` (Codex CLI)

Dry-run preview:
```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
bash "$KMP_REPO/scripts/sync-local-assistant-skills.sh" --dry-run
```

---

## Phase 3 — Consumer Project Update

When working inside a consumer project that vendors `.agents/skills`:

1. **Deploy latest skills**:
   ```bash
   for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
   bash "$KMP_REPO/scripts/update-consumer-skills.sh" --agent-dir .agents/skills
   ```
2. **Regenerate lockfile**:
   ```bash
   python3 .agents/skills/kmp-project-docs-maintainer/scripts/generate_skills_lock.py --project .
   ```
3. **Verify lockfile consistency**:
   ```bash
   python3 .agents/skills/kmp-project-docs-maintainer/scripts/check_skills_lock.py --project .
   ```

---

## Phase 4 — Post-Update Verification

After synchronizing or deploying updates:

1. **Run Project Architecture Audit**:
   ```bash
   for KMP_SKILLS in "${CLAUDE_PLUGIN_ROOT}/skills" skills .agents/skills ~/.agents/skills ~/.claude/skills; do [ -d "$KMP_SKILLS/kmp-audit" ] && break; done
   python3 "$KMP_SKILLS/kmp-audit/scripts/audit_project.py" .
   ```
2. **Verify Zero Smell Regressions**:
   Ensure no new architecture violations were introduced and recheck baseline freshness.

---

## Common Anti-Patterns

| Mistake | Fix |
|---|---|
| Updating `.agents/skills/` without updating `.agents/skills.lock` | Always run `generate_skills_lock.py` immediately after `update-consumer-skills.sh` to keep the dependency lockfile consistent. |
| Manually copying individual skill files into consumer repos | Always use `update-consumer-skills.sh` or `sync-local-assistant-skills.sh` to preserve version markers and atomic directory states. |
| Overwriting project-specific custom skills inside `.agents/skills/` | Ensure project-owned skills reside in project-declared namespaces rather than colliding with upstream `kmp-*` skill names. |
| Skipping post-update architecture audits | Run `audit_project.py` after updates to catch newly introduced architecture rules or deprecations. |

---

## Testing

The scripts this skill drives are covered by pytest suites in the kmp-agent-skills repo:
- `tests/test_sync_local_assistant_skills.py`: dry-run safety, directory targeting, plugin-aware `~/.claude` skip.
- `tests/test_check_updates.py`: exit codes 0, 1 and 2 against mocked git output, and the plugin (non-git) case.
- `tests/test_update_consumer_skills.py`: consumer deployment, pruning, and the version marker, against temp directories.

```bash
python3 -m pytest tests/test_sync_local_assistant_skills.py tests/test_check_updates.py tests/test_update_consumer_skills.py -q
```

---

## Output Style

When executing `/kmp-update` or reporting update status:
1. State current active version vs. latest upstream version.
2. List all updated runtime targets in a compact bulleted list.
3. Print post-update audit results (clean / findings count).

---

## Related Skills

- `kmp-audit` — inspects codebases for architectural smells after skills updates
- `kmp-project-docs-maintainer` — regenerates lockfiles and validates documentation parity
- `kmp-release` — handles automated versioning and upstream release tags
- `kmp-openrewrite` — handles automated codebase code and dependency migrations

---

## Changelog

| Date | Version | Description |
|---|---|---|
| 2026-10-09 | 3.3.0 | Scripts resolve from the Claude Code plugin or a kmp-agent-skills checkout instead of the current directory; the audit runs from `kmp-audit`'s real path; notes that the sync skips `~/.claude` when the plugin is installed; Testing lists the real pytest suites. |
| 2026-09-18 | 3.0.14 | Initial release of `kmp-update` skill, bridging `/kmp-update` slash command support for Antigravity and unified upstream sync workflows. |
