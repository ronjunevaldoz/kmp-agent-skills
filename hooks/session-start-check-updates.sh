#!/usr/bin/env bash
# SessionStart hook: warns the agent up front when this repo's skills are behind
# origin/main, instead of relying on a maintainer to remember to run /check-updates.
# Non-blocking by design — a SessionStart hook must never fail the session, so this
# always exits 0 regardless of what check_updates.py reports.
#
# Wire into the host assistant's session-start hook (see kmp-setup-hooks.md).
# Only meaningful when run from a clone of kmp-agent-skills itself (checks against
# this repo's own origin/main) — not applicable to a deployed skills/ copy in a
# consumer project.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 "$REPO_ROOT/scripts/check_updates.py"
exit 0
