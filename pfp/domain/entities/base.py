"""Base Domain Entity definition.

AuthorityEffect: None.
Governing standard: RULE_VO_EXACT_TYPE_EQUALITY_001, Clean Architecture DDD.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Entity:
    """Base class for all Domain Entities.

    Entities possess a unique identity (id) that distinguishes them from all other
    instances, regardless of equality of their remaining attributes.
    Equality and hashing are strictly defined by (exact_type, id).
    """

    id: Any

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
