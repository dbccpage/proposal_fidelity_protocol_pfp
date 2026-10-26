"""Injected historical file-navigation port; no host I/O or authority."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class HistoricalSourceResolver(Protocol):
    def __call__(self, repository_root: Path, original_relative: str) -> Path:
        """Return the existing byte-verified file or refuse."""
        ...
