"""Thin host-compatible entrypoint for capability projection compilation.

This file is copied byte-for-byte into each host's ``operad/scripts`` folder.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / ".agents").is_dir() and (
            candidate / "omega_engine_operads"
        ).is_dir():
            return candidate
    raise RuntimeError("repository root containing .agents and OEWAS was not found")


def main(argv: tuple[str, ...] | None = None) -> int:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from omega_engine_operads.infrastructure.capability_catalog_compiler import (
        _main,
    )

    mode = tuple(sys.argv[1:]) if argv is None else argv
    if not mode:
        mode = ("--write",)
    return _main(("--repo-root", str(repo_root), *mode))


if __name__ == "__main__":
    raise SystemExit(main())
