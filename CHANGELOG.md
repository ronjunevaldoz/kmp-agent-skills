# Changelog

All notable changes to kmp-agent-skills are documented here.

## [v3.0.11] — 2026-09-18

### Added

- feat(delivery): mandate issue-id prefixed branch naming

---

## [v3.0.10] — 2026-09-18

### Added

- feat(delivery): add git worktree parallel execution runbook

---

## [v3.0.9] — 2026-09-18

### Added

- feat(skills): add kmp-delivery-lifecycle and kmp-openrewrite skills

### Docs

- docs: add testing and output style to new skills
- docs: add freshness rules and changelog to new skills

---

## [v3.0.8] — 2026-09-15

### Added

- feat(issue-gov): add visual and verification evidence standards

### Chore

- chore(agents): add .claude/ to .gitignore

---

## [v3.0.7] — 2026-09-14

### Added

- feat(scripts): sync user-level slash commands in sync-local-assistant-skills.sh
- feat(audit): flag misplaced GitHub automation scripts and redundant claude mirrors
- feat(skills): add kmp-github-issue-governance skill and payload validation

### Docs

- docs: index kmp-github-issue-governance and update count to 75 skills

---

## [v3.0.6] — 2026-09-12

### Added

- feat(skills): add cross-assistant token saving and mandate root bulk maven publishing

---

## [v3.0.5] — 2026-09-11

### Added

- feat(hooks): reject low-entropy micro-commits and block un-squashed fixups on push

---

## [v3.0.4] — 2026-09-11

### Added

- feat(kmp-audit): audit consumer skill spec and micro-scoped smells and agent persona standards
- feat(kmp-project-docs-maintainer): auto-archive completed tasks and normalize kebab-case in heal_docs
- feat(tasks): add new_task scaffolding script, /kmp-new-task command, and pre-commit hygiene gates
- feat(tasks): add task staleness auditing, checkbox progress tracking, and tasks.md self-healing

---

## [v3.0.3] — 2026-09-11

### Added

- feat(audit): add recursive non-doc asset auditing, canonical docs topology checks, and task archive exemptions

### Fixed

- fix(scaffold): resolve heal_docs path in pre-commit hook, correct install layout, and align agent setup

### Docs

- docs(hygiene): link assistant setup guides in INSTALL.md and prune stale test-coverage.md

---

## [v3.0.2] — 2026-09-11

### Docs

- docs(expect-actual): clarify expect/actual vs platform-exclusive file naming conventions

---

## [v3.0.1] — 2026-09-10

### Added

- feat(routing): prioritize project-owned skill namespaces

### Fixed

- fix(skills): make stale cleanup opt in
- fix(skills): preserve consumer-owned agent skills during sync

---

## [v3.0.0] — 2026-09-10

### Added

- feat(skills): make .agents the canonical project skill runtime

---

## [v2.60.0] — 2026-08-31

### Added

- feat(kmp-compose-web-performance): add wasmJs JS glue-code minification guidance

---

## [v2.59.1] — 2026-08-31

### Fixed

- fix(kmp-refactor): protect string literals in refactor_rename/refactor_bulk

---

## [v2.59.0] — 2026-08-30

### Added

- feat(kmp-audit): flag a CHANGELOG.md [Unreleased] section that never gets released

---

## [v2.58.1] — 2026-08-29

### Added

- feat(skills): wire UI parity and render quality tooling workflow into kmp-shadcn-compose
- feat(audit): add comprehensive 100% UI render quality and behavioral fidelity auditor
- feat(ui): complete UI tooling arsenal (contrast auditor, compose perf linter, visual diff, full-stack scaffolder)
- feat(shadcn): add automated shadcn_parity auditor tool and refine worktree filtering in doctor
- feat(refactor): add automated refactor_optimize_imports script with dry-run support
- feat(refactor): add automated bulk refactor tool for batch mappings with dry-run support
- feat(refactor): add robust build/gradle/git ignore filtering and word boundary precision to refactoring scripts
- feat(refactor): add automated refactor_rename_package tool with dry-run support
- feat(refactor): add automated semantic refactor_rename script with dry-run support
- feat(refactor): add semantic refactor_move tool and tech debt comment healing hooks
- feat(hooks): add canonical pre-commit hook with binary leak guard, auto-sitemap heal, and lesson reminder
- feat(docs): add developer-friendly vibe-to-plan template with real-world analogies
- feat(docs): add Audits category to heal_docs sitemap engine
- feat(lockfile): add check_skills_lock.py for upstream version freshness inspection
- feat(doctor): introduce heal_project.py and /kmp-doctor command for docs, hooks, permissions, and lockfile
- feat(docs): add subtle attribution footer to self-healed sitemaps
- feat(commands): make /kmp-update-skills default to global machine-wide sync
- feat(docs): introduce self-healing docs engine and kmp-heal-docs command
- feat(lockfile): add generate_skills_lock.py and framework-vs-app boundary guide
- feat(release): support multi-channel releases (alpha, beta, rc, dev, snapshot) with automated changelog

### Fixed

- fix(kmp-doctor): make heal/lock scripts actually reach consumer projects

### Docs

- docs(kmp-project-docs-maintainer): trim SKILL.md under the 500-line gate
- docs(kmp-refactor): add References section for references/git-history-surgery.md
- docs(skills): codify git history surgery for fixing buried bad commits in stacked history
- docs(skills): codify 3-tier README templates (root, docs sitemap, module) in kmp-project-docs-maintainer
- docs(skills): codify code examples and linking policy in kmp-project-docs-maintainer
- docs(skills): codify KDoc vs ground-truth docs boundary in kmp-project-docs-maintainer
- docs: update README with self-healing docs, global sync, and register kmp-heal-docs command
- docs: generalize framework-vs-app boundary guide to neutral domain taxonomy
- docs(install): promote global installation, warn against repo bloat, and standardize on .agents/skills

---

## [v2.58.0] — 2026-08-26

### Added

- feat(docs-hygiene): cross-reference avoid-ai-writing for deeper AI-tell removal

---

## [v2.57.0] — 2026-08-24

### Added

- feat(kmp-kotlinpoet): add skill for authoring custom KSP processors

---

## [v2.56.0] — 2026-08-24

### Added

- feat(kmp-security): add mobile security skill for pinning, RASP, storage, obfuscation

---

## [v2.55.0] — 2026-08-24

### Added

- feat(kmp-refine-skill): add consumer command for qualitative skill refinement

---

## [v2.54.0] — 2026-08-24

### Added

- feat(kmp-resilience): add resilience skill, exception design, and layer separation anti-patterns

---

## [v2.53.0] — 2026-08-24

### Added

- feat(kmp-mvi): extract cross-framework generic guidance for MVI and accessibility

---

## [v2.52.0] — 2026-08-24

### Added

- feat(kmp-audit): wire docs-hygiene into the CI governance check

---

## [v2.51.0] — 2026-08-24

### Added

- feat(kmp-compose-design-system): add typography scale rationale + text resilience

---

## [v2.50.0] — 2026-08-23

### Added

- feat(kmp-api-mimicry): add Clean-Room Provenance Record template
- feat(docs-hygiene): add Mermaid/code-snippet Writing Style rule

---

## [v2.49.0] — 2026-08-23

### Added

- feat(docs-hygiene): add starter templates for README.md, architecture.md, reference/

---

## [v2.48.0] — 2026-08-23

### Added

- feat(docs-hygiene): add Decision lane (ADR) and Per-Module README.md

---

## [v2.47.0] — 2026-08-23

### Added

- feat(docs-hygiene): enforce docs/tasks.md as a real status index

---

## [v2.46.0] — 2026-08-23

### Added

- feat(kmp-api-mimicry): add generic Compliance & Legal Audit

---

## [v2.45.0] — 2026-08-23

### Added

- feat(kmp-mcp-sdk): add skill for the official MCP Kotlin SDK

---

## [v2.44.0] — 2026-08-23

### Added

- feat(kmp-audit): enforce assets/ guidance, matching scripts/ and references/

---

## [v2.43.0] — 2026-08-23

### Added

- feat(kmp-audit): add construction/execution lifecycle coupling as judgment-only check

---

## [v2.42.0] — 2026-08-22

### Added

- feat(docs-hygiene): task filenames encode status, date moves into content

---

## [v2.41.0] — 2026-08-22

### Added

- feat(kmp-unit-testing): add Kover test coverage guidance

---

## [v2.40.0] — 2026-08-22

### Added

- feat(kmp-code-quality): add investigation-narration comment rule

---

## [v2.39.0] — 2026-08-22

### Added

- feat(kmp-audit): add ponytail comment density detector

---

## [v2.38.1] — 2026-08-21

### Docs

- docs: add KI-R18 for pre-commit-audit.sh REPO_ROOT silent no-op

---

## [v2.38.0] — 2026-08-21

### Fixed

- fix(hooks): pre-commit-audit.sh gates docs hygiene, fix REPO_ROOT resolution

---

## [v2.37.0] — 2026-08-21

### Added

- feat(kmp-code-quality): put the reference pointer first for delicate code

---

## [v2.36.0] — 2026-08-21

### Added

- feat(kmp-audit): widen robotic-phrase docs check, add orphaned-doc detector

