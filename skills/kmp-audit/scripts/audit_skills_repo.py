#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_MARKERS = (
    "## When to Use This Skill",
    "Trigger keywords:",
    "metadata:",
    "last-updated:",
    "## Changelog",
)

# Design-system content checks ─────────────────────────────────────────────────

# The base skill declares exactly these 6 core components — all must be implemented.
_DS_CORE_COMPONENTS = (
    "fun AppButton",
    "fun AppBadge",
    "fun AppCard",
    "fun AppChip",
    "fun AppTextField",
    "fun AppText",
)

# AppTheme.spacing.X / AppTheme.colors.X / AppTheme.typography.X — static access anti-pattern.
# Requires the trailing property name (.lg, .primary, …) to avoid matching inline-doc backticks.
_DS_STATIC_ACCESS_RE = re.compile(r"AppTheme\.(spacing|colors|typography)\.\w+")

# override val X = N.dp — hardcoded dp in a sealed-interface layout property.
# `override val dp = N.dp` (component dimension enums like IconSize, AvatarSize) is exempt.
# Plain `val` token definitions are also exempt; only other `override val` properties are flagged.
_DS_HARDCODED_DP_RE = re.compile(r"override val (?!dp\b)\w+ = \d+\.dp\b")


def _check_design_system(skill_dir: Path, text: str, findings: list[str]) -> None:
    """Targeted content checks for the design-system skills."""
    name = skill_dir.name
    if name not in (
        "kmp-compose-design-system",
        "kmp-compose-design-system-extended",
    ):
        return

    if name == "kmp-compose-design-system":
        # All 6 declared core components must have an implementation.
        missing = [c for c in _DS_CORE_COMPONENTS if c not in text]
        if missing:
            findings.append(
                f"{name}: missing component implementation(s): "
                + ", ".join(missing)
            )

        # Must have a Component Previews section with at least one previews/ block.
        if "## Component Previews" not in text or "### `previews/" not in text:
            findings.append(
                f"{name}: missing Component Previews section — "
                "add '## Component Previews' with previews/AppXxxPreview.kt blocks"
            )

        # `enum class TextStyle` collides with Compose's own TextStyle — rename to AppTextStyle.
        if re.search(r"\benum class TextStyle\b", text):
            findings.append(
                f"{name}: 'enum class TextStyle' shadows Compose's TextStyle — "
                "rename to AppTextStyle"
            )

        # ExperimentalStylesApi usage requires a visible @OptIn note.
        if "ExperimentalStylesApi" in text and "OptIn(ExperimentalStylesApi" not in text:
            findings.append(
                f"{name}: ExperimentalStylesApi used without @OptIn — "
                "add @file:OptIn(ExperimentalStylesApi::class) or a note in Steps 5–6"
            )

    # Both skills: AppTheme.<property>.<field> is a compile error — use appTheme accessor.
    if _DS_STATIC_ACCESS_RE.search(text):
        findings.append(
            f"{name}: AppTheme.<property>.<field> static access found — "
            "use the appTheme @Composable accessor instead"
        )

    # Both skills: hardcoded dp in override val should reference AppSpacing() tokens.
    if _DS_HARDCODED_DP_RE.search(text):
        findings.append(
            f"{name}: 'override val X = N.dp' found — "
            "use AppSpacing() token reference (e.g. AppSpacing().xxl)"
        )


FAST_MOVING_HINTS = (
    "agp",
    "buildkonfig",
    "compose",
    "koin",
    "ktor",
    "kotlin rpc",
    "kotlinx rpc",
    "navigation",
    "sqldelight",
    "resources",
    "graphics",
    "network",
    "database",
    "mvi",
)


# Subdirectories where all .md files must be kebab-case
KEBAB_DIRS = ("agents", "commands", "docs", "samples")

# Root-level .md files must be SCREAMING_CASE (all uppercase stem + optional underscores/hyphens)
_SCREAMING_RE = re.compile(r"^[A-Z][A-Z0-9_-]*$")
_KEBAB_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}-)?[a-z][a-z0-9-]*$")

