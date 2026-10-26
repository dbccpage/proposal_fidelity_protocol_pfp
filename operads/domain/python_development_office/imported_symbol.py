#!/usr/bin/env python3
"""ImportedSymbol value object for python_development_office domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportedSymbol:
    """Immutable value object representing an imported module or symbol."""

    module: str
    name: str
    alias: str | None
    lineno: int
    is_relative: bool = False

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ImportedSymbol)
        return (
            self.module == other.module
            and self.name == other.name
            and self.alias == other.alias
            and self.lineno == other.lineno
            and self.is_relative == other.is_relative
        )

    def __hash__(self) -> int:
        return hash((type(self), self.module, self.name, self.alias, self.lineno, self.is_relative))
