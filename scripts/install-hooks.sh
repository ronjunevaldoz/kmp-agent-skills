#!/usr/bin/env bash
# Installs KMP Agent Skills hooks into the consumer project's .git/hooks/.
#
# Run from the ROOT of the project you want to protect (not from this repo):
#   bash path/to/kmp-agent-skills/scripts/install-hooks.sh
#
# Or, if you've copied/symlinked the skills repo into your project:
#   bash skills/scripts/install-hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR/../hooks"
GIT_HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"

if [[ ! -d "$GIT_HOOKS_DIR" ]]; then
  echo "❌  .git/hooks not found. Run this script from inside a git repository." >&2
  exit 1
fi

install_hook() {
  local src="$HOOKS_DIR/$1"
  local dst="$GIT_HOOKS_DIR/$2"

  if [[ ! -f "$src" ]]; then
    echo "⚠️   $src not found — skipping"
    return
  fi

  ln -sf "$src" "$dst"
  chmod +x "$src"
  echo "✅  $2 → $src"
}

echo ""
echo "Installing KMP Agent Skills hooks..."
echo ""

install_hook "pre-commit-audit.sh"       "pre-commit"
install_hook "validate-architecture.sh"  "post-rewrite"
install_hook "commit-msg"               "commit-msg"
install_hook "pre-push"                 "pre-push"


echo ""
echo "check-skill-freshness.sh is a manual/CI check — not installed as a git hook."
echo "Run it directly:  bash $HOOKS_DIR/check-skill-freshness.sh"
echo ""
echo "Done. Hooks are active for this repo."
