#!/usr/bin/env python3
"""
check_updates.py — compare local skills against origin/main
(https://github.com/ronjunevaldoz/kmp-agent-skills)

Exit codes:
  0 — up to date
  1 — updates available (non-fatal; callers should warn, not abort)
  2 — could not reach remote (non-fatal; network may be unavailable)
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTE = "origin"
BRANCH = "main"
REPO_URL = "https://github.com/ronjunevaldoz/kmp-agent-skills"


def run(cmd: str) -> tuple[str, int]:
    # Git must inspect this skills checkout, not whichever project the caller runs in.
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT)
    return result.stdout.strip(), result.returncode


def read_version(json_text: str) -> str:
    try:
        return json.loads(json_text).get("version", "?")
    except Exception:
        return "?"


def main() -> int:
    print(f"Checking for skill updates from {REMOTE}/{BRANCH}…")

    # The Claude Code plugin is installed as a copy with no git history to compare.
    if not (ROOT / ".git").exists():
        print(f"⚠️  {ROOT} is not a git checkout — if it is the Claude Code plugin, update with:")
        print("   claude plugin update kmp-agent-skills@kmp-agent-skills")
        return 2

    # 1. Fetch remote — non-fatal if offline
    _, rc = run(f"git fetch {REMOTE} {BRANCH} --quiet 2>&1")
    if rc != 0:
        print(f"⚠️  Could not reach {REMOTE}/{BRANCH} — continuing with local skills")
        print(f"   Source: {REPO_URL}")
        return 2

    # 2. Commits behind
    count_str, _ = run(f"git rev-list HEAD..{REMOTE}/{BRANCH} --count")
    try:
        count = int(count_str)
    except ValueError:
        count = 0

    if count == 0:
        # Also check commits ahead (local unpushed work)
        ahead_str, _ = run(f"git rev-list {REMOTE}/{BRANCH}..HEAD --count")
        ahead = int(ahead_str or "0")
        if ahead > 0:
            print(f"✅  Local skills are up to date (and {ahead} commit(s) ahead of remote)")
        else:
            print("✅  Local skills are up to date with origin/main")
        return 0

    # 3. Version comparison
    local_skills_path = ROOT / "skills.json"
    local_version = read_version(local_skills_path.read_text()) if local_skills_path.exists() else "?"
    remote_json, _ = run(f"git show {REMOTE}/{BRANCH}:skills.json 2>/dev/null")
    remote_version = read_version(remote_json)

    print(f"\n⚠️  Local skills are {count} commit(s) behind {REMOTE}/{BRANCH}")
    print(f"   Local version:  v{local_version}")
    print(f"   Remote version: v{remote_version}")
    print(f"   Source: {REPO_URL}")

    # 4. Categorise changed files
    changed_raw, _ = run(
        f"git diff HEAD..{REMOTE}/{BRANCH} --name-only "
        f"-- skills/ agents/ commands/ scripts/ KNOWN_ISSUES.md CHANGELOG.md"
    )
    changed = [f for f in changed_raw.splitlines() if f]

    buckets: dict[str, list[str]] = {
        "New/updated skills":   [],
        "Updated agents":       [],
        "Updated commands":     [],
        "Updated scripts":      [],
        "Other":                [],
    }
    for f in changed:
        if f.startswith("skills/"):
            buckets["New/updated skills"].append(f)
        elif f.startswith("agents/"):
            buckets["Updated agents"].append(f)
        elif f.startswith("commands/"):
            buckets["Updated commands"].append(f)
        elif f.startswith("scripts/"):
            buckets["Updated scripts"].append(f)
        else:
            buckets["Other"].append(f)

    for label, files in buckets.items():
        if files:
            print(f"\n   {label} ({len(files)}):")
            for f in files:
                # Mark new files (not present locally)
                local_path = ROOT / f
                marker = "  NEW" if not local_path.exists() else "  UPD"
                print(f"    {marker}  {f}")

    # 5. Changelog excerpt from remote
    changelog_diff, _ = run(
        f"git diff HEAD..{REMOTE}/{BRANCH} -- CHANGELOG.md 2>/dev/null"
    )
    if changelog_diff:
        # Extract only added lines (skip diff headers)
        added = [
            line[1:] for line in changelog_diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ][:20]
        if added:
            print("\n   Recent changelog entries (remote):")
            for line in added:
                if line.strip():
                    print(f"     {line}")

    print(f"\n   To update: git pull {REMOTE} {BRANCH}")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
