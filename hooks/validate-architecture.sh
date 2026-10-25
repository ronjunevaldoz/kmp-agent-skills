#!/usr/bin/env bash
# Runs the architecture audit on the file an edit just changed.
# Claude Code invokes this as a PostToolUse hook on Edit/Write.
# Exits 0 (clean, skipped or timed out) or 1 (findings) — Claude Code surfaces failures inline.
#
# Usage: validate-architecture.sh [modified-file] [project-root]
#   modified-file  Path of the file that was just edited (optional, default: tool_input.file_path
#                  from the hook's stdin). Only .kt/.kts/.md files are audited; with no file the
#                  hook does nothing, since a whole-project audit is too slow to run per edit.
#   project-root   Gradle project the file belongs to (optional, default: $CLAUDE_PROJECT_DIR,
#                  else repo root). Useful for tests that need to point at a clean temp project.
#
# Bounded by design: only the edited file is audited, the audit stops itself after
# KMP_ARCH_HOOK_TIMEOUT seconds (default 20) so no process outlives a killed hook, and a
# per-project lock skips the run while an earlier one is still going.
#
# Turn it off with KMP_ARCH_HOOK_DISABLE=1, or for one project by creating
# <project>/.claude/kmp-arch-hook-disabled.

set -euo pipefail

case "${KMP_ARCH_HOOK_DISABLE:-}" in
  1|true|yes|on) exit 0 ;;
esac

# On Windows, python3 can be the Microsoft Store stub, which only prints an install hint.
PYTHON=python3
"$PYTHON" -c '' 2>/dev/null || PYTHON=python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUDIT_SCRIPT="$REPO_ROOT/skills/kmp-audit/scripts/audit_project.py"
TIMEOUT="${KMP_ARCH_HOOK_TIMEOUT:-20}"

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

if [[ -f "$PROJECT_ROOT/.claude/kmp-arch-hook-disabled" ]]; then
  exit 0
fi

# Installed as a plugin this hook fires in every project — only Gradle projects get audited.
if [[ ! -f "$PROJECT_ROOT/settings.gradle.kts" && ! -f "$PROJECT_ROOT/settings.gradle" ]]; then
  exit 0
fi

case "$MODIFIED_FILE" in
  *.kt|*.kts|*.md) ;;
  *) exit 0 ;;
esac

if [[ ! -f "$AUDIT_SCRIPT" ]]; then
  echo "audit_project.py not found at $AUDIT_SCRIPT" >&2
  exit 1
fi

status=0
"$PYTHON" "$AUDIT_SCRIPT" "$PROJECT_ROOT" --files "$MODIFIED_FILE" --timeout "$TIMEOUT" --lock || status=$?
if [[ "$status" -eq 124 ]]; then
  echo "validate-architecture: audit of $MODIFIED_FILE exceeded ${TIMEOUT}s and was stopped" >&2
  exit 0
fi
exit "$status"
