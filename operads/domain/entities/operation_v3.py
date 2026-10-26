"""OperationV3 Entity in OEWAS V3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..value_objects.authority import AUTHORITY_RANK, AuthorityEffect
from ..value_objects.content_digest import ContentDigest
from ..value_objects.identifier import ColourId, OperandId, OperationId, SchemaRef
from ..value_objects.lifecycle_facets import SkillLifecycleV3


@dataclass(frozen=True, slots=True)
class PortSpecV3:
    name: str
    colour_id: ColourId
    schema_ref: SchemaRef
    schema_digest: ContentDigest
    validator_ref: str
    validator_digest: ContentDigest

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.name == other.name
            and self.colour_id == other.colour_id
            and self.schema_ref == other.schema_ref
            and self.schema_digest == other.schema_digest
            and self.validator_ref == other.validator_ref
            and self.validator_digest == other.validator_digest
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.name,
            self.colour_id,
            self.schema_ref,
            self.schema_digest,
            self.validator_ref,
            self.validator_digest,
        ))


@dataclass(frozen=True, slots=True)
class OperationV3:
    operation_id: OperationId
    inputs: Tuple[PortSpecV3, ...]
    output: PortSpecV3
    operand_refs: Tuple[OperandId, ...]
    lifecycle: SkillLifecycleV3
    residual_status: str
    effects: Tuple[str, ...] = ()
    tool_refs: Tuple[str, ...] = ()
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    authority_ceiling: AuthorityEffect = AuthorityEffect.NONE
    invocation_grade: str = "entry"
    description: str = ""
    replacement_operation_id: OperationId | None = None

    def __post_init__(self) -> None:
        if self.replacement_operation_id is not None and (
            self.lifecycle.admission.value != "Retired"
            or self.replacement_operation_id == self.operation_id
        ):
            raise ValueError("only a retired operation may name a distinct replacement")
        if AUTHORITY_RANK[self.authority_effect] > AUTHORITY_RANK[self.authority_ceiling]:
            raise ValueError(
                f"operation effect {self.authority_effect.value} exceeds ceiling {self.authority_ceiling.value}"
            )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.operation_id == other.operation_id
            and self.inputs == other.inputs
            and self.output == other.output
            and self.operand_refs == other.operand_refs
            and self.lifecycle == other.lifecycle
            and self.residual_status == other.residual_status
            and self.effects == other.effects
            and self.tool_refs == other.tool_refs
            and self.authority_effect == other.authority_effect
            and self.authority_ceiling == other.authority_ceiling
            and self.invocation_grade == other.invocation_grade
            and self.replacement_operation_id == other.replacement_operation_id
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.operation_id,
            self.inputs,
            self.output,
            self.operand_refs,
            self.lifecycle,
            self.residual_status,
            self.effects,
            self.tool_refs,
            self.authority_effect,
            self.authority_ceiling,
            self.invocation_grade,
            self.replacement_operation_id,
        ))
