# /kmp-setup-agents $ARGUMENTS

**KMP Agent Skills** — initialize `.agents/` in an existing KMP project so the team
gets agent-driven workflows without running the full scaffold.

`$ARGUMENTS` is optional: a path to the project root (defaults to `.`).

Use this when:
- The project already exists and you're adding `kmp-agent-skills` for the first time
- You want to reset or regenerate the `.agents/` setup after major architecture changes
- A teammate needs to onboard to the agent workflow

Do NOT use this for brand-new projects — `/kmp-new-project` handles agent setup as part of scaffold.

This command deploys **this collection's own** skills/commands into `.agents/`, and
scaffolds the project-owned source locations Claude teams should keep in Git: `agents/`,
`rules/`, `hooks/`, `commands/`, `skills/`, `docs/reference/ai-collaboration.md`, and a
root `AGENTS.md`. For a project's own custom command, agent, skill, or hook, author it in
those project-owned locations first, then deploy a copy into `.agents/` — never author a
project-specific artifact directly into `.agents/` as its only copy.

---

## Step 1 — Locate and validate the project

Resolve `$ARGUMENTS` as the project root (default `.`). Confirm it is a KMP project by
checking for at least one of:
- `settings.gradle.kts` or `settings.gradle`
- `gradle/libs.versions.toml`
- A `build.gradle.kts` with `kotlin("multiplatform")` or `id("com.android.kotlin.multiplatform.library")`

If none of these exist, stop and tell the user this command is for KMP projects only.

Print:
```
PROJECT: <project root>
```

---

## Step 2 — Detect project type and discover the module graph

### 2a — Determine: app or library?

Read `settings.gradle.kts` and all root/module `build.gradle.kts` files.

**Library signals** (if any are present → treat as library project):
- `com.vanniktech.maven.publish` plugin applied
- `org.jetbrains.kotlinx.binary-compatibility-validator` plugin applied
- `maven-publish` plugin applied without `com.android.application` anywhere
- No module with `com.android.application` or `androidApplication` plugin
- No `:composeApp`, `:androidapp`, `:app` module that uses the application plugin

**App signals** (default if no library signals detected):
- `com.android.application` or `androidApplication` plugin present
- `:composeApp`, `:app`, or `:androidApp` module exists with application plugin

Print:
```
Project type: APP | LIBRARY
```

### 2b — Module graph

Read `settings.gradle.kts` and extract all included modules. Group them:

**For APP projects:**
```
Modules discovered:
  :app / :composeApp / :androidApp    — entry points
  :core:common, :core:network, ...    — core modules
  :feature:auth:*                     — feature layers
  ...
```

**For LIBRARY projects:**
```
Modules discovered:
  :library (or main artifact module)  — published artifact
  :library-testing                    — test helpers for consumers (if present)
  :bom                                — Bill of Materials (if present)
  :sample / :sample:androidApp        — sample app (not published)
```

### 2c — Detect active skills from `gradle/libs.versions.toml`

**Always include, regardless of detected signals** (matches `/kmp-new-project`'s Step 5
mandatory baseline — a project scaffolded via either command must end up with the same
routing, not depend on which command happened to initialize it):
- `code-quality` — Ktlint/Detekt is a baseline expectation, not library-specific
- `unit-testing` — same reasoning; don't gate this behind a `turbine` signal alone
- `android-cli` — Android target build/deploy/emulator tooling applies whenever an
  Android target exists, which every app project and most libraries have
- `project-docs-maintainer` — README/onboarding upkeep, not tied to any dependency

**App projects additionally check for:**
- `koin` → dependency-injection
- `ktor` → network-layer
- `sqldelight` → sqldelight-setup
- `androidx.datastore` → datastore
- `roborazzi` → roborazzi
- navigation libraries → navigation

**Library projects additionally check for:**
- `vanniktech` or `maven.publish` → library-publishing
- `binary-compatibility-validator` → library-publishing (apiCheck)
- `dokka` → library-publishing (Javadoc jars)
- `iosX64`, `iosArm64` targets in build files → xcframework-spm
- `@DslMarker`-annotated types with names ending in `Modifier`/`Scope`/`UiDsl`, or a
  `MIRROR_MAP.md` at the project root → api-mimicry
