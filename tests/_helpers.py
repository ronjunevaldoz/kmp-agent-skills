from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _find_bash() -> str:
    """The bash that runs this repo's shell scripts.

    On Windows a bare "bash" resolves to WSL's launcher in System32 before PATH is searched,
    which runs scripts in a Linux distro that can't see these paths. Use Git for Windows' bash.
    """
    if os.name != "nt":
        return "bash"
    git = shutil.which("git")
    for parent in Path(git).resolve().parents if git else ():
        candidate = parent / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return shutil.which("bash") or "bash"


BASH = _find_bash()


def bash_path(path: Path) -> str:
    """`path` the way bash sees it: C:/x → /c/x under Git Bash on Windows, unchanged elsewhere."""
    text = path.as_posix()
    if os.name == "nt" and text[1:2] == ":":
        text = "/" + text[0].lower() + text[2:]
    return text


def minimal_path() -> str:
    """A bare POSIX PATH for scripts under test, plus the running Python's directory
    (Git Bash on Windows keeps no Python in /usr/bin)."""
    return f"/usr/bin:/bin:{bash_path(Path(sys.executable).parent)}"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def load_module_registered(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module   # register BEFORE exec so @dataclass can resolve __module__
    spec.loader.exec_module(module)
    return module
