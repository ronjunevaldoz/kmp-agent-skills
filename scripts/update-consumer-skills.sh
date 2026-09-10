#!/usr/bin/env bash
# update-consumer-skills.sh — pull the latest kmp-agent-skills and re-deploy
# to the current consumer project.
#
# Skills (skills/) are copied automatically — they are passive reference docs.
# Commands (commands/) are NOT copied automatically — each file becomes an
# agent-executable slash command and must be reviewed and approved explicitly.
#
# Run from your KMP project root:
#   bash path/to/kmp-agent-skills/scripts/update-consumer-skills.sh
#
# Options:
#   --source PATH        Path to kmp-agent-skills clone (auto-detected if omitted).
#                         Auto-detect checks $KMP_AGENT_SKILLS_SOURCE first (falls back
#                         to the legacy $KMM_AGENT_SKILLS_SOURCE name) — set it once in
#                         your shell profile so every consumer project on this machine
#                         finds the clone without re-prompting.
#   --agent-dir PATH     Destination skills directory (auto-detected if omitted)
#   --commands-dir PATH  Destination for slash commands (default: .agents/commands)
#   --install-commands   List available commands and prompt to install each one
#   --prune-stale        Remove stale bundled kmp-* skill directories (opt-in)
#   --dry-run            Show what would change without writing anything

set -euo pipefail

SKILLS_SOURCE=""
AGENT_DIR=""
COMMANDS_DIR=""
INSTALL_COMMANDS=false
PRUNE_STALE=false
SETUP_AGENTS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)           SKILLS_SOURCE="$2"; shift 2 ;;
    --agent-dir)        AGENT_DIR="$2"; shift 2 ;;
    --commands-dir)     COMMANDS_DIR="$2"; shift 2 ;;
    --install-commands) INSTALL_COMMANDS=true; shift ;;
    --prune-stale)      PRUNE_STALE=true; shift ;;
    --setup-agents)     SETUP_AGENTS=true; shift ;;
    --dry-run)          DRY_RUN=true; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Locate the skills source ──────────────────────────────────────────────────

