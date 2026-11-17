"""ImportedSymbol value object for python_development_office domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportedSymbol:
    module: str
    name: str
    alias: str | None
    lineno: int
    is_relative: bool = False
