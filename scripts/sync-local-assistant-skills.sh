#!/usr/bin/env bash
# sync-local-assistant-skills.sh — sync the latest kmp-agent-skills release
# into local assistant skill bundles on this machine.
#
# This updates user-level installs:
#   ~/.claude/skills, ~/.claude/commands
#   ~/.codex/skills
#   ~/.gemini/skills
#   ~/.agents/skills, ~/.agents/commands — the cross-client convention
#
# Options:
#   --source PATH      Path to kmp-agent-skills clone (auto-detected if omitted)
#   --skip-commands    Skip synchronizing user-level slash commands (~/.agents/commands, ~/.claude/commands)
#   --dry-run          Show what would change without writing anything

set -euo pipefail

SKILLS_SOURCE=""
SYNC_COMMANDS=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)        SKILLS_SOURCE="$2"; shift 2 ;;
    --skip-commands) SYNC_COMMANDS=false; shift ;;
    --dry-run)       DRY_RUN=true; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

resolve_source() {
  local candidate
  if [[ -n "$SKILLS_SOURCE" ]]; then
    return 0
  fi

  candidate="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  if [[ -f "$candidate/skills.json" ]]; then
    SKILLS_SOURCE="$candidate"
    return 0
  fi
  if [[ -f "../kmp-agent-skills/skills.json" ]]; then
    SKILLS_SOURCE="$(cd ../kmp-agent-skills && pwd)"
    return 0
  fi
  if [[ -f "$HOME/dev/kmp-agent-skills/skills.json" ]]; then
    SKILLS_SOURCE="$HOME/dev/kmp-agent-skills"
    return 0
  fi
  if [[ -f "$HOME/Documents/kmp-agent-skills/skills.json" ]]; then
    SKILLS_SOURCE="$HOME/Documents/kmp-agent-skills"
    return 0
  fi

  echo "❌ Could not find kmp-agent-skills. Pass --source PATH." >&2
  exit 1
}

version_of() {
  python3 - <<'PY' "$1"
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "skills.json"
print(json.loads(p.read_text())["version"])
PY
}

resolve_source

SOURCE_VERSION="$(version_of "$SKILLS_SOURCE")"
TARGETS=(
  "$HOME/.claude/skills"
  "$HOME/.codex/skills"
  "$HOME/.gemini/skills"
  "$HOME/.agents/skills"
)

echo ""
echo "  Skills source : $SKILLS_SOURCE"
echo "  Release       : v$SOURCE_VERSION"
echo "  Targets       :"
for target in "${TARGETS[@]}"; do
  echo "    - $target"
done
if $DRY_RUN; then
  echo "  Mode          : DRY RUN"
fi
echo ""

for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  echo "Syncing $(basename "$(dirname "$target")") skills..."

  if $DRY_RUN; then
    echo "  [dry-run] would mirror $SKILLS_SOURCE/skills/ -> $target/"
    continue
  fi

  if [[ -d "$target" ]] && [[ -n "$(find "$target" -mindepth 1 -maxdepth 1 2>/dev/null | head -1)" ]]; then
    backup_dir="${target}-backup-kmp-agent-skills-$(date +%Y%m%d%H%M%S)"
    cp -a "$target" "$backup_dir"
    echo "  Backed up existing install to $backup_dir"
  fi

  rsync -a --delete --exclude '.git' --exclude '.DS_Store' --exclude '.pytest_cache' \
    --exclude '.kmp-agent-skills-version' \
    "$SKILLS_SOURCE/skills/" "$target/"

  # A global (non-git) install otherwise has no record of what version it's on,
  # making "is this stale?" unanswerable without diffing file contents by hand —
  # the exact pain that motivated adding this marker. Written after rsync and
  # excluded from it above, so --delete never removes it.
  echo "$SOURCE_VERSION" > "$target/.kmp-agent-skills-version"

  echo "  ✅  Synced"
done

if $SYNC_COMMANDS && [[ -d "$SKILLS_SOURCE/commands" ]]; then
  COMMAND_TARGETS=(
    "$HOME/.agents/commands"
    "$HOME/.claude/commands"
  )
  echo ""
  for cmd_target in "${COMMAND_TARGETS[@]}"; do
    mkdir -p "$cmd_target"
    client_name="$(basename "$(dirname "$cmd_target")")"
    echo "Syncing $client_name user-level slash commands..."

    if $DRY_RUN; then
      echo "  [dry-run] would sync consumer commands -> $cmd_target/"
      continue
    fi

    # Sync consumer commands (do not overwrite custom non-kmp commands)
    for cmd_file in "$SKILLS_SOURCE/commands"/kmp-*.md; do
      [[ -f "$cmd_file" ]] || continue
      cp "$cmd_file" "$cmd_target/"
    done
    echo "  ✅  Synced $(ls "$SKILLS_SOURCE/commands"/kmp-*.md | wc -l | tr -d ' ') commands"
  done
fi

echo ""
echo "All local assistant skill bundles now match v$SOURCE_VERSION."
