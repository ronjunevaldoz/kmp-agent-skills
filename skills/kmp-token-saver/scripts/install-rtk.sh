#!/usr/bin/env bash
# install-rtk.sh — install the RTK binary (safe, local package install) and preview
# the global hook-wiring step without applying it.
#
# RTK has two install phases with different authorization needs:
#   Phase 1 — `brew install rtk` (macOS/Linux) or `winget install rtk-ai.rtk` (Windows):
#             a normal local package install, no Claude Code config changes.
#             Safe to run directly.
#   Phase 2 — `rtk init -g`: patches global `~/.claude/settings.json` and
#             `~/.claude/CLAUDE.md` to wire a PreToolUse hook into every future
#             session. This is a persistent, global change — it needs the user's
#             confirmation of the *specific* diff, not a generic "go ahead."
#
# This script only does Phase 1, then runs `rtk init -g --dry-run` to print the
# exact diff Phase 2 would make. It never applies Phase 2 itself — you run
# `rtk init -g` yourself after reviewing the preview.

set -euo pipefail

RTK=rtk

if command -v rtk &>/dev/null; then
  echo "  ✅  rtk already installed ($(rtk --version 2>/dev/null || echo 'version unknown')) — skipping install."
elif command -v brew &>/dev/null; then
  echo "Installing rtk via brew (local package install, no config changes)..."
  brew install rtk
  echo "  ✅  Installed."
elif command -v winget &>/dev/null; then
  echo "Installing rtk via winget (official rtk-ai.rtk package, no Claude Code config changes)..."
  winget install --id rtk-ai.rtk --exact --source winget --disable-interactivity
  # winget links rtk.exe into WinGet\Links, which a shell started before the install
  # may not have on PATH yet.
  if ! command -v rtk &>/dev/null && [[ -n "${LOCALAPPDATA:-}" ]] && command -v cygpath &>/dev/null; then
    RTK="$(cygpath -u "$LOCALAPPDATA")/Microsoft/WinGet/Links/rtk.exe"
    echo "  (open a new terminal to get rtk on PATH)"
  fi
  echo "  ✅  Installed."
else
  echo "  ❌  Neither Homebrew nor winget found. Install RTK with 'brew install rtk' (macOS/Linux)" >&2
  echo "      or 'winget install rtk-ai.rtk' (Windows); see https://github.com/rtk-ai/rtk for other options." >&2
  exit 1
fi

echo ""
echo "Previewing the global hook-wiring step (not applying it)..."
echo ""
"$RTK" init -g --dry-run || true

cat <<'EOF'

That preview shows exactly what `rtk init -g` would change in
~/.claude/settings.json and ~/.claude/CLAUDE.md. This script does not apply it —
review the diff above, then run it yourself if you want the hook active:

  rtk init -g              # hook + ~/.claude/RTK.md, referenced from CLAUDE.md
  rtk init -g --hook-only  # just the settings.json hook

The hook only affects Bash commands in sessions started after that completes; it
does not apply retroactively to the current session.
EOF
