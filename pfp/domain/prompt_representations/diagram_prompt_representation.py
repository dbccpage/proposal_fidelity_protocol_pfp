"""Monoidal Category String Diagram Prompt Representation Model.

Characteristics:
- String diagram planar wire-and-box syntax for monoidal multicategory prompts.
- Explicitly models typed object wires (colors) and generating morphisms (boxes).
- Binds prompt spans to functional processing nodes (boxes) with declared input/output ports.
- Derived from category-theoretic multicategory operad designs and string diagram calculi.

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


class DiagramBox(BaseRepresentationRecord):
    """Represents a morphism node (box) in the string diagram."""

    box_id: Annotated[StrictStr, Field(pattern=r"^b[0-9]+$")]
    label: StrictStr = Field(..., min_length=1)
    inputs: List[StrictStr] = Field(..., description="Incoming wire IDs.")
    outputs: List[StrictStr] = Field(..., description="Outgoing wire IDs.")


class DiagramWire(BaseRepresentationRecord):
    """Represents a typed directed wire connecting diagram ports."""

    wire_id: Annotated[StrictStr, Field(pattern=r"^w[0-9]+$")]
    color: StrictStr = Field(..., min_length=1, description="Object type / color label.")
    source: StrictStr = Field(..., description="Source box ID or 'IN' boundary port.")
    target: StrictStr = Field(..., description="Target box ID or 'OUT' boundary port.")


class DiagramSpanBinding(BaseRepresentationRecord):
    """Represents a prompt span bound to a diagram box."""

    slot: Annotated[StrictStr, Field(pattern=r"^s[0-9]+$")]
    role: Role
    box_id: Annotated[StrictStr, Field(pattern=r"^b[0-9]+$")]
    text: StrictStr


class DiagramPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the monoidal string diagram prompt representation."""

    source_id: StrictStr = Field(..., min_length=1)
    source_sha256: Digest
    proposal_sha256: Digest
    colors: Annotated[List[StrictStr], Field(min_length=1, max_length=MAX_SEGMENTS)]
    boxes: Annotated[List[DiagramBox], Field(min_length=1, max_length=MAX_SEGMENTS)]
    wires: Annotated[List[DiagramWire], Field(min_length=1, max_length=MAX_SEGMENTS)]
    spans: Annotated[List[DiagramSpanBinding], Field(min_length=1, max_length=MAX_SEGMENTS)]
    representation_kind: Literal["diagram"] = "diagram"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_diagram_invariants(self) -> DiagramPromptRepresentation:
        # Verify box sequence monotonicity b0, b1, ...
        for idx, box in enumerate(self.boxes):
            expected_box = f"b{idx}"
            if box.box_id != expected_box:
                raise ValueError(
                    f"BOX_ORDER_MISMATCH: box {idx} has ID '{box.box_id}', expected '{expected_box}'"
                )

        # Verify wire sequence monotonicity w0, w1, ...
        for idx, wire in enumerate(self.wires):
            expected_wire = f"w{idx}"
            if wire.wire_id != expected_wire:
                raise ValueError(
                    f"WIRE_ORDER_MISMATCH: wire {idx} has ID '{wire.wire_id}', expected '{expected_wire}'"
                )

        # Verify slot sequence monotonicity s0, s1, ...
        for idx, span in enumerate(self.spans):
            expected_slot = f"s{idx}"
            if span.slot != expected_slot:
                raise ValueError(
                    f"SLOT_ORDER_MISMATCH: span {idx} has slot '{span.slot}', expected '{expected_slot}'"
                )

        # Verify mandatory task span
        if not any(span.role == "task" for span in self.spans):
            raise ValueError("TASK_SPAN_REQUIRED: at least one span must have role='task'")

        # Verify wire colors belong to declared colors
        declared_colors = set(self.colors)
        for wire in self.wires:
            if wire.color not in declared_colors:
                raise ValueError(
                    f"UNDECLARED_COLOR: wire '{wire.wire_id}' has undeclared color '{wire.color}'"
                )

        # Verify wire endpoints connect declared boxes or boundary ports
        valid_box_endpoints = set(b.box_id for b in self.boxes) | {"IN", "OUT"}
        for wire in self.wires:
            if wire.source not in valid_box_endpoints:
                raise ValueError(
                    f"UNKNOWN_WIRE_SOURCE: wire '{wire.wire_id}' has unknown source '{wire.source}'"
                )
            if wire.target not in valid_box_endpoints:
                raise ValueError(
                    f"UNKNOWN_WIRE_TARGET: wire '{wire.wire_id}' has unknown target '{wire.target}'"
                )

        # Verify all spans reference defined boxes
        declared_boxes = set(b.box_id for b in self.boxes)
        for span in self.spans:
            if span.box_id not in declared_boxes:
                raise ValueError(
                    f"UNKNOWN_BOX_REFERENCE: span '{span.slot}' references undeclared box '{span.box_id}'"
                )

        return self

    def render(self) -> str:
        """Renders the canonical String Diagram prompt wire text."""
        lines = [
            "-- Monoidal Category String Diagram Representation",
            f"-- Source ID: {self.source_id} | Hash: {self.source_sha256[:16]}",
            f"Colors: {', '.join(sorted(self.colors))}",
            "Wires:",
        ]
        for wire in self.wires:
            lines.append(f"  {wire.wire_id}: {wire.color} ({wire.source} -> {wire.target})")

        lines.append("Boxes:")
        for box in self.boxes:
            in_str = ", ".join(box.inputs)
            out_str = ", ".join(box.outputs)
            lines.append(f"  {box.box_id} [{box.label}]: [{in_str}] -> [{out_str}]")

        lines.append("Spans:")
        for span in self.spans:
            lines.append(f"  {span.slot} [{span.role} @ {span.box_id}]: {span.text}")

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
            "color_count": len(self.colors),
            "box_count": len(self.boxes),
            "wire_count": len(self.wires),
            "span_count": len(self.spans),
        }
