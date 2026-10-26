"""Shared Kernel: ObjectiveTypedV1 Value Object constructed from Shared Kernel types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .id import DemandId, ObstructionId
from .kind import Kind
from .summary import Summary


@dataclass(frozen=True, slots=True)
class ObjectiveTypedV1:
    """Structured objective declaration for a prompt turn."""

    kind: Kind
    summary: Summary
    target_obstruction_ids: tuple[ObstructionId, ...] = field(default_factory=tuple)
    target_demand_ids: tuple[DemandId, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, Kind):
            object.__setattr__(self, "kind", Kind.from_str(self.kind))
        if not isinstance(self.summary, Summary):
            object.__setattr__(self, "summary", Summary.from_str(self.summary))
        object.__setattr__(
            self,
            "target_obstruction_ids",
            tuple(sorted(set(
                x if isinstance(x, ObstructionId) else ObstructionId.from_str(x)
                for x in self.target_obstruction_ids
            ), key=lambda x: x.value)),
        )
        object.__setattr__(
            self,
            "target_demand_ids",
            tuple(sorted(set(
                x if isinstance(x, DemandId) else DemandId.from_str(x)
                for x in self.target_demand_ids
            ), key=lambda x: x.value)),
        )

    @classmethod
    def create(
        cls,
        *,
        kind: str | Kind = "prompt_turn",
        summary: str | Summary = "structured prompt turn",
        target_obstruction_ids: Sequence[str | ObstructionId] = (),
        target_demand_ids: Sequence[str | DemandId] = (),
    ) -> ObjectiveTypedV1:
        return cls(
            kind=Kind.from_str(kind),
            summary=Summary.from_str(summary),
            target_obstruction_ids=tuple(ObstructionId.from_str(x) for x in target_obstruction_ids),
            target_demand_ids=tuple(DemandId.from_str(x) for x in target_demand_ids),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": str(self.kind),
            "summary": str(self.summary),
            "target_obstruction_ids": [str(x) for x in self.target_obstruction_ids],
            "target_demand_ids": [str(x) for x in self.target_demand_ids],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ObjectiveTypedV1:
        return cls.create(
            kind=str(data.get("kind", "prompt_turn")),
            summary=str(data.get("summary", "structured prompt turn")),
            target_obstruction_ids=tuple(str(x) for x in data.get("target_obstruction_ids", ())),  # type: ignore[arg-type]
            target_demand_ids=tuple(str(x) for x in data.get("target_demand_ids", ())),  # type: ignore[arg-type]
        )
