#!/usr/bin/env python3
"""
Release script for kmp-agent-skills.

Usage:
    python3 scripts/release.py patch          # stable release — bug fixes, version bumps
    python3 scripts/release.py minor          # stable release — new skills, new features
    python3 scripts/release.py major          # stable release — breaking changes
    python3 scripts/release.py patch --rc     # release candidate — vX.Y.Z-rc.N tag
    python3 scripts/release.py patch --dry-run
    python3 scripts/release.py patch --rc --dry-run

Versioning tiers (see docs/reference/versioning-policy.md for the full policy):
    dev    — no tag; dev commits accumulate freely; CHANGELOG is never touched manually
    rc     — vX.Y.Z-rc.N tag; pre-release GitHub Release; CHANGELOG auto-generated
    stable — vX.Y.Z tag; full GitHub Release; CHANGELOG auto-generated

Versioning policy:
    patch — fixes only: audit false-positive corrections, typos, freshness date bumps,
            KNOWN_ISSUES updates, PLAN.md housekeeping, library version bumps
    minor — additive work: new skill, new audit pattern, new reviewer check, new command,
            new fixer rule, new agent, layout/theme enforcement additions
    major — breaking: skill section headers renamed (breaks external tooling that parses
            SKILL.md), skills.json schema changed, skill directories removed or renamed

What it does (in order):
    1.  Verify git working tree is clean
    2.  Run audit_skills_repo.py — must be zero findings
    3.  Run scan_skill_issues.py — must report zero issues
    4.  Run scan_command_shell_portability.py — commands/*.md must have no known-fragile find predicates
    5.  Run validate_skill_map.py — README and kmp-expert references must match
    6.  Run validate_keyword_routing.py — every skill must have routing coverage
    7.  Run pytest — must be 100% passing
    8.  Bump version in skills.json (semver base version, no pre-release suffix)
    9.  Regenerate all skill entries in skills.json from SKILL.md frontmatter
    10. Update shipped skill count in PLAN.md
    11. Prepend new section to CHANGELOG.md (auto-generated from git log)
    11b. Regenerate docs/reference/skills-report.md (per-skill health-at-a-glance)
    12. Stage skills.json, PLAN.md, CHANGELOG.md, docs/reference/skills-report.md
    13. Create a release commit: "Release vX.Y.Z" or "Release vX.Y.Z-rc.N"
    14. Create an annotated git tag vX.Y.Z or vX.Y.Z-rc.N
    15. Print push instructions — does NOT push automatically, does NOT create a
        GitHub Release yet (see `publish` below for why)

After pushing, run:
    python3 scripts/release.py publish            # publishes the current HEAD's tag
    python3 scripts/release.py publish v1.2.3      # or an explicit tag

This creates the GitHub Release — it must run AFTER `git push`, since `gh release
create` requires the tag to already exist on the remote. Calling it before the push
(the previous behavior) failed every single time, silently (logged as non-fatal) —
confirmed via `gh release list`: 142 of 255 tags had no GitHub Release at all, and
"latest" was stuck weeks behind the real latest tag.

Agents: run this script exactly as shown above. Do not push to remote
without explicit user confirmation. Never run `git tag` manually.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILLS_JSON = REPO_ROOT / "skills.json"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLAN_MD = REPO_ROOT / "PLAN.md"
CHANGELOG_MD = REPO_ROOT / "CHANGELOG.md"
SKILLS_DIR = REPO_ROOT / "skills"
AUDIT_SCRIPT = REPO_ROOT / "skills" / "kmp-audit" / "scripts" / "audit_skills_repo.py"
SCAN_ISSUES_SCRIPT = REPO_ROOT / "scripts" / "scan_skill_issues.py"
SCAN_COMMAND_SHELL_PORTABILITY_SCRIPT = REPO_ROOT / "scripts" / "scan_command_shell_portability.py"
VALIDATE_SKILL_MAP_SCRIPT = REPO_ROOT / "skills" / "kmp-expert" / "scripts" / "validate_skill_map.py"
VALIDATE_KEYWORD_ROUTING_SCRIPT = REPO_ROOT / "skills" / "kmp-expert" / "scripts" / "validate_keyword_routing.py"
CHECK_COMPAT_MATRIX_SCRIPT = REPO_ROOT / "scripts" / "check_compat_matrix.py"
TESTS_DIR = REPO_ROOT / "tests"


# ── helpers ──────────────────────────────────────────────────────────────────

# Child scripts print emoji; UTF-8 mode keeps them from failing on a Windows code page.
_CHILD_ENV = {**os.environ, "PYTHONUTF8": "1"}


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=REPO_ROOT, check=check, env=_CHILD_ENV)


def fail(msg: str) -> None:
    print(f"\n❌  {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"✅  {msg}")


def info(msg: str) -> None:
    print(f"    {msg}")


# ── step 1: clean working tree ────────────────────────────────────────────────

def check_clean_tree() -> None:
    result = run(["git", "status", "--porcelain"])
    if result.stdout.strip():
        fail(
            "Working tree is not clean. Commit or stash changes before releasing.\n"
            + result.stdout
        )
    ok("Working tree is clean")


# ── step 2: audit ─────────────────────────────────────────────────────────────

def run_audit() -> None:
    result = run([sys.executable, str(AUDIT_SCRIPT), str(REPO_ROOT)], check=False)
    if result.returncode != 0 or result.stdout.strip():
        fail(
            "audit_skills_repo.py found issues. Fix them before releasing.\n"
            + result.stdout
            + result.stderr
        )
    ok("Audit clean — zero findings")


def run_scan_skill_issues() -> None:
    result = run([sys.executable, str(SCAN_ISSUES_SCRIPT)], check=False)
    if result.returncode != 0:
        fail(
            "scan_skill_issues.py found issues. Fix them before releasing.\n"
            + result.stdout
            + result.stderr
        )
    ok("Skill issue scan clean — zero issues")


def run_command_shell_portability_scan() -> None:
    result = run([sys.executable, str(SCAN_COMMAND_SHELL_PORTABILITY_SCRIPT)], check=False)
    if result.returncode != 0:
        fail(
            "scan_command_shell_portability.py found issues. Fix them before releasing.\n"
            + result.stdout
            + result.stderr
        )
    ok("Command shell portability scan clean")


def run_skill_map_validation() -> None:
    result = run(
        [sys.executable, str(VALIDATE_SKILL_MAP_SCRIPT), "--repo-root", str(REPO_ROOT)],
        check=False,
    )
    if result.returncode != 0:
        fail(
            "validate_skill_map.py failed. Fix README/kmp-expert routing before releasing.\n"
            + result.stdout
            + result.stderr
        )
    ok("Skill map validation passed")


def run_keyword_routing_validation() -> None:
    result = run(
        [sys.executable, str(VALIDATE_KEYWORD_ROUTING_SCRIPT), "--repo-root", str(REPO_ROOT)],
        check=False,
    )
    if result.returncode != 0:
        fail(
            "validate_keyword_routing.py failed. Fix invocation map coverage before releasing.\n"
            + result.stdout
            + result.stderr
        )
    ok("Keyword routing validation passed")


# ── step 3: tests ─────────────────────────────────────────────────────────────

def run_tests() -> None:
    result = run([sys.executable, "-m", "pytest", str(TESTS_DIR), "-v", "--tb=short"], check=False)
    if result.returncode != 0:
        fail("Tests are failing. Fix them before releasing.\n" + result.stdout + result.stderr)
    # Count passed
    match = re.search(r"(\d+) passed", result.stdout)
    count = match.group(1) if match else "?"
    ok(f"All tests pass ({count} passed)")


def run_compat_matrix_check() -> None:
    result = run([sys.executable, str(CHECK_COMPAT_MATRIX_SCRIPT)], check=False)
    if result.returncode != 0:
        fail(
            "Compatibility matrix is out of sync with skill files. "
            "Update docs/reference/compatibility-matrix.md before releasing.\n"
            + result.stdout
        )
    ok("Compatibility matrix in sync")


def run_release_validation() -> None:
    run_audit()
    run_scan_skill_issues()
    run_command_shell_portability_scan()
    run_skill_map_validation()
    run_keyword_routing_validation()
    run_compat_matrix_check()
    run_tests()


# ── step 4+5: bump version & regenerate skills.json ──────────────────────────

def bump_version(current: str, bump: str) -> str:
    parts = current.split(".")
    if len(parts) != 3:
        fail(f"Unexpected version format in skills.json: {current!r}")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def extract_skills() -> list[dict]:
    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        text = skill_md.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)

        name = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        license_ = re.search(r"^license:\s*(.+)$", fm, re.MULTILINE)
        last_updated = re.search(r"last-updated:\s*['\"]?(.+?)['\"]?\s*$", fm, re.MULTILINE)

        # `>-`/`|-` (YAML "strip" chomp) are as common as bare `>`/`|` in this repo's
        # skills — the old regex only matched a bare `>` immediately before the
        # newline, so `description: >-` fell through to the single-line fallback and
        # captured the literal ">-" as the description. Confirmed shipped broken in
        # skills.json for 18 of 64 skills before this fix.
        desc_match = re.search(r"^description:\s*[>|]-?\n((?:  .+\n?)+)", fm, re.MULTILINE)
        if desc_match:
            desc = " ".join(line.strip() for line in desc_match.group(1).splitlines())
        else:
            dm2 = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
            desc = dm2.group(1).strip() if dm2 else ""

        kw_block = re.search(r"keywords:\n((?:    - .+\n?)+)", fm)
        keywords = []
        if kw_block:
            keywords = [re.sub(r"^\s*-\s*", "", l).strip()
                        for l in kw_block.group(1).splitlines() if l.strip()]

        trigger_match = re.search(r"\*\*Trigger keywords:\*\*\s*(.+?)(?=\n\n|\n\*\*)", text, re.DOTALL)
        triggers = []
        if trigger_match:
            raw = trigger_match.group(1).replace("\n", " ")
            triggers = [t.strip().strip(".") for t in raw.split(",") if t.strip()]

        scripts_dir = skill_dir / "scripts"
        scripts = [p.name for p in sorted(scripts_dir.glob("*.py"))] if scripts_dir.exists() else []

        skills.append({
            "name": name.group(1).strip() if name else skill_dir.name,
            "path": f"skills/{skill_dir.name}",
            "description": desc,
            "license": license_.group(1).strip() if license_ else "Apache-2.0",
            "last_updated": last_updated.group(1).strip() if last_updated else "",
            "keywords": keywords,
            "triggers": triggers,
            "scripts": scripts,
        })
    return skills


def update_skills_json(new_version: str) -> None:
    skills = extract_skills()
    manifest = {"version": new_version, "skills": skills}
    SKILLS_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    ok(f"skills.json updated — version {new_version}, {len(skills)} skills")


def update_plugin_json(new_version: str) -> None:
    """Keep .claude-plugin/plugin.json's version in lockstep with skills.json's —
    otherwise the Claude Code plugin marketplace entry silently drifts behind every
    release, the exact staleness this script already exists to prevent for skills.json.
    """
    if not PLUGIN_JSON.exists():
        return
    manifest = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    manifest["version"] = new_version
    # An explicit `commands` list replaces the default scan (keeps commands/references/
    # out of the slash menu), so every new command must be registered here.
    manifest["commands"] = plugin_command_paths()
    PLUGIN_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    ok(f".claude-plugin/plugin.json updated — version {new_version}")

    if MARKETPLACE_JSON.exists():
        market = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
        skill_count = len(list(SKILLS_DIR.glob("*/SKILL.md")))
        for entry in market.get("plugins", []):
            if entry.get("name") == manifest["name"]:
                entry["version"] = new_version
                entry["description"] = (
                    f"{skill_count} Kotlin Multiplatform agent skills, {len(manifest['commands'])} "
                    f"slash commands, and {len(manifest.get('agents', []))} role agents covering the "
                    "full KMP stack: architecture, MVI, networking, persistence, design systems, "
                    "testing, and release."
                )
        MARKETPLACE_JSON.write_text(json.dumps(market, indent=2) + "\n", encoding="utf-8")
        ok(".claude-plugin/marketplace.json updated — counts and version")


def plugin_command_paths() -> list[str]:
    return [f"./commands/{p.name}" for p in sorted((REPO_ROOT / "commands").glob("*.md"))]


def update_skills_report() -> None:
    """Regenerate docs/reference/skills-report.md so it never drifts from the
    skills.json / scan_skill_issues.py state actually being released.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_skills_report import build_report, REPORT_MD
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(build_report(), encoding="utf-8")
    ok("docs/reference/skills-report.md regenerated")


