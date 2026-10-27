#!/usr/bin/env python3
"""Thin skill wrapper for review/approval/packetization verbs."""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    for candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (candidate / ".agents").is_dir() and (candidate / "engine").is_dir():
            return candidate
    raise RuntimeError("repository root not found")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {
        "approve",
        "packetize",
        "review",
        "validate-registry",
    }:
        raise SystemExit("core-prompt permits: review, approve, packetize, validate-registry")
    root = _repo_root()
    sys.path.insert(0, str(root))
    from engine.crates.prompt_civilization.cli import main as runtime_main

    return runtime_main()


if __name__ == "__main__":
    raise SystemExit(main())
