# /kmp-update-skills $ARGUMENTS

Update `kmp-agent-skills` to the latest release across global assistant bundles or consumer projects.

---

## Default: Global Machine-Wide Update (Recommended)

When run without arguments, updates global AI assistant bundles on this machine (`~/.claude/skills`, `~/.gemini/skills`, `~/.codex/skills`, `~/.agents/skills`):

```bash
bash scripts/sync-local-assistant-skills.sh || bash ~/.agents/skills/scripts/sync-local-assistant-skills.sh
```

---

## Project-Level Update (When --project is passed)

If `$ARGUMENTS` specifies a project path (e.g. `/kmp-update-skills --project .`), updates the project's `.agents/skills/` and regenerates `.agents/skills.lock`:

```bash
bash scripts/update-consumer-skills.sh --agent-dir .agents/skills
python3 .agents/skills/kmp-project-docs-maintainer/scripts/generate_skills_lock.py --project . || python3 skills/kmp-project-docs-maintainer/scripts/generate_skills_lock.py --project .
```

---

## Post-Update Verification

Verify the active version:

```bash
bash scripts/check-installed-skills-version.sh ~/.gemini/skills
```
