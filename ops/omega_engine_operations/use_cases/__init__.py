"""use_cases Clean Architecture layer for oeops."""

from __future__ import annotations

import sys

_PUBLIC_IDENTITIES = (
    "omega_engine_operations.use_cases",
    "use_cases",
    "omega_engine.omega_engine_operations.use_cases",
)

if __name__ in _PUBLIC_IDENTITIES:
    _this_module = sys.modules[__name__]
    for _public_identity in _PUBLIC_IDENTITIES:
        _existing_module = sys.modules.get(_public_identity)
        if (
            _existing_module is not None
            and _existing_module is not _this_module
            and getattr(_existing_module, "__file__", None)
            != getattr(_this_module, "__file__", None)
        ):
            raise RuntimeError("OPERATIONS_USE_CASES_IDENTITY_CONFLICT")
        sys.modules[_public_identity] = _this_module


def __getattr__(name: str) -> object:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
