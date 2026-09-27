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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUDIT_SCRIPT="$REPO_ROOT/skills/kmp-audit/scripts/audit_project.py"

# Optional overrides for testability
MODIFIED_FILE="${1:-}"
PROJECT_ROOT="${2:-${CLAUDE_PROJECT_DIR:-$REPO_ROOT}}"
# Claude Code sends hook input as JSON on stdin (tool_input.file_path); the positional
# argument is for tests and manual runs. select() keeps a never-closed stdin from hanging.
if [[ -z "$MODIFIED_FILE" && ! -t 0 ]]; then
  MODIFIED_FILE="$(python3 -c 'import json,select,sys
r, _, _ = select.select([sys.stdin], [], [], 1)
print((json.load(sys.stdin).get("tool_input") or {}).get("file_path", "") if r else "")' 2>/dev/null || true)"
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

python3 "$AUDIT_SCRIPT" "$PROJECT_ROOT"