if [[ -z "$SKILLS_SOURCE" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CANDIDATE="$(cd "$SCRIPT_DIR/.." && pwd)"

  if [[ -n "${KMP_AGENT_SKILLS_SOURCE:-}" && -f "$KMP_AGENT_SKILLS_SOURCE/skills.json" ]]; then
    SKILLS_SOURCE="$KMP_AGENT_SKILLS_SOURCE"
  elif [[ -n "${KMM_AGENT_SKILLS_SOURCE:-}" && -f "$KMM_AGENT_SKILLS_SOURCE/skills.json" ]]; then
    SKILLS_SOURCE="$KMM_AGENT_SKILLS_SOURCE"
  elif [[ -f "$CANDIDATE/skills.json" ]]; then
    SKILLS_SOURCE="$CANDIDATE"
  elif [[ -f "skills/skills.json" ]]; then
    SKILLS_SOURCE="$(cd skills && pwd)"
  elif [[ -f "../kmp-agent-skills/skills.json" ]]; then
    SKILLS_SOURCE="$(cd ../kmp-agent-skills && pwd)"
  elif [[ -f "$HOME/dev/kmp-agent-skills/skills.json" ]]; then
    SKILLS_SOURCE="$HOME/dev/kmp-agent-skills"
  else
    echo "" >&2
    echo "  ❌  Could not find kmp-agent-skills." >&2
    echo "  Pass --source PATH, or set \$KMP_AGENT_SKILLS_SOURCE once in your shell" >&2
    echo "  profile so every consumer project auto-detects it:" >&2
    echo "    export KMP_AGENT_SKILLS_SOURCE=/path/to/your/kmp-agent-skills" >&2
    echo "" >&2
    exit 1
  fi
fi

# ── Detect agent destination ──────────────────────────────────────────────────

if [[ -z "$AGENT_DIR" ]]; then
  AGENT_DIR=".agents/skills"
fi

# Default commands dir mirrors the agent dir's parent (e.g. .agents/commands)
if [[ -z "$COMMANDS_DIR" ]]; then
  AGENT_PARENT="$(dirname "$AGENT_DIR")"
  COMMANDS_DIR="$AGENT_PARENT/commands"
fi

echo ""
echo "  Skills source : $SKILLS_SOURCE"
echo "  Skills target : $AGENT_DIR"
echo "  Commands dir  : $COMMANDS_DIR (manual install only)"
if $DRY_RUN; then echo "  Mode          : DRY RUN"; fi
echo ""

# ── Read current local version ────────────────────────────────────────────────

OLD_VERSION="?"
if command -v python3 &>/dev/null && [[ -f "$SKILLS_SOURCE/skills.json" ]]; then
  OLD_VERSION=$(python3 -c \
    "import json; print(json.load(open('$SKILLS_SOURCE/skills.json'))['version'])" \
    2>/dev/null || echo "?")
fi

# ── Pull latest ───────────────────────────────────────────────────────────────

echo "Checking for updates…"
REMOTE_OK=true
git -C "$SKILLS_SOURCE" fetch origin main --quiet 2>/dev/null || {
  echo "  ⚠️  Could not reach remote — continuing with local skills (v$OLD_VERSION)"
  REMOTE_OK=false
}

BEHIND="0"
if $REMOTE_OK; then
  BEHIND=$(git -C "$SKILLS_SOURCE" rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
fi

if [[ "$BEHIND" == "0" ]]; then
  echo "  ✅  Already up to date (v$OLD_VERSION)"
else
  if $DRY_RUN; then
    echo "  [dry-run] would pull $BEHIND commit(s) from origin/main"
  else
    git -C "$SKILLS_SOURCE" pull origin main --ff-only --quiet
    echo "  ✅  Pulled $BEHIND commit(s) from origin/main"
  fi
fi

NEW_VERSION="?"
if command -v python3 &>/dev/null; then
  NEW_VERSION=$(python3 -c \
    "import json; print(json.load(open('$SKILLS_SOURCE/skills.json'))['version'])" \
    2>/dev/null || echo "?")
fi

echo "  ✅  v$OLD_VERSION → v$NEW_VERSION"
echo ""

# ── Deploy skills (auto — passive reference docs) ─────────────────────────────

# `cp -r` only adds and overwrites. By default, preserve every existing target skill:
# consumer projects may keep skills directly under .agents/skills, and an updater must
# not make a destructive assumption about their ownership. Stale bundled skills can be
# removed deliberately with --prune-stale after reviewing the dry-run output.
# Resolve a skill's deploy target to the real directory to write into. A destination
# that's a symlink — for example a per-skill link into another deployment, a real
# layout found deployed in production, one symlink per skill rather than the whole
# directory — breaks writing to it directly, confirmed by direct reproduction on both
# tools this script uses: BSD/macOS `cp -r` errors "Not a directory" on a directory
# source copied onto a destination whose last path component is a symlink, even though
# the link resolves to a real directory; Apple's `openrsync` (shipped since macOS 15,
# not GPL rsync — `rsync --version` reports "openrsync") reports success and "sent N
# bytes" while silently writing nothing through it. Resolving to the real path first
# and writing there works correctly with every tool tried.
resolve_target() {
  local target="$1"
  if [[ -L "$target" ]]; then
    local link_val resolved
    link_val="$(readlink "$target")"
    if [[ "$link_val" = /* ]]; then
      resolved="$link_val"
    else
      resolved="$(cd "$(dirname "$target")" 2>/dev/null && cd "$(dirname "$link_val")" 2>/dev/null && pwd)/$(basename "$link_val")"
    fi
    if [[ -n "$resolved" && -d "$(dirname "$resolved")" ]]; then
      echo "$resolved"
      return
    fi
    # Broken symlink (target's parent doesn't exist) — remove it and fall through to
    # treating the original path as a plain, not-yet-existing directory.
    rm -f "$target"
  fi
  echo "$target"
}

prune_stale_skills() {
  local target="$1"
  [[ -d "$target" ]] || return 0

  local stale_dir stale_name
  for stale_dir in "$target"/*; do
    [[ -d "$stale_dir" ]] || continue
    [[ -L "$stale_dir" ]] && continue        # symlinked mirror, not a real deployed copy
    stale_name="$(basename "$stale_dir")"

    [[ -d "$SKILLS_SOURCE/skills/$stale_name" ]] && continue   # still shipped upstream
    [[ -d "skills/$stale_name" ]] && continue                  # project-owned custom skill
    # The bundled collection uses the kmp-* namespace. Preserve consumer-owned
    # skills stored directly in the target (for example, Awaken's awake-* skills).
    [[ "$stale_name" == kmp-* ]] || continue

    if $DRY_RUN; then
      echo "  [dry-run] would remove stale skill: $target/$stale_name"
    else
      rm -rf "$stale_dir"
      echo "  🗑   removed stale skill (no longer shipped upstream): $stale_name"
    fi
  done
}

echo "Deploying skills to ${AGENT_DIR}…"

if $DRY_RUN; then
  # `HEAD@{1}` needs a reflog entry, which a fresh clone, a shallow clone, or a CI
  # checkout doesn't have — and under `set -o pipefail` that git failure propagates
  # through the pipeline and kills the whole script mid-run. Fall back to 0 instead:
  # a dry-run's change count is informational, never worth aborting the run over.
  CHANGED=$(git -C "$SKILLS_SOURCE" diff "HEAD@{1}..HEAD" --name-only -- skills/ 2>/dev/null | wc -l | tr -d ' ' || echo 0)
  [[ -n "$CHANGED" ]] || CHANGED=0
  echo "  [dry-run] would copy $CHANGED changed skill file(s) → $AGENT_DIR/"
  $PRUNE_STALE && prune_stale_skills "$AGENT_DIR"
else
  for skill_src in "$SKILLS_SOURCE"/skills/*/; do
    skill_name="$(basename "$skill_src")"
    resolved_target="$(resolve_target "$AGENT_DIR/$skill_name")"
    mkdir -p "$(dirname "$resolved_target")"
    rm -rf "$resolved_target"
    cp -r "$skill_src" "$resolved_target"
  done
  if $PRUNE_STALE; then
    prune_stale_skills "$AGENT_DIR"
  else
    echo "  ℹ️   Preserved existing skills (use --prune-stale to remove stale kmp-* skills)"
  fi
  # Version marker — read by scripts/check-installed-skills-version.sh, which
  # commands/kmp-setup-hooks.md wires as the Option E SessionStart hook for exactly
  # this deploy path. Without it that hook reports "no version marker" on every
  # session and the stale-skills check silently never runs.
  echo "$NEW_VERSION" > "$AGENT_DIR/.kmp-agent-skills-version"
  echo "  ✅  Skills deployed (v$NEW_VERSION)"
fi

# ── Deploy project-owned custom skills (auto — source of truth at ./skills) ──

echo ""
echo "Syncing project-owned custom skills…"

CUSTOM_SKILLS_COUNT=0
if [[ -d "skills" ]]; then
  for skill_dir in skills/*; do
    # A symlink here is a mirrored bundled skill (e.g. skills/<name> -> .agents/skills/<name>),
    # not a project-owned one — skip it before the collision check below, otherwise every
    # bundled skill mirrored this way falsely reports as "colliding with itself".
    [[ -L "$skill_dir" ]] && continue
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    [[ "$skill_name" == "README.md" ]] && continue
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    CUSTOM_SKILLS_COUNT=$((CUSTOM_SKILLS_COUNT + 1))

    if [[ -d "$SKILLS_SOURCE/skills/$skill_name" ]]; then
      echo "  ❌  project-owned skill '$skill_name' collides with a bundled kmp-agent-skills skill."
      echo "      Rename the project-owned skill (for example, make it app-specific) and run again."
      exit 1
    fi

    target="$AGENT_DIR/$skill_name"
    if $DRY_RUN; then
      echo "  [dry-run] would sync $skill_dir/ → $target/"
      continue
    fi

    # resolve_target: same symlinked-destination problem as the bundled-skill deploy
    # above applies here too — write into the real resolved directory, never through
    # a per-skill symlink.
    resolved_target="$(resolve_target "$target")"
    mkdir -p "$resolved_target"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete "$skill_dir/" "$resolved_target/"
    else
      rm -rf "$resolved_target"
      mkdir -p "$(dirname "$resolved_target")"
      cp -R "$skill_dir" "$resolved_target"
    fi
    echo "  ✅  project skill synced: $skill_name"

  done
fi

if [[ "$CUSTOM_SKILLS_COUNT" == "0" ]]; then
  echo "  ℹ️   No project-owned custom skills found under ./skills/"
fi

# ── Changelog excerpt ─────────────────────────────────────────────────────────

CHANGELOG="$SKILLS_SOURCE/CHANGELOG.md"
if [[ -f "$CHANGELOG" ]]; then
  echo ""
  echo "  What changed:"
  awk "/^## \[v$NEW_VERSION\]/{found=1} found && /^---$/{exit} found{print \"    \" \$0}" \
    "$CHANGELOG" | head -20
fi

# ── Commands (manual — require explicit approval) ─────────────────────────────

# Only warn when something has actually drifted — this used to print unconditionally
# on every single update, even when every command was already current, which trained
# consumers to ignore it. Compute drift first (cheap: a cmp -s loop, no prompting),
# then only surface the warning, with the actual drifted names, when it's true.
COMMANDS_SRC="$SKILLS_SOURCE/commands"
DRIFTED_COMMANDS=()
if [[ -d "$COMMANDS_SRC" ]]; then
  for cmd_file in "$COMMANDS_SRC"/*.md; do
    [[ -f "$cmd_file" ]] || continue
    dest="$COMMANDS_DIR/$(basename "$cmd_file")"
    if [[ ! -f "$dest" ]] || ! cmp -s "$cmd_file" "$dest"; then
      DRIFTED_COMMANDS+=("$(basename "$cmd_file" .md)")
    fi
  done
fi

if [[ ${#DRIFTED_COMMANDS[@]} -gt 0 ]] && ! $INSTALL_COMMANDS; then
  echo ""
  echo "  ⚠️  ${#DRIFTED_COMMANDS[@]} slash command(s) new or changed upstream, not"
  echo "      copied automatically: ${DRIFTED_COMMANDS[*]/#//}"
  echo "  Commands tell the agent to run shell operations and must be reviewed"
  echo "  before install. Use --install-commands to review and approve each one."
  echo ""
fi

if $INSTALL_COMMANDS; then
  if [[ ! -d "$COMMANDS_SRC" ]]; then
    echo "  No commands/ directory found in $SKILLS_SOURCE"
  else
    mkdir -p "$COMMANDS_DIR"
    echo "  Available commands (review each before approving):"
    echo ""

    for cmd_file in "$COMMANDS_SRC"/*.md; do
      [[ -f "$cmd_file" ]] || continue
      cmd_name="$(basename "$cmd_file" .md)"
      first_line="$(head -1 "$cmd_file")"
      dest="$COMMANDS_DIR/$(basename "$cmd_file")"

      # Three states, not two: an already-installed command whose source has since
      # changed upstream must be distinguishable from one that's current. Reporting
      # both as "[installed]" is how a consumer silently keeps running a stale copy of
      # a command that was fixed upstream — they see "installed" and skip it.
      default_answer="N"
      if [[ ! -f "$dest" ]]; then
        status="[new]"
      elif cmp -s "$cmd_file" "$dest"; then
        status="[installed]"
      else
        status="[outdated]"
        default_answer="Y"
      fi

      echo "  $status /$cmd_name"
      echo "         $first_line"
      echo "         Source: $cmd_file"
      echo ""

      if ! $DRY_RUN; then
        if [[ "$default_answer" == "Y" ]]; then
          printf "  Update /%s? [Y/n] " "$cmd_name"
        else
          printf "  Install /%s? [y/N] " "$cmd_name"
        fi
        read -r answer </dev/tty
        [[ -z "$answer" ]] && answer="$default_answer"
        if [[ "$answer" =~ ^[Yy]$ ]]; then
          cp "$cmd_file" "$dest"
          if [[ "$status" == "[outdated]" ]]; then
            echo "  ✅  /$cmd_name updated"
          else
            echo "  ✅  /$cmd_name installed"
          fi
        else
          echo "  —  /$cmd_name skipped"
        fi
        echo ""
      fi
    done

    if $DRY_RUN; then
      echo "  [dry-run] would prompt to install each command above"
    fi
  fi
fi

# ── Agent setup (--setup-agents) ─────────────────────────────────────────────

if $SETUP_AGENTS; then
  AGENTS_MD="AGENTS.md"
  AI_COLLAB_DOC="docs/reference/ai-collaboration.md"
  AGENT_CATALOG_DOC="docs/reference/agent-catalog.md"
  SOURCE_READMES=(
    "agents/README.md"
    "rules/README.md"
    "hooks/README.md"
    "commands/README.md"
    "skills/README.md"
  )

  echo ""
  echo "Setting up agent configuration…"

  for readme in "${SOURCE_READMES[@]}"; do
    if [[ -f "$readme" ]]; then
      echo "  ✓  $readme already exists"
      continue
    fi

    if $DRY_RUN; then
      echo "  [dry-run] would create $readme"
      continue
    fi

    mkdir -p "$(dirname "$readme")"
    case "$readme" in
      "agents/README.md")
        cat > "$readme" <<'EOF'
# agents/

Project-specific agent personas live here as the canonical source.
Deploy copies into `.agents/` after edits; do not keep generated files as the only copy.
EOF
        ;;
      "rules/README.md")
        cat > "$readme" <<'EOF'
# rules/

Optional project-specific assistant rules or overlays live here.
Do not duplicate the canonical policy from `docs/reference/ai-collaboration.md`; keep this folder for short assistant-facing overlays only.
EOF
        ;;
      "hooks/README.md")
        cat > "$readme" <<'EOF'
# hooks/

Project-owned hook scripts live here.
Keep hook wiring in the provider's runtime configuration; do not author the only copy inside runtime config.
EOF
        ;;
      "commands/README.md")
        cat > "$readme" <<'EOF'
# commands/

Project-specific slash command sources live here.
Deploy copies into `.agents/commands/` after edits.
EOF
        ;;
      "skills/README.md")
        cat > "$readme" <<'EOF'
# skills/

Project-specific skills live flat under `skills/<skill-name>/`.
Keep `SKILL.md` as the canonical source and deploy copies into `.agents/skills/`.

Minimal starter:

```md
skills/my-project-skill/SKILL.md
---
name: my-project-skill
description: Short trigger-oriented description of what this skill handles.
---

## When to Use This Skill
- Use this for project-specific work only.

## Rules
- Keep this skill project-owned.
- Re-deploy after edits so `.agents/skills/my-project-skill/` stays in sync.
```
EOF
        ;;
    esac
    echo "  ✅  $readme created"
  done

  if [[ -f "$AI_COLLAB_DOC" ]]; then
    echo "  ✓  $AI_COLLAB_DOC already exists"
  else
    if $DRY_RUN; then
      echo "  [dry-run] would create $AI_COLLAB_DOC"
    else
      mkdir -p "$(dirname "$AI_COLLAB_DOC")"
      cat > "$AI_COLLAB_DOC" <<'EOF'
# AI Collaboration

## Canonical project-owned sources

- `agents/` — project-specific agent personas
- `rules/` — optional project-specific assistant overlays only
- `hooks/` — hook script source
- `commands/` — slash command source
- `skills/` — project-owned skills

## Docs vs skills

- `docs/*` answers "how is this project designed?"
- `skills/*` answers "how should an agent work in this repo?"

## Shared agent runtime

- `AGENTS.md` is the universal project entrypoint
- `.agents/skills/` is the shared Agent Skills discovery directory
- `.agents/commands/` contains provider-neutral command sources
- Provider-specific adapters are generated separately and are never canonical

## Duplication rule

Keep the collaboration policy canonical in this file.
Use `rules/` only for small assistant-facing overlays; do not mirror this whole document there.

## Maintenance rule

Edit project-owned artifacts first, then re-deploy the changed copy into `.agents/`.
EOF
      echo "  ✅  $AI_COLLAB_DOC created"
    fi
  fi

  if [[ -f "$AGENT_CATALOG_DOC" ]]; then
    echo "  ✓  $AGENT_CATALOG_DOC already exists"
  else
    if $DRY_RUN; then
      echo "  [dry-run] would create $AGENT_CATALOG_DOC"
    else
      mkdir -p "$(dirname "$AGENT_CATALOG_DOC")"
      cat > "$AGENT_CATALOG_DOC" <<'EOF'
# Agent Catalog

Use provider-neutral model tiers:

- `flagship-coding`
- `balanced-coding`
- `fast-utility`
- `precision-review`

Keep provider-specific model mapping in this one canonical doc, not in every agent file.

Thin entrypoints like `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` should point here instead of hardcoding stale provider model names.
EOF
      echo "  ✅  $AGENT_CATALOG_DOC created"
    fi
  fi

  if [[ -f "$AGENTS_MD" ]]; then
    echo "  ⚠️  $AGENTS_MD already exists — skipping (run /kmp-setup-agents to regenerate)."
  else
    # Detect project name from settings.gradle.kts
    PROJECT_NAME="KMP Project"
    for f in settings.gradle.kts settings.gradle; do
      if [[ -f "$f" ]]; then
        PROJECT_NAME=$(grep 'rootProject.name' "$f" | head -1 | sed 's/.*= *"//;s/".*//')
        break
      fi
    done

    if $DRY_RUN; then
      echo "  [dry-run] would write $AGENTS_MD for project: $PROJECT_NAME"
    else
      cat > "$AGENTS_MD" <<AGENTS_EOF
# AGENTS.md — $PROJECT_NAME

This project uses [kmp-agent-skills](https://github.com/ronjunevaldoz/kmp-agent-skills).
Skills are installed in \`.agents/skills/\`.

## Skill routing

| Topic | Skill |
|---|---|
| New feature end-to-end | \`kmp-feature-scaffold\` → \`kmp-clean-architecture\` → \`kmp-mvi\` |
| ViewModel / screen state | \`kmp-mvi\` |
| Navigation | \`kmp-navigation\` |
| Dependency injection | \`kmp-dependency-injection\` |
| Design system | \`kmp-compose-design-system\` |
| Code quality / linting | \`kmp-code-quality\` |
| Unit tests | \`kmp-unit-testing\` |
| Android CLI / emulator / deploy | \`kmp-android-cli\` |
| Project docs / onboarding | \`kmp-project-docs-maintainer\` |
| Architecture audit | \`kmp-audit\` |

## Commands installed

See \`.agents/commands/kmp-*.md\` for available commands.
Key commands:
- \`/kmp-implement-feature <name>\` — plan → implement → validate → review a new feature
- \`/kmp-run-audit\` — run architecture audit with per-finding remediation
- \`/kmp-verify\` — full validation pipeline (tests, audit, design, screenshots)
- \`/kmp-execute-ticket <id>\` — implement a GitHub issue end-to-end
- \`/kmp-fix-design\` — scan and fix design system violations
- \`/kmp-update-skills\` — pull latest skills and re-deploy
AGENTS_EOF
      echo "  ✅  $AGENTS_MD generated"
      echo "  ℹ️   Run /kmp-setup-agents for a version tailored to your module graph"
    fi
  fi

  # Keep shared pipeline state outside provider-specific directories so translated
  # agent instructions can use the same path on every client.
  PIPELINE_CONTEXT=".agents/pipeline-context.json"
  if [[ -f "$PIPELINE_CONTEXT" ]]; then
    echo "  ✓  $PIPELINE_CONTEXT already exists"
  else
    if $DRY_RUN; then
      echo "  [dry-run] would write $PIPELINE_CONTEXT"
    else
      mkdir -p ".agents"
      cat > "$PIPELINE_CONTEXT" <<PIPELINE_EOF
{
  "project": "$PROJECT_NAME",
  "group_id": "",
  "platforms": [],
  "skills_used": [],
  "recurring_issues": [],
  "proven_patterns": []
}
PIPELINE_EOF
      echo "  ✅  $PIPELINE_CONTEXT seeded (empty — fill in as the project evolves, or run /kmp-setup-agents for a version populated from the actual module graph)"
    fi
  fi
fi

echo "  Done. Run your audit to verify:"
echo "  python3 $AGENT_DIR/kmp-audit/scripts/audit_project.py ."
echo ""
echo "  Not yet wired: git/CI architecture hooks (pre-commit audit, PostToolUse"
echo "  validation). Run /kmp-setup-hooks to add them."
echo ""
