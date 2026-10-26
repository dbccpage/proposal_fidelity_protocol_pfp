"""Separated operand representations in OEWAS V3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .byte_span import SourceByteSpan
from .content_digest import ContentDigest
from .identifier import ColourId, OperandId, SchemaRef


@dataclass(frozen=True, slots=True)
class InstructionOperand:
    """An explicitly declared instruction clause."""
    operand_id: OperandId
    kind: str
    instruction_body: str
    span: SourceByteSpan
    dependencies: Tuple[OperandId, ...] = ()
    emitted_observations: Tuple[str, ...] = ()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.operand_id == other.operand_id
            and self.kind == other.kind
            and self.instruction_body == other.instruction_body
            and self.span == other.span
            and self.dependencies == other.dependencies
            and self.emitted_observations == other.emitted_observations
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.operand_id,
            self.kind,
            self.instruction_body,
            self.span,
            self.dependencies,
            self.emitted_observations,
        ))


@dataclass(frozen=True, slots=True)
class ArtifactOperandRef:
    """An admitted runtime input with a receipt."""
    provenance_digest: ContentDigest
    colour_id: ColourId
    schema_ref: SchemaRef
    schema_digest: ContentDigest
    validator_digest: ContentDigest

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.provenance_digest == other.provenance_digest
            and self.colour_id == other.colour_id
            and self.schema_ref == other.schema_ref
            and self.schema_digest == other.schema_digest
            and self.validator_digest == other.validator_digest
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.provenance_digest,
            self.colour_id,
            self.schema_ref,
            self.schema_digest,
            self.validator_digest,
        ))


@dataclass(frozen=True, slots=True)
class ResidualPackageSpan:
    """The mathematical (R_in <- E -> R_out) residual object."""
    input_residual: str
    evidence_span: SourceByteSpan
    output_residual: str
    evidence_digest: Optional[ContentDigest] = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.input_residual == other.input_residual
            and self.evidence_span == other.evidence_span
            and self.output_residual == other.output_residual
            and self.evidence_digest == other.evidence_digest
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.input_residual,
            self.evidence_span,
            self.output_residual,
            self.evidence_digest,
        ))
