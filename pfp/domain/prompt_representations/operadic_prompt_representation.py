"""Operadic Prompt Representation Model.

Characteristics:
- 3-Layer compact operad architecture:
  * Layer 0 (Environment): Algebraic ring, coordinate domain, regional boundaries.
  * Layer 1 (TreeSkeleton): Typed operator signatures and composition morphisms.
  * Layer 2 (SpanTable): Bound prompt spans, congruence ideals, and mined antibodies.
- Derived from the empirical MUB(6) and PFP multi-turn benchmark suites (Pilots 001-050).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import Field, StrictStr, model_validator

from .common import (
    MAX_SEGMENTS,
    BaseRepresentationRecord,
    Digest,
    Role,
    sha256_digest,
)


class OperadEnvironment(BaseRepresentationRecord):
    """Layer 0 Environment defining algebraic ring and spatial boundaries."""

    ring: StrictStr = Field(..., min_length=1, description="Algebraic field or ring (e.g. 'Q', 'Q[x, y]').")
    region: Optional[StrictStr] = Field(None, description="Spatial coordinate bounds (e.g. '[-3, 3] x [-3, 3]').")
    constants: Dict[StrictStr, StrictStr] = Field(default_factory=dict, description="Named invariant constants.")


class OperadTreeSkeleton(BaseRepresentationRecord):
    """Layer 1 TreeSkeleton defining typed operations and morphism signatures."""

    operations: Annotated[List[StrictStr], Field(min_length=1, max_length=MAX_SEGMENTS)]


class OperadSpanBinding(BaseRepresentationRecord):
    """Represents a bounded substring segment with assigned role and slot identifier."""

    slot: Annotated[StrictStr, Field(pattern=r"^s[0-9]+$")]
    role: Role
    text: StrictStr


class OperadSpanTable(BaseRepresentationRecord):
    """Layer 2 SpanTable containing bound spans, congruence ideals, and antibodies."""

    spans: Annotated[List[OperadSpanBinding], Field(min_length=1, max_length=MAX_SEGMENTS)]
    ideals: List[StrictStr] = Field(default_factory=list, description="Congruence ideals and safety fences.")
    antibodies: List[StrictStr] = Field(default_factory=list, description="Epistemic antibodies / trapped failure modes.")


class OperadicPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the 3-Layer compact operad prompt representation."""

    source_id: StrictStr = Field(..., min_length=1)
    source_sha256: Digest
    proposal_sha256: Digest
    environment: OperadEnvironment
    skeleton: OperadTreeSkeleton
    span_table: OperadSpanTable
    representation_kind: Literal["operadic"] = "operadic"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_operadic_invariants(self) -> OperadicPromptRepresentation:
        # Verify slot sequence monotonicity s0, s1, ...
        for idx, span in enumerate(self.span_table.spans):
            expected_slot = f"s{idx}"
            if span.slot != expected_slot:
                raise ValueError(
                    f"SLOT_ORDER_MISMATCH: span {idx} has slot '{span.slot}', expected '{expected_slot}'"
                )

        # Verify mandatory task span
        if not any(span.role == "task" for span in self.span_table.spans):
            raise ValueError("TASK_SPAN_REQUIRED: at least one span must have role='task'")

        # Verify at least one ideal or safety fence invariant is declared
        if not self.span_table.ideals:
            raise ValueError("IDEAL_REQUIRED: Layer 2 SpanTable must declare at least one congruence ideal or fence rule")

        return self

    def render(self) -> str:
        """Renders the canonical 3-Layer Operad prompt wire text."""
        lines = [
            "[TASK DESCRIPTION: 3-LAYER COMPRESSED OPERAD PROMPT]",
            "AuthorityEffect: None.",
            "Firewall: stated region only; mints no authority.",
            "",
            "Layer 0 (Environment):",
            f"Ring: {self.environment.ring}.",
        ]
        if self.environment.region:
            lines.append(f"Region: {self.environment.region}.")
        for k, v in sorted(self.environment.constants.items()):
            lines.append(f"{k}: {v}.")

        lines.extend([
            "",
            "Layer 1 (TreeSkeleton):",
        ])
        for op in self.skeleton.operations:
            lines.append(f"{op}.")

        lines.extend([
            "",
            "Layer 2 (SpanTable):",
        ])
        for span in self.span_table.spans:
            lines.append(f"{span.slot} [{span.role}]: {span.text}")

        if self.span_table.ideals:
            lines.append(f"Ideals: {', '.join(sorted(self.span_table.ideals))}.")
        if self.span_table.antibodies:
            lines.append(f"Antibodies: {', '.join(sorted(self.span_table.antibodies))}.")

        return "\n".join(lines)

    def to_canonical_metadata(self) -> Dict[str, Any]:
        """Emits metadata dictionary for audit and storage."""
        rendered = self.render()
        return {
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "proposal_sha256": self.proposal_sha256,
            "prompt_sha256": sha256_digest(rendered),
            "representation_kind": self.representation_kind,
            "authority_effect": self.authority_effect,
            "ring": self.environment.ring,
            "operation_count": len(self.skeleton.operations),
            "span_count": len(self.span_table.spans),
            "ideal_count": len(self.span_table.ideals),
            "antibody_count": len(self.span_table.antibodies),
        }
