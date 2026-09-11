#!/usr/bin/env python3
"""heal_docs.py — Self-Healing Documentation Engine for KMP Projects

Automates:
  1. Safe cleanup: auto-renames snake_case files to kebab-case and updates inbound links.
  2. Safe cleanup: auto-archives completed tasks (*-done or 100% checked) to docs/tasks/<parent>/archive/.
  3. Sitemap synchronization in docs/README.md (extracts title, category, status, and summaries).
  4. Task index synchronization in docs/tasks.md with verified checkbox progress metrics.
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

_SNAKE_CASE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)+$")


def extract_doc_info(file_path: Path, repo_root: Path) -> dict:
    content = file_path.read_text(encoding="utf-8")
    rel_path = file_path.relative_to(repo_root)
    
    # Extract Title
    title = file_path.stem.replace("-", " ").title()
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        
    # Determine Category
    parts = rel_path.parts
    category = "General"
    if "architecture" in parts:
        category = "Architecture"
    elif "decisions" in parts:
        category = "Decisions (ADR)"
    elif "audits" in parts:
        category = "Audits"
    elif "tasks" in parts:
        category = "Tasks (Archive)" if "archive" in parts else "Active Task"
    elif "reference" in parts:
        category = "Reference"
    elif file_path.name in ("roadmap.md", "mvp-scope.md", "mmorpg-roadmap.md"):
        category = "Strategy & Roadmap"
        
    # Determine Status
    status = "Active"
    if "archive" in parts:
        status = "Archived"
    elif category == "Architecture":
        status = "Stable"
    elif category == "Decisions (ADR)":
        status = "Accepted"
    elif category == "Strategy & Roadmap":
        status = "In Progress"
        
    # Extract 1-line Summary
    summary = "Documentation for " + title
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith(">") and not line.startswith("```") and not line.startswith("-"):
            summary = line[:120] + ("..." if len(line) > 120 else "")
            break
            
    return {
        "title": title,
        "path": str(rel_path),
        "rel_from_docs": str(file_path.relative_to(repo_root / "docs")),
        "category": category,
        "status": status,
        "summary": summary
    }

def auto_rename_kebab(docs_dir: Path, repo_root: Path, dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Safely renames snake_case markdown files to kebab-case and updates inbound links."""
    renamed = []
    for md in sorted(docs_dir.rglob("*.md")):
        if "archive" in md.parts or md.name in ("README.md", "CHANGELOG.md", "KNOWN_ISSUES.md"):
            continue
        if _SNAKE_CASE_RE.match(md.stem):
            kebab = md.stem.replace("_", "-").lower()
            target_path = md.parent / f"{kebab}.md"
            if target_path.exists() and target_path != md:
                continue
            renamed.append((md, target_path))

    if not renamed:
        return []

    for old_path, new_path in renamed:
        old_name = old_path.name
        new_name = new_path.name
        print(f"  ✏️ Renaming: {old_path.relative_to(repo_root)} -> {new_name}")
        if not dry_run:
            old_path.rename(new_path)
            for doc in docs_dir.rglob("*.md"):
                if not doc.is_file():
                    continue
                try:
                    text = doc.read_text(encoding="utf-8")
                    if old_name in text:
                        doc.write_text(text.replace(old_name, new_name), encoding="utf-8")
                except Exception:
                    pass
    return renamed


