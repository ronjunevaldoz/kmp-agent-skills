#!/usr/bin/env bash
# check-installed-skills-version.sh — checks a *globally installed* (non-git)
# kmp-agent-skills bundle against the latest GitHub release, using the
# .kmp-agent-skills-version marker sync-local-assistant-skills.sh writes.
#
# Unlike scripts/check_updates.py (which assumes cwd is a git clone of this
# repo and uses `git rev-list`/`git show`), this works from any machine that
# only has the synced skills/ directory — no git clone required, just curl.
#
# Usage:
#   bash scripts/check-installed-skills-version.sh [target-dir]
#   target-dir defaults to ~/.agents/skills
#
# Exit codes:
#   0 — up to date
#   1 — update available
#   2 — no version marker found, or couldn't reach GitHub

set -euo pipefail

TARGET="${1:-$HOME/.agents/skills}"
REPO="ronjunevaldoz/kmp-agent-skills"
MARKER="$TARGET/.kmp-agent-skills-version"

if [[ ! -f "$MARKER" ]]; then
  echo "⚠️  No version marker at $MARKER"
  echo "   This install predates the version-marker fix, or wasn't created by"
  echo "   sync-local-assistant-skills.sh. Re-run that script to get one."
  exit 2
fi

INSTALLED_VERSION="$(cat "$MARKER")"

LATEST_TAG="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null \
  | grep -m1 '"tag_name"' | sed -E 's/.*"tag_name": *"v?([^"]+)".*/\1/')"

if [[ -z "$LATEST_TAG" ]]; then
  echo "⚠️  Could not reach GitHub to check the latest release — offline, or rate-limited."
  echo "   Installed version: $INSTALLED_VERSION"
  exit 2
fi

echo "Installed: v$INSTALLED_VERSION"
echo "Latest:    v$LATEST_TAG"

if [[ "$INSTALLED_VERSION" == "$LATEST_TAG" ]]; then
  echo "✅  Up to date"
  exit 0
fi

echo "⚠️  Update available — re-run scripts/sync-local-assistant-skills.sh with a fresh clone,"
echo "   or 'npx skills add $REPO' to pull the latest release."
exit 1
