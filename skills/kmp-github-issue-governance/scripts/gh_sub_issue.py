#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""
GitHub Sub-Issue CLI Helper.

Interacts with GitHub's native Sub-Issues GraphQL API to add, create,
list, and remove parent-child issue relationships.

Prerequisites:
  - GitHub CLI (`gh`) must be installed and authenticated (`gh auth status`).

Commands:
  add <parent> <child>          Attach an existing issue as a sub-issue of parent
  create <parent> --title ...   Create a new issue and immediately attach it to parent
  list <parent>                 List all sub-issues of a parent issue
  remove <parent> <child>       Detach a sub-issue from its parent
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_gh_cmd(args: list[str]) -> tuple[int, str, str]:
    """Execute a `gh` command and return (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["gh"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        print("Error: `gh` CLI is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)


def detect_repo(override_repo: str | None = None) -> tuple[str, str]:
    """Detect owner and repo from current git directory or override."""
    if override_repo:
        if "/" not in override_repo:
            print(f"Error: Repository must be in 'owner/repo' format, got: {override_repo}", file=sys.stderr)
            sys.exit(1)
        owner, name = override_repo.split("/", 1)
        return owner.strip(), name.strip()

    code, out, err = run_gh_cmd(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    if code != 0 or not out:
        print(f"Error: Could not determine GitHub repository context: {err}", file=sys.stderr)
        print("Specify `--repo owner/repo` explicitly.", file=sys.stderr)
        sys.exit(1)

    owner, name = out.strip().split("/", 1)
    return owner, name


def execute_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Run a GraphQL query with variables via `gh api graphql`."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, val in variables.items():
        if val is None:
            continue
        if isinstance(val, (int, bool)):
            args.extend(["-F", f"{key}={val}"])
        else:
            args.extend(["-f", f"{key}={str(val)}"])

    code, out, err = run_gh_cmd(args)
    if code != 0:
        print(f"GraphQL Error:\n{err or out}", file=sys.stderr)
        sys.exit(code)

    try:
        data = json.loads(out)
        if "errors" in data and data["errors"]:
            print(f"GraphQL Error: {json.dumps(data['errors'], indent=2)}", file=sys.stderr)
            sys.exit(1)
        return data.get("data", {})
    except json.JSONDecodeError:
        print(f"Failed to decode GraphQL response: {out}", file=sys.stderr)
        sys.exit(1)


def get_issue_node_id(owner: str, repo: str, issue_number: int) -> tuple[str, str]:
    """Get the GraphQL node ID and title of an issue."""
    query = """
    query($owner: String!, $repo: String!, $num: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $num) {
          id
          title
        }
      }
    }
    """
    data = execute_graphql(query, {"owner": owner, "repo": repo, "num": issue_number})
    issue_data = data.get("repository", {}).get("issue")
    if not issue_data:
        print(f"Error: Issue #{issue_number} not found in {owner}/{repo}.", file=sys.stderr)
        sys.exit(1)
    return issue_data["id"], issue_data["title"]


def cmd_add(args: argparse.Namespace) -> None:
    owner, repo = detect_repo(args.repo)
    parent_id, parent_title = get_issue_node_id(owner, repo, args.parent)
    child_id, child_title = get_issue_node_id(owner, repo, args.child)

    mutation = """
    mutation($parentId: ID!, $subIssueId: ID!) {
      addSubIssue(input: {issueId: $parentId, subIssueId: $subIssueId}) {
        subIssue {
          number
          title
        }
      }
    }
    """
    execute_graphql(mutation, {"parentId": parent_id, "subIssueId": child_id})
    print(f"✅ Attached #{args.child} (\"{child_title}\") as sub-issue of #{args.parent} (\"{parent_title}\").")


def cmd_create(args: argparse.Namespace) -> None:
    owner, repo = detect_repo(args.repo)
    parent_id, parent_title = get_issue_node_id(owner, repo, args.parent)

    create_cmd = ["issue", "create", "--repo", f"{owner}/{repo}", "--title", args.title]
    if args.body_file:
        create_cmd.extend(["--body-file", args.body_file])
    elif args.body:
        create_cmd.extend(["--body", args.body])
    else:
        create_cmd.extend(["--body", ""])

    for label in (args.labels or []):
        create_cmd.extend(["--label", label])

    code, out, err = run_gh_cmd(create_cmd)
    if code != 0 or not out:
        print(f"Error creating child issue: {err or out}", file=sys.stderr)
        sys.exit(code)

    created_url = out.strip().split()[-1]
    child_number_str = created_url.split("/")[-1]
    try:
        child_num = int(child_number_str)
    except ValueError:
        print(f"Error: Could not parse issue number from created URL: {created_url}", file=sys.stderr)
        sys.exit(1)

    child_id, _ = get_issue_node_id(owner, repo, child_num)

    mutation = """
    mutation($parentId: ID!, $subIssueId: ID!) {
      addSubIssue(input: {issueId: $parentId, subIssueId: $subIssueId}) {
        subIssue {
          number
          title
        }
      }
    }
    """
    execute_graphql(mutation, {"parentId": parent_id, "subIssueId": child_id})
    print(f"✅ Created #{child_num} (\"{args.title}\") and attached as sub-issue of #{args.parent} (\"{parent_title}\").")


def cmd_list(args: argparse.Namespace) -> None:
    owner, repo = detect_repo(args.repo)
    query = """
    query($owner: String!, $repo: String!, $num: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $num) {
          title
          state
          subIssues(first: 50) {
            totalCount
            nodes {
              number
              title
              state
            }
          }
        }
      }
    }
    """
    data = execute_graphql(query, {"owner": owner, "repo": repo, "num": args.parent})
    issue_data = data.get("repository", {}).get("issue")
    if not issue_data:
        print(f"Error: Issue #{args.parent} not found in {owner}/{repo}.", file=sys.stderr)
        sys.exit(1)

    sub_issues = issue_data.get("subIssues", {})
    count = sub_issues.get("totalCount", 0)
    nodes = sub_issues.get("nodes", [])

    print(f"Parent #{args.parent}: \"{issue_data['title']}\" [{issue_data['state']}]")
    print(f"Sub-issues ({count}):")
    if not nodes:
        print("  (None)")
        return

    for node in nodes:
        icon = "✅" if node["state"] == "CLOSED" else "⏳"
        print(f"  {icon} #{node['number']} {node['title']} [{node['state']}]")


def cmd_remove(args: argparse.Namespace) -> None:
    owner, repo = detect_repo(args.repo)
    parent_id, parent_title = get_issue_node_id(owner, repo, args.parent)
    child_id, child_title = get_issue_node_id(owner, repo, args.child)

    mutation = """
    mutation($parentId: ID!, $subIssueId: ID!) {
      removeSubIssue(input: {issueId: $parentId, subIssueId: $subIssueId}) {
        subIssue {
          number
          title
        }
      }
    }
    """
    execute_graphql(mutation, {"parentId": parent_id, "subIssueId": child_id})
    print(f"✅ Detached #{args.child} (\"{child_title}\") from parent #{args.parent} (\"{parent_title}\").")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GitHub Sub-Issues GraphQL CLI Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", help="Target repository in 'owner/repo' format (auto-detected if omitted)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Attach an existing issue as a sub-issue")
    add_p.add_argument("parent", type=int, help="Parent issue number (Epic)")
    add_p.add_argument("child", type=int, help="Child issue number to attach")

    create_p = subparsers.add_parser("create", help="Create a new issue and attach as sub-issue")
    create_p.add_argument("parent", type=int, help="Parent issue number (Epic)")
    create_p.add_argument("--title", required=True, help="Child issue title")
    create_p.add_argument("--body-file", help="Path to markdown payload file")
    create_p.add_argument("--body", help="Inline markdown body (use --body-file for multiline/backticks)")
    create_p.add_argument("--label", action="append", dest="labels", help="Labels to apply")

    list_p = subparsers.add_parser("list", help="List all sub-issues of a parent issue")
    list_p.add_argument("parent", type=int, help="Parent issue number")

    remove_p = subparsers.add_parser("remove", help="Detach a sub-issue from its parent")
    remove_p.add_argument("parent", type=int, help="Parent issue number")
    remove_p.add_argument("child", type=int, help="Child issue number to detach")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "remove":
        cmd_remove(args)


if __name__ == "__main__":
    main()
