#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
pr_visual_evidence.py — Build a before/after screenshot section for a PR body or comment.

Diffs committed screenshot goldens (Roborazzi snapshots) between a base and a head
commit and renders an HTML table whose images are SHA-pinned GitHub blob links:

  https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true

No upload is needed — `gh` and the REST API cannot attach images to a PR body, but
blob links to committed PNGs render inline. Both SHAs must be pushed. In private repos
the images render only for signed-in members.

  A (added)     -> "New" section
  M/T (changed) -> Before | After pair
  R (renamed)   -> Before | After pair (old path at base, new path at head)
  C (copied)    -> "New" section
  D (deleted)   -> "Removed" section

Usage:
  python3 pr_visual_evidence.py > /tmp/visual.md
  python3 pr_visual_evidence.py --base <sha-of-rerecord-commit> --head HEAD
  python3 pr_visual_evidence.py --glob '**/src/desktopTest/snapshots/*.png'
  python3 pr_visual_evidence.py --target origin/develop --repo owner/repo
"""
from __future__ import annotations

import argparse
import re
import struct
import subprocess
import sys
from urllib.parse import quote

MARKER = "<!-- pr-visual-evidence -->"
DEFAULT_GLOBS = ["**/snapshots/**/*.png"]
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
PHONE_WIDTH = 360
DESKTOP_WIDTH = 420
DETAILS_THRESHOLD = 3  # sections longer than this collapse into <details>


def git(*args: str, cwd: str | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def parse_github_repo(remote_url: str) -> str | None:
    """Return 'owner/repo' from an https/ssh GitHub remote URL."""
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", remote_url.strip())
    return f"{match.group(1)}/{match.group(2)}" if match else None


def to_pathspec(glob: str) -> str:
    """Use :(glob) magic so '**/' matches zero or more directories."""
    return glob if glob.startswith(":") else f":(glob){glob}"


def diff_snapshots(base: str, head: str, globs: list[str], cwd: str | None = None) -> list[tuple]:
    """Return (status, old_path, new_path) entries for changed image files."""
    out = git(
        "diff", "--name-status", "-z", "-M", base, head, "--",
        *[to_pathspec(g) for g in globs], cwd=cwd,
    )
    fields = out.split("\0")
    entries = []
    i = 0
    while i < len(fields) and fields[i]:
        status = fields[i][0]
        if status in "RC":
            old, new = fields[i + 1], fields[i + 2]
            i += 3
        else:
            old = new = fields[i + 1]
            i += 2
        if new.lower().endswith(IMAGE_EXTENSIONS) or old.lower().endswith(IMAGE_EXTENSIONS):
            entries.append((status, old, new))
    return entries


def image_width(sha: str, path: str, cwd: str | None = None) -> int:
    """Landscape PNG (desktop) -> DESKTOP_WIDTH, otherwise PHONE_WIDTH."""
    header = subprocess.run(
        ["git", "cat-file", "blob", f"{sha}:{path}"], cwd=cwd, capture_output=True
    ).stdout[:24]
    if header[:8] == b"\x89PNG\r\n\x1a\n" and len(header) == 24:
        width, height = struct.unpack(">II", header[16:24])
        if width > height:
            return DESKTOP_WIDTH
    return PHONE_WIDTH


def img(repo: str, sha: str, path: str, width: int, alt: str) -> str:
    url = f"https://github.com/{repo}/blob/{sha}/{quote(path)}?raw=true"
    return f'<img src="{url}" width="{width}" alt="{alt}">'


def section(title: str, rows: list[str], header: str) -> list[str]:
    table = ["<table>", header, *rows, "</table>"]
    if len(rows) > DETAILS_THRESHOLD:
        return [f"### {title} ({len(rows)})", "", "<details>",
                f"<summary>Show {len(rows)}</summary>", "", *table, "", "</details>", ""]
    return [f"### {title} ({len(rows)})", "", *table, ""]


def render(entries: list[tuple], repo: str, base_sha: str, head_sha: str,
           width: int | None = None, cwd: str | None = None) -> str:
    span = f"`{base_sha[:7]}`..`{head_sha[:7]}`"
    if not entries:
        return f"{MARKER}\nNo before/after: no committed snapshot changed in {span}.\n"

    changed, added, removed = [], [], []
    for status, old, new in entries:
        if status == "D":
            w = width or image_width(base_sha, old, cwd)
            removed.append(f"<tr><td><code>{old}</code><br>{img(repo, base_sha, old, w, 'removed')}</td></tr>")
        elif status in "AC":
            w = width or image_width(head_sha, new, cwd)
            added.append(f"<tr><td><code>{new}</code><br>{img(repo, head_sha, new, w, 'new')}</td></tr>")
        else:  # M, T, R
            w = width or image_width(head_sha, new, cwd)
            label = f"<code>{old}</code> → <code>{new}</code>" if old != new else f"<code>{new}</code>"
            changed.append(
                f'<tr><td colspan="2">{label}</td></tr>\n'
                f"<tr><td>{img(repo, base_sha, old, w, 'before')}</td>"
                f"<td>{img(repo, head_sha, new, w, 'after')}</td></tr>"
            )

    lines = [MARKER, "## Visual evidence", "",
             f"Before `{base_sha[:7]}` · After `{head_sha[:7]}` (committed snapshots).", ""]
    if changed:
        lines += section("Changed", changed, "<tr><th>Before</th><th>After</th></tr>")
    if added:
        lines += section("New", added, "<tr><th>New snapshot</th></tr>")
    if removed:
        lines += section("Removed", removed, "<tr><th>Removed snapshot</th></tr>")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render before/after snapshot evidence for a PR body from committed goldens."
    )
    parser.add_argument("--base", help="Before ref (default: merge-base of --target and --head)")
    parser.add_argument("--head", default="HEAD", help="After ref (default: HEAD)")
    parser.add_argument("--target", default="origin/main",
                        help="Branch the PR merges into, used for the default --base")
    parser.add_argument("--glob", action="append", dest="globs",
                        help=f"Snapshot glob, repeatable (default: {DEFAULT_GLOBS[0]})")
    parser.add_argument("--repo", help="owner/repo (default: parsed from `git remote get-url origin`)")
    parser.add_argument("--width", type=int,
                        help=f"Force image width (default: {PHONE_WIDTH} portrait, {DESKTOP_WIDTH} landscape)")
    args = parser.parse_args()

    try:
        head_sha = git("rev-parse", f"{args.head}^{{commit}}").strip()
        base_ref = args.base or git("merge-base", args.target, head_sha).strip()
        base_sha = git("rev-parse", f"{base_ref}^{{commit}}").strip()
        repo = args.repo or parse_github_repo(git("remote", "get-url", "origin"))
        entries = diff_snapshots(base_sha, head_sha, args.globs or DEFAULT_GLOBS)
    except subprocess.CalledProcessError as exc:
        print(f"Error: git {' '.join(exc.cmd[1:])} failed: {exc.stderr.strip()}", file=sys.stderr)
        return 1
    if not repo:
        print("Error: origin is not a GitHub remote; pass --repo owner/repo", file=sys.stderr)
        return 1

    sys.stdout.write(render(entries, repo, base_sha, head_sha, args.width))
    return 0


if __name__ == "__main__":
    sys.exit(main())
