"""Command Handlers for OEWAS V3."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .compile_catalog import CompileCatalogHandler
    from .compile_licensed_term import CompileLicensedTermHandler
    from .compile_projection import CompileProjectionHandler
    from .verify_catalog import VerifyCatalogHandler

__all__ = ['CompileCatalogHandler', 'CompileLicensedTermHandler', 'CompileProjectionHandler', 'VerifyCatalogHandler']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CompileCatalogHandler': ('.compile_catalog', 'CompileCatalogHandler'),
    'CompileLicensedTermHandler': ('.compile_licensed_term', 'CompileLicensedTermHandler'),
    'CompileProjectionHandler': ('.compile_projection', 'CompileProjectionHandler'),
    'VerifyCatalogHandler': ('.verify_catalog', 'VerifyCatalogHandler'),
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
