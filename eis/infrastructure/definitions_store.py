"""Read OEEIS definition files. The domain receives the text."""

from __future__ import annotations

import os
from pathlib import Path


def definitions_dir() -> Path:
    """OEEIS-owned definition source, or an explicit operator override."""
    override = os.environ.get("OEEIS_DEFINITIONS_DIR")
    if override:
        return Path(override)
    current = Path(__file__).resolve().parent
    repo = Path(__file__).resolve().parents[2]
    for parent in [current] + list(current.parents):
        if (parent / ".agents").is_dir() or (parent / ".git").is_dir():
            repo = parent
            break
    canonical = repo / "omega_engine_epistemic_immune_system" / "antibodies" / "definitions"
    return canonical


def read_definition(filename: str) -> str | None:
    """UTF-8 text of one definition file, or None when it is not a file."""
    path = definitions_dir() / filename
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


__all__ = ["definitions_dir", "read_definition"]
