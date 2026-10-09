#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
validate_issue_payload.py — Lint and validate GitHub issue/comment markdown payloads.

Checks:
1. Escaped newline corruption (literal '\\n\\n' in text).
2. Unclosed code blocks (```) or unclosed inline backticks (`).
3. Required section headings based on issue template type.
4. With --pr: deferred work ("Not in this PR", "Follow-up", ...) that links no issue.

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


def check_markdown_fences(content: str) -> list[str]:
    """Check for unclosed code fences and backticks."""
    errors = []
    # Check triple backtick fences
    fence_count = len(re.findall(r"^```", content, re.MULTILINE))
    if fence_count % 2 != 0:
        errors.append(f"Unmatched code block fences (```): found {fence_count} (must be even).")

    # Strip code blocks before checking inline backticks
    stripped = re.sub(r"```[\s\S]*?```", "", content)
    inline_ticks = len(re.findall(r"(?<!`)`(?!`)", stripped))
    if inline_ticks % 2 != 0:
        errors.append(f"Unmatched inline backticks (`): found {inline_ticks} single backticks.")

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


def validate_payload(content: str, template: str | None = None, pr: bool = False) -> list[str]:
    """Run all validation checks and return list of errors."""
    errors = []
    errors.extend(check_escaped_newlines(content))
    errors.extend(check_markdown_fences(content))
    if template:
        errors.extend(check_template_sections(content, template))
    if pr:
        errors.extend(check_deferred_items(content))
    return errors


def main() -> int:
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
    args = parser.parse_args()

    if args.file == "-":
        content = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1
        content = path.read_text(encoding="utf-8")

    errors = validate_payload(content, args.template, args.pr)

    if errors:
        print("❌ Payload validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✅ Markdown payload is valid and shell-safe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
