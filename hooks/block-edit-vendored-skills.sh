#!/usr/bin/env bash
# PreToolUse hook: blocks Edit/Write calls that target a deployed skill mirror
# instead of the real source. Deployed copies under .claude/skills/,
# .agents/skills/, .codex/skills/, or .gemini/skills/ are synced FROM a source
# — either this repo's own skills/<name>/SKILL.md (bundled) or a consumer
# project's root skills/<name>/SKILL.md (project-owned custom skill) — and any
# direct edit there is silently overwritten by the next sync, or worse,
# diverges unnoticed until audit_project.py's agent-setup drift check catches
# it after the fact. This hook blocks the edit before it happens.
#
# Wire via a PreToolUse matcher on "Edit|Write" in settings.json — the matcher
# filters by tool; this script only decides whether the target path is a
# deployed mirror.
#
# Usage: block-edit-vendored-skills.sh [target-file-path]   (else read from stdin JSON)
#   Exit 2 blocks the tool call (Claude Code shows stderr to the agent).
#   Exit 0 allows it (not a mirror path, or no path given).

set -euo pipefail

# On Windows, python3 can be the Microsoft Store stub, which only prints an install hint.
PYTHON=python3
"$PYTHON" -c '' 2>/dev/null || PYTHON=python

TARGET="${1:-}"
# Claude Code sends hook input as JSON on stdin (tool_input.file_path); the positional
# argument is for tests and manual runs. The 1s thread timeout keeps a never-closed stdin
# from hanging (select() won't do: on Windows it only accepts sockets).
if [[ -z "$TARGET" && ! -t 0 ]]; then
  TARGET="$("$PYTHON" -c 'import json,os,sys,threading
got = []
t = threading.Thread(target=lambda: got.append(sys.stdin.read()), daemon=True)
t.start(); t.join(1)
print((json.loads(got[0]).get("tool_input") or {}).get("file_path", "") if got and got[0].strip() else "", flush=True)
os._exit(0)  # a reader thread still blocked on stdin can abort normal shutdown' 2>/dev/null || true)"
fi

if [[ -z "$TARGET" ]]; then
  exit 0
fi

if [[ "$TARGET" =~ (^|/)\.claude/skills/ ]] \
  || [[ "$TARGET" =~ (^|/)\.agents/skills/ ]] \
  || [[ "$TARGET" =~ (^|/)\.codex/skills/ ]] \
  || [[ "$TARGET" =~ (^|/)\.gemini/skills/ ]]; then
  cat >&2 <<'EOF'
Blocked: this path is a deployed skill mirror, not the source. Edits here get
silently overwritten by the next sync, or drift unnoticed until an audit
catches it.

Edit the real source instead:
  - Bundled kmp-agent-skills skill: edit upstream at
    github.com/ronjunevaldoz/kmp-agent-skills, then re-sync.
  - Project-owned custom skill: edit this project's own root skills/<name>/SKILL.md,
    then re-sync into the deployed copies.
EOF
  exit 2
fi

exit 0
