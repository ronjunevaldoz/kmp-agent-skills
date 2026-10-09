---
name: kmp-doctor
description: Comprehensive project health doctor — heals docs sitemaps, git hooks, script permissions, and .agents/skills.lock.
---

# /kmp-doctor $ARGUMENTS

Run the project health doctor to audit and self-heal the repository:

```bash
for KMP_SKILLS in "${CLAUDE_PLUGIN_ROOT}/skills" skills .agents/skills ~/.agents/skills ~/.claude/skills; do [ -d "$KMP_SKILLS/kmp-project-docs-maintainer" ] && break; done
python3 "$KMP_SKILLS/kmp-project-docs-maintainer/scripts/heal_project.py"
```

## What it Heals:
1. **Documentation**: Generates high-density `docs/README.md` sitemap table and deletes completed tasks.
2. **Git Hooks**: Installs and syncs `.git/hooks/pre-commit` from `hooks/`.
3. **Executable Permissions**: Ensures `chmod +x` across all `scripts/`, `tools/`, and `hooks/`.
4. **Skills Lockfile**: Regenerates `.agents/skills.lock` with upstream version provenance.
