---
name: kmp-heal-docs
description: Self-heal project documentation sitemap (docs/README.md), verify link hygiene, and delete finished task plans.
---

# Self-Heal Project Documentation

Run the self-healing documentation engine across the project:

```bash
for KMP_SKILLS in "${CLAUDE_PLUGIN_ROOT}/skills" skills .agents/skills ~/.agents/skills ~/.claude/skills; do [ -d "$KMP_SKILLS/kmp-project-docs-maintainer" ] && break; done
python3 "$KMP_SKILLS/kmp-project-docs-maintainer/scripts/heal_docs.py"
```

This command:
1. Rebuilds the high-density sitemap table in `docs/README.md`.
2. Deletes finished tasks (`-done` or every box checked) from `docs/tasks/<parent>/` and lists any
   file that still cites them, so you can fix those links. Git history keeps the old plans.
3. Verifies zero broken relative links.
4. Prevents AI agents from performing expensive recursive scans.