- `CMakeLists.txt` or `*.def` cinterop files present → check whether the referenced
  native code already exists as a 3rd-party/vendored source (→ jni-pro) or is authored
  first-party in this repo (→ native-authoring); read the file paths, don't assume

Print the detected skill set — always-included skills first, then signal-detected ones.

---

## Step 3 — Check for existing `.agents/` setup

Look for:
- `AGENTS.md` — already initialized?
- `.agents/commands/kmp-*.md` — commands already installed?
- `.agents/skills/` — skills already deployed?

If any exist, print their current state and ask:
```
AGENTS.md already exists. Overwrite or skip? [overwrite/skip]
.agents/commands/ has N kmp-*.md files. Update or skip? [update/skip]
```

Proceed based on the answer. Default is `skip` if the user presses Enter.

---

## Step 4 — Generate `.claude/AGENTS.md`

Write (or overwrite) `.claude/AGENTS.md` tailored to the detected project type,
module graph, and skill set.

Both templates (APP and LIBRARY variants) live in
`kmp-expert`'s `references/agents-md-templates.md` — one owner, so the
copy this command writes can't drift from the one `/kmp-new-project` produces (it
already did once: the LIBRARY variant lost five skill-routing rows before the two were
consolidated). Read that file, pick the variant matching the detected project type, and
fill every `<placeholder>` from the module graph and skill set detected in Step 2.

Consumer projects read it at `.agents/skills/kmp-expert/references/agents-md-templates.md`;
in this repo it's `skills/kmp-expert/references/agents-md-templates.md`.

## Step 5 — Scaffold project-owned source locations (MANDATORY — do not skip)

This step is not optional and not secondary to Step 4. `.agents/` is a **deployed
runtime copy** — these root-level paths are the actual git-tracked source of truth this
whole scaffold exists to protect. A setup that only produces `.claude/` and stops has not
finished, even if `.claude/AGENTS.md` looks complete on its own.

Create these project-owned paths if they do not exist yet:

```
agents/README.md
rules/README.md
hooks/README.md
commands/README.md
skills/README.md
docs/reference/ai-collaboration.md
docs/reference/agent-catalog.md
KNOWN_ISSUES.md
```

Each README should say what belongs there and that `.agents/` is the deployed runtime
copy, not the only source of truth. `skills/README.md` should include a minimal
`skills/<name>/SKILL.md` starter template so the first project-owned custom skill has a
correct frontmatter shape from day one.

`KNOWN_ISSUES.md` tracks confirmed agent behavior gaps, tool limitations, and workarounds
for *this* project — the narrative counterpart to `.agents/pipeline-context.json`'s
`recurring_issues` (a flat blocker list `/kmp-execute-ticket` reads before starting work;
this file is where the full write-up for one of those blockers lives). Seed it with just
the header and empty `## Open` / `## Resolved` sections — same shape as this repo's own
`KNOWN_ISSUES.md`, entries added as real issues are actually found, never pre-filled with
speculative ones. Owned going forward by `kmp-project-docs-maintainer`.

`docs/reference/ai-collaboration.md` should explain:
- `AGENTS.md` is the universal bootstrap and points to the canonical docs
- project-specific artifacts live in `agents/`, `rules/`, `hooks/`, `commands/`, `skills/`
- `docs/reference/ai-collaboration.md` is the canonical explanation of that layout
- `rules/` is optional for assistant-specific overlays and must not duplicate the canonical policy doc
- `docs/*` owns stable project design; `skills/*` owns repo-local execution guidance
- provider-specific runtime settings own permissions and hook wiring
- any edit to a project-owned skill must be re-deployed into `.agents/skills/` — `update-consumer-skills.sh` handles this automatically

`docs/reference/agent-catalog.md` should explain:
- provider-neutral model tiers such as `flagship-coding`, `balanced-coding`, `fast-utility`, `precision-review`
- provider-specific model mapping belongs in one canonical doc, not in every agent file; `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` should point back to this catalog instead of hardcoding stale model names

If any of these files already exist, print their current contents and skip unless the
user explicitly asks to overwrite them.

### Library-specific maintainer agents (project-owned, optional)

