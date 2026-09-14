---
name: kmp-github-issue-governance
description: >
  Govern GitHub issue creation, sub-issue hierarchy, and status updates for KMP
  repositories. Use when decomposing work into epics and sub-issues, preventing ticket
  spam or comment flooding, drafting bug reports and technical tasks, or transporting
  markdown payloads safely through the GitHub CLI without escaping corruption.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-14'
  keywords:
    - github issue
    - sub-issue
    - epic
    - ticket spam
    - comment flooding
    - gh cli
    - issue template
    - markdown corruption
    - in-place updates
---

# GitHub Issue & Sub-Issue Governance

## When to Use This Skill

Use this skill when:
- Deciding whether a new initiative warrants an **Epic**, a **Standalone Feature/Bug**, or a **Child Sub-Issue**
- Decomposing multi-PR roadmaps into structured parent-child issue hierarchies
- Posting status or progress reports to GitHub issues without spamming tickets with repetitive comments
- Safely transmitting multi-line markdown with code blocks, backticks, or tables via GitHub CLI (`gh`)
- Preventing shell-stripping bugs and raw `\n\n` escape artifacts in public issue bodies

**Trigger keywords:** github issue, sub-issue, epic, ticket spam, issue template, gh issue, comment flooding, markdown corruption, gh sub-issue, in-place update.

## Recommendation First

Three hard defaults eliminate ticket clutter and markdown corruption:

1. **Decompose multi-PR tracks into an Epic first.**
   Never create loose root tickets for active milestones; attach child sub-issues with `gh_sub_issue.py`.
2. **Never pass multi-line markdown via `-b` or `--body`.**
   Always write payloads to a temporary file and pass `--body-file` or piped stdin.
3. **Use in-place updates over comment spam.**
   Update checkboxes in the issue description or edit the pinned status comment via REST/GraphQL API.

---

## 1. Issue Hierarchy Decision Engine

Always classify the unit of work before filing a GitHub issue:

```
                          Is the work contained within
                                a single atomic PR?
                                  /            \
                                YES             NO
                                /                \
                Is it a bug or a feature?    Does it belong to an
                  /                  \       existing epic/roadmap?
                BUG                FEATURE       /            \
                /                      \       YES             NO
          bug_report.yml       feature_request.yml /             \
       (standalone bug)      (standalone feature)  /               \
                                            task.yml            epic.yml
                                          (sub-issue)        (umbrella epic)
```

### Classification Rules

| Issue Type | Template | When to Use | Attachment Rule |
|---|---|---|---|
| **Epic** | `epic.yml` | Multi-PR roadmap (3+ PRs), cross-platform verification matrix (Desktop + Wasm + Vulkan), multi-day effort | Parent container. Never attached as a child. |
| **Sub-Issue** | `task.yml` | Concrete technical track, refactor slice, or sub-task belonging to an active Epic | **Must** be attached to parent Epic via `gh_sub_issue.py add` or `create`. |
| **Standalone Feature** | `feature_request.yml` | Single-PR enhancement with no children | Top-level root issue. |
| **Standalone Bug** | `bug_report.yml` | Localized regression or defect not part of an ongoing Epic | Top-level root issue. (Attach to Epic if found during Epic testing). |

Full matrix: [references/epic-vs-subissue-matrix.md](references/epic-vs-subissue-matrix.md).

---

## 2. Anti-Spam & Comment Governance

Repetitive micro-status comments (`Audit update`, `Still working`, `Fresh build`) pollute notification streams and turn issue boards into unreadable logs.

### Operational Guardrails

1. **Maximum 1 Comment Per Session Per Issue**:
   Never append multiple interim comments during a single debugging or execution run.
2. **In-Place Progress Updates (Mandatory)**:
   - When marking progress, check off the task checkbox in the issue description:
     ```markdown
     - [x] Isolate Game play session from Scene3D editor (#27)
     ```
   - If editing a pinned status comment, update the comment in place via GitHub REST/GraphQL API instead of appending a new comment:
     ```bash
     gh api -X PATCH "repos/{owner}/{repo}/issues/comments/{comment_id}" \
       -f body="$(cat /tmp/status-update.md)"
     ```
3. **New Comments Restricted to Milestone Transitions**:
   Only post a new issue comment on verifiable state transitions:
   - **BLOCKED**: With a direct link to the blocking issue or dependency.
   - **READY FOR REVIEW**: With a direct link to the opened Pull Request.
   - **RESOLVED / CLOSED**: With closing commit SHAs and verified test evidence.

---

## 3. Shell-Safe Markdown Transport (Hard Boundary)

Passing markdown containing backticks, newlines, or special characters through CLI flags (`-b "..."` or `--body "$STR"`) causes severe payload corruption:
- Double quotes cause bash/zsh to execute backticks `` `command` `` as subshell substitutions, stripping branch names and code identifiers.
- String interpolation often escapes newlines into literal `\n\n` characters visible as plain text in the GitHub UI.

### Mandatory CLI Transport Recipes