# docs/tasks/<parent>/<NN>-<slug>-<status>.md — status lives in the filename, not
# hidden in frontmatter, so it's readable without opening the file. Numbering resets
# per parent folder, not enforced as globally unique here (authoring convention, not
# a mechanical invariant worth flagging gaps/reuse for).
_TASK_FILE_RE = re.compile(r"^\d{2}-[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(todo|doing|blocked|done)$")
_TASK_DATE_RE = re.compile(r"\*\*Date:\*\*\s*\d{4}-\d{2}-\d{2}")

# docs/decisions/<NNNN>-<slug>.md — Architecture Decision Records. Verified against
# the real, widely-adopted Nygard ADR pattern: one decision per file, 4-digit
# sequential numbering (found by number in a flat directory listing, not per-parent
# like tasks), a Status line so a reader can tell Accepted from Superseded without
# opening every file — same "status readable without opening the file" reasoning
# as the task-file convention above.
_DECISION_FILE_RE = re.compile(r"^\d{4}-[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_DECISION_STATUS_RE = re.compile(
    r"\*\*Status:\*\*\s*(Proposed|Accepted|Deprecated|Superseded)", re.IGNORECASE
)

# The only root-level .md files this repo's own docs-hygiene policy (see
# agents/docs-maintainer.md "Doc lifecycle") treats as permanent Reference docs
# (or the resolved-stays-for-reference KNOWN_ISSUES.md registry). Anything else at
# root is either a new permanent doc that needs adding here deliberately, or a
# Task-kind doc (an audit report, gap analysis, migration snapshot) that belongs
# in docs/tasks/ — never at repo root, archived to docs/tasks/archive/ when done.
_PERMANENT_ROOT_DOCS = {
    "AGENTS", "CHANGELOG", "CLAUDE", "CONTRIBUTING", "FUNDING",
    "GETTING_STARTED", "INSTALL", "KNOWN_ISSUES", "PLAN", "README", "RELEASING",
}


def _check_naming_conventions(root: Path, findings: list[str]) -> None:
    # Root-level .md files must be SCREAMING_CASE
    for f in root.glob("*.md"):
        if not _SCREAMING_RE.match(f.stem):
            findings.append(
                f"naming: root-level {f.name} should be SCREAMING_CASE "
                f"(e.g. {f.stem.upper()}.md)"
            )

    # Subdirectory .md files must be kebab-case
    for subdir_name in KEBAB_DIRS:
        subdir = root / subdir_name
        if not subdir.exists():
            continue
        for f in subdir.rglob("*.md"):
            # docs/tasks/ has its own <NN>-<slug>-<status>.md convention, validated
            # separately by _check_docs_hygiene — skip it here to avoid a false
            # positive against the generic kebab regex.
            if subdir_name == "docs" and f.relative_to(subdir).parts[0] == "tasks":
                continue
            if not _KEBAB_RE.match(f.stem):
                findings.append(
                    f"naming: {f.relative_to(root)} should be kebab-case "
                    f"(e.g. {f.stem.lower().replace('_', '-')}.md)"
                )


def _check_stale_task_docs_at_root(root: Path, findings: list[str]) -> None:
    for f in root.glob("*.md"):
        if f.stem.upper() not in _PERMANENT_ROOT_DOCS:
            findings.append(
                f"docs-hygiene: root-level {f.name} looks like a Task-kind doc "
                f"(one-off audit/report/gap-analysis) — move to "
                f"docs/tasks/<parent>/01-slug-todo.md, and rename to "
                f"docs/tasks/<parent>/archive/01-slug-done.md once actioned. "
                f"If this is a genuinely new permanent doc, add its name to "
                f"_PERMANENT_ROOT_DOCS in audit_skills_repo.py."
            )


# _check_docs_hygiene's 150-line limit only ever scans docs_dir = root / "docs" — every
# _PERMANENT_ROOT_DOCS file sits at the root, one directory above that, and was
# completely outside any size check. Found real: INSTALL.md had grown to 609 lines with
# nobody catching it. CHANGELOG.md is deliberately excluded — it's auto-generated,
# append-only (policy: never edit for dev commits), and its growth is the whole point,
# unlike every other root doc here which should stay navigable.
ROOT_DOC_MAX_LINES = 500
_ROOT_DOCS_WITH_SIZE_LIMIT = _PERMANENT_ROOT_DOCS - {"CHANGELOG"}