The generic `agents/*.md` roster this collection ships (`planner`, `implementer`,
`reviewer`, `fixer`, ...) is domain-agnostic — none of them own a library's own
sub-domain concept, like a mimicked UI DSL's mirror-map staying honest, or a native core
staying separated from its JNI/cinterop bridge. When a library has a real, distinct
sub-domain like that, author a project-owned maintainer agent the same way a project
authors a custom skill: `agents/<name>-maintainer.md` at the root, deployed to
`.claude/agents/<name>-maintainer.md`.

Only do this when the sub-domain is real and ongoing — a one-off task doesn't need a standing agent. Two concrete cases this collection's own skills already point at (UI DSL mimicry, first-party native core) with full example templates: `kmp-expert`'s `references/agents-md-templates.md` → "Library-specific maintainer agent examples". Both are starting points, not fixed templates — the real checklist should reflect the project's actual `MIRROR_MAP.md`/native layout, not be copied verbatim.

**Gate — verify before proceeding:**

```bash
ls agents/README.md rules/README.md hooks/README.md commands/README.md skills/README.md \
   docs/reference/ai-collaboration.md docs/reference/agent-catalog.md
```

Every path must exist on disk. If any are missing, create them now — do not move to
Step 6 with a partial scaffold, and do not rely on Step 10's summary to catch it later; that summary reports what this gate already confirmed, not a fresh check.

---

## Step 6 — Install consumer commands

Locate the `kmp-agent-skills` clone. Check in order:
1. `$ARGUMENTS/../kmp-agent-skills`
2. `~/dev/kmp-agent-skills`
3. Ask the user for the path

Copy the consumer command set to `.agents/commands/`:

```
Consumer commands (safe to install):
  kmp-implement-feature.md      — implement a new feature
  kmp-run-audit.md              — architecture audit + auto skill-gap reporting
  kmp-harvest-lessons.md        — collect positive patterns; auto-propose GitHub issues
  kmp-audit-adaptive.md         — adaptive layout coverage + redundant title check
  kmp-generate-palette.md       — generate AppColors + preview from N brand seed colors
  kmp-vectorize.md              — compile raster/SVG into Kotlin ImageVector (no PNG icons)
  kmp-review-changes.md         — review git diff against architecture rules
  kmp-verify.md                 — full validation pipeline
  kmp-execute-ticket.md         — implement a GitHub issue end-to-end
  kmp-fix-design.md             — fix design system violations
  kmp-audit-screenshots.md      — visual audit of Roborazzi goldens
  kmp-record-design-baselines.md — record new golden PNGs
  kmp-audit-design-visual.md    — cross-screen visual consistency check
  kmp-update-design-system.md   — pull latest design system components
  kmp-update-skills.md          — pull latest skills and re-deploy
  kmp-report-skill-issue.md     — file a skill bug report
  kmp-check-updates.md          — check for skill updates
  kmp-clean-comments.md         — refactor code documentation
  kmp-migrate-to-shadcn.md      — migrate design system to shadcn-compose
  kmp-refine-skill.md           — refine a project-owned skill against agentskills.io best practices
  kmp-heal-docs.md              — self-heal project documentation sitemap (docs/README.md)
  kmp-new-task.md               — scaffold a new structured task note under docs/tasks/<parent>/
  kmp-doctor.md                 — project doctor (heals docs, hooks, permissions, lockfile)
```

Do NOT copy repo-internal commands — each one operates on `kmp-agent-skills` itself, not
on the consumer project: `kmp-new-skill.md`, `kmp-modify-skill.md`, `kmp-maintain-docs.md`,
`kmp-release-notes.md`, `kmp-setup-hooks.md`, `kmp-new-project.md`, `kmp-setup-agents.md`,
`kmp-submit-issue.md`, `kmp-summarize-issues.md`, `kmp-sync-local-skills.md`.
Both lists must cover every file in `commands/`.

For each file: if it already exists in `.agents/commands/` and the content differs,
show a one-line diff summary and ask `[update/skip]` before overwriting.

---

## Step 6a — Deploy to Codex and Gemini (ask first, project-scoped only)

Ask the user: "Also deploy this project's agents/commands to Codex CLI and/or Gemini
CLI? [codex/gemini/both/skip]" — never deploy silently, this is a persistent addition
to the project's own repo, not just this machine's home directory.