# ── step 6: update PLAN.md shipped count ─────────────────────────────────────

def update_plan_md(skill_count: int) -> None:
    text = PLAN_MD.read_text(encoding="utf-8")
    updated = re.sub(
        r"## Shipped Skills \(\d+\)",
        f"## Shipped Skills ({skill_count})",
        text,
    )
    if updated == text:
        info("PLAN.md shipped count already correct — no change needed")
        return
    PLAN_MD.write_text(updated, encoding="utf-8")
    ok(f"PLAN.md updated — Shipped Skills ({skill_count})")


# ── step 7–9: git commit + tag ────────────────────────────────────────────────

def get_previous_tag() -> str:
    result = run(["git", "describe", "--tags", "--abbrev=0", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def get_previous_stable_tag() -> str:
    """Return the most recent stable tag (no -rc suffix), or empty string."""
    result = run(["git", "tag", "--list", "v*", "--sort=-version:refname"], check=False)
    if result.returncode != 0:
        return ""
    for tag in result.stdout.strip().splitlines():
        if re.match(r"^v\d+\.\d+\.\d+$", tag.strip()):
            return tag.strip()
    return ""


def detect_bump_type(since_tag: str) -> str:
    """
    Infer the correct semver bump from conventional commits since *since_tag*.

    Rules (mirrors the Conventional Commits spec):
      - Any commit with '!' after the type, or a 'BREAKING CHANGE' footer → major
      - Any 'feat(...)' or 'feat:' commit                                  → minor
      - Everything else (fix, chore, docs, refactor, test, build, ci)      → patch

    Falls back to 'patch' if git log cannot be read.
    """
    ref = f"{since_tag}..HEAD" if since_tag else "HEAD"
    result = run(["git", "log", ref, "--pretty=format:%s%n%b"], check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return "patch"

    lines = result.stdout.strip().splitlines()
    has_breaking = any(
        re.match(r"^[a-z]+(\([^)]+\))?!:", line) or "BREAKING CHANGE" in line
        for line in lines
    )
    has_feat = any(re.match(r"^feat(\([^)]+\))?:", line) for line in lines)

    if has_breaking:
        return "major"
    if has_feat:
        return "minor"
    return "patch"


def get_next_prerelease_number(base_version: str, channel: str) -> int:
    """Return the next pre-release sequence number for the given base version and channel (1-based)."""
    result = run(["git", "tag", "--list", f"v{base_version}-{channel}.*"], check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return 1
    nums = [
        int(m.group(1))
        for tag in result.stdout.strip().splitlines()
        if (m := re.search(rf"-{re.escape(channel)}\.(\d+)$", tag.strip()))
    ]
    return max(nums) + 1 if nums else 1


def generate_changelog_section(new_version: str, prev_tag: str) -> str:
    """Build a CHANGELOG section from git log since prev_tag."""
    import datetime
    date = datetime.date.today().isoformat()
    tag = f"v{new_version}"

    if prev_tag:
        result = run(["git", "log", "--oneline", f"{prev_tag}..HEAD"])
    else:
        result = run(["git", "log", "--oneline"])

    lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]

    # Bucket by conventional commit prefix
    buckets: dict[str, list[str]] = {
        "feat": [], "fix": [], "docs": [], "chore": [], "other": []
    }
    for line in lines:
        sha, _, rest = line.partition(" ")
        prefix = rest.split("(")[0].split(":")[0].strip().lower()
        if prefix in buckets:
            buckets[prefix].append(f"- {rest}")
        else:
            buckets["other"].append(f"- {rest}")

    section = [f"## [{tag}] — {date}\n"]
    labels = [("feat", "Added"), ("fix", "Fixed"), ("docs", "Docs"), ("chore", "Chore"), ("other", "Other")]
    for key, heading in labels:
        if buckets[key]:
            section.append(f"### {heading}\n")
            section.extend(buckets[key])
            section.append("")

    return "\n".join(section)


def update_changelog(new_version: str, prev_tag: str, dry_run: bool) -> str:
    header = "# Changelog\n\nAll notable changes to kmp-agent-skills are documented here.\n\n"
    existing = CHANGELOG_MD.read_text(encoding="utf-8") if CHANGELOG_MD.exists() else header

    # Skip git log + prepend if a detailed entry was already written manually.
    if not dry_run and f"## [{new_version}]" in existing:
        ok(f"CHANGELOG.md already contains {new_version} entry — skipping prepend")
        return ""

    section = generate_changelog_section(new_version, prev_tag)

    if dry_run:
        info(f"[dry-run] CHANGELOG section preview:\n{section[:300]}…")
        return section

    # Strip the header so we can prepend the new section after it
    body = existing[len(header):] if existing.startswith(header) else existing
    CHANGELOG_MD.write_text(header + section + "\n---\n\n" + body, encoding="utf-8")
    ok(f"CHANGELOG.md updated — {new_version} section prepended")
    return section


def create_github_release(tag: str, changelog_section: str, dry_run: bool, prerelease: bool = False) -> None:
    result = run(["gh", "--version"], check=False)
    if result.returncode != 0:
        info("gh CLI not found — skipping GitHub Release creation")
        return

    if dry_run:
        kind = "pre-release" if prerelease else "release"
        info(f"[dry-run] would create GitHub {kind} {tag}")
        return

    cmd = ["gh", "release", "create", tag, "--title", tag, "--notes", changelog_section]
    if prerelease:
        cmd.append("--prerelease")

    result = run(cmd, check=False)
    if result.returncode == 0:
        ok(f"GitHub Release {tag} created")
    else:
        info(f"GitHub Release creation failed (non-fatal): {result.stderr.strip()}")


def changelog_section_for_tag(tag: str) -> str:
    """Extract one version's section body from CHANGELOG.md, keyed by its tag."""
    text = CHANGELOG_MD.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## \[{re.escape(tag)}\].*?\n(.*?)(?=^## \[|\Z)", re.MULTILINE | re.DOTALL
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip().rstrip("-").strip()


def cmd_publish(tag: str | None) -> int:
    """Create the GitHub Release for an already-pushed tag.

    Must run AFTER `git push origin <tag>` — `gh release create` requires the tag
    to exist on the remote first. See the module docstring for why this is a
    separate step instead of happening automatically during the release commit.
    """
    if tag is None:
        result = run(["git", "describe", "--tags", "--exact-match"], check=False)
        if result.returncode != 0:
            fail("HEAD is not exactly on a tag — pass the tag explicitly: release.py publish vX.Y.Z")
        tag = result.stdout.strip()

    # Confirm the tag actually exists on the remote before attempting gh release create
    # — a clear error here beats gh's own less obvious failure message.
    result = run(["git", "ls-remote", "--tags", "origin", tag], check=False)
    if not result.stdout.strip():
        fail(f"Tag {tag} not found on origin — push it first: git push origin {tag}")

    changelog_section = changelog_section_for_tag(tag)
    if not changelog_section:
        info(f"No CHANGELOG.md section found for {tag} — creating release with empty notes")

    prerelease = "-rc." in tag
    create_github_release(tag, changelog_section, dry_run=False, prerelease=prerelease)
    return 0


def git_commit_and_tag(
    new_version: str,
    tag: str,
    skill_count: int,
    changelog_section: str,
    dry_run: bool,
    prerelease: bool = False,
) -> None:
    msg = f"Release {tag}\n\n{skill_count} skills shipped. See CHANGELOG.md for details."

    if dry_run:
        info(f"[dry-run] would stage: skills.json .claude-plugin/plugin.json PLAN.md CHANGELOG.md")
        info(f"[dry-run] would commit: {msg.splitlines()[0]}")
        info(f"[dry-run] would tag:    {tag}")
        return

    run([
        "git", "add", "skills.json", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
        "PLAN.md", "CHANGELOG.md", "docs/reference/skills-report.md",
    ])
    run(["git", "commit", "-m", msg])
    run(["git", "tag", "-a", tag, "-m", f"Release {tag} — {skill_count} skills"])
    ok(f"Committed and tagged {tag}")
    # NOTE: does NOT create the GitHub Release here — `gh release create` requires the
    # tag to already exist on the remote, and pushing is a separate, later, manual step
    # (see the printed instructions below). Calling it at this point failed 100% of the
    # time, every release, for months (confirmed: 142 of 255 tags had no GitHub Release
    # — `gh release list` showed "latest" stuck at a release from weeks before the real
    # latest tag). Use `python3 scripts/release.py publish <tag>` after pushing instead.


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    # The ✅/❌ status lines can't be encoded on a Windows code page when output is piped.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")

    # `publish` is a separate mode (post-push GitHub Release creation) — dispatched
    # before the main argparse setup since it takes an optional tag, not a bump choice.
    if len(sys.argv) >= 2 and sys.argv[1] == "publish":
        tag = sys.argv[2] if len(sys.argv) >= 3 else None
        return cmd_publish(tag)

    parser = argparse.ArgumentParser(description="Release kmp-agent-skills")
    parser.add_argument(
        "bump",
        choices=["major", "minor", "patch", "auto"],
        help=(
            "Version component to bump. "
            "'auto' detects from conventional commits: "
            "feat!/ BREAKING CHANGE → major, feat → minor, fix/chore/docs → patch."
        ),
    )
    parser.add_argument("--channel", choices=["stable", "rc", "beta", "alpha", "dev", "snapshot"], default="stable",
                        help="Target release channel: stable, rc, beta, alpha, dev, snapshot (default: stable)")
    parser.add_argument("--rc", action="store_true",
                        help="Alias for --channel rc")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and preview without writing anything")
    args = parser.parse_args()

    channel = "rc" if args.rc else args.channel
    tier = channel.upper()
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}kmp-agent-skills release — bump: {args.bump}, channel: {channel}\n")

    if not args.dry_run:
        check_clean_tree()

    run_release_validation()

    # Determine new base version
    manifest = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    current_version = manifest["version"]

    bump = args.bump
    if bump == "auto":
        prev_stable = get_previous_stable_tag()
        bump = detect_bump_type(prev_stable)
        info(f"Auto-detected bump: {bump} (based on commits since {prev_stable or 'beginning'})")

    new_base_version = bump_version(current_version, bump)

    # Build the full tag string
    if channel == "snapshot":
        full_version = f"{new_base_version}-SNAPSHOT"
    elif channel in ("rc", "beta", "alpha", "dev"):
        seq_num = get_next_prerelease_number(new_base_version, channel)
        full_version = f"{new_base_version}-{channel}.{seq_num}"
    else:
        full_version = new_base_version
    is_prerelease = channel != "stable"

    tag = f"v{full_version}"
    info(f"Version: {current_version} → {new_base_version}  |  Tag: {tag}")

    if args.dry_run:
        skills = extract_skills()
        info(f"Skills count: {len(skills)}")
        prev_tag = get_previous_tag()
        info(f"Previous tag: {prev_tag or '(none)'}")
        update_changelog(full_version, prev_tag, dry_run=True)
        git_commit_and_tag(new_base_version, tag, len(skills), "", dry_run=True, prerelease=is_prerelease)
        info("Dry run complete — nothing written")
        return 0

    prev_tag = get_previous_tag()
    info(f"Previous tag: {prev_tag or '(none)'}")

    # skills.json always stores the base semver (no -rc suffix)
    update_skills_json(new_base_version)
    update_plugin_json(new_base_version)
    skill_count = len(json.loads(SKILLS_JSON.read_text(encoding="utf-8"))["skills"])
    update_plan_md(skill_count)
    changelog_section = update_changelog(full_version, prev_tag, dry_run=False)
    update_skills_report()
    git_commit_and_tag(new_base_version, tag, skill_count, changelog_section, dry_run=False, prerelease=is_prerelease)

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {'Release candidate' if args.rc else 'Release'} {tag} ready.

  Push when confirmed, then publish the GitHub Release:
    git push origin main
    git push origin {tag}
    python3 scripts/release.py publish {tag}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
