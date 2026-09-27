# Epic vs Sub-Issue Decision Matrix & Lifecycle

Part of `kmp-github-issue-governance`. Load this file when deciding how to structure and decompose new issues.

---

## 1. Unit of Work Sizing

GitHub repositories stay organized when issues match real units of delivery. Decomposing initiatives accurately prevents ticket clutter and duplicate tracking.

### Comparison Table

| Property | **Epic (`epic.yml`)** | **Standalone Feature (`feature_request.yml`)** | **Sub-Issue / Task (`task.yml`)** | **Bug Report (`bug_report.yml`)** |
|---|---|---|---|---|
| **Goal** | Deliver an umbrella capability or workflow | Deliver an independent enhancement | Complete a focused technical track | Fix a verified defect |
| **PR Count** | Multiple (3+ PRs across layers) | Exactly 1 atomic PR | 1 PR or atomic commit lane | 1 PR |
| **Timeline** | Multiple days or multi-sprint | 1 day to 1 sprint | 1–2 days | Hours to 2 days |
| **Parent/Child** | Holds 2+ child sub-issues | None (root level) | Always attached to a parent Epic | Root level (or sub-issue of Epic) |
| **Labels** | `enhancement`, `epic` | `enhancement` | `task` | `bug` |
| **Branch Target** | Merged across multiple feature branches | Single `feat/<name>` branch | Specific track branch | `fix/<name>` branch |

---

## 2. When to Create an Epic

Create an Epic if **any** of the following conditions are true:
1. **Cross-Layer Implementation**: The work touches multiple disconnected layers (e.g. Core C++/Rust bindings -> KMP commonMain -> Compose UI -> Platform backend).
2. **Matrixed Acceptance Criteria**: Acceptance requires independent verification across multiple targets (e.g., Desktop JVM, WebGPU, Vulkan, Android).
3. **Sequential Milestone Dependencies**: Track B cannot begin until Track A merges.
4. **Multiple Contributors or Subagents**: Different people or autonomous agents will work on separate slices concurrently.

### Epic Structure Example

```markdown
# feat: MMORPG Authoring Workflow Completeness (#39)

## Objective & Scope
Verify that scene authoring, terrain manipulation, asset importing, and game runtime play sessions function deterministically across Desktop and Web/Wasm targets.

## Tracks / Sub-Issues
- [ ] #27 task(studio): Isolate Game play session from Scene3D editor
- [ ] #28 task(studio): Prevent transient shading artifacts during slider drags
- [ ] #30 task(studio): Normalize gizmo visibility across Desktop and WebGPU
- [ ] #31 task(studio): Restore opaque button-group separators
- [ ] #32 task(studio): Make Desktop environment rendering and live updates observable

## Acceptance Criteria
- All 5 child tracks merged and verified.
- Matrix evidence documented in `docs/authoring-matrix.md`.
```

---

## 3. When to Create a Sub-Issue (Task)

Create a Sub-Issue when:
- Breaking down an Epic into focused execution units.
- An unexpected blocker or bug is discovered *during* the execution of an active Epic that requires its own focused PR.

### Attaching Sub-Issues

Use the bundled GraphQL CLI helper:
```bash
# Attach existing issue as child of parent #39
python3 scripts/gh_sub_issue.py add 39 27

# Create a new child task directly under parent #39
python3 scripts/gh_sub_issue.py create 39 \
  --title "task(studio): isolate game session" \
  --body-file /tmp/task-body.md \
  --label "task"
```

---

## 4. Closing Protocol

1. **Child Sub-Issues Close via Pull Requests**:
   - Every child PR includes `Fixes #<sub_issue_id>` in its description.
   - When the PR merges to `main`, GitHub automatically closes the sub-issue and updates the parent Epic's native progress bar (`X of Y completed`).
2. **Parent Epic Closes Last**:
   - An Epic is only closed once all child sub-issues are closed and the overarching acceptance criteria (e.g. end-to-end integration tests, documentation) are verified.
