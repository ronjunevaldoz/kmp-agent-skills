---
name: kmp-github-issue-governance
description: >
  Govern GitHub issue creation, sub-issue hierarchy, and status updates for KMP
  repositories. Use when decomposing work into epics and sub-issues, preventing ticket
  spam or comment flooding, drafting bug reports and technical tasks, tracking work a PR
  defers, labelling issues so they can be prioritised, or transporting markdown payloads
  safely through the GitHub CLI without escaping corruption.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-10-09'
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
    - deferred work
    - triage labels
    - priority
---

# GitHub Issue & Sub-Issue Governance

## When to Use This Skill

Use this skill when:
- Deciding whether a new initiative warrants an **Epic**, a **Standalone Feature/Bug**, or a **Child Sub-Issue**
- Decomposing multi-PR roadmaps into structured parent-child issue hierarchies
- Posting status or progress reports to GitHub issues without spamming tickets with repetitive comments
- Safely transmitting multi-line markdown with code blocks, backticks, or tables via GitHub CLI (`gh`)
- Preventing shell-stripping bugs and raw `\n\n` escape artifacts in public issue bodies
- Opening or merging a PR that defers work, or closing an issue
- Labelling issues so a backlog can be ordered by priority

**Trigger keywords:** github issue, sub-issue, epic, ticket spam, issue template, gh issue, comment flooding, markdown corruption, gh sub-issue, in-place update, deferred work, triage labels, priority.

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

### Milestone & Version Target Binding (Mandatory)

Never create or merge tickets without an explicit release destination:
1. **Every Epic and Sub-Issue MUST have a Milestone**:
   - Assign the issue to the target release cycle:
     ```bash
     gh issue create --title "..." --body-file /tmp/payload.md --milestone "v0.3.0"
     ```
   - If a milestone is undecided, assign it to a designated triage milestone (e.g. `Backlog` or `Next`), never left blank.
2. **Pull Requests MUST inherit the Issue Milestone**:
   - When opening a PR, attach the corresponding milestone immediately:
     ```bash
     gh pr create --title "..." --body-file /tmp/pr-payload.md --milestone "v0.3.0"
     ```
3. **Commit SemVer Parity**:
   - The conventional commit prefix must reflect the targeted milestone version change (`fix:` for patch releases, `feat:` for minor features, `BREAKING CHANGE:` for major releases).

### Deferred Work Becomes an Issue (Mandatory)

A PR body's "Not in this PR", "Follow-ups" or "Known limits" list is not tracking; it disappears
once the PR merges. Before opening or merging a PR:

1. Every deferred bullet links the issue that tracks it (`#123`, `owner/repo#123`, or an issue URL),
   or is cut from the body. File the issue first.
2. Check it: `gh pr view <n> --json body --jq .body | python3 scripts/validate_issue_payload.py - --pr`.
3. A verification-only remainder (a device or emulator check) stays the issue's last unchecked
   "Done when" bullet with an owner, or becomes its own issue.

### Closing an Issue

Close only when every "Done when" bullet holds **on the default branch**, not in a PR description.
A PR that says it deleted a file, verified on a device, or shipped a half "earlier" is a claim;
check the tree or the linked PR. Reopen an issue closed with an unmet bullet, saying which one.

### Triage Labels (Mandatory)

Milestones say *when*; labels say *what first*. Every open issue carries exactly one of each:

| Axis | Labels | Meaning |
|---|---|---|
| Type | `bug`, `enhancement`, `task`, `documentation` | Defect, new capability, internal work, docs |
| Priority | `priority: P0` … `priority: P3` | P0 broken release or data loss; P1 blocks the milestone or a user flow; P2 should land this milestone; P3 when convenient |
| Area | `area: <name>` | One per subsystem, named after the repo's modules (`area: render`, `area: input`) |

Create the taxonomy once per repository (idempotent):

```bash
for l in "priority: P0|b60205" "priority: P1|d93f0b" "priority: P2|fbca04" "priority: P3|c5def5" "task|ededed"; do
  gh label create "${l%%|*}" --color "${l##*|}" --force
done
gh label create "area: render" --color 1d76db --force   # one per subsystem
```

File with all three: `gh issue create ... --label bug --label "priority: P1" --label "area: render"`.
Order work by milestone, then priority, then dependency. Find gaps with
`gh issue list --state open --search "-label:\"priority: P0\" -label:\"priority: P1\" -label:\"priority: P2\" -label:\"priority: P3\""`.

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

## 4. Visual & Verification Evidence Standards (PRs & Issues)

Visual changes, rendering bugs, and multi-platform behavioral fixes require objective evidence attached to the issue or PR.

### PR Visual Comparison: Before vs After Table (Recommended)
For any UI, theme, shader, or layout adjustment, place a side-by-side comparison table directly under the PR summary. Use fixed HTML width attributes (`width="380"`) so images do not distort table columns or overflow GitHub's review container:

