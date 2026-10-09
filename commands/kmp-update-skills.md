---
description: "Update `kmp-agent-skills` to the latest release across global assistant bundles or consumer projects."
argument-hint: "[arguments]"
---

# /kmp-update-skills $ARGUMENTS

Update `kmp-agent-skills` to the latest release across global assistant bundles or consumer projects.

---

## Default: Global Machine-Wide Update (Recommended)

When run without arguments, updates global AI assistant bundles on this machine (`~/.claude/skills`, `~/.gemini/skills`, `~/.codex/skills`, `~/.agents/skills`). With the Claude Code plugin installed, `~/.claude` is skipped: update the plugin itself with `claude plugin update kmp-agent-skills@kmp-agent-skills` and restart Claude Code.

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
bash "$KMP_REPO/scripts/sync-local-assistant-skills.sh"
```

If no kmp-agent-skills checkout or plugin is found, clone the repo or set `KMP_AGENT_SKILLS_SOURCE` to an existing clone.

---

## Project-Level Update (When --project is passed)

If `$ARGUMENTS` specifies a project path (e.g. `/kmp-update-skills --project .`), updates the project's `.agents/skills/` and regenerates `.agents/skills.lock`:

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
bash "$KMP_REPO/scripts/update-consumer-skills.sh" --agent-dir .agents/skills
python3 "$KMP_REPO/skills/kmp-project-docs-maintainer/scripts/generate_skills_lock.py" --project .
```

---

## Post-Update Verification

Verify the active version:

```bash
for KMP_REPO in "${CLAUDE_PLUGIN_ROOT}" "${KMP_AGENT_SKILLS_SOURCE}" . ../kmp-agent-skills ~/dev/kmp-agent-skills ~/Documents/kmp-agent-skills; do [ -f "$KMP_REPO/skills.json" ] && break; done
bash "$KMP_REPO/scripts/check-installed-skills-version.sh" ~/.gemini/skills
```
