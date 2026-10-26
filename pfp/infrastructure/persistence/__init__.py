"""Persistence infrastructure modules."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .file_context import SymbolGameDbContext
    from .memory_context import InMemoryDbContext
    from .repositories import FilePromptRepository, MemoryPromptRepository, MemoryTurnRepository

__all__ = ['FilePromptRepository', 'InMemoryDbContext', 'MemoryPromptRepository', 'MemoryTurnRepository', 'SymbolGameDbContext']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'SymbolGameDbContext': ('.file_context', 'SymbolGameDbContext'),
    'InMemoryDbContext': ('.memory_context', 'InMemoryDbContext'),
    'FilePromptRepository': ('.repositories', 'FilePromptRepository'),
    'MemoryPromptRepository': ('.repositories', 'MemoryPromptRepository'),
    'MemoryTurnRepository': ('.repositories', 'MemoryTurnRepository'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