```markdown
## Visual Changes

| Before | After |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/xxxx-before" width="380" alt="Before" /> | <img src="https://github.com/user-attachments/assets/yyyy-after" width="380" alt="After" /> |
```

### Multi-Platform & Diagnostic Captures: Collapsible `<details>` Block
When providing proof across multiple platforms (e.g. Desktop Vulkan, Wasm WebGPU, iOS Metal) or lengthy execution logs, wrap evidence in a `<details>` block to prevent vertical clutter:

```markdown
<details>
<summary><b>📸 Visual Verification (Desktop & WebGPU)</b></summary>

### Desktop Vulkan
<img src="https://github.com/user-attachments/assets/xxxx-desktop" width="700" alt="Desktop Vulkan" />

### WebGPU / Wasm
<img src="https://github.com/user-attachments/assets/yyyy-webgpu" width="700" alt="WebGPU" />

</details>
```

### Media Inclusion Rules
1. **Drag-and-Drop / CDN URLs (`user-attachments`)**:
   - In GitHub Web UI: Paste or drag images (`.png`, `.jpg`, `.webp`) or animated clips (`.gif`, `.mp4` < 10MB) into the markdown editor. GitHub generates persistent `https://github.com/user-attachments/assets/<uuid>` URLs.
2. **Committed Assets — SHA-Pinned Blob URLs (agents: use this)**:
   - `gh` and the REST API cannot upload attachments, so an agent cannot produce `user-attachments` URLs.
     Link committed files by commit SHA instead — branch-pinned URLs break once the branch is deleted:
     `https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true`
   - For UI PRs, generate the Before/After table from committed Roborazzi goldens with
     `kmp-roborazzi/scripts/pr_visual_evidence.py` (recipe: `kmp-delivery-lifecycle` Phase 3A.3).
   - Private repos: these images render only for signed-in members.
3. **CLI Transport with Images**:
   - When using `gh pr create` or `gh issue create`, ensure image markdown tags (`![Alt](url)`) or HTML tags (`<img src="url" />`) reside inside your temporary `--body-file` to prevent shell stripping of quotes or brackets.

---

## 5. Automation Tools

This skill bundles two scripts in `scripts/`:

1. **`validate_issue_payload.py`**: Pre-flight linting of issue markdown payloads:
   - Flags literal `\n\n` escape sequences
   - Detects unclosed backticks and unclosed code fences
   - Verifies required section headings against issue templates
   ```bash
   python3 scripts/validate_issue_payload.py /tmp/payload.md --template task
   # PR body: every deferred item must link its issue
   gh pr view 42 --json body --jq .body | python3 scripts/validate_issue_payload.py - --pr
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
| Listing "Not in this PR" items with no issue | File each, link it, and run `validate_issue_payload.py - --pr` |
| Closing an issue because the PR says it's done | Check every "Done when" bullet on the default branch first |
| Filing issues with a milestone but no labels | Add one type, one `priority: P*` and one `area:` label |
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
3. Run `validate_issue_payload.py` to confirm syntax and section completeness (`--pr` for PR bodies).
4. Output the exact `gh` command using `--body-file`, with a milestone and type, priority and area labels.

Keep it terse and factual.

---

## References

- [references/epic-vs-subissue-matrix.md](references/epic-vs-subissue-matrix.md) — Comprehensive decision matrix for Epics, Features, Tasks, and Bugs.
- [references/shell-safe-gh-cli.md](references/shell-safe-gh-cli.md) — Technical guide on shell quoting, subshell escaping, and GitHub CLI transport.

---

## Changelog

| Date | Change |
|---|---|
| 2026-10-09 | `validate_issue_payload.py --pr`: prose that starts with a trigger word ("Deferred loading is ...") no longer opens a deferred list; any paragraph or `Label:` line ends it; numbered items are checked; code blocks are skipped. |
| 2026-10-03 | Deferred work must link an issue (`validate_issue_payload.py --pr` checks it), issues close only when "Done when" holds on the default branch, and every open issue carries a type, `priority: P0`–`P3` and `area:` label. |
| 2026-09-27 | Media Inclusion Rules: replaced branch-pinned raw URLs with SHA-pinned `blob/<sha>/<path>?raw=true` links and pointed agents (which cannot upload attachments via `gh`) to `kmp-roborazzi/scripts/pr_visual_evidence.py`. |
| 2026-09-15 | Added Visual & Verification Evidence Standards: Before vs After tables, collapsible `<details>` blocks for multi-platform captures, and shell-safe media inclusion rules. |
| 2026-09-14 | Initial release — codified Epic vs Sub-Issue decision tree, comment throttling rules, shell-safe CLI transport via `--body-file`, pre-flight payload validation (`validate_issue_payload.py`), and native GraphQL sub-issue integration (`gh_sub_issue.py`). |