def _check_root_doc_hygiene(root: Path, findings: list[str]) -> None:
    for f in root.glob("*.md"):
        if f.stem.upper() not in _ROOT_DOCS_WITH_SIZE_LIMIT:
            continue
        lines = f.read_text(encoding="utf-8", errors="ignore").count("\n")
        if lines > ROOT_DOC_MAX_LINES:
            findings.append(
                f"docs-hygiene: root-level {f.name} is {lines} lines "
                f"(limit {ROOT_DOC_MAX_LINES}) — split the least-central sections into "
                f"docs/reference/*.md and leave a pointer, same pattern used for "
                f"oversized SKILL.md/command files"
            )


# CHANGELOG.md itself is exempt from ROOT_DOC_MAX_LINES above (append-only, growth is
# the point), but a git-cliff-style `## [Unreleased]` section only ever gets flushed by
# an actual `git-cliff --tag` release run — nothing flags a project that just never cuts
# one, so it silently accumulates forever. This catches that case without depending on
# git (a filename/heading-only scan, consistent with every other check in this file).
CHANGELOG_UNRELEASED_BACKLOG_LIMIT = 20


def _check_changelog_unreleased_backlog(root: Path, findings: list[str]) -> None:
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    lines = changelog.read_text(encoding="utf-8", errors="ignore").splitlines()
    in_unreleased = False
    entry_count = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"^##\s*\[unreleased\]", stripped, re.IGNORECASE):
            in_unreleased = True
            continue
        if in_unreleased and stripped.startswith("## "):
            break
        if in_unreleased and stripped.startswith("- "):
            entry_count += 1

    if entry_count > CHANGELOG_UNRELEASED_BACKLOG_LIMIT:
        findings.append(
            f"docs-hygiene: CHANGELOG.md's [Unreleased] section has {entry_count} entries "
            f"(limit {CHANGELOG_UNRELEASED_BACKLOG_LIMIT}) — cut a release "
            f"(`git-cliff --tag vX.Y.Z --output CHANGELOG.md`, see kmp-release) so it "
            f"flushes into a dated version section instead of growing indefinitely"
        )


DOCS_MAX_LINES = 150
LESSON_STALE_DAYS = 30
LESSON_BACKLOG_LIMIT = 20

# Canonical top-level directories permitted under docs/
_CANONICAL_DOCS_SUBDIRS = {
    "reference",
    "tasks",
    "decisions",
    "lessons",
    "bugs",
    "mvp",
    "archive",
    "audits",
    "assets",
    "images",
}

# Non-doc extensions that do not belong directly inside docs/
_NON_DOC_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".xml", ".csv", ".toml",
    ".proto", ".graphql", ".sql", ".sh", ".py", ".kt",
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".7z",
    ".pdf", ".ipynb", ".bin", ".exe", ".dylib", ".so",
}

# Asset image extensions — only permitted inside docs/assets/ or docs/images/
_DOC_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp",
}

# Subdirectory names that are known non-doc homes inside docs/
# (do not flag files inside these — they were intentionally placed)
_KNOWN_NON_DOC_SUBDIRS = {"archive"}

# Case-insensitive: catches both snake_case and SCREAMING_SNAKE_CASE — docs/ subdirectory
# files must be kebab-case regardless of which underscore-separated case they picked.
# (Root-level docs are the opposite — _check_naming_conventions requires SCREAMING_CASE
# there — this check only ever runs against files under docs/.)
_SNAKE_CASE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)+$")


_JVM_ONLY_APIS = (
    "String.format(",
    ".format(",
    "DecimalFormat(",
    "SimpleDateFormat(",
    "java.text.",
    "java.util.Locale",
    "java.util.Date",
    "java.util.Calendar",
)


def _check_commonmain_jvm_apis(root: Path, findings: list[str]) -> None:
    """Flag JVM-only APIs used in commonMain Kotlin source files."""
    for common_main in root.rglob("commonMain"):
        if not common_main.is_dir():
            continue
        for kt in common_main.rglob("*.kt"):
            text = kt.read_text(encoding="utf-8")
            hits = [api for api in _JVM_ONLY_APIS if api in text]
            if hits:
                findings.append(
                    f"jvm-only in commonMain: {kt.relative_to(root)} uses "
                    + ", ".join(f"`{h.rstrip('(')}`" for h in hits)
                    + " — replace with Kotlin string templates or an expect/actual formatter"
                )


