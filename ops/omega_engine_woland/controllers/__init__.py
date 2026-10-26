"""Controllers and presentation adapters for the Woland Swarm.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib

__all__ = ["WolandBoutController", "WolandSwarmController"]

_EXPORTS = {
    "WolandBoutController": (".woland_bout_controller", "WolandBoutController"),
    "WolandSwarmController": (".woland_controller", "WolandSwarmController"),
}


def __getattr__(name):
    if name in _EXPORTS:
        module_name, attribute = _EXPORTS[name]
        value = getattr(importlib.import_module(module_name, __name__), attribute)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_EXPORTS))
