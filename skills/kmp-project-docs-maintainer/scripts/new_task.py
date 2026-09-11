#!/usr/bin/env python3
"""new_task.py — Scaffolds a new structured task note under docs/tasks/<parent>/.

Enforces:
  1. Parent grouping directory under docs/tasks/<parent>/
  2. Sequential 2-digit zero-padded number (<NN>-<slug>-todo.md)
  3. Proper metadata: **Date:** YYYY-MM-DD
  4. Standard 4-stage Clean Architecture deliverable checkboxes (:model, :domain, :presenter, :ui)
  5. Auto-triggers heal_docs.py to synchronize docs/tasks.md
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

def create_task(repo_root: Path, parent: str, slug: str) -> Path:
    docs_tasks = repo_root / "docs" / "tasks"
    parent_slug = re.sub(r"[^a-z0-9]+", "-", parent.lower()).strip("-")
    parent_dir = docs_tasks / parent_slug
    parent_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine next sequence number
    existing_nums = []
    task_num_re = re.compile(r"^(\d{2})-")
    for search_dir in (parent_dir, parent_dir / "archive"):
        if search_dir.exists():
            for f in search_dir.glob("*.md"):
                m = task_num_re.match(f.stem)
                if m:
                    existing_nums.append(int(m.group(1)))
                    
    next_num = max(existing_nums, default=0) + 1
    num_str = f"{next_num:02d}"
    
    clean_slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    filename = f"{num_str}-{clean_slug}-todo.md"
    task_path = parent_dir / filename
    
    title = clean_slug.replace("-", " ").title()
    today_str = datetime.date.today().isoformat()
    
    template = f"""# {title}

**Date:** {today_str}
**Status:** todo

## Overview
Brief description of the task requirements and objective.

## Deliverables
- [ ] `:model` — data models, entities, and value classes
- [ ] `:domain` — use cases, repository contracts, and domain business logic
- [ ] `:presenter` — MVI ViewModel, State/Intent/Effect contracts, and unit tests
- [ ] `:ui` — Compose screen components, theme tokens, and visual tests

## Verification
- [ ] `./gradlew check`
"""
    task_path.write_text(template, encoding="utf-8")
    print(f"✅ Created task: {task_path.relative_to(repo_root)}")
    
    # Run heal_docs to auto-sync docs/tasks.md if script exists
    heal_script = repo_root / "skills" / "kmp-project-docs-maintainer" / "scripts" / "heal_docs.py"
    if not heal_script.exists():
        heal_script = repo_root / ".agents" / "skills" / "kmp-project-docs-maintainer" / "scripts" / "heal_docs.py"
    if heal_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(heal_script), "--project", str(repo_root)], check=False, stdout=subprocess.DEVNULL)
        
    return task_path

def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new structured KMP task note")
    parser.add_argument("parent", help="Feature or parent grouping folder (e.g. auth, render, editor)")
    parser.add_argument("slug", help="Action-first task slug (e.g. add-token-refresh)")
    parser.add_argument("--project", default=".", help="Project root (default: current directory)")
    args = parser.parse_args()
    
    repo_root = Path(args.project).resolve()
    create_task(repo_root, args.parent, args.slug)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
