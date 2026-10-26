"""Shared Kernel: Obstruction Value Objects, families, and declared hints."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Mapping, Self

from ..exceptions import InvariantViolationError
from .description import Description
from .id import ObstructionId
from .kind import Kind


class ObstructionFamilyKind(str, Enum):
    """Registered canonical obstruction families."""

    CONTINUUM_FROM_FINITE = "continuum_from_finite"
    SYNTHETIC_CURVE = "synthetic_curve"
    LEAN_TOY_AS_MECHANIZED = "lean_toy_as_mechanized"
    COVERAGE_AS_PROOF = "coverage_as_proof"
    DUAL_WITNESS_MISSING = "dual_witness_missing"
    CLAIM_EVALUATOR_REQUIRED = "claim_evaluator_required"
    ONTOLOGY_SMUGGLING = "ontology_smuggling"
    PROPOSAL_EXECUTION_COLLAPSE = "proposal_execution_collapse"
    RECEIPT_WITHOUT_REPLAY = "receipt_without_replay"
    AUTHORITY_PROMOTION = "authority_promotion"
    UNDECIDABLE_TREATED_AS_EQUAL = "undecidable_treated_as_equal"
    OPAQUE_WHOLE_DECOMPOSED = "opaque_whole_decomposed"
    CUSTOM_OPEN = "custom_open"


@dataclass(frozen=True, slots=True)
class ObstructionFamily(Kind):
    """Obstruction taxonomic family Value Object (subtyping Kind)."""

    VALID_FAMILIES: ClassVar[frozenset[str]] = frozenset(
        f.value for f in ObstructionFamilyKind
    )

    @classmethod
    def from_str(cls: type[Self], val: str | Self | ObstructionFamilyKind) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, ObstructionFamilyKind):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str or ObstructionFamilyKind, got {type(val).__name__}"
            )
        return cls(val)


@dataclass(frozen=True, slots=True)
class ObstructionHintV1:
    """Declared obstruction with strongly-typed ID, family, and description."""

    obstruction_id: ObstructionId
    family: ObstructionFamily
    description: Description

    def __post_init__(self) -> None:
        if not isinstance(self.obstruction_id, ObstructionId):
            object.__setattr__(self, "obstruction_id", ObstructionId.from_str(self.obstruction_id))
        if not isinstance(self.family, ObstructionFamily):
            object.__setattr__(self, "family", ObstructionFamily.from_str(self.family))
        if not isinstance(self.description, Description):
            object.__setattr__(self, "description", Description.from_str(self.description))

    @classmethod
    def create(
        cls,
        *,
        obstruction_id: str | ObstructionId,
        family: str | ObstructionFamily,
        description: str | Description = "Declared obstruction",
    ) -> ObstructionHintV1:
        return cls(
            obstruction_id=ObstructionId.from_str(obstruction_id),
            family=ObstructionFamily.from_str(family),
            description=Description.from_str(description),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "obstruction_id": str(self.obstruction_id),
            "family": str(self.family),
            "description": str(self.description),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ObstructionHintV1:
        return cls.create(
            obstruction_id=str(data["obstruction_id"]),
            family=str(data["family"]),
            description=str(data.get("description", "Declared obstruction")),
        )
