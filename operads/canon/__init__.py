"""The operad canon: the one definition of every operad type, generated from Rust.

The values live in ``code/rust/core_operad_canon``; ``_generated.py`` and ``operad_canon.json``
are rendered from it and must not be edited by hand. Import vocabularies from here instead of
writing them out again.

AuthorityEffect: None.
"""

from __future__ import annotations

from operads.canon._generated import *  # noqa: F403
from operads.canon._generated import TYPES

__all__ = [name for name in dir() if name.isupper() or name in {"OperadColour", "DdcLetter", "HitDisposition"}]


def values_of(type_id: str) -> tuple[str, ...]:
    """The canonical values of one registered type."""
    return TYPES[type_id]["values"]  # type: ignore[return-value]
