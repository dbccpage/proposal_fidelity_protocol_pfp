"""Minimal typed error channel used by the QA receipt refusals.

The original package returned refusals through a shared railway-style
Result type. This demo carries only the Err half it needs, with the same
is_ok / is_err properties and unwrap_err() accessor.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

E = TypeVar("E")


@dataclass(frozen=True)
class Err(Generic[E]):
    """A failed result that carries a typed error value."""

    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True

    def unwrap_err(self) -> E:
        return self.error