def auto_archive_done_tasks(docs_dir: Path, repo_root: Path, dry_run: bool = False) -> list[str]:
    """Auto-archives completed tasks (*-done.md or 100% checked) to docs/tasks/<parent>/archive/."""
    tasks_dir = docs_dir / "tasks"
    if not tasks_dir.exists():
        return []

    archived = []
    task_status_re = re.compile(r"^(\d{2}-[a-z0-9-]+)-(todo|doing|blocked|done)$")

    for parent_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        if parent_dir.name == "archive":
            continue
        archive_dir = parent_dir / "archive"
        for md in sorted(parent_dir.glob("*.md")):
            if not md.is_file():
                continue
            content = md.read_text(encoding="utf-8", errors="ignore")
            total_boxes = len(re.findall(r"^\s*-\s*\[[ xX]\]", content, re.MULTILINE))
            checked_boxes = len(re.findall(r"^\s*-\s*\[[xX]\]", content, re.MULTILINE))
            is_100_percent = total_boxes > 0 and checked_boxes == total_boxes
            is_done_suffix = md.stem.endswith("-done")

            if is_done_suffix or is_100_percent:
                stem = md.stem
                m = task_status_re.match(stem)
                if m:
                    base_prefix = m.group(1)
                    target_name = f"{base_prefix}-done.md"
                else:
                    target_name = md.name if is_done_suffix else f"{stem}-done.md"

                target_path = archive_dir / target_name
                archived.append(f"{md.relative_to(repo_root)} -> {target_path.relative_to(repo_root)}")

                if not dry_run:
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    updated_content = re.sub(
                        r"(\*\*Status:\*\*\s*)(todo|doing|blocked)",
                        r"\1done",
                        content,
                    )
                    target_path.write_text(updated_content, encoding="utf-8")
                    if md != target_path:
                        md.unlink()
                    print(f"  📦 Archived: {md.name} -> tasks/{parent_dir.name}/archive/{target_name}")
    return archived


def heal_docs(repo_root: Path, dry_run: bool = False) -> int:
    docs_dir = repo_root / "docs"
    if not docs_dir.exists():
        print(f"❌ docs/ directory not found in {repo_root}", file=sys.stderr)
        return 1
        
    print(f"\n🩺 Self-Healing Documentation Scan: {repo_root.name}")
    print(f"{'='*60}")
    
    # 1. Safe auto-cleanups (snake_case normalization and archiving completed tasks)
    renamed = auto_rename_kebab(docs_dir, repo_root, dry_run)
    if renamed:
        print(f"  ✨ Normalized {len(renamed)} file(s) to kebab-case")

    archived = auto_archive_done_tasks(docs_dir, repo_root, dry_run)
    if archived:
        print(f"  📦 Auto-archived {len(archived)} completed task(s)")

    # 2. Scan all markdown files in docs/ (ignoring README.md itself)
    doc_entries = []
    for p in sorted(docs_dir.rglob("*.md")):
        if p.name == "README.md":
            continue
        doc_entries.append(extract_doc_info(p, repo_root))

        
    print(f"  Found {len(doc_entries)} documentation files across categories:")
    categories = {}
    for entry in doc_entries:
        categories.setdefault(entry["category"], []).append(entry)
        
    for cat, items in categories.items():
        print(f"    • {cat:20} : {len(items)} docs")
        
    # 2. Build High-Density Self-Healing Sitemap Table
    date_str = datetime.date.today().isoformat()
    table_lines = [
        "# Documentation Sitemap & System Status",
        "",
        "> [!TIP]",
        "> **AI Agent Navigation Directives**:",
        "> 1. **Never recursively scan the `docs/` folder.**",
        "> 2. Read this sitemap table to find the exact document you need.",
        "> 3. Only open the specific single file relevant to your current task.",
        "",
        f"**Last Self-Healed**: `{date_str}` | **Total Tracked Docs**: `{len(doc_entries)}`",
        "",
        "| Category | Document | Status | 1-Line Summary |",
        "| :--- | :--- | :--- | :--- |"
    ]
    
    # Sort order for categories
    priority = ["Strategy & Roadmap", "Architecture", "Decisions (ADR)", "Audits", "Active Task", "Reference", "Tasks (Archive)", "General"]
    for cat in priority:
        if cat in categories:
            for item in sorted(categories[cat], key=lambda x: x["path"]):
                link = f"[`{item['title']}`]({item['rel_from_docs']})"
                badge = f"`{item['status']}`"
                clean_summary = item['summary'].replace("|", "\\|")
                table_lines.append(f"| **{cat}** | {link} | {badge} | {clean_summary} |")
                
    table_lines.append("")
    table_lines.append("---")
    table_lines.append("*Automated documentation sitemap generated by [KMP Agent Skills](https://github.com/ronjunevaldoz/kmp-agent-skills)*")
    
    sitemap_content = "\n".join(table_lines) + "\n"
    readme_path = docs_dir / "README.md"
    
    if dry_run:
        print("\n[DRY RUN] Generated docs/README.md preview:")
        print("\n".join(table_lines[:25]) + "\n...")
        return 0
        
    readme_path.write_text(sitemap_content, encoding="utf-8")
    print(f"\n✅ Self-Healed {readme_path.relative_to(repo_root)} successfully!")
    
    # 3. Synchronize docs/tasks.md with objective progress and checkbox metrics
    sync_tasks(docs_dir, repo_root, dry_run)
    return 0

