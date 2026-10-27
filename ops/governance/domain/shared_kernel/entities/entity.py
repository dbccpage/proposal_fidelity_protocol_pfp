"""Strongly-Typed Domain Entity Base.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ..value_objects.identifier import Identifier

ID = TypeVar("ID", bound=Identifier)


@dataclass(slots=True, eq=False)
class Entity(Generic[ID]):
    """Domain entity base class with identity equality (self.id == other.id)."""

    id: ID

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((self.__class__, self.id))
