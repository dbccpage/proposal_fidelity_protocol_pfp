"""Read-only intelligence source adapters and native policy composition."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .miner import IntelligenceMiner
    from .native import NativeMetabolismKernel
    from .sources import SOURCE_REGISTRY, DataSourceAdapter

__all__ = ['DataSourceAdapter', 'IntelligenceMiner', 'NativeMetabolismKernel', 'SOURCE_REGISTRY']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'IntelligenceMiner': ('.miner', 'IntelligenceMiner'),
    'NativeMetabolismKernel': ('.native', 'NativeMetabolismKernel'),
    'SOURCE_REGISTRY': ('.sources', 'SOURCE_REGISTRY'),
    'DataSourceAdapter': ('.sources', 'DataSourceAdapter'),
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