def _check_docs_hygiene(root: Path, findings: list[str]) -> None:
    """Flag bloated, stale, or un-archived docs/ files in a consumer project."""
    docs_dir = root / "docs"
    if not docs_dir.exists():
        return

    import datetime

    today = datetime.date.today()

    # 0. Check top-level subdirectories in docs/ against canonical topology
    for d in sorted(docs_dir.iterdir()):
        if d.is_dir() and d.name not in _CANONICAL_DOCS_SUBDIRS:
            findings.append(
                f"docs hygiene: docs/{d.name}/ is not a canonical docs subdirectory "
                f"— move under docs/reference/, docs/tasks/, or docs/archive/"
            )

    # 1. Any docs/ file (outside archive/) exceeding the line limit
    for md in docs_dir.rglob("*.md"):
        if "archive" in md.parts:
            continue
        lines = md.read_text(encoding="utf-8").count("\n")
        if lines > DOCS_MAX_LINES:
            findings.append(
                f"docs hygiene: {md.relative_to(root)} is {lines} lines "
                f"(limit {DOCS_MAX_LINES}) — split or archive completed sections"
            )

    # 2. Lessons older than LESSON_STALE_DAYS still in active lessons dir
    lessons_dir = docs_dir / "lessons"
    if lessons_dir.exists():
        stale = []
        for md in sorted(lessons_dir.glob("*.md")):
            # Filename must start with YYYY-MM-DD
            stem = md.stem
            try:
                file_date = datetime.date.fromisoformat(stem[:10])
                age = (today - file_date).days
                if age > LESSON_STALE_DAYS:
                    stale.append((md.relative_to(root), age))
            except ValueError:
                findings.append(
                    f"docs hygiene: {md.relative_to(root)} filename does not start "
                    "with YYYY-MM-DD — rename to match lesson convention"
                )
        for path, age in stale:
            findings.append(
                f"docs hygiene: {path} is {age} days old and not yet harvested "
                "— run kmp-skill-harvester or archive"
            )

        # 3. Too many unprocessed lessons
        total = sum(1 for _ in lessons_dir.glob("*.md"))
        if total > LESSON_BACKLOG_LIMIT:
            findings.append(
                f"docs hygiene: {total} lesson files in docs/lessons/ "
                f"(limit {LESSON_BACKLOG_LIMIT}) — harvest and archive processed lessons"
            )

    # 4. Task files: docs/tasks/<parent>/<NN>-<slug>-<status>.md — status lives in the
    # filename (todo/doing/blocked/done), the date lives inside the content instead.
    tasks_dir = docs_dir / "tasks"
    if tasks_dir.exists():
        tasks_index = docs_dir / "tasks.md"
        tasks_index_text = (
            tasks_index.read_text(encoding="utf-8", errors="ignore") if tasks_index.exists() else ""
        )
        for loose in sorted(tasks_dir.glob("*.md")):
            findings.append(
                f"docs hygiene: {loose.relative_to(root)} sits directly in docs/tasks/ "
                "— move under a parent folder: docs/tasks/<parent>/01-slug-todo.md"
            )
        for parent_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
            if parent_dir.name == "archive":
                continue
            for md in sorted(parent_dir.rglob("*.md")):
                if "archive" in md.parts:
                    continue
                m = _TASK_FILE_RE.match(md.stem)
                if not m:
                    findings.append(
                        f"docs hygiene: {md.relative_to(root)} does not match "
                        "<NN>-<slug>-<status>.md (status: todo/doing/blocked/done) "
                        "— rename to match the task naming convention"
                    )
                    continue
                if m.group(1) == "done":
                    findings.append(
                        f"docs hygiene: {md.relative_to(root)} is marked done "
                        f"— move to {parent_dir.relative_to(root)}/archive/"
                    )
                if not _TASK_DATE_RE.search(
                    md.read_text(encoding="utf-8", errors="ignore")
                ):
                    findings.append(
                        f"docs hygiene: {md.relative_to(root)} is missing a "
                        "**Date:** YYYY-MM-DD line in its content"
                    )
                if md.name not in tasks_index_text:
                    findings.append(
                        f"docs hygiene: {md.relative_to(root)} is not indexed in "
                        "docs/tasks.md — add a Task Log row so status is readable "
                        "without opening every task file"
                    )

    # 4b. Decision records: docs/decisions/<NNNN>-<slug>.md, one decision per file,
    # a Status line so a reader can tell Accepted from Superseded without opening it.
    decisions_dir = docs_dir / "decisions"
    if decisions_dir.exists():
        for md in sorted(decisions_dir.glob("*.md")):
            if not _DECISION_FILE_RE.match(md.stem):
                findings.append(
                    f"docs hygiene: {md.relative_to(root)} does not match "
                    "<NNNN>-<slug>.md (4-digit, sequential) — rename to match the "
                    "ADR naming convention"
                )
                continue
            if not _DECISION_STATUS_RE.search(md.read_text(encoding="utf-8", errors="ignore")):
                findings.append(
                    f"docs hygiene: {md.relative_to(root)} is missing a "
                    "**Status:** line (Proposed/Accepted/Superseded/Deprecated)"
                )

    # 5. Non-markdown and asset files in docs/ (flag as non-docs / mislocated assets)
    for f in sorted(docs_dir.rglob("*")):
        if not f.is_file() or "archive" in f.parts:
            continue
        ext = f.suffix.lower()
        if ext in _NON_DOC_EXTENSIONS:
            findings.append(
                f"docs hygiene: {f.relative_to(root)} is a non-doc file inside docs/ "
                f"— move to tests/fixtures/, api/, or spec/"
            )
        elif ext in _DOC_IMAGE_EXTENSIONS:
            if not any(p in f.parts for p in ("assets", "images")):
                findings.append(
                    f"docs hygiene: {f.relative_to(root)} is an asset file outside docs/assets/ or docs/images/ "
                    f"— move to docs/assets/ or docs/images/"
                )

    # 6. Snake_case filenames in docs/ (should be kebab-case)
    for md in docs_dir.rglob("*.md"):
        if "archive" in md.parts:
            continue
        if _SNAKE_CASE_RE.match(md.stem):
            kebab = md.stem.replace("_", "-").lower()
            findings.append(
                f"docs hygiene: {md.relative_to(root)} is not kebab-case "
                f"— rename to {kebab}.md"
            )


