"""Governance corpus digest and hash-checked apply. AuthorityEffect: None."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from .apply_proposals import apply_proposals
from .digest_corpus import digest_corpus

if TYPE_CHECKING:
    from .lesson import lesson_status
    from .receipt_path import receipt_destination_allowed

__all__ = ['apply_proposals', 'digest_corpus', 'lesson_status', 'receipt_destination_allowed']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'lesson_status': ('.lesson', 'lesson_status'),
    'receipt_destination_allowed': ('.receipt_path', 'receipt_destination_allowed'),
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
