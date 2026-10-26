"""Base Domain Aggregate Root definition.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Tuple


@dataclass
class AggregateRoot:
    """Base class for all DDD Domain Aggregate Roots.

    Aggregates maintain consistency invariants across clusters of entities and
    value objects, exposing state-modifying operations through invariant-enforcing methods.
    """

    def _fields_tuple(self) -> Tuple[Any, ...]:
        return tuple(getattr(self, f.name) for f in fields(self))