# ── Orphaned reference doc (no inbound links from anywhere in the repo) ─────────
# docs-hygiene.md already tells a human to "grep for inbound links" before deleting a
# reference doc — this automates that grep as a nudge, not a verdict. A doc with zero
# inbound links isn't necessarily stale (it could be a fresh doc nothing points to yet,
# or an intentional standalone entry point), so this stays a review flag, same
# treatment as every other non-blocking hint in this file.

_REFERENCE_DOC_EXCLUDE_SUBDIR_NAMES = {"tasks", "lessons", "bugs", "mvp", "archive", "decisions"}


def _iter_reference_docs(docs_dir: Path):
    for f in sorted(docs_dir.glob("*.md")):
        yield f
    reference_dir = docs_dir / "reference"
    if reference_dir.is_dir():
        for f in sorted(reference_dir.rglob("*.md")):
            if "archive" in f.relative_to(reference_dir).parts:
                continue
            yield f


def _check_orphaned_reference_docs(root: Path, findings: list[str]) -> None:
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return
    reference_docs = list(_iter_reference_docs(docs_dir))
    if not reference_docs:
        return

    all_md_files = [p for p in root.rglob("*.md") if "archive" not in p.parts]
    combined_text = ""
    for p in all_md_files:
        try:
            combined_text += p.read_text(encoding="utf-8", errors="ignore") + "\n"
        except OSError:
            continue

    for doc in reference_docs:
        rel = doc.relative_to(root)
        # Every mention of this doc's own filename counts as an inbound link,
        # including the doc's own self-mention in a header comment — subtract 1.
        mentions = combined_text.count(doc.name)
        try:
            self_mentions = doc.read_text(encoding="utf-8", errors="ignore").count(doc.name)
        except OSError:
            self_mentions = 0
        if mentions - self_mentions <= 0:
            findings.append(
                f"docs hygiene: {rel} has no inbound links from anywhere else in the "
                f"repo — review whether it's stale and should be deleted, or just "
                f"needs linking from wherever introduces the topic (see docs-hygiene.md's "
                f"Delete vs Archive table before deleting)"
            )


