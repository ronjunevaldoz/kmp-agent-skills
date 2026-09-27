# AI Collaboration

Canonical cross-agent policy for downstream repos using `kmp-agent-skills`.

This doc exists to stop policy drift across `AGENTS.md`, repo-local skills, and one-off notes in `docs/`.

## Source Of Truth

Use these boundaries:

- `docs/*` — stable project design, ownership, architecture, and human-facing guidance
- `skills/*` (project root) — **project-owned custom skills only**, never bundled
  `kmp-agent-skills` content: what to read, what to run, what to validate
- `agents/*` — role/persona overlays for project-specific agents
- `rules/*` — optional short assistant-facing overlays only; never the only copy of
  canonical policy
- `commands/*` — repo-local slash-command sources
- `hooks/*` — repo-local hook sources
- `.agents/skills/` — the only automatic project skill target (bundled
  `kmp-agent-skills` + any custom skill), discovered by agentskills.io-compliant clients
- `.agents/commands/` — provider-neutral command sources/deployments

Quick rule:

- if it answers "how is this project designed?" -> `docs/*`
- if it answers "how should an agent work in this repo?" -> `skills/*`

Do not let `skills/*` grow into duplicated architecture docs.

## Canonical Layout

```text
<project root>/
├── docs/
│   ├── architecture.md
│   └── reference/
│       ├── ai-collaboration.md
│       ├── agent-catalog.md
│       └── <domain-rule>.md
├── agents/
├── rules/
├── commands/
├── hooks/
├── skills/            # source, custom skills only
│   └── <skill-name>/SKILL.md
├── AGENTS.md        # universal project bootstrap
├── .agents/
│   ├── skills/                  # deployed, cross-client target
│   └── commands/                # provider-neutral command sources
│   └── pipeline-context.json    # planner agent context
├── .codex/
│   ├── agents/      # *.toml — subagents; Codex has no custom-commands mechanism
│   └── skills/       # global only (~/.codex/skills) as of this writing, not project-local
└── .gemini/
    ├── commands/    # *.toml — custom commands; no confirmed subagent mechanism
    └── skills/       # global only (~/.gemini/skills) as of this writing, not project-local
```

Codex/Gemini support a different, non-symmetric subset of commands/agents/skills, in
TOML rather than Markdown — see `docs/reference/provider-capability-matrix.md` for the
real, verified matrix and the translation rules before deploying to either.
Claude-specific files such as `CLAUDE.md` may be supported through an optional adapter,
but they are not part of this repository's canonical or automatic project layout.

## What To Commit Vs Gitignore Under `.agents/`

Gitignore `.agents/skills/` when it is a reproducible deployment; commit provider-neutral
source files under `agents/`, `commands/`, and `skills/`. Rationale and `.gitignore` snippet:
`skills/kmp-expert/references/agents-md-templates.md`.

## Thin Entrypoints

`AGENTS.md` should stay thin — a short
"read these docs first" list, and a few startup-critical guardrails. They should never
become the only place architecture or repo policy lives.

## Duplication Rule

Keep the long-form explanation canonical in `docs/reference/ai-collaboration.md`,
`docs/reference/agent-catalog.md`, and other `docs/reference/*.md` domain rules.
Duplicate only short startup guardrails in entrypoint files, and only when: the agent
must reliably see it on startup, missing it would cause expensive/unsafe work, and the duplicated text stays short and points back to the canonical doc.

## Docs Versus Skills

Good `docs/*` content:

- module boundaries
- ownership rules
- architecture diagrams
- domain-specific technical decisions
- release policy summaries

Good `skills/*` content:

- which repo docs to read first
- which scripts/tests/commands to run
- routing rules for local work
- project-specific implementation checklists
- repository-specific review expectations

## Starter Templates

Minimal `AGENTS.md`:

```md
# AGENTS.md

Read first:
- docs/reference/ai-collaboration.md
- docs/reference/agent-catalog.md

Critical guardrails:
- Keep entrypoints thin.
- Keep architecture policy in docs, not in runtime-only files.
```

Minimal `GEMINI.md`:

```md
# GEMINI.md

Read first:
- docs/reference/ai-collaboration.md
- docs/reference/agent-catalog.md
```

## Related Doc

- `docs/reference/agent-catalog.md` — provider-neutral model tiers and agent catalog
