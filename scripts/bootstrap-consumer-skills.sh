#!/usr/bin/env bash
# bootstrap-consumer-skills.sh — auto-populates a MISSING .agents/skills/ deploy in a
# consumer project, for a project that gitignores the deployed skills payload and
# relies on this hook to fill it in fresh on first session (new clone, new teammate,
# CI runner).
#
# Does nothing if the target already has content — this only bootstraps a genuinely
# empty/missing deploy, it never overwrites or refreshes an existing one. Refreshing
# an already-deployed copy is /kmp-update-skills's job, on purpose: an existing deploy
# might carry state this hook has no business silently rewriting.
#
# Never installs commands/ (matches update-consumer-skills.sh's own default — commands
# execute shell operations and require explicit human review, not an automated hook).
#
# Wire into the host assistant's session-start hook (see kmp-setup-hooks.md Option I).
# Non-blocking by design — a SessionStart hook must never fail the session, so this
# always exits 0 regardless of what happened.
#
# Usage:
#   bash scripts/bootstrap-consumer-skills.sh [target-dir]
#   target-dir defaults to .agents/skills (project-scoped — this is for a project's
#   own gitignored deploy, unlike check-installed-skills-version.sh which defaults to
#   the global ~/.agents/skills).

set -uo pipefail

TARGET="${1:-.agents/skills}"
REPO="ronjunevaldoz/kmp-agent-skills"

# Already populated — nothing to bootstrap.
if [[ -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
  exit 0
fi

echo "⏳  $TARGET is empty or missing — bootstrapping $REPO..." >&2

# Fast path: a local kmp-agent-skills clone is already configured on this machine
# (same env vars update-consumer-skills.sh's own auto-detect already checks).
SOURCE="${KMP_AGENT_SKILLS_SOURCE:-${KMM_AGENT_SKILLS_SOURCE:-}}"
if [[ -n "$SOURCE" ]] && [[ -d "$SOURCE/scripts" ]]; then
  bash "$SOURCE/scripts/update-consumer-skills.sh" --source "$SOURCE" --agent-dir "$TARGET" >&2
  echo "✅  Bootstrapped $TARGET from $SOURCE" >&2
  exit 0
fi

# Portable fallback: no local clone configured on this machine, pull over the
# network via the real skills.sh CLI. Requires npx (Node) on PATH — if that's
# unavailable this silently no-ops, same as any other non-blocking SessionStart
# hook; /kmp-update-skills or a manual `npx skills add` stays available as an
# explicit fallback either way.
if command -v npx >/dev/null 2>&1; then
  npx --yes skills add "$REPO" >&2 || echo "⚠️  npx skills add failed — bootstrap skipped, try it manually." >&2
else
  echo "⚠️  No local \$KMP_AGENT_SKILLS_SOURCE and no npx on PATH — bootstrap skipped." >&2
  echo "   Run '/kmp-update-skills' or 'npx skills add $REPO' manually." >&2
fi

exit 0