---

## [v2.35.1] — 2026-08-21

### Docs

- docs(agents): recognize when research reaches a doc-worthy conclusion

---

## [v2.35.0] — 2026-08-21

### Added

- feat(kmp-code-quality): add mandatory bracket linking, sealed class KDoc, backtick literals

---

## [v2.34.0] — 2026-08-21

### Added

- feat(skill-behavior): add routing evaluation suite

---

## [v2.33.0] — 2026-08-20

### Added

- feat(kmp-code-quality): flag robotic/formal comment phrasing

---

## [v2.32.0] — 2026-08-19

### Added

- feat(kmp-expert): add kmp-coroutines-flow-patterns skill

---

## [v2.31.0] — 2026-08-19

### Added

- feat(kmp-code-quality): add scope functions and sequences guidance

---

## [v2.30.1] — 2026-08-19

### Docs

- docs(kmp-code-quality): flatten multi-line WHY examples to one // line

---

## [v2.30.0] — 2026-08-19

### Added

- feat(kmp-code-quality): a process never gets one // per step

---

## [v2.29.0] — 2026-08-19

### Added

- feat(kmp-audit): add duplicate-code-block detector

---

## [v2.28.0] — 2026-08-19

### Added

- feat(kmp-code-quality): document god-class-split roles, add builder detector

---

## [v2.27.0] — 2026-08-19

### Added

- feat(kmp-audit): add enum-masquerading-as-sealed detector

---

## [v2.26.0] — 2026-08-19

### Added

- feat(kmp-code-quality): document enum vs sealed class vs factory decision

---

## [v2.25.1] — 2026-08-18

### Fixed

- fix(kmp-audit): catch SCREAMING_CASE filenames in docs-hygiene kebab-case check

---

## [v2.25.0] — 2026-08-18

### Added

- feat(kmp-code-quality): document verb chaos and twin nouns naming anti-patterns

---

## [v2.24.0] — 2026-08-18

### Added

- feat(kmp-code-quality): document god-receiver extension sprawl anti-pattern

---

## [v2.23.0] — 2026-08-17

### Added

- feat(kmp-code-quality): flag comments that narrate history not purpose

---

## [v2.22.0] — 2026-08-17

### Added

- feat(kmp-code-quality): attribution comments need confirmation first

---

## [v2.21.0] — 2026-08-17

### Added

- feat(kmp-audit): detect hedging language in consumer docs

---

## [v2.20.0] — 2026-08-17

### Added

- feat(kmp-project-docs-maintainer): add writing-style guidance

---

## [v2.19.0] — 2026-08-15

### Added

- feat(setup-hooks): add Option I — auto-bootstrap a missing skills deploy

---

## [v2.18.2] — 2026-08-14

### Fixed

- fix(kmp-code-quality): document Detekt's KMP task-wiring footgun

---

## [v2.18.1] — 2026-08-14

### Fixed

- fix(update-consumer-skills): stop warning about commands that are current

---

## [v2.18.0] — 2026-08-11

### Added

- feat(kmp-clean-architecture): add API/Implementation Boundary section

---

## [v2.17.1] — 2026-08-11

### Docs

- docs(kmp-code-quality): extensions are syntax, not architecture

---

## [v2.17.0] — 2026-08-11

### Added

- feat(kmp-layout-system): switch wireframes from ASCII to SVG

---

## [v2.16.10] — 2026-08-10

### Added

- feat(kmp-new-project): persist requirements analysis at intake

---

## [v2.16.9] — 2026-08-10

### Fixed

- fix(kmp-new-project): split plan-confirmation into two turns

---

## [v2.16.8] — 2026-08-10

### Added

- feat(kmp-new-project): offer next milestone after MVP ships

---

## [v2.16.7] — 2026-08-10

### Docs

- docs: fill in the Apache 2.0 copyright appendix

---

## [v2.16.6] — 2026-08-08

### Docs

- docs(native-authoring): explain why // beats /* */, and the real C89 exception

---

## [v2.16.5] — 2026-08-08

### Docs

- docs(code-quality): note there is no @deprecated KDoc tag

---

## [v2.16.4] — 2026-08-08

### Docs

- docs(code-quality): add Kotlin's own conventions for extension visibility and file placement

---

## [v2.16.3] — 2026-08-08

### Docs

- docs(code-quality): add when to use / not use Kotlin extension functions

---

## [v2.16.2] — 2026-08-08

### Fixed

- fix(docs): eliminate PLAN.md's duplicate skill roster; mechanize count checks

---

## [v2.16.1] — 2026-08-08

### Fixed

- fix(docs): clean PLAN.md staleness; add it to docs-maintainer's scope

---

## [v2.16.0] — 2026-08-08

### Added

- feat(mvi): document a framework-agnostic Store for non-Compose consumers

---

## [v2.15.0] — 2026-08-08

### Added

- feat(audit): enforce a 500-line limit on root-level docs; split INSTALL.md
- feat(setup-agents): scaffold KNOWN_ISSUES.md for consumer projects

### Docs

- docs: file KI-010 — git tag creation is never mechanically blocked

---

## [v2.14.0] — 2026-08-08

### Added

- feat(setup-agents): scope .gitignore for .claude/ during setup, not just document it

---

## [v2.13.1] — 2026-08-08

### Fixed

- fix(audit): scan .claude/agents/ directly for the tier-name-as-model bug

---

## [v2.13.0] — 2026-08-08

### Added

- feat(audit): detect .claude/AGENTS.md, commands/, settings.json gitignored

### Docs

- docs: document what to commit vs gitignore under .claude/ and .agents/

---

## [v2.12.3] — 2026-08-07

### Fixed

- fix(setup-agents): classify 5 commands missing from the consumer-safe/repo-internal lists

---

## [v2.12.2] — 2026-08-07

### Fixed

- fix(update-consumer-skills): deploy correctly when a skill is individually symlinked

---

## [v2.12.1] — 2026-08-07

### Docs

- docs(code-quality): document Detekt's InvalidPackageDeclaration rule

---

## [v2.12.0] — 2026-08-07

### Added

- feat(style): adopt ASD-STE100's procedural rules for numbered steps only

---

## [v2.11.1] — 2026-08-07

### Fixed

- fix(audit): classify_declarations skipped nothing — local vars counted as API surface

---

## [v2.11.0] — 2026-08-07

### Added

- feat(audit): add classify_declarations.py — a real classifier for the core/sugar taxonomy

---

## [v2.10.7] — 2026-08-07

### Fixed

- fix(audit): three gaps in _detect_god_utils_file, incl. silent no-op under explicitApi()

---

## [v2.10.6] — 2026-08-07

### Fixed

- fix(audit): comment-surface audit — string-literal false positive, coverage gaps

---

## [v2.10.5] — 2026-08-07

### Other

- refactor(new-project): split into five phase references; close KI-009

---

## [v2.10.4] — 2026-08-07

### Other

- refactor(setup-agents): move AGENTS.md/CLAUDE.md templates to a deployed skill reference

---

## [v2.10.3] — 2026-08-07

### Fixed

- fix(new-project): delegate agent setup to /kmp-setup-agents instead of duplicating it

---

## [v2.10.2] — 2026-08-07

### Docs

- docs(update-skills): correct the version that ships automatic stale-skill pruning

---

## [v2.10.1] — 2026-08-07

### Fixed

- fix(consumer-update): version marker, stale-skill pruning, outdated-command detection

---

## [v2.10.0] — 2026-08-06

### Added

