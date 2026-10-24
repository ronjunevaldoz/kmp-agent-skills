#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
validate_issue_payload.py — Lint and validate GitHub issue/comment markdown payloads.

Checks:
1. Escaped newline corruption (literal '\\n\\n' in text).
2. Shell backtick-escape control characters (e.g. PowerShell `"..."` / `@"..."@` turning `` `a `` into '\\x07')
   and Windows cp1252 UTF-8 mojibake ('â€”', 'â€“', '\\ufffd').
3. Unclosed code blocks (```) or unclosed inline backticks (`).
4. Required section headings based on issue template type.
5. With --pr: deferred work ("Not in this PR", "Follow-up", ...) that links no issue.
6. AI-tool attribution: a "Generated with Claude Code"-style footer or an AI Co-authored-by line.

Usage:
  python3 validate_issue_payload.py /path/to/payload.md
  python3 validate_issue_payload.py /path/to/payload.md --template task
  gh pr view 42 --json body --jq .body | python3 validate_issue_payload.py - --pr
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Required sections per issue template type (case-insensitive substring check)
TEMPLATE_REQUIRED_SECTIONS: dict[str, list[str]] = {
    "epic": ["Objective", "Tracks", "Acceptance"],
    "task": ["Parent", "Description", "Acceptance"],
    "bug": ["Problem", "Evidence", "Acceptance"],
    "feature": ["Problem", "Proposal", "Acceptance"],
}

# Control characters outside \t (0x09), \n (0x0a), \r (0x0d). PowerShell double-quoted strings
# ("..." or @"..."@) turn `a -> \x07 (BEL), `b -> \x08 (BS), `f -> \x0c (FF), `v -> \x0b (VT),
# `0 -> \x00 (NUL), and `e -> \x1b (ESC).
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Common UTF-8 bytes decoded as Windows-1252 / Latin-1 when passed through non-UTF-8 shell pipes.
MOJIBAKE_PATTERNS: tuple[str, ...] = (
    "\u00e2\u20ac\u201d",  # â€” (em-dash —)
    "\u00e2\u20ac\u201c",  # â€“ (en-dash –)
    "\u00e2\u20ac\u2122",  # â€™ (right single quote ’)
    "\u00e2\u20ac\u0153",  # â€œ (left double quote “)
    "\u00e2\u2020\u2019",  # â†’ (right arrow →)
    "\u00c3\u2014",        # Ã— (multiplication sign ×)
    "\ufffd",              # Unicode replacement character
)


def check_escaped_newlines(content: str) -> list[str]:
    """Check for literal '\\n' sequences that should have been real newlines."""
    errors = []
    # Match literal \n\n or \n followed by word chars where a real newline was intended
    matches = re.findall(r"(?:[^\\]|^)(\\n(?:\\n)+)", content)
    if matches:
        errors.append(
            f"Found {len(matches)} literal '\\n' escape sequence(s). "
            "Markdown contains escaped newlines instead of real byte line breaks."
        )
    return errors


def check_shell_and_encoding_corruption(content: str) -> list[str]:
    """Check for PowerShell backtick-escape control characters and cp1252 UTF-8 mojibake."""
    errors = []
    control_matches = CONTROL_CHAR_RE.findall(content)
    if control_matches:
        sample = ", ".join(sorted({repr(ch) for ch in control_matches}))
        errors.append(
            f"Found {len(control_matches)} ASCII control character(s) ({sample}). "
            "PowerShell double-quoted strings (@\"...\"@) interpret `a, `b, `f, `v as control bytes and strip "
            "backticks; write the payload to a UTF-8 file and pass --body-file instead."
        )

    found_mojibake = [token for token in MOJIBAKE_PATTERNS if token in content]
    if found_mojibake:
        sample = ", ".join(repr(token) for token in found_mojibake)
        errors.append(
            f"Found corrupted UTF-8/cp1252 mojibake sequence(s) ({sample}). "
            "Prefer plain ASCII punctuation (-, --, ->, x) and pass UTF-8 files via --body-file."
        )
    return errors


def check_markdown_fences(content: str) -> list[str]:
    """Check for unclosed code fences and backticks."""
    errors = []
    # Check triple backtick fences
    fence_count = len(re.findall(r"^```", content, re.MULTILINE))
    if fence_count % 2 != 0:
        errors.append(f"Unmatched code block fences (```): found {fence_count} (must be even).")

    # Strip fenced code blocks, then strip balanced CommonMark inline code spans (`...`, `` `a ``, ``` `` `a `` ```)
    stripped = re.sub(r"```[\s\S]*?```", "", content)
    stripped = re.sub(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", "", stripped)
    unmatched_ticks = stripped.count("`")
    if unmatched_ticks > 0:
        errors.append(f"Unmatched inline backticks (`): found {unmatched_ticks} unmatched backtick(s).")

    return errors


def check_template_sections(content: str, template: str) -> list[str]:
    """Verify required section headers are present."""
    errors = []
    required = TEMPLATE_REQUIRED_SECTIONS.get(template.lower())
    if not required:
        return errors

    # Extract all markdown headers (#, ##, ###)
    headers = re.findall(r"^#{1,4}\s+(.+)$", content, re.MULTILINE)
    header_text = " ".join(headers).lower()

    for sec in required:
        if sec.lower() not in header_text:
            errors.append(f"Missing required section header containing '{sec}' for template '{template}'.")

    return errors


# A heading, bold lead-in, or bare "Label:" line that opens a list of work the PR leaves for
# later. Group 1 is the heading/bold marker; group 2 is the rest of the line.
DEFERRED_HEADING = re.compile(
    r"^\s*(#{1,6}\s+|\*\*)?\s*(?:not in this pr|follow[- ]?ups?|out of scope|known limits?"
    r"|left for later|deferred|still to do|not done)\b(.*)$",
    re.IGNORECASE,
)
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
ISSUE_LINK = re.compile(r"(?:[\w.-]+/[\w.-]+)?#\d+|/issues/\d+")


def check_deferred_items(content: str) -> list[str]:
    """Every list item under a deferred-work heading must link the issue that tracks it."""
    errors = []
    in_deferred = in_fence = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip():
            continue
        heading = DEFERRED_HEADING.match(line)
        # Prose that merely starts with a trigger word ("Deferred loading is ...") opens nothing.
        if heading and (heading.group(1) or heading.group(2).rstrip().endswith(":")):
            in_deferred = True
            continue
        if not in_deferred:
            continue
        if LIST_ITEM.match(line):
            if not ISSUE_LINK.search(line):
                errors.append(f"Deferred item links no issue: {line.strip()[:100]}")
        elif not line[0].isspace():
            in_deferred = False  # any heading, lead-in, or paragraph ends the list
    return errors


_AI_TOOL = r"(?:claude|anthropic|copilot|chatgpt|openai|codex|gemini)"
# A line that is only a footer like "🤖 Generated with [Claude Code](...)" or "Generated by GitHub
# Copilot"; prose that quotes the phrase mid-sentence is left alone.
AI_FOOTER = re.compile(
    rf"^\W*generated (?:with|by) \[?(?:[\w.-]+ )?{_AI_TOOL}[\w .-]*\]?(?:\([^)]*\))?\W*$", re.IGNORECASE)
# A co-author line crediting an AI tool; human co-authors are fine.
AI_COAUTHOR = re.compile(rf"^\s*co-authored-by:.*\b{_AI_TOOL}", re.IGNORECASE)


def check_ai_attribution(content: str) -> list[str]:
    """Issues, PR bodies and comments carry no AI-tool attribution footer or co-author line."""
    errors = []
    in_fence = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and (AI_FOOTER.match(line) or AI_COAUTHOR.match(line)):
            errors.append(f"AI attribution line (remove it): {line.strip()[:100]}")
    return errors


def extract_h2_headings(markdown: str) -> list[str]:
    """Return all level-2 markdown headings (`## Heading`) outside fenced code blocks."""
    headings: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1))
    return headings