#### Pattern A: Temporary File with `--body-file` (Recommended)
Always write rendered markdown to a temporary file before invoking `gh`:

```bash
# 1. Generate clean markdown
cat <<'EOF' > /tmp/issue-payload.md
### Problem
The orientation gizmo inherits `renderer.wireframe`.

### Evidence
- `SceneOrientationGizmo.kt` prepares offscreen pass with `renderer.wireframe`.
- Vulkan pipeline uses wireframe state.
EOF

# 2. Transmit safely via --body-file
gh issue create --title "bug(editor): isolate gizmo wireframe" \
  --body-file /tmp/issue-payload.md \
  --label "bug"

# 3. Clean up
rm -f /tmp/issue-payload.md
```

#### Pattern B: Quoted Heredoc via Stdin
When piping directly from a script, quote `'EOF'` to suppress shell parameter and subshell expansion:

```bash
cat <<'EOF' | gh issue comment 27 --body-file -
Audit update: **COMPLETE**
- Verified branch `refactor/studio-authoring-boundaries`
- Desktop and WebGPU pass regression tests
EOF
```

Full details and GraphQL recipes: [references/shell-safe-gh-cli.md](references/shell-safe-gh-cli.md).

---

## 4. Automation Tools

This skill bundles two scripts in `scripts/`:

1. **`validate_issue_payload.py`**: Pre-flight linting of issue markdown payloads:
   - Flags literal `\n\n` escape sequences
   - Detects unclosed backticks and unclosed code fences
   - Verifies required section headings against issue templates
   ```bash
   python3 scripts/validate_issue_payload.py /tmp/payload.md --template task
   ```

2. **`gh_sub_issue.py`**: Native GitHub Sub-Issues GraphQL CLI helper:
   ```bash
   # Attach existing issue 27 as a sub-issue of Epic 39
   python3 scripts/gh_sub_issue.py add 39 27

   # Create a new sub-issue attached directly to Epic 39
   python3 scripts/gh_sub_issue.py create 39 \
     --title "task(studio): align gizmo handles" \
     --body-file /tmp/payload.md \
     --label "task"

   # List all sub-issues of Epic 39
   python3 scripts/gh_sub_issue.py list 39
   ```

---

## Common Anti-Patterns

| Mistake | Fix |
|---|---|
| Creating 5–10 root-level issues for a single feature initiative | Create 1 Epic (`epic.yml`) and attach child sub-issues via `gh_sub_issue.py create` |
| Using `-b "..."` with text containing backticks or newlines | Always use `--body-file payload.md` or `cat <<'EOF' \| gh ... --body-file -` |
| Appending micro-status comments every time a test passes or fails | Update checkboxes in the issue description or edit the pinned status comment in place |
| Filing an Epic for a single-PR task | Use `feature_request.yml`; reserve Epics strictly for multi-PR milestones |
| Leaving sub-issues unlinked in issue descriptions | Use `gh_sub_issue.py add <parent> <child>` so GitHub's native progress bar tracks completion |
| Submitting markdown with literal `\n\n` text | Run `validate_issue_payload.py` to ensure newlines are real byte linebreaks, not escaped strings |

**Freshness rule:** recheck GitHub GraphQL API schemas for Sub-Issues (`addSubIssue`, `removeSubIssue`) before modifying mutation queries, as GitHub evolves project and issue GraphQL endpoints.

## Testing

Validate this skill with short payload validation and CLI argument checks:
- `@Test` the payload validator against corrupt literal `\n\n` strings and unclosed code fences (`test_github_issue_governance.py`).
- `runTest` on `gh_sub_issue.py` argument parsing and command registration with a fake/mock subprocess runner.
- Use a fake payload file when verifying template section conformance.

## Related Skills

- `kmp-ci-github-actions` — automation workflows and CI triggers for pull requests
- `kmp-release` — release tagging, GitHub Release publishing, and changelogs
- `kmp-audit` — repository health checks and drafting issues from findings (`draft_issue.py`)
- `kmp-expert` — skill sequencing and feature decomposition

## Output Style

1. Identify the unit of work (Epic, Standalone Feature, or Sub-Issue).
2. Write the markdown payload to a local temporary file.
3. Run `validate_issue_payload.py` to confirm syntax and section completeness.
4. Output the exact `gh` command using `--body-file`.

Keep it terse and factual.

---

## References

- [references/epic-vs-subissue-matrix.md](references/epic-vs-subissue-matrix.md) — Comprehensive decision matrix for Epics, Features, Tasks, and Bugs.
- [references/shell-safe-gh-cli.md](references/shell-safe-gh-cli.md) — Technical guide on shell quoting, subshell escaping, and GitHub CLI transport.

---

## Changelog

| Date | Change |
|---|---|
| 2026-09-14 | Initial release — codified Epic vs Sub-Issue decision tree, comment throttling rules, shell-safe CLI transport via `--body-file`, pre-flight payload validation (`validate_issue_payload.py`), and native GraphQL sub-issue integration (`gh_sub_issue.py`). |
