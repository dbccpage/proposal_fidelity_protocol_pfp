"""Exact finite belief games and independently replayed certificates."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .checker import check_certificate
    from .model import Arena, ModelError, compile_model, digest
    from .producer import solve_progress

__all__ = ['Arena', 'ModelError', 'check_certificate', 'compile_model', 'digest', 'solve_progress']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'check_certificate': ('.checker', 'check_certificate'),
    'Arena': ('.model', 'Arena'),
    'ModelError': ('.model', 'ModelError'),
    'compile_model': ('.model', 'compile_model'),
    'digest': ('.model', 'digest'),
    'solve_progress': ('.producer', 'solve_progress'),
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
