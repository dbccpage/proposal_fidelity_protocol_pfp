"""Shared Kernel: Declared demand item Value Object constructed from Shared Kernel types.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .description import Description
from .id import DemandId, ObstructionId


@dataclass(frozen=True, slots=True)
class DemandItemV1:
    """Declared demand item with strongly-typed ID, description, and target obstruction ID."""

    demand_id: DemandId
    description: Description
    target_obstruction_id: ObstructionId

    def __post_init__(self) -> None:
        if not isinstance(self.demand_id, DemandId):
            object.__setattr__(self, "demand_id", DemandId.from_str(self.demand_id))
        if not isinstance(self.description, Description):
            object.__setattr__(self, "description", Description.from_str(self.description))
        if not isinstance(self.target_obstruction_id, ObstructionId):
            object.__setattr__(self, "target_obstruction_id", ObstructionId.from_str(self.target_obstruction_id))

    @classmethod
    def create(
        cls,
        *,
        demand_id: str | DemandId,
        description: str | Description,
        target_obstruction_id: str | ObstructionId,
    ) -> DemandItemV1:
        return cls(
            demand_id=DemandId.from_str(demand_id),
            description=Description.from_str(description),
            target_obstruction_id=ObstructionId.from_str(target_obstruction_id),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "demand_id": str(self.demand_id),
            "description": str(self.description),
            "target_obstruction_id": str(self.target_obstruction_id),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DemandItemV1:
        return cls.create(
            demand_id=str(data["demand_id"]),
            description=str(data.get("description", "Declared demand")),
            target_obstruction_id=str(data["target_obstruction_id"]),
        )
