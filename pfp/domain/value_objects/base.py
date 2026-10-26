"""Base Value Object definition enforcing exact-type equality.

AuthorityEffect: None.
Governing standard: RULE_VO_EXACT_TYPE_EQUALITY_001.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Tuple


@dataclass(frozen=True)
class ValueObject:
    """Base class for all domain Value Objects.

    Enforces:
    1. Immutability (frozen=True).
    2. Input validation in __post_init__.
    3. Strict exact-type equality (type(self) is type(other)).
    4. Deterministic composite hashing.
    """

    def _fields_tuple(self) -> Tuple[Any, ...]:
        return tuple(getattr(self, f.name) for f in fields(self))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, ValueObject):
            return False
        return self._fields_tuple() == other._fields_tuple()

    def __hash__(self) -> int:
        return hash((type(self), self._fields_tuple()))
