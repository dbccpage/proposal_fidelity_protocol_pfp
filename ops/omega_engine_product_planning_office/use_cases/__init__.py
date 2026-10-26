"""Product-planning verification use cases.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_product_planning_office.use_cases.epic_manifest_audit import (
        audit_epic_manifest,
        rebuild_manifest,
    )

__all__ = [
    "audit_epic_manifest",
    "rebuild_manifest",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "audit_epic_manifest": (".epic_manifest_audit", "audit_epic_manifest"),
    "rebuild_manifest": (".epic_manifest_audit", "rebuild_manifest"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        module_name, attr_name = target
        module = importlib.import_module(module_name, __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals().keys(), *_LAZY_IMPORTS.keys()})
