#!/usr/bin/env bash
# Runs the lightweight architecture audit after any file edit.
# Claude Code invokes this as a PostToolUse hook on Edit/Write.
# Exits 0 (clean) or 1 (findings) — Claude Code surfaces failures inline.
#
# Usage: validate-architecture.sh [modified-file] [project-root]
#   modified-file  Path of the file that was just edited (optional).
#                  Non-.kt/.kts/.md files are skipped immediately.
#   project-root   Directory to audit (optional, default: $CLAUDE_PROJECT_DIR, else repo root).
#                  Useful for tests that need to point at a clean temp project.

set -euo pipefail

# On Windows, python3 can be the Microsoft Store stub, which only prints an install hint.
PYTHON=python3
"$PYTHON" -c '' 2>/dev/null || PYTHON=python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUDIT_SCRIPT="$REPO_ROOT/skills/kmp-audit/scripts/audit_project.py"

# Optional overrides for testability
MODIFIED_FILE="${1:-}"
PROJECT_ROOT="${2:-${CLAUDE_PROJECT_DIR:-$REPO_ROOT}}"
# Claude Code sends hook input as JSON on stdin (tool_input.file_path); the positional
# argument is for tests and manual runs. The 1s thread timeout keeps a never-closed stdin
# from hanging (select() won't do: on Windows it only accepts sockets).
if [[ -z "$MODIFIED_FILE" && ! -t 0 ]]; then
  MODIFIED_FILE="$("$PYTHON" -c 'import json,os,sys,threading
got = []
t = threading.Thread(target=lambda: got.append(sys.stdin.read()), daemon=True)
t.start(); t.join(1)
print((json.loads(got[0]).get("tool_input") or {}).get("file_path", "") if got and got[0].strip() else "", flush=True)
os._exit(0)  # a reader thread still blocked on stdin can abort normal shutdown' 2>/dev/null || true)"
fi

# Installed as a plugin this hook fires in every project — only Gradle projects get audited.
if [[ ! -f "$PROJECT_ROOT/settings.gradle.kts" && ! -f "$PROJECT_ROOT/settings.gradle" ]]; then
  exit 0
fi

# Only run when a Kotlin or build file was modified
if [[ -n "$MODIFIED_FILE" ]]; then
  case "$MODIFIED_FILE" in
    *.kt|*.kts|*.md) ;;
    *) exit 0 ;;
  esac
fi

if [[ ! -f "$AUDIT_SCRIPT" ]]; then
  echo "audit_project.py not found at $AUDIT_SCRIPT" >&2
  exit 1
fi

"$PYTHON" "$AUDIT_SCRIPT" "$PROJECT_ROOT"
