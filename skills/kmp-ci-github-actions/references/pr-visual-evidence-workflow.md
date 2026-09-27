# PR Visual Evidence Workflow (Optional)

Part of `kmp-ci-github-actions`. Load this file when working on: before/after screenshot
comment on pull requests.

---

Posts (or updates in place) one PR comment with a Before | After table for every changed
committed snapshot PNG. No Gradle, no JDK — just `git`, `python3`, and `gh`, so it runs in
seconds. It complements, not replaces, the evidence in the PR body
(`kmp-delivery-lifecycle` Phase 3A.3).

**Setup:** copy `kmp-roborazzi/scripts/pr_visual_evidence.py` (stdlib only) into the
project as `scripts/pr_visual_evidence.py`. Adjust `paths:` and add `--glob` if goldens
don't live under a `snapshots/` directory.

```yaml
# .github/workflows/pr-visual-evidence.yml
name: PR visual evidence

on:
  pull_request:
    paths:
      - '**/snapshots/**'

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: pr-visual-evidence-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  comment:
    # Fork PRs get a read-only token and cannot comment — skip them.
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # not the synthetic merge commit
          fetch-depth: 0                                   # merge-base needs history

      - name: Render before/after table
        env:
          BASE_REF: ${{ github.base_ref }}
        run: python3 scripts/pr_visual_evidence.py --target "origin/$BASE_REF" > visual.md

      - name: Post or update PR comment
        env:
          GH_TOKEN: ${{ github.token }}
          PR: ${{ github.event.pull_request.number }}
          REPO: ${{ github.repository }}
        run: |
          id=$(gh api "repos/$REPO/issues/$PR/comments" --paginate \
            --jq '.[] | select(.body | startswith("<!-- pr-visual-evidence -->")) | .id' | head -n1)
          if [ -n "$id" ]; then
            gh api -X PATCH "repos/$REPO/issues/comments/$id" -F body=@visual.md > /dev/null
          elif grep -q '<table>' visual.md; then
            gh pr comment "$PR" --repo "$REPO" --body-file visual.md
          fi
```

Notes:
- The script's output starts with a `<!-- pr-visual-evidence -->` marker; the job finds
  its own comment by that marker and edits it, so pushes never stack comments.
- No comment is created when no snapshot changed; an existing one is updated to the
  one-line "No before/after" message.
- Images are SHA-pinned `blob/<sha>/<path>?raw=true` links. In private repos they render
  only for signed-in members.
- Keep this job out of required checks — it is reviewer convenience, not a gate. The
  Roborazzi verify job (`kmp-roborazzi` → `references/ci-integration.md`) is the gate.
