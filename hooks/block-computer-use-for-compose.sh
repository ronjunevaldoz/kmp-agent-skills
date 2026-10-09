#!/usr/bin/env bash
# PreToolUse hook: blocks computer-use / manual-app-driving tool calls when the
# current project is a Compose Multiplatform / KMP project, where Roborazzi +
# runComposeUiTest already give a deterministic, CI-committable verification
# path. Wire this via a PreToolUse matcher on "mcp__computer-use__.*" in
# settings.json — the matcher does the tool-name filtering; this script only
# decides whether *this project* qualifies for the block.
#
# Usage: block-computer-use-for-compose.sh [project-root]
#   Exit 2 blocks the tool call (Claude Code shows stderr to the agent).
#   Exit 0 allows it (non-Compose project, or none detected).

set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"

is_compose_project() {
  find "$PROJECT_ROOT" \
    -path "*/build" -prune -o \
    -path "*/.gradle" -prune -o \
    \( -name "*.gradle.kts" -o -name "libs.versions.toml" \) -print0 \
    2>/dev/null \
  | xargs -0 grep -lE "org\.jetbrains\.compose|compose-multiplatform|jetbrains\.androidx\.compose" 2>/dev/null \
  | head -1 \
  | grep -q .
}

if is_compose_project; then
  cat >&2 <<'EOF'
Blocked: computer-use is not the verification path for this Compose Multiplatform
project. Use the kmp-roborazzi skill instead:
  - runComposeUiTest interaction tests (commonTest) for behavior
  - captureRoboImage Roborazzi goldens (jvmTest) for visual verification
Both are deterministic and CI-committable; computer-use screenshots are neither.
Reserve computer-use for non-Compose, non-KMP contexts.
EOF
  exit 2
fi

exit 0
