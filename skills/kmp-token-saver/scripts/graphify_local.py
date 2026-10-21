#!/usr/bin/env python3
"""Optional code-only Graphify workflow; stdlib, no hooks or global configuration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

GRAPHIFY_VERSION = "0.9.93"


def paths(root: Path, scope: str) -> tuple[Path, Path]:
    root = root.expanduser().resolve()
    source = (root / scope).resolve()
    if not source.is_relative_to(root) or not source.is_dir():
        raise ValueError("--scope must be an existing directory within --root")
    cache_home = os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else os.environ.get("XDG_CACHE_HOME")
    cache_base = Path(cache_home).expanduser() if cache_home else Path.home() / ".cache"
    key = hashlib.sha256(str(source).encode()).hexdigest()[:16]
    cache = (cache_base / "kmp-agent-skills" / "graphify" / key).resolve()
    if cache.is_relative_to(root):
        raise ValueError("Cache location is inside the checkout; choose an external cache home")
    return source, cache


def run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, env=env, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("info", "build", "query", "explain", "export"))
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Checkout root (default: current directory)")
    parser.add_argument("--scope", default=".", help="Directory relative to root; start with one module")
    parser.add_argument("--text", help="Question or path::symbol for query/explain")
    parser.add_argument("--budget", type=int, default=1000, help="Approximate query context budget")
    args = parser.parse_args(argv)
    if args.action in ("query", "explain") and not args.text:
        parser.error("--text is required for query/explain")
    if not 100 <= args.budget <= 4000:
        parser.error("--budget must be between 100 and 4000; narrow a noisy query first")
    try:
        source, cache = paths(args.root, args.scope)
        graph = cache / "graphify-out" / "graph.json"
        if args.action == "info":
            print(json.dumps({"source": str(source), "cache": str(cache), "graph": str(graph),
                              "vault": str(cache / "obsidian"), "version": GRAPHIFY_VERSION}, indent=2))
            return 0
        executable = shutil.which("graphify")
        if not executable:
            raise ValueError(f"Install the optional CLI: uv tool install graphifyy=={GRAPHIFY_VERSION}")
        env = dict(os.environ, GRAPHIFY_BACKEND="none", GRAPHIFY_QUERY_LOG_DISABLE="1",
                   GRAPHIFY_OUT="graphify-out")
        version = subprocess.run([executable, "--version"], env=env, text=True,
                                 capture_output=True, check=True).stdout.strip()
        if version != f"graphify {GRAPHIFY_VERSION}":
            raise ValueError(f"Expected graphify {GRAPHIFY_VERSION}, got {version!r}; review upgrades explicitly")
        if args.action == "build":
            run([executable, "extract", str(source), "--code-only", "--max-workers", "2", "--out", str(cache)], env)
            run([executable, "cluster-only", str(cache)], env)
        else:
            if not graph.is_file():
                raise ValueError("No graph for this checkout/scope; run build with the same --root and --scope")
            if args.action == "query":
                run([executable, "query", args.text, "--budget", str(args.budget), "--graph", str(graph)], env)
            elif args.action == "explain":
                run([executable, "explain", args.text, "--graph", str(graph)], env)
            else:
                run([executable, "export", "obsidian", "--graph", str(graph), "--dir", str(cache / "obsidian")], env)
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"graphify-local: {exc}", file=sys.stderr)
        return exc.returncode if isinstance(exc, subprocess.CalledProcessError) else 1


if __name__ == "__main__":
    raise SystemExit(main())