- feat(audit): add 500-line guideline to references/*.md files, split one offender

---

## [v2.9.2] — 2026-08-06

### Docs

- docs(code-quality): add Kotlin delegation guidance (class delegation + delegated properties)

---

## [v2.9.1] — 2026-08-06

### Docs

- docs(code-quality): add core/helper/sugar/sample-local/deprecated categorization + DSL guidance

---

## [v2.9.0] — 2026-08-04

### Added

- feat(plugin): wire this repo as an installable Claude Code plugin

---

## [v2.8.0] — 2026-08-04

### Added

- feat(audit): flag justification comments over single dependency lines; add TODO/FIXME convention

---

## [v2.7.0] — 2026-08-04

### Added

- feat(shadcn-compose-layouts): add page-composition skill for shadcn-compose

### Fixed

- fix(update-consumer-skills): don't treat symlinked bundled-skill mirrors as collisions

---

## [v2.6.13] — 2026-08-04

### Other

- refactor(skills): finish KI-008 — split remaining 12 oversized SKILL.md files

---

## [v2.6.12] — 2026-08-04

### Other

- refactor(skills): split 9 more oversized SKILL.md files into references/

---

## [v2.6.11] — 2026-08-04

### Other

- refactor(compose-design-system-extended): split SKILL.md into references/

---

## [v2.6.10] — 2026-08-04

### Docs

- docs: cross-reference kmp-code-quality naming conventions from 4 more skills

---

## [v2.6.9] — 2026-08-04

### Docs

- docs(docs-maintainer): add Delete vs Archive rule to docs-hygiene.md

---

## [v2.6.8] — 2026-08-04

### Docs

- docs(api-mimicry): fix Engine placeholder, MIRROR_MAP.md placement, multi-reference mimicry

---

## [v2.6.7] — 2026-08-04

### Fixed

- fix(clean-architecture): rename fabricated UnnecessaryAbstractClass to real AbstractClassCanBeInterface

---

## [v2.6.6] — 2026-08-04

### Docs

- docs(api-mimicry): add convenience-shorthand-coverage check to MIRROR_MAP.md

---

## [v2.6.5] — 2026-08-04

### Fixed

- fix(audit): add WHY-signal exemption to long-stacked-comment-block detector

---

## [v2.6.4] — 2026-08-03

### Fixed

- fix(code-quality): remove fabricated CouplingBetweenObjects Detekt rule

---

## [v2.6.3] — 2026-08-03

### Docs

- docs(readme): fix category-count table drift (65 -> 68 total)

---

## [v2.6.2] — 2026-08-03

### Docs

- docs(readme): add author credit line, fix stale 66 -> 68 skill count

---

## [v2.6.1] — 2026-08-03

### Fixed

- fix(setup-hooks): wire commit-msg alongside pre-commit in Option A

---

## [v2.6.0] — 2026-08-03

### Added

- feat(skills): add kmp-compose-web-performance

---

## [v2.5.2] — 2026-08-03

### Fixed

- fix(design-system): stop ComponentRegistryRule flagging legitimate DS wrappers

---

## [v2.5.1] — 2026-08-03

### Docs

- docs(native-authoring): add header-vs-implementation comment convention

---

## [v2.5.0] — 2026-08-03

### Added

- feat(audit): add _detect_repository_in_composable

---

## [v2.4.2] — 2026-08-02

### Fixed

- fix(audit): stop viewmodel-in-viewmodel false positive on comments and local vals

---

## [v2.4.1] — 2026-08-02

### Docs

- docs(code-quality): document NamedArguments rule and argument-wrapping conventions

---

## [v2.4.0] — 2026-08-02

### Added

- feat(skills): add kmp-refactor for rename/move/copy/delete decisions

---

## [v2.3.0] — 2026-08-02

### Added

- feat: add migrate-kmm-to-kmp.sh to clean up stale pre-v2.2.0 skill copies

---

## [v2.2.0] — 2026-08-02

### Other

- refactor: rename Compose-only skills to kmp-compose-* prefix

---

## [v2.1.1] — 2026-08-02

### Fixed

- fix(audit): archive stale AUDIT_REPORT.md, add Task-vs-Reference doc lifecycle rule

---

## [v2.1.0] — 2026-08-02

### Added

- feat(hooks): block edits to vendored skill mirrors

---

## [v2.0.0] — 2026-08-02

### Other

- refactor: rename kmm-agent-skills to kmp-agent-skills, kotlin-multiplatform-* skills to kmp-*

---

# Changelog

All notable changes to kmm-agent-skills are documented here.

## [v1.120.0] — 2026-08-02

### Added

- feat(audit): add heuristic redundancy detector for skills and agents

---

## [v1.119.0] — 2026-08-02

### Added

- feat(hooks): block computer-use for Compose UI verification (Option G)

---

## [v1.118.1] — 2026-08-02

### Fixed

- fix(audit): resolve findings from deep technical audit (H-1/H-2, M-1..M-5, L-1/L-2)

---

## [v1.118.0] — 2026-08-02

### Added

- feat(code-quality): add compiler-warnings coverage

---

## [v1.117.0] — 2026-08-02

### Added

- feat(setup-hooks): add Option F — secrets scan before commit (gitleaks)

---

## [v1.116.0] — 2026-08-02

### Added

- feat(audit): add patch-not-root-cause hints, document Detekt's ForbiddenComment

---

## [v1.115.0] — 2026-08-02

### Added

- feat(audit): add _detect_context_leak_in_singleton

---

## [v1.114.0] — 2026-08-02

### Added

- feat(code-quality): enable Detekt Performance ruleset, add 2 perf/encapsulation detectors

---

## [v1.113.3] — 2026-08-01

### Docs

- docs(expert): add explicit non-KMP scope guard

---

## [v1.113.2] — 2026-08-01

### Fixed

- fix(library-publishing): initial version was 1.0.0, contradicting the pre-1.0 policy

---

## [v1.113.1] — 2026-08-01

### Docs

- docs(provider-matrix): add Antigravity, resolve Gemini path discrepancy

---

## [v1.113.0] — 2026-08-01

### Added

- feat(audit): add _detect_vague_class_name_suffix

---

## [v1.112.0] — 2026-08-01

### Added

- feat(audit): add _detect_hardcoded_ui_string

---

## [v1.111.0] — 2026-08-01

### Added

- feat(code-quality): add kotlin-reflect, god-utils, regex-readability rules

---

## [v1.110.1] — 2026-08-01

### Fixed

- fix(audit): .agents/skills was never the deploy/detection default it claimed to be

---

## [v1.110.0] — 2026-07-31

### Added

- feat(code-quality): add partial-param-documentation detector

---

## [v1.109.4] — 2026-07-31

### Fixed

- fix(kmm-setup-agents): add mandatory verification gate for project-owned scaffold

---

## [v1.109.3] — 2026-07-31

### Fixed

- fix(library-publishing): build-logic was never actually wired for libraries

---

## [v1.109.2] — 2026-07-31

### Fixed

- fix(library-publishing): correct false claim — kmp-wizard DOES have a library equivalent

---

## [v1.109.1] — 2026-07-31

### Fixed

- fix(kmm-new-project): clean up ugly Step 11 summary template

---

## [v1.109.0] — 2026-07-31

### Added

- feat(library-publishing): add pre-1.0 policy, NOTICE file, OSS scaffolding, vuln scanning

---

## [v1.108.0] — 2026-07-31

### Added

- feat(library-publishing): add multi-module library splitting guidance

---

## [v1.107.0] — 2026-07-31

### Added

- feat(code-quality): add Android Kotlin style guide naming conventions

---

## [v1.106.0] — 2026-07-31

### Added

- feat(native-authoring): add new skill for first-party native C/C++ core authoring

---

## [v1.105.0] — 2026-07-31

### Added

- feat(audit): enforce demo-code removal and shadcn raw-component checks, default App to shadcn-compose

---

## [v1.104.1] — 2026-07-31

### Fixed

- fix(feature-scaffold): correct module paths to match real kmp-wizard template, gate :app:* boundary

---

## [v1.104.0] — 2026-07-31

### Added

- feat(api-mimicry): add new skill — mimic a reference API's shape for a from-scratch library

---

## [v1.103.0] — 2026-07-31

### Added

- feat(audit): add structure diagram and non-blocking naming-drift hint

---

## [v1.102.0] — 2026-07-31

### Added

- feat(kotlin-rpc): document SSE vs kRPC streaming decision guidance

---

## [v1.101.1] — 2026-07-31

### Fixed

- fix(scripts): fix the actual consumer skills updater, move pipeline-context

---

## [v1.101.0] — 2026-07-31

### Added

- feat(kmm-new-project): add Library project scaffolding, not just App

---

## [v1.100.1] — 2026-07-31

### Fixed

- fix(commands): align existing-project init with new-project init

---

## [v1.100.0] — 2026-07-31

### Added

- feat(scripts): add skills health report, regenerated every release

---

## [v1.99.4] — 2026-07-31

### Fixed

- fix(release): stop creating GitHub Releases before the tag is pushed

---

## [v1.99.3] — 2026-07-31

### Docs

- docs(skills): semver discipline for apiCheck, .agents/skills in project scaffold

---

## [v1.99.2] — 2026-07-31

### Docs

- docs(readme): simplify skill list, add Agent Skills spec compliance mention

---

## [v1.99.1] — 2026-07-31

### Fixed

- fix(scripts): sync to ~/.agents/skills, the real cross-client convention

---

## [v1.99.0] — 2026-07-31

### Added

- feat(scripts): audit and enforce agentskills.io compliance

---

## [v1.98.4] — 2026-07-31

### Fixed

- fix(audit): enforce :core as a folder group, not a monolithic module

---

## [v1.98.3] — 2026-07-31

### Fixed

- fix(kmm-new-project): make CI/CD wiring optional, not always-on
- fix(audit): enforce ViewModel-depends-only-on-domain, not just document it

---

## [v1.98.2] — 2026-07-31

### Docs

- docs(mvi): name the God State smell properly as Divergent Change

---

## [v1.98.1] — 2026-07-31

### Docs

- docs(mvi): clarify god-ViewModel field-count test with a relatedness litmus

---

## [v1.98.0] — 2026-07-31

### Added

- feat(audit): style-file bundling and two more god-ViewModel signals

---

## [v1.97.1] — 2026-07-31

### Fixed

- fix(skills): coordinator de-escalation + component-file bloat

---

## [v1.97.0] — 2026-07-26

### Added

- feat(code-quality): name Long Parameter List's worse variant

---

## [v1.96.0] — 2026-07-25

### Added

- feat(skills): cover general KMM anti-patterns and library decoupling rules

---

## [v1.95.0] — 2026-07-25

### Added

- feat(audit): detect runBlocking, Koin cycles, unstable Compose collections

---

## [v1.94.0] — 2026-07-25

### Added

- feat(audit): repo-wide god-class detection and coupling limits

---

## [v1.93.0] — 2026-07-20

### Added

- feat(audit): detect pattern-adoption opportunities, not just misuse

---

## [v1.92.0] — 2026-07-20

### Added

- feat(skills): cover value class + context parameters

---

## [v1.91.1] — 2026-07-20

### Fixed

- fix(android-cli): defer to the real official skill instead of duplicating it

---

## [v1.91.0] — 2026-07-19

### Added

- feat(migration): retrofit path for projects on an older skills release

---

## [v1.90.0] — 2026-07-19

### Added

- feat(kmm-new-project): bake in mandatory baseline skill set

---

## [v1.89.0] — 2026-07-19

### Added

- feat(android-cli): broaden triggers + cross-reference from feature-scaffold

---

## [v1.88.0] — 2026-07-19

### Added

- feat(skills): add kotlin-multiplatform-android-cli skill
- feat(hooks): auto-check for skill updates every session

### Docs

- docs: wire kotlin-multiplatform-android-cli into README + planner routing

---

## [v1.87.0] — 2026-07-19

### Added

- feat(code-quality): add Side-Effect-Free Accessors rule + audit detector

---

## [v1.86.0] — 2026-07-18

### Added

- feat(new-project): persist plan to PLAN.md, use AskUserQuestion, fix format

---

## [v1.85.0] — 2026-07-18

### Added

- feat(agents): add QA engineer, fix stale test_skill_scripts.py references

### Fixed

- fix(layout-system): use box-drawing chars for wireframe borders

---

## [v1.84.0] — 2026-07-17

### Added

- feat(audit): add agent file standards + deployment drift detectors

---

## [v1.83.0] — 2026-07-17

### Added

- feat(docs): fill real model tier mapping, add Codex/Gemini scaffold generation
- feat(audit): detect mixed ShadcnTheme/AppTheme usage, enforce never-combine rule

### Fixed

- fix(docs): split provider capability matrix into its own file

---

## [v1.82.0] — 2026-07-16

### Added

- feat(docs): add cross-agent collaboration templates

---

## [v1.81.0] — 2026-07-15

### Added

- feat(skills): sync consumer project-owned custom skills
- feat(scaffold): complete claude consumer scaffold

### Docs

- docs(scaffold): clarify rules overlay boundary

---

## [v1.80.0] — 2026-07-14

### Added

- feat(code-quality): enforce and refine the comment/KDoc conventions
- feat(ci-github-actions): add local dry-run via act, document free-tier minutes

---

## [v1.79.0] — 2026-07-14

### Added

- feat(audit): add project-owned skill standards detector, fix expert doc nesting

---

## [v1.78.0] — 2026-07-14

### Added

- feat(expert): add source-of-truth rule for project-specific commands/agents/skills

---

## [v1.77.1] — 2026-07-14

### Other

- refactor(tests): split test_skill_scripts.py into per-script test files

---

## [v1.77.0] — 2026-07-14

### Added

- feat(design-system): require UI interaction tests alongside preview/screenshot coverage

---

## [v1.76.1] — 2026-07-13

### Docs

- docs(shadcn-compose): add Shadcn Studio as a layout-pattern lookup reference

---

## [v1.76.0] — 2026-07-13

### Added

- feat(shadcn-compose): add worked multi-component composition example

---

## [v1.75.1] — 2026-07-13

### Fixed

- fix(shadcn-compose): recheck README/Maven Central, add 2 new components

---

## [v1.75.0] — 2026-07-13

### Added

- feat(repository-pattern): add in-memory repository rule for no-backend-yet bring-up

---

## [v1.74.0] — 2026-07-13

### Added

- feat(shadcn-compose): add full component keyword matrix

---

## [v1.73.1] — 2026-07-13

### Fixed

- fix(routing): remove shadcn keyword collision, detect it in the validator

---

## [v1.73.0] — 2026-07-13

### Added

- feat: add tmp-clone installer for local assistant skill sync

---

## [v1.72.0] — 2026-07-13

### Added

- feat(audit): detect hardcoded base URLs in commonMain

---

## [v1.71.1] — 2026-07-13

### Fixed

- fix(token-saver): document Headroom's missing settings.json routing step

---

## [v1.71.0] — 2026-07-13

### Added

- feat(token-saver): add install scripts for Ponytail, Caveman-adjacent Headroom, and RTK

---

## [v1.70.0] — 2026-07-12

### Added

- feat(shadcn-compose): add signature-fetch script, fix two real bugs

---

## [v1.69.0] — 2026-07-12

### Added

- feat(new-project): require wireframes + architecture diagram before code

---

## [v1.68.0] — 2026-07-12

### Added

- feat(lessons): proactively draft a GitHub issue for high-severity bugs

### Fixed

- fix(known-issues): fix stale Open Issues heading match, clean up KNOWN_ISSUES.md

---

## [v1.67.0] — 2026-07-12

### Added

- feat(audit): add module layer-order and cross-feature dependency detector

---

## [v1.66.1] — 2026-07-12

### Docs

- docs(token-saver): correct install-risk framing for all four tools

---

## [v1.66.0] — 2026-07-12

### Added

- feat(clean-architecture): add composition-over-inheritance rule and detector

---

## [v1.65.0] — 2026-07-11

### Added

- feat(shadcn-compose): add migration command and layout-quality suggestions

---

## [v1.64.0] — 2026-07-11

### Added

- feat(skills): add kotlin-multiplatform-shadcn-compose consumption skill

---

## [v1.63.0] — 2026-07-11

### Added

- feat(new-project): offer shadcn-compose/heroicons-compose/tailwind-compose in setup

---

## [v1.62.3] — 2026-07-11

### Fixed

- fix(design-system): exclude deployed skill bundles from scan_design_violations.py

---

## [v1.62.2] — 2026-07-11

### Fixed

- fix(audit): fix _has() always-True bug, extend exclusion to all detectors

---

## [v1.62.1] — 2026-07-11

### Fixed

- fix(scripts): check KMM_AGENT_SKILLS_SOURCE before guessing a clone path

---

## [v1.62.0] — 2026-07-11

### Added

- feat(skills): add docs-site skill, libraries/testing pages to docs-maintainer

---

## [v1.61.1] — 2026-07-11

### Fixed

- fix(commands): replace fragile find -not predicate, add portability scanner

---

## [v1.61.0] — 2026-07-10

### Added

- feat(roborazzi): add bounds sidecar for exact position/size regression

---

## [v1.60.0] — 2026-07-10

### Added

- feat(audit): add what-comment detector and /kmm-clean-comments command

---

## [v1.59.1] — 2026-07-10

### Docs

- docs(code-quality): document comment conventions by architectural level

---

## [v1.59.0] — 2026-07-10

### Added

- feat(skills): add benchmark skill, fix Ktor client-reuse bug, cross-reference tailwind-compose

---

## [v1.58.0] — 2026-07-10

### Added

- feat(expert): add performance request routing decision tree

### Docs

- docs(known-issues): re-investigate KI-007, correct to reflect reality

---

## [v1.57.3] — 2026-07-10

### Docs

- docs(token-saver): document RTK's real two-phase install

---

## [v1.57.2] — 2026-07-10

### Docs

- docs: add local skill sync and benchmark guidance

---

## [v1.57.1] — 2026-07-10

### Docs

- docs: refine routing and docs guidance

---

## [v1.57.0] — 2026-07-10

### Added

- feat(skills): add token saver routing and skill

---

## [v1.56.1] — 2026-07-09

### Docs

- docs: refine kmm project bootstrap and guidance

---

## [v1.56.0] — 2026-07-09

### Added

- feat(audit): enforce one-file-per-X rules with 3 new detectors

### Other

- refactor(code-quality): simplify comment conventions; wire into reviewer

---

## [v1.55.3] — 2026-07-09

### Docs

- docs(code-quality): add KDoc tag reference, license headers, comment/notes split
- docs(shared-resources): add px/dp density-bucket conversion reference

---

## [v1.55.2] — 2026-07-08

### Docs

- docs(code-quality): add Kotlin comment and KDoc conventions

---

## [v1.55.1] — 2026-07-08

### Fixed

- fix(imagevector-generator): detect stroke-only SVGs, normalize via picosvg

---

## [v1.55.0] — 2026-07-08

### Added

- feat(imagevector-generator): add --package override flag

---

## [v1.54.2] — 2026-07-08

### Fixed

- fix(imagevector-generator): backport picosvg's arc precision fixes

---

## [v1.54.1] — 2026-07-08

### Fixed

- fix(imagevector-generator): flatten SVG arcs instead of rejecting them

---

## [v1.54.0] — 2026-07-08

### Added

- feat(design-system-extended): add ScrollArea and ResizablePanelGroup

---

## [v1.53.3] — 2026-07-08

### Fixed

- fix(design-system): stop animating border width on focus; fix tooltip blink

---

## [v1.53.2] — 2026-07-08

### Fixed

- fix(commits): add missing refine/enforce types to commit-msg hook

---

## [v1.53.1] — 2026-07-08

### Chore

- chore(commits): reject Co-Authored-By trailer, repo and consumer hooks

---

## [v1.53.0] — 2026-07-08

### Added

- feat(audit): detect toggle icon swap and bare conditional collapse

---

## [v1.52.0] — 2026-07-08

### Added

- feat(design-system): add rememberStyle() and StyleVariant marker interface

---

## [v1.51.0] — 2026-07-07

### Added

- feat(roborazzi): move interaction tests to commonTest via runComposeUiTest

---

## [v1.50.0] — 2026-07-07

### Added

- feat(imagevector-generator): support fetching remote Heroicons SVGs

---

## [v1.49.0] — 2026-07-07

### Added

- feat(adaptive-layout): document the FlexBox layout container

### Fixed

- fix(ci): install pytest before running the test suite

---

## [v1.48.0] — 2026-07-04

### Added

- feat(audit): detect empty platform-specific source sets

---

## [v1.47.2] — 2026-07-04

### Fixed

- fix(design-system): generate the real prefix directly, never leave App* to rename later

---

## [v1.47.1] — 2026-07-04

### Fixed

- fix(design-system-extended): rename Toast* to AppToast*, add missing AppCircularProgress

---

## [v1.47.0] — 2026-07-04

### Added

- feat(audit): complete Style API auditing; wire AppAvatar; document coverage honestly

---

## [v1.46.0] — 2026-07-04

### Added

- feat(design-system): derive component prefix from project name instead of hardcoding App

---

## [v1.45.3] — 2026-07-04

### Fixed

- fix(design-system): audit against official Compose Styles API docs; fix isEnabled bug

---

## [v1.45.2] — 2026-07-04

### Fixed

- fix(release): document + detect platform-native version field derivation (closes #2)

---

## [v1.45.1] — 2026-07-03

### Fixed

- fix: add repo-relative fallback paths for Codex/Gemini installs

---

## [v1.45.0] — 2026-07-03

### Added

- feat: imagevector-generator skill (59th) — raster/SVG → compiled ImageVector pipeline + deterministic layout contracts

---

## [v1.44.0] — 2026-06-30

### Added

- feat(layout-system): deterministic one-file-per-screen wireframe creator

---

## [v1.43.0] — 2026-06-30

### Added

- feat(lessons): deterministic per-lesson file creator (one file per finding)

---

## [v1.42.0] — 2026-06-29

### Added

- feat(audit): detect fixed widths that overflow a compact phone

---

## [v1.41.0] — 2026-06-29

### Added

- feat(audit): detect raw Material components that bypass the design system

---

## [v1.40.0] — 2026-06-29

### Added

- feat(audit): attach file:line + matched-source evidence to findings

---

## [v1.39.0] — 2026-06-29

### Added

- feat(audit): enforce repository-pattern boundary — interface must not expose DTO/entity

---

## [v1.38.0] — 2026-06-29

### Added

- feat(audit): detect string-based (non-type-safe) navigation

---

## [v1.37.3] — 2026-06-29

### Fixed

- fix(audit): catch ViewModel-in-ViewModel via property, instantiation, and DI lookup

---

## [v1.37.2] — 2026-06-29

### Docs

- docs: genericize examples in mvi/navigation skills — remove project-specific names

---

## [v1.37.1] — 2026-06-29

### Docs

- docs(navigation): add one-NavHost-+-nested-graphs vs multiple-NavHosts decision table

---

## [v1.37.0] — 2026-06-29

### Added

- feat(audit): harden detectors against alternate naming and domain-path assumptions

---

## [v1.36.2] — 2026-06-29

### Fixed

- fix(audit): detect color/spacing/dark-theme/layer smells by Compose content, not /ui/ path

---

## [v1.36.1] — 2026-06-29

### Fixed

- fix(audit): detect composable/VM smells regardless of /ui/ package path

---

## [v1.36.0] — 2026-06-29

### Added

- feat: detect ViewModel passed as composable param; align finding messages with decision order

---

## [v1.35.2] — 2026-06-29

### Docs

- docs: lead feature orchestration with separate-screens + NavHost + repository

---

## [v1.35.1] — 2026-06-29

### Fixed

- fix: ViewModel must never take another ViewModel as constructor param

---

## [v1.35.0] — 2026-06-29

### Added

- feat: detect god composables and add Coordinator ViewModel pattern to MVI skill

---

## [v1.34.0] — 2026-06-29

### Added

- feat: image palette extraction and multi-ViewModel screen detector

---

## [v1.33.0] — 2026-06-29

### Added

- feat(design-system): add dynamic palette generator with Compose preview output

---

## [v1.32.1] — 2026-06-29

### Docs

- docs: add kmm-harvest-lessons and kmm-audit-adaptive to README consumer commands table

---

## [v1.32.0] — 2026-06-29

### Added

- feat(audit): detect named color constants and hardcoded divider colors that break dark mode

---

## [v1.31.0] — 2026-06-29

### Added

- feat(audit): add redundant-title and adaptive-coverage detectors; new /kmm-audit-adaptive command

---

## [v1.30.1] — 2026-06-29

### Docs

- docs: feature auto-reporting + smart versioning in README; add harvest-lessons to consumer setup

---

## [v1.30.0] — 2026-06-29

### Added

- feat(commands): auto-report skill gaps and lessons as GitHub issues; add release auto-bump

---

## [v1.29.32] — 2026-06-29

### Added

- feat(skills): kotlin-multiplatform-library-publishing + library detection in kmm-setup-agents

### Fixed

- fix(library-publishing): add Output Style, Common Anti-Patterns, Related Skills sections
- fix(library-publishing): add required Trigger keywords, Freshness rule, and Changelog sections

### Chore

- chore: register library-publishing in README, expert map (58 skills), and planner routing

---

## [v1.29.32] — 2026-06-29

### Added

- feat(skills): new `kotlin-multiplatform-library-publishing` skill — vanniktech plugin setup, Sonatype OSSRH/Central Portal, GitHub Packages, multi-artifact BOM, binary-compatibility-validator (apiCheck/apiDump), GPG signing, SNAPSHOT vs stable channels, release checklist, iOS/SPM cross-reference
- feat(commands): `/kmm-setup-agents` now detects library vs app project type — library projects get a library-shaped AGENTS.md routing to `library-publishing`, `xcframework-spm`, `expect-actual`, `unit-testing`, `code-quality`, `ci-github-actions`
- feat(expert): `kotlin-multiplatform-library-publishing` registered in Skill Invocation Map with 20 trigger keywords

---

## [v1.29.31] — 2026-06-29

### Added

- feat(audit): --harvest mode + /kmm-harvest-lessons command for lesson collection pipeline

---

## [v1.29.31] — 2026-06-29

### Added

- feat(audit): `--harvest` mode in `audit_project.py` — outputs `{ findings, lessons }` JSON; detects 12 positive patterns consumers can upstream to skills (LocalAppDarkTheme, ThemeSettings persistence, currentIsDark(), BaseViewModel wrapper, timed undo window, Contract grouping, build-logic plugins, FuzzyMatcher, governance.yml, per-surface deploy workflows, agent setup)
- feat(commands): `/kmm-harvest-lessons` command — reads harvest JSON, checks each lesson against the target skill, and outputs actionable skill-update proposals with suggested section text
- feat(audit): `harvest_project(root)` public function for use in tests and future tooling

---

## [v1.29.30] — 2026-06-29

### Fixed

- fix(audit): guard _detect_agent_setup to real Gradle projects + fix test for ViewModel data-import exclusion
- fix(audit): exclude worktrees/ to prevent duplicate findings from .claude/worktrees/

### Chore

- chore: sync skills.json version to 1.29.29 to match highest git tag
- chore: restore CHANGELOG after failed release attempt, consolidate v1.29.30 section

### Other

- Release v1.29.28
- Release v1.29.27

---

## [v1.29.28] — 2026-06-29

### Fixed

- fix(audit): guard _detect_agent_setup to real Gradle projects + fix test for ViewModel data-import exclusion
- fix(audit): exclude worktrees/ to prevent duplicate findings from .claude/worktrees/

### Chore

- chore: restore CHANGELOG after failed release attempt, consolidate v1.29.30 section

### Other

- Release v1.29.27

---

## [v1.29.30] — 2026-06-29

### Fixed

- fix(audit): exclude `worktrees/` directory from `_EXCLUDED_DIRS` — prevents `.claude/worktrees/` agent scratch copies from being scanned, which was causing duplicate findings (same violation reported 5-6× for a single real file)
- fix(audit): guard `_detect_agent_setup` to real Gradle projects — empty temp dirs in unit tests no longer trigger agent-setup findings
- fix(audit): `test_audit_project_finds_smells` now uses a separate `AuthScreen.kt` for the data-import assertion (ViewModels are correctly excluded from that check)

---

## [v1.29.29] — 2026-06-29

### Fixed

- fix(audit): `iter_files` now scans `.kt`/`.kts` only — eliminates false positives from `.md` docs, skill references, and vendored READMEs
- fix(audit): exclude list expanded with `build/`, `.gradle/`, `.git/`, `vendor/`, `third_party/`, `node_modules/`, `.idea/`, `.kotlin/`, `kotlin-js-store/`, and any directory ending in `.cpp` (e.g. `llama.cpp/`, `stable-diffusion.cpp/` submodules)
- fix(audit): `data import in ui` pattern now skips `*ViewModel.kt` files — ViewModels legitimately import domain/data interfaces through repositories
- fix(design-system): added trigger keywords for `LocalAppDarkTheme`, `isSystemInDarkTheme`, `dark mode toggle`, `in-app theme override`, `user theme preference`, `dynamic theme`, `runtime theme switch`

---

## [v1.29.28] — 2026-06-29

### Added

- feat(audit): new checklist section 8 — Agent & Consumer Setup (AGENTS.md completeness, .claude/commands/, .claude/skills/, CLAUDE.md, multi-surface coverage)
- feat(audit): `_detect_agent_setup` in `audit_project.py` — HIGH/MEDIUM findings for missing .claude/ infrastructure
- feat(audit): `_detect_mvi_placement` — flags MviViewModel defined in a feature module instead of :shared:core
- feat(audit): `_detect_design_system_wiring` — flags MaterialTheme wrapping, hardcoded `darkTheme=false`, and parallel ULong token files

---

## [v1.29.27] — 2026-06-29

### Fixed

- fix(design-system): AppTheme now defaults to `isSystemInDarkTheme()` on all platforms — Android, iOS, and Desktop follow OS dark mode automatically without passing `darkTheme` explicitly
- fix(design-system): removed hardcoded `darkTheme = false` from Desktop and iOS Step 7 entry point wiring
- feat(design-system): added `LocalAppDarkTheme` (`compositionLocalOf<Boolean?>`) for in-app theme override — null=system, true=force dark, false=force light; wired before `AppTheme` call, no signature change needed

---

## [v1.29.26] — 2026-06-29

### Added

- feat(commands): close all remaining /kmm-new-project gaps

---

## [v1.29.25] — 2026-06-29

### Added

- feat(commands): enforce planning/implementation separation; add per-sprint gate

---

## [v1.29.24] — 2026-06-29

### Added

- feat(commands): add design token draft step to /kmm-new-project Step 6

---

## [v1.29.23] — 2026-06-29

### Added

- feat(commands): planning phase always drafts recommendations for easy selection

---

## [v1.29.22] — 2026-06-29

### Added

- feat(commands): add planning phase to /kmm-new-project (Step 3)

---

## [v1.29.21] — 2026-06-29

### Added

- feat(commands): add screen layout and design step to /kmm-new-project

---

## [v1.29.20] — 2026-06-29

### Fixed

- fix(commands): fix /kmm-new-project header prefix and add empty-args prompt

---

## [v1.29.19] — 2026-06-29

### Added

- feat(commands): fix kmm-new-project gaps; update GETTING_STARTED

---

## [v1.29.18] — 2026-06-29

### Docs

- docs(readme): restore docs-boundary classifier line required by test
- docs(readme): restore start-here and roadmap markers required by audit
- docs(readme): simplify README — lead with main use cases, cut diagrams and trigger table

---

## [v1.29.17] — 2026-06-29

### Added

- feat(skills): add proguard-r8, in-app-purchases, desktop-app; close remaining gaps

### Fixed

- fix(skills): update expert skill count 54→57; add new skills to planner routing table

---

## [v1.29.16] — 2026-06-29

### Added

- feat(commands): add /kmm-setup-agents command; agent generation in /kmm-new-project; expand README commands table

---

## [v1.29.15] — 2026-06-29

### Docs

- docs: add new project intake flow

### Other

- test: update command filename assertions to kmm- prefix
- refactor(commands): add kmm- prefix to all slash commands for namespacing

---

## [v1.29.14] — 2026-06-28

### Docs

- docs(readme): add trigger keywords for @Stable/@Immutable, CoroutineExceptionHandler, rememberUpdatedState

---

## [v1.29.13] — 2026-06-28

### Added

- feat(skills): @Stable/@Immutable annotations, CoroutineExceptionHandler, rememberUpdatedState

---

## [v1.29.12] — 2026-06-28

### Added

- feat(skills): combine/flatMapLatest/snapshotFlow patterns, WhileSubscribed rule, session scope, derivedStateOf

---

## [v1.29.11] — 2026-06-28

### Added

- feat(skills): collectAsStateWithLifecycle rule, LaunchedEffect decision table, SavedStateHandle Koin wiring

---

## [v1.29.10] — 2026-06-28

### Fixed

- fix(skills): correct AppNavigator Koin binding; expand CompositionLocal; complete README trigger keywords

---

## [v1.29.9] — 2026-06-28

### Added

- feat(skills): tie MVI + NavHost + clean architecture together end-to-end

---

## [v1.29.8] — 2026-06-28

### Added

- feat(audit): detect god ViewModels and missing feature layer split

---

## [v1.29.7] — 2026-06-28

### Added

- feat(mvi): add ViewModel size rule, decomposition guide, and god ViewModel anti-patterns

---

## [v1.29.6] — 2026-06-28

### Added

- feat(agents): add router, auditor, harvester agents; clarify skills vs agents split

---

## [v1.29.5] — 2026-06-28

### Added

- feat(skills): add migration skill, audit roadmap, and scaffold layer-depth decision
- feat(skills): refine MVI + clean-architecture skills and make both mandatory

### Other

- refactor(skills): enforce start-thin principle in MVI and clean-architecture

---

## [v1.29.4] — 2026-06-28

### Added

- feat(navigation): add bindToBrowserNavigation pattern for WasmJs hash routing

### Fixed

- fix(install): separate skills auto-deploy from commands manual install

---

## [v1.29.3] — 2026-06-28

### Other

- refactor(commands): rename /new-skill → /kmm-new-skill

---

## [v1.29.2] — 2026-06-28

### Added

- feat(skills): enforce kotlin-multiplatform- prefix on all suggested new skill names

---

## [v1.29.1] — 2026-06-28

### Added

- feat(consumer): add quick-update script, commit-msg hook, compat-matrix drift check, and fix stale README versions

---

## [v1.29.0] — 2026-06-28

### Added

- feat(release): add versioning tiers, commit-msg hook, and changelog policy

### Fixed

- fix(skills): add missing required sections and register layout-system, lessons, skill-harvester in expert/planner/README

### Docs

- docs(versioning): trim versioning-policy.md to under 150 lines
- docs: add dependency compatibility matrix with conflict zones

---

## [Unreleased]

_Dev commits accumulate here. This section is auto-promoted to a versioned entry when `scripts/release.py` is run. Do not edit this section manually — use conventional commits so the release script generates meaningful entries._

---

## [v1.28.6] — 2026-06-27

### Chore

- Bump all library versions to latest stable: agp 9.2.0, koin 4.2.2, ktor 3.5.0, sqldelight 2.3.2, buildkonfig 0.22.0, androidx-lifecycle 2.11.0, coroutines 1.11.0, roborazzi 1.64.0, navigation-compose 2.9.2, decompose 3.5.0
- Add `kotlin-multiplatform-layout-system` skill with ASCII wireframe templates (Patterns A–D), scroll annotations, phone variants, and platform column in component registry
- Fix compile-breaking issues across 7 skills: `id()` → `alias()`, missing catalog entries, KSP version scheme, CMP `@Preview` import, navigation test types, startKoin guard, cross-platform `sed`
- Add JVM-only API lint check to audit script (`_check_commonmain_jvm_apis`)
- Fix audit regex to accept YYYY-MM-DD-prefixed filenames

---

## [v1.28.5] — 2026-06-26

### Other

- Add collection discovery keywords to expert and audit skills

---

## [v1.28.4] — 2026-06-26

### Docs

- docs: refine layout and slot guidance

---

## [v1.28.3] — 2026-06-25

### Docs

- docs: enforce string resources in compose ui

---

## [v1.28.2] — 2026-06-25

### Docs

- docs: prefer commonMain before abstractions

---

## [v1.28.1] — 2026-06-25

### Docs

- docs: clarify repo vs consumer docs routing

---

## [v1.28.0] — 2026-06-25

### Docs

- docs(expert): add Required vs Optional skill classification

---

## [v1.27.1] — 2026-06-25

### Fixed

- fix(routing): make offline-first opt-in, stop auto-triggering on generic data terms

---

## [v1.27.0] — 2026-06-25

### Added

- feat: expand trigger keywords across 8 core skills for broad coverage

---

## [v1.26.1] — 2026-06-25

### Added

- feat: expand MVI and presenter trigger keywords for natural requests

---

## [v1.26.0] — 2026-06-24

### Docs

- docs: harden preview coverage audits

---

## [v1.25.20] — 2026-06-24

### Docs

- docs: refine routing precedence

---

## [v1.25.19] — 2026-06-24

### Docs

- docs: refine designer routing guidance

---

## [v1.25.18] — 2026-06-24

### Added

- feat: expand trigger keywords for data/content architecture requests

---

## [v1.25.17] — 2026-06-24

### Added

- feat: expand trigger keywords for broader instruction matching

---

## [v1.25.16] — 2026-06-24

### Docs

- docs: add wasmjs hash routing guidance
- docs: simplify README overview

---

## [v1.25.15] — 2026-06-24

### Docs

- docs: split repo and project docs routing
- docs: route ui-only planning through designer
- docs: add design handoff template
- docs: add designer agent for wireframes and layouts

---

## [v1.25.14] — 2026-06-24

### Docs

- docs: add logger wrapper contract
- docs: bump kotlin-logging to 8.0.4

---

## [v1.25.13] — 2026-06-24

### Docs

- docs: support kotlin-logging and Kermit

---

## [v1.25.12] — 2026-06-24

### Docs

- docs: guard consumer skill version pins

---

## [v1.25.11] — 2026-06-24

### Docs

- docs: add architecture diagram guidance for project docs

---

## [v1.25.10] — 2026-06-24

### Docs

- docs: add repo architecture diagram
- docs: route release project to release skill

---

## [v1.25.9] — 2026-06-24

### Docs

- docs: clarify consumer docs and changelog policy

---

## [v1.25.8] — 2026-06-24

### Docs

- docs: clarify skill scope and changelog path
- docs: add fix maturity lanes
- docs: add task lifecycle guidance
- docs: define archived task docs policy
- docs: support dated task docs folders
- docs: add default project docs topology
- docs: keep skills consumer-facing
- docs: add project and skill docs maintainers
- docs: clarify docs maintainer scope
- docs: add docs maintainer agent

---

## [v1.25.7] — 2026-06-23

### Docs

- docs: align skill routing indexes

### Chore

- chore: harden skill repo validation

---

## [v1.25.6] — 2026-06-23

### Chore

- chore(funding): remove Buy Me a Coffee (unsupported in Philippines)

---

## [v1.25.5] — 2026-06-23

### Chore

- chore(funding): update PayPal link

---

## [v1.25.4] — 2026-06-23

### Chore

- chore(funding): update donation addresses to Binance wallet

---

## [v1.25.3] — 2026-06-23

### Docs

- docs: add consumer getting started guide, license file, and funding options

---

## [v1.25.2] — 2026-06-23

### Other

- refactor: rename jni-kotlin-pro to kotlin-multiplatform-jni-pro

---

## [v1.25.1] — 2026-06-23

### Docs

- docs(readme): add release skill, governance section, clean up roadmap

---

## [v1.25.0] — 2026-06-23

### Added

- feat(governance): add CI enforcement gate for skill consumers

---

## [v1.24.1] — 2026-06-23

### Added

- feat(release): add development versioning guidance

---

## [v1.24.0] — 2026-06-23

### Added

- feat(release): add kotlin-multiplatform-release skill

---

## [v1.23.2] — 2026-06-23

### Added

- feat(ci): add Maven Central publish, Doppler, git-cliff changelog, versioning

### Fixed

- fix(report-skill-issue): add Step 0 triage gate — skill vs project issue

### Other

- Revert "feat(ci): add Maven Central publish, Doppler, git-cliff changelog, versioning"
- Release v1.23.1

---

## [v1.23.1] — 2026-06-23

### Fixed

- fix(report-skill-issue): add Step 0 triage gate — skill vs project issue

---

## [v1.23.0] — 2026-06-23

### Added

- feat(consumer): GitHub issue templates, /report-skill-issue command, draft_issue --submit

---

## [v1.22.0] — 2026-06-22

### Added

- feat(design-system): detect cross-screen layout inconsistency

---

## [v1.21.9] — 2026-06-22

### Docs

- docs(known-issues): add KI-007 — external skill trigger isolation unverifiable

---

## [v1.21.8] — 2026-06-22

### Other

- refactor(AGENTS.md): pointer model — remove embedded rule copies

---

## [v1.21.7] — 2026-06-22

### Other

- refactor(kotlin-multiplatform-jni-pro): compress B1/B2 bloat — merge stack sections, table-ify anti-patterns

---

## [v1.21.6] — 2026-06-22

### Fixed

- fix(routing): correct JNI skill vocabulary, cross-ref immutability rule, add routing matrix

### Chore

- chore: workspace agent config (AGENTS.md persona + CLAUDE.md CLI profile)

---

## [v1.21.5] — 2026-06-22

### Added

- feat(kotlin-multiplatform-jni-pro): header compatibility matrix + architectural feedback schema

---

## [v1.21.4] — 2026-06-22

### Added

- feat(kotlin-multiplatform-jni-pro): cmake-jni-setup.md + wrapper-patterns.md references

---

## [v1.21.3] — 2026-06-22

### Added

- feat(kotlin-multiplatform-jni-pro): Phase 0 discovery gate + wrapper-call pattern

---

## [v1.21.2] — 2026-06-22

### Fixed

- fix(kotlin-multiplatform-jni-pro): hard stop rule for 3rd party file modification

---

## [v1.21.1] — 2026-06-22

### Added

- feat(design-system): add references/design-system-template.md

### Docs

- docs(design-system): add References section for references/ directory

---

## [v1.21.0] — 2026-06-22

### Added

- feat(design-system): RedundantScreenTitleRule + HardcodedGridColumnsRule + MultiDevicePreview

---

## [v1.20.1] — 2026-06-22

### Fixed

- fix(design-system): use GROUP_ID placeholder in detekt-rules module

---

## [v1.20.0] — 2026-06-22

### Added

- feat(design-system): PSI-based detekt scanner + Roborazzi baselines + visual audit

### Chore

- chore: consolidate v1.19.1 CHANGELOG into single detailed entry

---

## [v1.19.1] — 2026-06-22

### Fixed

- fix(release): release script no longer prepends a duplicate CHANGELOG entry when a detailed one was already written manually; version guard now runs before git log so no subprocess call is made
- fix(audit): `_check_design_system()` now flags missing `## Component Previews` section and `### previews/` blocks in the base design-system skill
- test: update `_DS_GOOD_CONTENT` fixture to include previews section; add `test_ds_flags_missing_component_previews` (total: 126 tests)

---

## [v1.19.0] — 2026-06-22

### Added

- feat(design-system): add per-component preview files — `previews/AppThemePreviewWrapper.kt` + one preview file per base component (AppButton, AppBadge, AppCard, AppChip, AppTextField, AppText) with light/dark and key-state variants
- feat(design-system): extend `update_design_system.py` to sync `previews/` blocks alongside `components/` blocks; `find_component_dir` now returns parent dir so both subdirectories are covered
- feat(fix-design): add component-level Roborazzi step — run `:core:designsystem:jvmTest` first to verify components in isolation before feature tests
- test: add 7 tests for preview block parsing and syncing (total: 125 tests)

---

## [v1.18.0] — 2026-06-22

### Added

- feat(design-system): add `scripts/scan_design_violations.py` — scans Compose files for hardcoded colors, dp literals, MaterialTheme usage, TextStyle construction, and nested containers; exit 0/1/2, `--json` and `--file` modes
- feat(design-system): add `commands/kmm-fix-design.md` — fix violations file-by-file with per-file diff confirmation, regenerate Roborazzi screenshots, and verify fixes with Claude vision
- feat(expert): add `/fix-design` routing keywords to Skill Invocation Map
- test: add 22 tests for `scan_design_violations.py` (total: 120 tests passing)

---

## [v1.17.0] — 2026-06-22

### Added

- feat(design-system): add ownership model (project-owned tokens vs skill-owned components), stability tiers for all components, and `scripts/update_design_system.py`
- feat(design-system): add `/update-design-system` command with diff-and-confirm workflow
- feat(expert): add `/update-design-system` routing keywords to Skill Invocation Map
- test: add 13 tests for `update_design_system.py` (total: 98 tests)

---

## [v1.16.5] — 2026-06-22

### Other

- enforce(audit): add design-system content checks to audit_skills_repo

---

## [v1.16.4] — 2026-06-22

### Fixed

- fix(design-system): resolve all 7 audit findings

---

## [v1.16.3] — 2026-06-22

### Fixed

- fix(adaptive-layout): add missing trigger keywords for mobile/desktop/detail-split routing

---

## [v1.16.2] — 2026-06-21

### Other

- enforce(naming): document and audit file naming conventions

---

## [v1.16.1] — 2026-06-21

### Other

- refine(legal-docs): auto-detect data collection + consent gate explanation + CI gate

---

## [v1.16.0] — 2026-06-21

### Added

- feat(legal-docs): add kotlin-multiplatform-legal-docs lawyer agent skill

---

# Changelog

All notable changes to **kmm-agent-skills** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [v1.15.0] — 2026-06-21

### Added
- `CONTRIBUTING.md` — contribution guide covering skill authoring, commit format, PR checklist, and release process
- `agents/changelog.md` — changelog agent: categorizes git + skill diff into Breaking/New/Improved/Fixed and generates consumer-facing release notes
- `commands/kmm-release-notes.md` — `/release-notes` command: generates per-skill or collection release notes from git history and `## Changelog` tables
- `scripts/generate_release_notes.py` — reads git log, maps commits to skills, parses per-skill `## Changelog` tables; outputs structured JSON for the changelog agent
- `## Changelog` section added to all 47 skills — consumer-facing release note table travels with each skill when installed

### Changed
- `feature-scaffold` skill: app versioning pattern defined — `VERSION_NAME`/`VERSION_CODE` in `gradle.properties` as single source of truth; `androidApp` reads from properties; `BuildKonfig` exposes `APP_VERSION` to `commonMain`; `libs.versions.toml` is for dependency versions only
- `flavor-environment` skill: `APP_VERSION` added to `BuildKonfig defaultConfigs`; `AppConfig.versionName` added to public facade
- `feature-scaffold` skill Step 3 rewritten: mandatory `Kotlin/kmp-wizard` clone replaces manual file creation
- `feature-scaffold` skill Step 4 rewritten: extend kmp-wizard's build-logic rather than recreate it
- `feature-scaffold` anti-patterns: hand-scaffolding and precompiled `.gradle.kts` script plugins now listed as explicit blockers
- `/new-project` command F-01 step updated to clone-first mandate with `./gradlew help` gate
- `audit_skills_repo.py`: `## Changelog` added to `REQUIRED_MARKERS` — skills without it now fail the audit

### Fixed
- `kotlin-multiplatform-expert` skill: removed private Carpool project reference from docs-first rule

### Docs
- `kotlin-multiplatform-audit` skill: defined `[category] short description` issue title format with category table and examples

---

## [v1.14.0] — 2026-06-21

### Added
- `/new-project` command — natural language to full KMP scaffold, 8-step pipeline, no user gates; infers platforms, features, data, backend from a single prompt
- `samples/todo-app.md` — E2E test spec for the todo app: 4 features, SQLDelight persistence, 12 skills, objective pass/fail quality bar (audit + jvmTest + Roborazzi + visual audit)

### Changed
- `/verify` command: added Step 5 visual design audit (runs `/audit-screenshots` when PNGs modified)
- `agents/reviewer.md`: added Check 13 visual design audit on Roborazzi screenshots
- `kotlin-multiplatform-roborazzi` skill: documented visual design audit and dynamic path resolution

---

## [v1.13.0] — 2026-06-18

### Added
- `validate_keyword_routing.py` script — ensures every skill has at least one trigger keyword registered; now part of CI gate
- Visual design audit step integrated into `/verify` and `agents/reviewer.md`

### Fixed
- `/audit-screenshots` command: Roborazzi output directory resolved dynamically from `build.gradle.kts` instead of hardcoded path; falls back to `src/jvmTest/snapshots/` or `src/test/snapshots/`

---

## [v1.12.0] — 2026-06-21

### Added
- Tests for pipeline flag contract (KI-005) and hook script behaviour (KI-006)

---

## [v1.11.1] — 2026-06-21

### Added
- `/verify` command — KMP validation pipeline: module graph, unit tests, screenshot tests, architecture audit, summary

### Docs
- Updated `PLAN.md` and `KNOWN_ISSUES.md` to reflect v1.11.0 state

---

## [v1.11.0] — 2026-06-21

### Added
- Test maintenance enforcement: planner routing validation and skill freshness gates added to pipeline

---

## [v1.10.0] — 2026-06-21

### Added
- 7 pipeline gap fixes: planner routing, `/new-skill` command, Detekt rule reference, PR template, hooks guide, test additions, 2 new skills

---

## [v1.9.0] — 2026-06-21

### Added
- ktlint enforcement gate in CI and reviewer pipeline
- Proactive issue tracking: reviewer now creates `[build]` issues for lint failures

---

## [v1.8.0] — 2026-06-21

### Added
- `## Testing` sections added to 18 skills that were missing them
- Contribution rules added to `AGENTS.md`

### Fixed
- Medium-priority audit findings resolved across 6 skills

---

## [v1.7.1] — 2026-06-21

### Fixed
- `[TRANSPORT]` fixer rule for kRPC boundary enforcement
- Stale shipped-skill count in `PLAN.md`
- kRPC context flag added to `pipeline-context.json`
- Run-audit quality scan added to release gate

---

## [v1.7.0] — 2026-06-21

### Added
- `/summarize-issues` command — scans all skills for quality gaps and outputs copy-paste fix prompts
- `scan_skill_issues.py` script — automated gap detection across the skills repo

---

## [v1.6.0] — 2026-06-21

### Added
- Skills freshness check at pipeline start — auto-detects when local skills are behind `origin/main` and prompts the user to pull before proceeding

---

## [v1.5.2] — 2026-06-21

### Fixed
- `kotlin-multiplatform-mongodb-database`: added `## Testing` section covering `FakeRepository`, Flapdoodle integration tests, change stream testing, and document mapping

---

## [v1.5.1] — 2026-06-21

### Fixed
- `kotlin-multiplatform-kotlin-rpc`: added kRPC transport pre-check to prevent HTTP bypass when RPC already owns the boundary

---

## [v1.5.0] — 2026-06-21

### Added
- 11 new skills: `analytics`, `form-validation`, `image-loading`, `permissions`, `deep-linking`, `compose-animation`, `biometric-auth`, `push-notifications`, `workmanager`, `feature-flags`, `accessibility`

---

## [v1.4.0] — 2026-06-21

### Added
- `kotlin-multiplatform-paging` skill — Paging 3 for KMP: `PagingSource`, `Pager`, `PagingData`, cursor vs offset, `RemoteMediator`, load-state handling

### Fixed
- `adaptive_layout_migration_mode` flag added to `pipeline-context.json` (KI-003)
- Pipeline context committed at end of every pipeline run (KI-001)
- `scripts/install-hooks.sh` one-liner added (KI-002)

---

## [v1.3.0] — 2026-06-21

### Added
- Screen layout contract and scaffold consistency enforcement in reviewer
- `kotlin-multiplatform-adaptive-layout` skill — WindowSizeClass breakpoints, list-detail, adaptive navigation
- Magic color literal detection in `audit_project.py`

### Fixed
- `audit_project.py`: excluded `0.dp` from hardcoded spacing pattern (KI-004)

### Docs
- `KNOWN_ISSUES.md` created with 4 open and 5 resolved issues

---

## [v1.2.3] — 2026-06-20

### Added
- `kotlin-multiplatform-jni-pro` skill — JNI bridge from Kotlin/JVM to native C/C++; 4-layer stack, memory safety, symbol isolation, GPU sync

### Fixed
- Added `## References` section to skills that have a `references/` directory

---

## [v1.2.2] — 2026-06-18

### Changed
- Rebranded all pipeline agent, command, and hook files with `kmm-agent-skills` identity

---

## [v1.2.1] — 2026-06-18

### Added
- `/execute-ticket` command — 9-phase pipeline: fetch GitHub Issue → plan → branch → implement → validate → review → commit → pipeline-context update → summary

---

## [v1.2.0] — 2026-06-18

### Added
- `agents/planner.md` — Layer Planner with work-type skill loading matrix and 6-layer build order
- `agents/implementer.md` — Layer Implementer with stack declaration, layer rules, Koin wiring, test generation
- `agents/reviewer.md` — Architecture Reviewer with 5 checks and APPROVE / NEEDS_FIXES verdict
- `agents/validator.md` — Build Validator with 4 graduated validation levels
- `agents/fixer.md` — Targeted Fixer with per-blocker fix rules and confidence ratings
- `commands/kmm-implement-feature.md`, `commands/kmm-review-changes.md`, `commands/kmm-run-audit.md`
- `hooks/pre-commit-audit.sh`, `hooks/validate-architecture.sh`, `hooks/check-skill-freshness.sh`
- `.claude/pipeline-context.json` — pipeline state store shared across agents

---

## [v1.1.7] — 2026-06-17

### Docs
- `## Trigger Keywords` table added to README — 31 rows, 3–4 phrases per skill

---

## [v1.1.6] — 2026-06-17

### Fixed
- Expanded trigger keywords across 14 skills to close natural-language routing gaps

---

## [v1.1.5] — 2026-06-17

### Fixed
- `kotlin-multiplatform-roborazzi` trigger keywords expanded to cover canvas/layout testing queries

---

## [v1.1.4] — 2026-06-17

### Added
- `manual screen capture` audit pattern in `audit_project.py` — flags Playwright, `adb screencap`, `xcrun simctl io`

---

## [v1.1.3] — 2026-06-17

### Changed
- `kotlin-multiplatform-roborazzi` expanded to cover the full UI testing stack including `@Preview` screenshot workflow

---

## [v1.1.2] — 2026-06-17

### Fixed
- YAML parse error in `roborazzi` and `preview-driven-development` skills (`@Preview` value unquoted)

### Added
- `.claude-plugin/plugin.json` for marketplace submission

---

## [v1.1.1] — 2026-06-17

### Fixed
- Full audit pass across all 31 skills — missing sections, stale `last-updated` frontmatter

---

## [v1.1.0] — 2026-06-17

### Added
- `kotlin-multiplatform-datastore` skill — Preferences DataStore, `createDataStore {}` expect/actual factory, Flow reads, Koin wiring, SharedPreferences migration

---

## [v1.0.2] — 2026-06-17

### Fixed
- Test coverage expanded from 12 to 16 tests covering two high-priority gaps

---

## [v1.0.1] — 2026-06-17

### Added
- `skills.sh.json` manifest and `npx skills add` install path
- `scripts/release.py` release automation
- `RELEASING.md` release guide

---

## [v1.0.0] — 2026-06-17

### Added
- Initial release — 6-layer clean architecture, 31 skills, `skills.json` manifest
- `audit_project.py` — KMP architecture smell detector
- `audit_skills_repo.py` — skills repo metadata and freshness checker