def audit_skills_repo(root: Path) -> list[str]:
    findings: list[str] = []
    skills_dir = root / "skills"

    if not skills_dir.exists():
        return [f"missing skills directory: {skills_dir}"]

    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            findings.append(f"{skill_dir.name}: missing SKILL.md")
            continue

        text = skill_file.read_text(encoding="utf-8")
        missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
        if missing:
            findings.append(f"{skill_dir.name}: missing markers: {', '.join(missing)}")

        if (skill_dir / "references").exists() and "Reference" not in text and "Docs to Recheck First" not in text:
            findings.append(f"{skill_dir.name}: has references/ but no references guidance in SKILL.md")

        if (skill_dir / "scripts").exists() and "Script" not in text and "scripts/" not in text:
            findings.append(f"{skill_dir.name}: has scripts/ but no script guidance in SKILL.md")

        # agentskills.io's real spec (docs/reference/agentskills-io-standards.md) lists
        # assets/ as the official "templates, static resources" directory — same
        # undocumented-directory risk as scripts/ and references/ above, so it gets the
        # same guard. Note: this repo's pre-existing templates/ (4 skills, project
        # scaffolding trees) predates that doc and isn't part of the spec — a separate,
        # still-unchecked convention, not folded into this check.
        if (skill_dir / "assets").exists() and "Asset" not in text and "assets/" not in text:
            findings.append(f"{skill_dir.name}: has assets/ but no assets guidance in SKILL.md")

        design_system_text = text
        references_dir = skill_dir / "references"
        if references_dir.exists():
            design_system_text += "\n" + "\n".join(
                ref.read_text(encoding="utf-8") for ref in sorted(references_dir.glob("*.md"))
            )
        _check_design_system(skill_dir, design_system_text, findings)

        if any(hint in text.lower() for hint in FAST_MOVING_HINTS) and re.search(
            r"latest|freshness|recheck",
            text,
            re.IGNORECASE,
        ) is None:
            findings.append(f"{skill_dir.name}: missing freshness guidance for fast-moving dependencies")

        if skill_dir.name == "kmp-feature-scaffold" and "all-targets" not in text:
            findings.append(
                "kmp-feature-scaffold: missing all-targets branch guidance for full-stack KMP scaffolds"
            )

        if skill_dir.name == "kmp-feature-scaffold" and (
            "build-logic" not in text or "libs.versions.toml" not in text
        ):
            findings.append(
                "kmp-feature-scaffold: missing build-logic and libs.versions.toml guidance"
            )

    _check_naming_conventions(root, findings)
    _check_stale_task_docs_at_root(root, findings)
    _check_docs_hygiene(root, findings)
    _check_root_doc_hygiene(root, findings)
    _check_changelog_unreleased_backlog(root, findings)
    _check_commonmain_jvm_apis(root, findings)

    readme = root / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
        if "Start here" not in readme_text:
            findings.append("README.md: missing start-here guidance")
        if "Roadmap" not in readme_text:
            findings.append("README.md: missing roadmap section")
    else:
        findings.append("missing README.md")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the skills repo for documentation hygiene.")
    parser.add_argument("root", type=Path, help="Repo root")
    parser.add_argument(
        "--docs-hygiene-only",
        action="store_true",
        help="Run only the docs/ hygiene checks (line limits, stale lessons, done tasks)",
    )
    parser.add_argument(
        "--jvm-api-only",
        action="store_true",
        help="Scan only for JVM-only APIs in commonMain Kotlin files",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if args.docs_hygiene_only:
        findings: list[str] = []
        _check_docs_hygiene(root, findings)
        _check_root_doc_hygiene(root, findings)
        _check_changelog_unreleased_backlog(root, findings)
        _check_orphaned_reference_docs(root, findings)
    elif args.jvm_api_only:
        findings = []
        _check_commonmain_jvm_apis(root, findings)
    else:
        findings = audit_skills_repo(root)
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
