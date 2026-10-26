"""Create or verify the read-only vendored clone named in PINS.json.

The clone is made from the recorded clone URL, never from, and never as a
worktree of, the author's own checkout.  Nothing here writes outside
``vendor/``.  ``--check`` only reads.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from omega_engine_operations.domain.level_engine_context import (
    current_context,
)

ROOT = current_context().runtime_root


def _git(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def load_pin(name: str = "19L57G1") -> dict[str, str]:
    pins = json.loads((current_context().governance_path("PINS.json")).read_text(encoding="utf-8"))
    entry = pins["vendored"][name]
    assert isinstance(entry, dict)
    return {str(k): str(v) for k, v in entry.items()}


def check(name: str = "19L57G1") -> list[str]:
    """Problems with the vendored clone; empty when it matches its pin."""
    pin = load_pin(name)
    path = current_context().vendor_root
    if path is None:
        raise ValueError("VENDOR_UNAVAILABLE: supply --vendor with the pinned clone")
    if not (path / ".git").exists():
        return [f"{name}: vendored clone missing at {pin['path']}"]
    out: list[str] = []
    head = _git("rev-parse", "HEAD", cwd=path)
    tree = _git("rev-parse", "HEAD^{tree}", cwd=path)
    if head != pin["commit"]:
        out.append(f"{name}: HEAD {head} != pinned {pin['commit']}")
    if tree != pin["tree"]:
        out.append(f"{name}: tree {tree} != pinned {pin['tree']}")
    dirty = _git("status", "--porcelain", "--untracked-files=no", cwd=path)
    if dirty:
        out.append(f"{name}: vendored clone has tracked modifications")
    return out


def create(name: str = "19L57G1") -> None:
    pin = load_pin(name)
    path = current_context().vendor_root
    if path is None:
        raise ValueError("VENDOR_UNAVAILABLE: supply --vendor with the pinned clone")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--no-checkout", pin["clone_url"], str(path))
        _git("config", "core.autocrlf", "false", cwd=path)
    _git("checkout", "--detach", pin["commit"], cwd=path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify only")
    args = ap.parse_args(argv)
    if not args.check:
        create()
    problems = check()
    for p in problems:
        print(f"PIN FAIL (RR-PIN): {p}")
    if not problems:
        print("PIN OK: vendor/19L57G1 at the pinned commit and tree, clean")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