def sync_tasks(docs_dir: Path, repo_root: Path, dry_run: bool = False) -> None:
    tasks_dir = docs_dir / "tasks"
    if not tasks_dir.exists():
        return
        
    tasks_file = docs_dir / "tasks.md"
    active_tasks = []
    
    task_file_re = re.compile(r"^\d{2}-[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(todo|doing|blocked|done)$")
    task_date_re = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")

    for parent_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        if parent_dir.name == "archive":
            continue
        for md in sorted(parent_dir.rglob("*.md")):
            if "archive" in md.parts:
                continue
            m = task_file_re.match(md.stem)
            status = m.group(1) if m else "doing"
            content = md.read_text(encoding="utf-8", errors="ignore")
            
            title = md.stem
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
                
            date_match = task_date_re.search(content)
            task_date = date_match.group(1) if date_match else "-"
            
            total_boxes = len(re.findall(r"^\s*-\s*\[[ xX]\]", content, re.MULTILINE))
            checked_boxes = len(re.findall(r"^\s*-\s*\[[xX]\]", content, re.MULTILINE))
            if total_boxes > 0:
                pct = int((checked_boxes / total_boxes) * 100)
                progress = f"{pct}% ({checked_boxes}/{total_boxes})"
            else:
                progress = "-"
                
            rel_link = f"tasks/{parent_dir.name}/{md.name}"
            active_tasks.append({
                "name": md.name,
                "title": title,
                "link": f"[{title}]({rel_link})",
                "status": status,
                "progress": progress,
                "parent": parent_dir.name,
                "date": task_date,
            })
            
    if not active_tasks and not tasks_file.exists():
        return
        
    lines = [
        "# Tasks",
        "",
        "> Single source of truth for active project tasks, progress status, and parent feature lanes.",
        "",
        f"**Last Synchronized**: `{datetime.date.today().isoformat()}` | **Active Tasks**: `{len(active_tasks)}`",
        "",
        "| Task | Status | Progress | Date | Parent |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for t in active_tasks:
        lines.append(f"| {t['link']} | `{t['status']}` | {t['progress']} | {t['date']} | `{t['parent']}` |")
        
    lines.append("")
    tasks_content = "\n".join(lines) + "\n"
    if dry_run:
        print("\n[DRY RUN] Generated docs/tasks.md preview:")
        print("\n".join(lines[:15]))
    else:
        tasks_file.write_text(tasks_content, encoding="utf-8")
        print(f"✅ Self-Healed {tasks_file.relative_to(repo_root)} successfully ({len(active_tasks)} active tasks)!")

def main() -> int:
    parser = argparse.ArgumentParser(description="Self-Healing Documentation Engine")
    parser.add_argument("--project", default=".", help="Path to project root (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Preview sitemap without writing")
    args = parser.parse_args()
    
    project_root = Path(args.project).resolve()
    return heal_docs(project_root, args.dry_run)

if __name__ == "__main__":
    raise SystemExit(main())