**Real, verified capability per provider — do not assume symmetry** (see
`docs/reference/ai-collaboration.md`'s Per-Provider Capability Matrix):
- Codex CLI: subagents only (`.codex/agents/*.toml`), no custom-commands mechanism
- Gemini CLI: commands only (`.gemini/commands/*.toml`), no confirmed subagent mechanism

If the user chose `codex` or `both`, for each file in `agents/*.md` (this project's
own project-owned agent sources — not `kmp-agent-skills`' own `agents/` directory,
which are internal to that repo, not deployable), translate to
`.codex/agents/<name>.toml`:

```toml
name = "<from the .md frontmatter's name field>"
description = "<from the .md frontmatter's description field>"
developer_instructions = """
<the .md file's body, verbatim>
"""
```

Only include `model` if the source frontmatter's `model:` value is a real, verified
Codex model id — check `docs/reference/agent-catalog.md`'s Mapping Rule table for the
current one rather than guessing; omit the field entirely if unverified.

If the user chose `gemini` or `both`, for each file in `commands/*.md` (this
project's own project-owned command sources), translate to
`.gemini/commands/<name>.toml`:

```toml
description = "<one-line summary — the command file's first heading/description line>"
prompt = """
<the .md file's body, with every $ARGUMENTS occurrence rewritten to {{args}}>
"""
```

**Tell the user explicitly, in the same message, that translated content may
reference Claude-specific tool names or conventions (Read/Edit/Bash/Skill) that don't
map cleanly to Codex/Gemini's own tool surface — review the generated TOML before
relying on it, this isn't a guaranteed verbatim port.**

---

## Step 7 — Deploy skills

If `.agents/skills/` does not exist:
- **For standard Consumer App projects**: create `.agents/skills/` and copy the curated core skills (`kmp-clean-architecture`, `kmp-feature-scaffold`, `kmp-mvi`, `kmp-audit`, `kmp-dependency-injection`, `kmp-network-layer`). Prompt the user before bulk-copying all 74 skills.
- **For Frameworks, 3D Engines & Starter Kits**: **never bulk-copy all 74 skills**. Only commit engine/domain-specific skills in `.agents/skills/` plus core architecture (`kmp-clean-architecture`, `kmp-mvi`, `kmp-audit`); rely on the global assistant install (`~/.agents/skills`) for generic KMP rules to avoid context bloat.

If `.agents/skills/` already exists, run the equivalent of `update-consumer-skills.sh`
to sync changed skills without prompting for each file (skills are passive docs).
That sync includes both the shared `kmp-agent-skills` bundle and any project-owned
custom skills under `skills/<name>/`.

Deploy to `.agents/skills/` — the project-level agentskills.io
cross-client convention (verified in `docs/reference/agentskills-io-standards.md`;
the global sync script covers the user-level half at `~/.agents/skills`). Mirror the
same copy into `.agents/skills/` so any agentskills.io-compliant client working in this
project sees the same skills, not just Claude Code.

---

## Step 7a — Seed `.agents/pipeline-context.json`

If `.agents/pipeline-context.json` does not already exist, write it so the `planner`
agent has project context from the first run instead of starting cold — this was
previously only seeded for brand-new projects via `/kmp-new-project`, never for a
project being initialized after the fact. Not under `.claude/`: `agents/planner.md`'s
body is copied verbatim into `.codex/agents/planner.toml` if the user opts into Codex
deployment (Step 6a above) — `.agents/` is the cross-client-neutral location:

```json
{
  "project": "<project name, from settings.gradle.kts rootProject.name>",
  "group_id": "<group ID, from gradle.properties or root build.gradle.kts>",
  "platforms": ["<platforms detected from the module graph in Step 2b>"],
  "skills_used": ["<the detected skill set from Step 2c, always-included + signal-detected>"],
  "recurring_issues": [],
  "proven_patterns": []
}
```

If it already exists, print its current contents and skip — don't overwrite a project's
accumulated `recurring_issues`/`proven_patterns` history.

---

## Step 7b — Update `.gitignore`

Without this step a fresh project silently inherits a real bug found in a consumer
project: `.claude/` blanket-gitignored, so `.claude/AGENTS.md` — the file `CLAUDE.md`
loads as the literal system prompt — was never tracked, leaving every fresh clone with
no system prompt until someone reran this command.

Read `kmp-expert`'s `references/agents-md-templates.md` → "What to commit vs gitignore"
section for the exact entries and the blanket-vs-scoped replacement logic (same file
and dual-path convention as Step 4's templates), and apply it to this project's
`.gitignore` — creating the file if it doesn't exist yet.

---

## Step 8 — Write `CLAUDE.md`

If `CLAUDE.md` does not exist in the project root, create a minimal one that tells
Claude Code where the skills live and where the canonical project-owned agent policy
is maintained:

See `kmp-expert`'s `references/agents-md-templates.md` → `CLAUDE.md` section for the
exact body (same file as Step 4's templates, same dual path).

If `CLAUDE.md` already exists, print its contents and skip — do not overwrite.

---

## Step 9 — Write `.claude/settings.json`

If `.claude/settings.json` does not exist, create it with a Bash allowlist for
common read-only and build operations:

```json
{
  "permissions": {
    "allow": [
      "Bash(./gradlew *)",
      "Bash(git status)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(python3 .agents/skills/kmp-audit/scripts/*)",
      "Bash(find . -name *.kt*)",
      "Bash(grep *)"
    ]
  }
}
```

If it already exists, print the current permissions and skip — do not overwrite.

---

## Step 10 — Summary

**Before printing this summary, re-verify each line — do not print `✅` from the
template blindly.** Run the same check Step 5's gate already ran
(`ls agents/README.md rules/README.md hooks/README.md commands/README.md
skills/README.md`) plus `AGENTS.md`, `.agents/commands/`, `.agents/skills/`,
`.agents/pipeline-context.json`,
`.gitignore`. Print `✅`
only for a path that actually exists on disk right now; print `❌ missing` for anything
that doesn't, and go back and create it before telling the user setup is complete. Never
print a raw `<if>`/`</if>` tag — resolve the Codex/Gemini lines to plain text, present
only when actually deployed.

```
AGENT SETUP COMPLETE
─────────────────────
Project:   <name> (<root>)
Features:  <N> detected (<list>)
Skills:    <N> deployed → .agents/skills/

Generated:
  ✅ agents/ rules/ hooks/ commands/ skills/   — project-owned source scaffold
  ✅ docs/reference/ai-collaboration.md        — canonical cross-agent policy
  ✅ AGENTS.md                                  — universal skill routing tailored to this project
  ✅ .agents/commands/                          — <N> consumer commands installed
  ✅ .agents/skills/                            — <N> skills deployed (cross-client)
  ✅ .agents/pipeline-context.json             — project context seeded for the planner agent
  ✅ .gitignore                                — scoped to ignore skill mirrors, track AGENTS.md
  ✅ .codex/agents/                            — <N> subagents translated to TOML (only if Codex was deployed)
  ✅ .gemini/commands/                         — <N> commands translated to TOML (only if Gemini was deployed)

Detected skill set:
  <list of skills matched from libs.versions.toml>

Not yet wired: git/CI architecture hooks (pre-commit audit, PostToolUse validation).
Run /kmp-setup-hooks now to add them — recommended for every team project.

Try it now:
  /kmp-setup-hooks               — wire git pre-commit + PostToolUse architecture hooks
  /kmp-run-audit                 — check architecture health (auto-reports skill gaps)
  /kmp-harvest-lessons           — collect good patterns; propose GitHub issues upstream
  /kmp-implement-feature <name>  — add a new feature
  /kmp-verify                    — run full validation pipeline
```

---

## Notes

- Run this again after major architecture changes (adding/removing features, changing
  the module graph) to regenerate `AGENTS.md` with the current structure.
- Skills are passive docs — re-running always syncs them safely.
- Commands are only overwritten with explicit `[update]` confirmation.
- `settings.json` is never overwritten — add permissions manually if needed.
- Keep project-owned artifacts in the root scaffold even if they only contain README
  placeholders today; that empty scaffold prevents future edits from drifting straight
  into `.claude/`.
- Step 7b handles `.gitignore` scoping automatically now — see "What To Commit Vs
  Gitignore" in `docs/reference/ai-collaboration.md` if you need to apply it by hand.
