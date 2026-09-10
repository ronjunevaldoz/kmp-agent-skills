#!/usr/bin/env bash
# migrate-kmm-to-kmp.sh — clean up a consumer project after kmp-agent-skills
# v2.0.0 (kotlin-multiplatform-* -> kmp-*) and v2.2.0 (kmp-design-system etc.
# -> kmp-compose-*) — both hard cutovers with no automatic migration.
#
# update-consumer-skills.sh's rsync only cleans files INSIDE a matched target
# dir; it cannot remove an orphaned dir whose source no longer exists under
# that name. Run this once per consumer project to remove the resulting
# stale copies, after your skills source is already on v2.2.0+.
#
# Run from your KMP project root:
#   bash path/to/kmp-agent-skills/scripts/migrate-kmm-to-kmp.sh
#
# Options:
#   --dry-run   Show what would be removed without deleting anything

set -euo pipefail

DRY_RUN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Every known deploy location this collection or another agentskills.io client uses.
AGENT_DIRS=(
  ".claude/skills" ".agents/skills" ".codex/skills" ".gemini/skills"
  ".cursor/skills" ".continue/skills" ".github/copilot/skills"
)

# The 6 skills renamed a second time (v2.0.0 name -> v2.2.0 kmp-compose-* name).
COMPOSE_RENAMES=(
  "kmp-design-system" "kmp-design-system-extended" "kmp-adaptive-layout"
  "kmp-accessibility" "kmp-preview-driven-development" "kmp-graphics-modifiers"
)

removed_count=0
run_or_show() {
  if $DRY_RUN; then
    echo "  [dry-run] would remove: $1"
  else
    rm -rf "$1"
    echo "  removed: $1"
  fi
  removed_count=$((removed_count + 1))
}

echo ""
echo "Scanning for stale pre-v2.2.0 skill copies…"
echo ""

for agent_dir in "${AGENT_DIRS[@]}"; do
  [[ -d "$agent_dir" ]] || continue

  # v1 -> v2: any leftover kotlin-multiplatform-* directory
  for stale in "$agent_dir"/kotlin-multiplatform-*; do
    [[ -d "$stale" ]] || continue
    run_or_show "$stale"
  done

  # v2 -> v3: the 6 skills renamed to kmp-compose-*
  for name in "${COMPOSE_RENAMES[@]}"; do
    stale="$agent_dir/$name"
    [[ -d "$stale" ]] || continue
    run_or_show "$stale"
  done
done

# Old command files: commands/kmm-*.md -> commands/kmp-*.md
for commands_dir in ".agents/commands" ".claude/commands" ".cursor/commands"; do
  [[ -d "$commands_dir" ]] || continue
  for stale in "$commands_dir"/kmm-*.md; do
    [[ -f "$stale" ]] || continue
    run_or_show "$stale"
  done
done

# Version-pin marker: .kmm-skills -> .kmp-skills
if [[ -f ".kmm-skills" ]]; then
  if $DRY_RUN; then
    echo "  [dry-run] would rename: .kmm-skills -> .kmp-skills"
  else
    mv ".kmm-skills" ".kmp-skills"
    echo "  renamed: .kmm-skills -> .kmp-skills"
  fi
  removed_count=$((removed_count + 1))
fi

echo ""
if [[ "$removed_count" -eq 0 ]]; then
  echo "✅  Nothing stale found — already migrated, or nothing was installed pre-v2.2.0."
else
  echo "✅  Migration cleanup done ($removed_count item(s))."
  echo ""
  echo "Next: re-run update-consumer-skills.sh to make sure kmp-compose-* and any"
  echo "new skills are actually deployed (this script only removes stale copies,"
  echo "it does not install anything):"
  echo "  bash .agents/skills/scripts/update-consumer-skills.sh"
  echo ""
  echo "If you installed slash commands, reinstall them under the new kmp-* names:"
  echo "  bash .agents/skills/scripts/update-consumer-skills.sh --install-commands"
fi
