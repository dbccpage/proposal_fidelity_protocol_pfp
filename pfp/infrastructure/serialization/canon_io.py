"""Filesystem edge for the domain solver canonical codec.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

from omega_engine_pfp.domain.solvers.canon import loads


def load_path(path: Path) -> object:
    return loads(path.read_bytes())


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


__all__ = ["load_path", "write_bytes"]
