# Installation Guide

This guide covers how to install and use the KMP agent skills with every major AI coding assistant.

---

## 🚀 Recommended: Global Machine-Wide Install (Zero Repo Bloat)

For individual developers, pair-programming assistants, and multi-repo workflows, installing globally is the cleanest approach. It makes all 74 skills instantly available to your AI assistant across **every KMP project** on your machine with **zero git pollution**, **zero token waste on specialized repos**, and **zero repository maintenance**.

### Fast Global Sync

```bash
# Sync latest released skills into supported local assistants (~/.claude, ~/.gemini, ~/.codex, ~/.agents)
# Refresh global Claude / Codex / Gemini / Agent Skills installs on this Mac:
bash scripts/sync-local-assistant-skills.sh
```

Or using the [skills CLI](https://skills.sh):

```bash
# Install globally for all agents
npx skills add -g ronjunevaldoz/kmp-agent-skills
```

---

## 📦 Project-Level Installation: Selective vs Bulk

When configuring a team repository where all contributors should share committed skills via Git, follow these best practices:

### 1. Consumer App Repositories (Android / iOS / Desktop / Web Apps)
Install the standard architectural core:

```bash
# Copy the core architectural skills into the cross-client .agents/skills directory
mkdir -p your-project/.agents/skills
cp -r kmp-agent-skills/skills/kmp-clean-architecture your-project/.agents/skills/
cp -r kmp-agent-skills/skills/kmp-feature-scaffold  your-project/.agents/skills/
cp -r kmp-agent-skills/skills/kmp-mvi               your-project/.agents/skills/
cp -r kmp-agent-skills/skills/kmp-audit             your-project/.agents/skills/
```

### 2. Frameworks, 3D Engines & Starter Kits (e.g., Awake Engine, Game Packs)
> [!IMPORTANT]
> **Avoid Bulk Copying All 74 Skills into Specialized Repositories.**
> Committing mobile app skills (Biometrics, In-App Billing, MongoDB, Push Notifications) into a 3D graphics engine or starter kit causes prompt dilution, context bloat, and maintenance tech debt.
> - **Rule**: Only commit engine/domain-specific skills in `.agents/skills/` (e.g., `awake-render-vulkan`, `starterkit-world-openworld`).
> - Rely on the **Global Install** (`~/.claude/skills/`, `~/.gemini/skills/`, `~/.codex/skills/`, `~/.agents/skills/`) for generic Kotlin Multiplatform rules.

---

## Directory Layout & Cross-Client Compatibility

Standardize on **`.agents/skills/`** as the single authoritative cross-client destination (the [agentskills.io](https://agentskills.io) standard):

```
your-project/
├── AGENTS.md                    # Universal guide for Gemini, Claude Code, Codex, Cursor
└── .agents/
    ├── skills/                  # Single cross-client skills target
    └── commands/                # Provider-neutral command sources
        ├── kmp-feature-scaffold/
        │   └── SKILL.md
        └── kmp-clean-architecture/
            └── SKILL.md
```

---

## Usage

Start any session with the expert skill to get routed to the right skill:

```
@kmp-expert what should I do next?
```

Or trigger a skill directly via keyword:

```
scaffold a new feature module for auth
set up the presenter layer for the user profile screen
run the KMP architecture audit
```

Claude Code, Gemini, and Codex match trigger keywords in each `SKILL.md` frontmatter and load relevant skills on demand.

---

## Slash Commands (Optional Project-Local Tools)

Commands in `commands/` define executable slash commands. Install only the commands you review:

```bash
mkdir -p your-project/.agents/commands/
cp kmp-agent-skills/commands/kmp-new-skill.md your-project/.agents/commands/
cp kmp-agent-skills/commands/kmp-run-audit.md your-project/.agents/commands/
```

**Key Commands**:
| Command | What it does |
|---|---|
| `/kmp-new-project <desc>` | Scaffold a full KMP project with 6-layer architecture |
| `/kmp-setup-agents [path]` | Generate tailored AGENTS.md from settings.gradle.kts |
| `/kmp-implement-feature <name>` | Plan → Implement → Validate → Review feature loop |
| `/kmp-run-audit [path]` | Run architecture audit with per-finding remediation |
| `/kmp-verify [path]` | Full test, audit, and design verification |

---

## Keeping Skills Up to Date

When a new release of `kmp-agent-skills` is tagged:

```bash
# Refresh global assistants on this Mac
# Refresh local Claude / Codex / Gemini installs on this Mac:
bash scripts/sync-local-assistant-skills.sh

# Or update consumer project skills
bash scripts/update-consumer-skills.sh
```
