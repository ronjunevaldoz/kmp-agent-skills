#!/usr/bin/env bash
# Warns when a skill's last-updated date is more than ~6 months old.
# Run manually or as a scheduled CI check — not a blocking hook.
# Usage: ./hooks/check-skill-freshness.sh [skills-dir]
#   skills-dir  Optional override for the skills directory (default: <repo-root>/skills).
#               Used by tests to point at a temp directory without touching the real repo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="${1:-$REPO_ROOT/skills}"

THRESHOLD_DAYS=182  # 6 months — keep in sync with STALE_MONTHS in scripts/scan_skill_issues.py
TODAY=$(date +%s)
STALE_COUNT=0

# nullglob: if no SKILL.md files exist the loop body is never entered
shopt -s nullglob

for skill_md in "$SKILLS_DIR"/*/SKILL.md; do
  skill_name=$(basename "$(dirname "$skill_md")")
  last_updated=$(grep "last-updated:" "$skill_md" | sed "s/.*last-updated: *'//" | sed "s/'.*//") || true

  if [[ -z "$last_updated" ]]; then
    echo "WARN: $skill_name — no last-updated date found"
    continue
  fi

  skill_ts=$(date -j -f "%Y-%m-%d" "$last_updated" +%s 2>/dev/null || date -d "$last_updated" +%s 2>/dev/null || echo "0")
  if [[ "$skill_ts" -eq 0 ]]; then
    echo "WARN: $skill_name — could not parse date: $last_updated"
    continue
  fi

  age_days=$(( (TODAY - skill_ts) / 86400 ))
  if [[ $age_days -gt $THRESHOLD_DAYS ]]; then
    echo "STALE ($age_days days): $skill_name — last updated $last_updated"
    STALE_COUNT=$((STALE_COUNT + 1))
  fi
done

if [[ $STALE_COUNT -eq 0 ]]; then
  echo "OK: all skills updated within the last $THRESHOLD_DAYS days"
  exit 0
else
  echo ""
  echo "$STALE_COUNT skill(s) may need a freshness review."
  exit 1
fi
