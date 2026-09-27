#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
validate_issue_payload.py — Lint and validate GitHub issue/comment markdown payloads.

Checks:
1. Escaped newline corruption (literal '\\n\\n' in text).
2. Unclosed code blocks (```) or unclosed inline backticks (`).
3. Required section headings based on issue template type.

Usage:
  python3 validate_issue_payload.py /path/to/payload.md
  python3 validate_issue_payload.py /path/to/payload.md --template task
  cat payload.md | python3 validate_issue_payload.py -
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


def validate_payload(content: str, template: str | None = None) -> list[str]:
    """Run all validation checks and return list of errors."""
    errors = []
    errors.extend(check_escaped_newlines(content))
    errors.extend(check_markdown_fences(content))
    if template:
        errors.extend(check_template_sections(content, template))
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
    args = parser.parse_args()

    if args.file == "-":
        content = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1
        content = path.read_text(encoding="utf-8")

    errors = validate_payload(content, args.template)

    if errors:
        print("❌ Payload validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✅ Markdown payload is valid and shell-safe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
