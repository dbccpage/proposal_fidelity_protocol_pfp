"""ModuleInfo domain entity for python_development_office."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from python_development_office.domain.imported_symbol import (
    ImportedSymbol,
)


@dataclass
class ModuleInfo:
    path: Path
    package: str
    layer: str | None = None
    imports: set[str] = field(default_factory=set)
    imported_symbols: list[ImportedSymbol] = field(default_factory=list)
    imported_by: set[str] = field(default_factory=set)
    class_names: set[str] = field(default_factory=set)
    function_names: set[str] = field(default_factory=set)
    loc: int = 0
    is_test: bool = False
