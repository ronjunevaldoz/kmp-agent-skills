#!/usr/bin/env bash
# Pre-commit hook: runs the architecture audit before allowing a commit.
# Install: ln -sf ../../hooks/pre-commit-audit.sh .git/hooks/pre-commit
# Or configure as a Claude Code PreToolUse hook on Bash(git commit).

set -euo pipefail

# On Windows, python3 can be the Microsoft Store stub, which only prints an install hint.
PYTHON=python3
"$PYTHON" -c '' 2>/dev/null || PYTHON=python

# Deriving REPO_ROOT from ${BASH_SOURCE[0]} breaks under the real install path:
# scripts/install-hooks.sh symlinks this file to .git/hooks/pre-commit, and git
# invokes it via that .git/hooks/ path — dirname("$REPO_ROOT/.git/hooks/pre-commit")
# + cd ".." lands on "$REPO_ROOT/.git", one level short of the actual repo root.
# Verified live: this silently no-op'd both checks below for every commit made
# through the real symlinked hook, undetected because a silent skip looks
# identical to "ran clean". `git rev-parse --show-toplevel` is invocation-path
# independent — always the real working tree root, symlink or not.
REPO_ROOT="$(git rev-parse --show-toplevel)"

# kmp-audit deploys to different paths depending on whether this is the skills
# repo itself (skills/) or a consumer project (.claude/skills/, .agents/skills/,
# .codex/skills/, .gemini/skills/) — try each in order, first one wins.
find_kmp_audit_dir() {
  for candidate in \
    "$REPO_ROOT/skills/kmp-audit/scripts" \
    "$REPO_ROOT/.claude/skills/kmp-audit/scripts" \
    "$REPO_ROOT/.agents/skills/kmp-audit/scripts" \
    "$REPO_ROOT/.codex/skills/kmp-audit/scripts" \
    "$REPO_ROOT/.gemini/skills/kmp-audit/scripts"
  do
    if [[ -d "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}
KMP_AUDIT_DIR="$(find_kmp_audit_dir || true)"

# tests/ was split from one monolithic test_skill_scripts.py into one file per
# script (tests/test_<script-name>.py, plus a shared tests/_helpers.py) — match any
# test file, not one hardcoded name.
TEST_FILE_PATTERN='^tests/test_.*\.py$'

STAGED=$(git diff --cached --name-only)

# --- Check 1: architecture audit on Kotlin files ---
STAGED_KT=$(echo "$STAGED" | grep -E '\.(kt|kts)$' || true)
if [[ -n "$STAGED_KT" ]] && [[ -n "$KMP_AUDIT_DIR" ]]; then
  echo "Running architecture audit on staged Kotlin files..."
  "$PYTHON" "$KMP_AUDIT_DIR/audit_project.py" "$REPO_ROOT"
  STATUS=$?
  if [[ $STATUS -ne 0 ]]; then
    echo ""
    echo "Commit blocked: architecture audit found issues."
    echo "Run: python3 $KMP_AUDIT_DIR/audit_project.py ."
    echo "Or: /run-audit to see findings with remediation steps."
    exit 1
  fi
fi

# --- Check 1b: docs hygiene on any staged docs/ or root-level doc changes ---
# Found real: a consumer project's own docs grew past 1000+ lines with nothing
# catching it, because this hook only ever audited .kt files — docs-only commits
# never ran any check at all. audit_skills_repo.py --docs-hygiene-only is the
# script that actually owns line-cap/staleness/naming checks for docs/, distinct
# from audit_project.py above (Kotlin/Compose code smells).
STAGED_DOCS=$(echo "$STAGED" | grep -E '(^docs/.*\.md$|^[A-Z_]+\.md$)' || true)
if [[ -n "$STAGED_DOCS" ]] && [[ -n "$KMP_AUDIT_DIR" ]]; then
  echo "Running docs hygiene check on staged docs..."
  if ! "$PYTHON" "$KMP_AUDIT_DIR/audit_skills_repo.py" "$REPO_ROOT" --docs-hygiene-only; then
    echo ""
    echo "Commit blocked: docs hygiene found issues (line-cap, naming, orphaned reference doc)."
    echo "Run: python3 $KMP_AUDIT_DIR/audit_skills_repo.py . --docs-hygiene-only"
    exit 1
  fi
fi

# --- Check 2: Python script changes must include test updates ---
STAGED_PY=$(echo "$STAGED" | grep -E '^(scripts/|skills/.*/scripts/).*\.py$' || true)
STAGED_TEST=$(echo "$STAGED" | grep -E "$TEST_FILE_PATTERN" || true)
if [[ -n "$STAGED_PY" ]] && [[ -z "$STAGED_TEST" ]]; then
  echo ""
  echo "Commit blocked: Python scripts changed without updating a tests/test_*.py file"
  echo ""
  echo "Changed scripts:"
  echo "$STAGED_PY" | sed 's/^/  /'
  echo ""
  echo "Add or update the matching tests/test_<script-name>.py then re-stage it before committing."
  echo "Pattern: see existing test files under tests/ for examples."
  exit 1
fi

exit 0