def check_pr_template_sections(content: str, pr_template_path: Path | None) -> list[str]:
    """Verify that all `## ...` headings from `.github/pull_request_template.md` are present."""
    if pr_template_path is None or not pr_template_path.is_file():
        return []
    expected = extract_h2_headings(pr_template_path.read_text(encoding="utf-8"))
    actual_lower = {h.lower() for h in extract_h2_headings(content)}
    errors = []
    for heading in expected:
        if heading.lower() not in actual_lower:
            errors.append(
                f"Missing required PR template section '## {heading}' (from {pr_template_path.as_posix()})."
            )
    return errors


IMAGE_EMBED_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)|<img\b[^>]*\bsrc\s*=", re.IGNORECASE)


def check_pr_visual_evidence(content: str) -> list[str]:
    """When `--ui` is set, require at least one embedded screenshot/image in the PR body."""
    if not IMAGE_EMBED_RE.search(content):
        return [
            "UI PR is missing visual evidence: include at least one screenshot (`![alt](url)` or `<img src=\"...\" />`)."
        ]
    return []


def validate_payload(
    content: str,
    template: str | None = None,
    pr: bool = False,
    pr_template_path: Path | None = None,
    ui: bool = False,
) -> list[str]:
    """Run all validation checks and return list of errors."""
    errors = []
    errors.extend(check_escaped_newlines(content))
    errors.extend(check_shell_and_encoding_corruption(content))
    errors.extend(check_markdown_fences(content))
    errors.extend(check_ai_attribution(content))
    if template:
        errors.extend(check_template_sections(content, template))
    if pr:
        errors.extend(check_deferred_items(content))
        if pr_template_path is not None:
            errors.extend(check_pr_template_sections(content, pr_template_path))
        if ui:
            errors.extend(check_pr_visual_evidence(content))
    return errors


def _configure_utf8_stdio() -> None:
    """Ensure stdin/stdout/stderr use UTF-8 on Windows cp1252 consoles."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main() -> int:
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Lint and validate GitHub issue and comment markdown payloads."
    )
    parser.add_argument("file", help="Path to markdown payload file or '-' for stdin")
    parser.add_argument(
        "--template",
        choices=["epic", "task", "bug", "feature"],
        help="Optional issue template schema to validate sections against",
    )
    parser.add_argument(
        "--pr",
        action="store_true",
        help="Treat the payload as a PR body: deferred work must link its tracking issue",
    )
    parser.add_argument(
        "--pr-template",
        help="Optional path to .github/pull_request_template.md to verify all required ## headings are present",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="With --pr, require at least one embedded screenshot or image in the PR body",
    )
    args = parser.parse_args()

    if args.file == "-":
        content = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1
        content = path.read_text(encoding="utf-8")

    pr_template_path = Path(args.pr_template) if args.pr_template else None
    errors = validate_payload(
        content,
        args.template,
        args.pr,
        pr_template_path=pr_template_path,
        ui=args.ui,
    )

    if errors:
        print("❌ Payload validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✅ Markdown payload is valid and shell-safe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
