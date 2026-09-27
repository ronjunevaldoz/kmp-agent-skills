#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_skill_map(repo_root: Path) -> list[str]:
    skills_dir = repo_root / "skills"
    readme_path = repo_root / "README.md"
    expert_path = skills_dir / "kmp-expert" / "SKILL.md"

    skill_dirs = sorted(
        p.parent for p in skills_dir.glob("*/SKILL.md") if p.is_file()
    )
    skill_names = {p.name for p in skill_dirs}

    readme_text = read_text(readme_path)
    expert_text = read_text(expert_path)

    # The invocation map and detailed routing tables are canonical references so the
    # planner agent does not duplicate the entire skill catalog.
    expert_references_dir = expert_path.parent / "references"
    expert_search_text = expert_text + "\n" + "\n".join(
        read_text(p) for p in sorted(expert_references_dir.glob("*.md"))
    ) if expert_references_dir.exists() else expert_text

    errors: list[str] = []

    count_match = re.search(r"## The (\d+) Skills and What They Own", expert_text)
    if not count_match:
        errors.append("expert skill map header missing or malformed")
    else:
        declared_count = int(count_match.group(1))
        if declared_count != len(skill_names):
            errors.append(
                f"expert declares {declared_count} skills but repo has {len(skill_names)} skill folders"
            )

    # Use literal name lookup so non-standard prefixes (e.g. jni-kotlin-pro) are found.
    missing_in_readme = sorted(name for name in skill_names if name not in readme_text)
    missing_in_expert = sorted(name for name in skill_names if name not in expert_search_text)

    if missing_in_readme:
        errors.append("missing from README: " + ", ".join(missing_in_readme))
    if missing_in_expert:
        errors.append("missing from expert: " + ", ".join(missing_in_expert))

    # Prose skill-count mentions drift silently — every skill *name* appearing in
    # README.md (checked above) doesn't catch a stale "68 skills" summary line sitting
    # next to an accurate list. Found real: README.md and agentskills-io-standards.md
    # both said "68 skills" while the repo had 69. Positive-presence check, not a
    # negative "no wrong number" scan — the latter would false-positive on legitimate
    # historical counts (e.g. "the 22-skill backlog was resolved on <date>").
    count_phrase = f"{len(skill_names)} skills"
    if count_phrase not in readme_text:
        errors.append(f"README.md is missing the current count phrase {count_phrase!r} — a skill-count summary line has likely gone stale")
    standards_path = repo_root / "docs" / "reference" / "agentskills-io-standards.md"
    if standards_path.exists():
        standards_text = read_text(standards_path)
        if count_phrase not in standards_text:
            errors.append(f"agentskills-io-standards.md is missing the current count phrase {count_phrase!r} — a skill-count summary line has likely gone stale")

    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate the skill map against README and expert docs.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Path to the repo root (defaults to the current repo)",
    )
    args = parser.parse_args(argv)

    errors = validate_skill_map(args.repo_root.resolve())

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    skill_count = len({p.parent for p in (args.repo_root / "skills").glob("*/SKILL.md") if p.is_file()})
    print(f"OK: {skill_count} skills indexed in README and expert references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
