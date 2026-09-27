---
name: kmp-new-task
description: Scaffold a new structured task note under docs/tasks/<parent>/ with Clean Architecture deliverable checkboxes.
---

# /kmp-new-task $ARGUMENTS

**KMP Agent Skills** — scaffold a new structured task note under `docs/tasks/<parent>/`.

Usage:
```bash
/kmp-new-task <parent> <slug>
```
Example:
```bash
/kmp-new-task auth session-refresh
```

---

## What This Command Does

Runs the task scaffolding engine:

```bash
python3 .agents/skills/kmp-project-docs-maintainer/scripts/new_task.py $ARGUMENTS || python3 skills/kmp-project-docs-maintainer/scripts/new_task.py $ARGUMENTS
```

1. **Enforces Canonical Folder**: Places the file in `docs/tasks/<parent>/` (never loose in `docs/tasks/` or ad-hoc `docs/plans/`).
2. **Assigns Next Sequence Number**: Auto-increments to `<NN>-<slug>-todo.md` (`01`, `02`, `03`).
3. **Embeds Clean Architecture Milestones**:
   - `- [ ] :model` — data structures & value classes
   - `- [ ] :domain` — use cases & repository contracts
   - `- [ ] :presenter` — MVI ViewModel & unit tests
   - `- [ ] :ui` — Compose screen components & visual tests
4. **Self-Heals `docs/tasks.md`**: Automatically triggers `heal_docs.py` to register the new task in the centralized Task Log table.
