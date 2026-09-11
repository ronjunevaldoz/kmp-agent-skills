# Versioning Policy

Canonical rules for commits, changelogs, and releases. Agents and contributors must follow exactly.

---

## Version Tiers

| Tier | Tag | Example | GitHub Release | CHANGELOG |
|---|---|---|---|---|
| **dev** | none | — | no | never touched manually |
| **rc** | `vX.Y.Z-rc.N` | `v1.29.0-rc.1` | pre-release | auto-generated |
| **stable** | `vX.Y.Z` | `v1.29.0` | full release | auto-generated |

**dev** — commit freely; CHANGELOG is never edited manually; hook enforces Conventional Commit format.

**rc** — `python3 scripts/release.py <bump> --rc`; tags `vX.Y.Z-rc.N` (N auto-increments); pre-release GitHub Release; dev commits continue normally after.

**stable** — `python3 scripts/release.py <bump>`; CHANGELOG auto-generated from git log since last stable tag; full GitHub Release. Never create this tag manually.

---

## Commit Format

Every commit must follow Conventional Commit format — enforced by `.githooks/commit-msg`:

```
<type>[optional scope]: <description>
```

| Type | When |
|---|---|
| `feat` | New skill, audit pattern, script, command |
| `fix` | Bug fix in skill, script, or tooling |
| `docs` | Documentation only |
| `chore` | Version bumps, housekeeping |
| `refactor` | Restructuring, no behavior change |
| `test` | Adding or updating tests |
| `build` / `ci` | Build system, CI/CD |

Examples: `feat(skills): add layout-system skill` · `fix: correct KSP version` · `chore(versions): bump ktor 3.5.0`

Rejected: `wip` · `fix stuff` · `update` · `agent commit`

### Atomic Commits vs. Micro-Commit Bloat

- **One atomic commit per completed task lane**: Group the whole feature/fix (source, documentation, and unit tests) into a single cohesive commit.
- **No broken intermediate commits**: The repository must build cleanly and pass all tests at every commit on `main`.
- **Amend rather than churn**: If a typo, lint error, or small omission is discovered after committing but before pushing to remote, use `git commit --amend --no-edit` or `git commit --fixup <sha>` + `git rebase -i --autosquash`.
- **Low-entropy messages rejected**: Messages like `fix: typo`, `feat: wip`, `test: fix`, or single-word descriptions are blocked by the `commit-msg` hook.

---


## CHANGELOG Rules

| Action | Rule |
|---|---|
| Dev commit | Do NOT touch CHANGELOG.md |
| RC or stable release | `release.py` auto-generates from git log |
| Manual edit | Only to fix a typo in an already-released entry |

Good commit messages → meaningful CHANGELOG entries.

---

## Version Bump Decision

| What changed | Bump | Conventional Commit type |
|---|---|---|
| Bug fix, typo, version update, freshness date | `patch` | `fix`, `chore`, `docs`, `refactor`, `test` |
| New skill, new command, new script, new pattern | `minor` | `feat` |
| Skill renamed/removed, schema broken, command deleted | `major` | `feat!` or `BREAKING CHANGE` footer |

**Rule:** Multiple small `fix` commits do NOT justify a `minor` bump — only `feat` does.
**Rule:** Do not accumulate 5+ patch releases in one session without a `minor`. If a session
adds a new skill or command, that session's release must be `minor`, not a string of patches.

---

## Release Commands

```bash
# Preferred: let the script detect the bump from conventional commits
python3 scripts/release.py auto            # → detects major/minor/patch from git log

# Manual override (use only when auto gets it wrong)
python3 scripts/release.py patch           # → vX.Y.Z stable
python3 scripts/release.py minor           # → vX.(Y+1).0 stable
python3 scripts/release.py major           # → v(X+1).0.0 stable

# Pre-release
python3 scripts/release.py auto --rc       # → vX.Y.Z-rc.1 (N auto-increments)
python3 scripts/release.py auto --dry-run  # preview what bump auto would pick
```

**`auto` mode logic:**
- Scans `git log <last-stable-tag>..HEAD` subject + body lines
- `feat!:` or `BREAKING CHANGE` in any commit → `major`
- `feat:` or `feat(scope):` in any commit → `minor`
- Only `fix`/`chore`/`docs`/`refactor`/`test`/`build`/`ci` → `patch`

---

## Hard Rules for Agents

1. **Never `git tag` manually** — always use `scripts/release.py`.
2. **Never edit `CHANGELOG.md`** for dev commits.
3. **Every commit must use Conventional Commit format** — hook enforces this.
4. **Do not push** tags or release commits without explicit user confirmation.
5. Stable release requires clean tree + passing audit + passing tests — the script enforces this, do not bypass.

---

## Activating the Hook

```bash
git config core.hooksPath .githooks   # run once per clone
```
