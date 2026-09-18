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
  last-updated: '2026-09-18'
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
# 1. Check if updates exist
python3 scripts/check_updates.py

# 2. Sync all local assistant skill runtimes
bash scripts/sync-local-assistant-skills.sh
```

In Antigravity, slash commands are populated directly by active skills. Invoking `/kmp-update` in the chat canvas triggers this runbook.

---

## Phase 1 — Drift & Upstream Check

To verify if local skills are current relative to upstream:

```bash
python3 scripts/check_updates.py
```

- **Exit 0**: Skills are up to date.
- **Exit 1**: Updates are available. Inspect the list of changed skills and commits.
- **Exit 2**: Offline or unable to reach remote. Continue with local cache and warn user.

To check the installed version in a specific target directory:

```bash
bash scripts/check-installed-skills-version.sh ~/.gemini/skills
```

---

## Phase 2 — Machine-Wide Global Sync

To update all assistant bundles across the current machine:

```bash
bash scripts/sync-local-assistant-skills.sh
```

This synchronizes the latest release to:
- `~/.gemini/config/plugins/kmp-agent-skills/` (Antigravity plugin manifest + skills)
- `~/.gemini/skills/` and `~/.gemini/commands/` (Gemini CLI)
- `~/.agents/skills/` and `~/.agents/commands/` (Cross-client convention)
- `~/.claude/skills/` and `~/.claude/commands/` (Claude Code)
- `~/.codex/skills/` (Codex CLI)

Dry-run preview:
```bash
bash scripts/sync-local-assistant-skills.sh --dry-run
```

---

## Phase 3 — Consumer Project Update

When working inside a consumer project that vendors `.agents/skills`:

1. **Deploy latest skills**:
   ```bash
   bash scripts/update-consumer-skills.sh --agent-dir .agents/skills
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
   python3 scripts/audit_project.py .
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

Validate update workflows and sync script reliability using unit test suites:
- Run `@Test` cases in `tests/test_sync_local_assistant_skills.py` to verify dry-run safety and directory targeting.
- Execute `runTest` harness in `tests/test_check_updates.py` to confirm exit codes (0, 1, 2) against mocked remote git states.
- Use `FakeDirectoryFixture` when validating consumer skills deployment and lockfile verification in isolation.

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
| 2026-09-18 | 3.0.14 | Initial release of `kmp-update` skill, bridging `/kmp-update` slash command support for Antigravity and unified upstream sync workflows. |
