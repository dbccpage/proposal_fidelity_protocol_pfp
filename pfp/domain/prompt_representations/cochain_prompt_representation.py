"""Simplicial Complex Cochain Prompt Representation Model.

Characteristics:
- Simplicial complex & discrete exterior calculus boundary representation.
- Maps prompt structure onto 0-simplices (vertices), 1-simplices (edges), and 2-simplices (faces).
- Carries exact rational cochains over Q to witness circulation, boundary defects, and curvature walls.
- Derived from discrete Hodge theory (Pilot 006), Bianchi identity contractions (Pilot 041),
  and simplicial cochain curvature walls (Pilot 042).

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import Field, StrictStr, model_validator

from .common import (
    MAX_SEGMENTS,
    BaseRepresentationRecord,
    Digest,
    Role,
    sha256_digest,
)

RATIONAL_REGEX = re.compile(r"^-?[0-9]+(/[1-9][0-9]*)?$")


def validate_rational(val: str, field_name: str) -> None:
    """Verifies that a value string parses as an exact rational in Q without float representation."""
    if not RATIONAL_REGEX.match(val):
        raise ValueError(f"NON_RATIONAL_VALUE in {field_name}: '{val}' is not an exact integer or fraction")
    try:
        Fraction(val)
    except Exception as exc:
        raise ValueError(f"INVALID_RATIONAL in {field_name}: '{val}'") from exc


class CochainSpanBinding(BaseRepresentationRecord):
    """Represents a prompt span bound to a geometric simplex."""

    slot: Annotated[StrictStr, Field(pattern=r"^s[0-9]+$")]
    role: Role
    simplex: StrictStr = Field(..., description="Target simplex (e.g. 'v0', 'e(v0,v1)').")
    text: StrictStr


class CochainPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the simplicial complex and cochain defect prompt representation."""

    source_id: StrictStr = Field(..., min_length=1)
    source_sha256: Digest
    proposal_sha256: Digest
    vertices: Annotated[List[StrictStr], Field(min_length=1, max_length=MAX_SEGMENTS)]
    edges: List[List[StrictStr]] = Field(default_factory=list, description="Oriented 1-simplices [u, v].")
    faces: List[List[StrictStr]] = Field(default_factory=list, description="Oriented 2-simplices [u, v, w].")
    cochain_0: Dict[StrictStr, StrictStr] = Field(
        default_factory=dict,
        description="Vertex potentials in Q.",
    )
    cochain_1: Dict[StrictStr, StrictStr] = Field(
        default_factory=dict,
        description="Edge circulation values in Q keyed by 'u->v'.",
    )
    cochain_2: Dict[StrictStr, StrictStr] = Field(
        default_factory=dict,
        description="Face curvature defect values in Q.",
    )
    spans: Annotated[List[CochainSpanBinding], Field(min_length=1, max_length=MAX_SEGMENTS)]
    representation_kind: Literal["cochain"] = "cochain"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_cochain_invariants(self) -> CochainPromptRepresentation:
        # Verify vertices are unique and non-empty
        if len(self.vertices) != len(set(self.vertices)):
            raise ValueError("DUPLICATE_VERTICES: vertex identifiers must be unique")

        vertex_set = set(self.vertices)

        # Verify edge endpoints are valid declared vertices
        for idx, edge in enumerate(self.edges):
            if len(edge) != 2:
                raise ValueError(f"MALFORMED_EDGE: edge {idx} must be a pair [u, v]")
            u, v = edge
            if u not in vertex_set or v not in vertex_set:
                raise ValueError(f"UNDECLARED_EDGE_VERTEX: edge [{u}, {v}] has undeclared vertices")
            if u == v:
                raise ValueError(f"SELF_LOOP_PROHIBITED: edge [{u}, {v}] cannot be a self-loop")

        # Verify face vertices are valid declared vertices
        for idx, face in enumerate(self.faces):
            if len(face) != 3:
                raise ValueError(f"MALFORMED_FACE: face {idx} must be a triple [u, v, w]")
            for vert in face:
                if vert not in vertex_set:
                    raise ValueError(f"UNDECLARED_FACE_VERTEX: face vertex '{vert}' is undeclared")

        # Verify all cochain values are exact rationals over Q
        for vert, val in self.cochain_0.items():
            if vert not in vertex_set:
                raise ValueError(f"UNKNOWN_COCHAIN_VERTEX: vertex '{vert}' in cochain_0 is not in vertices")
            validate_rational(val, f"cochain_0['{vert}']")

        for edge_key, val in self.cochain_1.items():
            validate_rational(val, f"cochain_1['{edge_key}']")

        for face_key, val in self.cochain_2.items():
            validate_rational(val, f"cochain_2['{face_key}']")

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

        return self

    def render(self) -> str:
        """Renders the canonical Simplicial Cochain prompt wire text."""
        v_str = ", ".join(sorted(self.vertices))
        e_str = ", ".join(f"({e[0]},{e[1]})" for e in self.edges)
        lines = [
            "-- Simplicial Complex Cochain Representation (Domain: Q)",
            f"-- Source ID: {self.source_id} | Hash: {self.source_sha256[:16]}",
            f"Simplices: V={{{v_str}}}",
        ]
        if self.edges:
            lines.append(f"Edges: E={{{e_str}}}")
        if self.faces:
            f_str = ", ".join(f"({f[0]},{f[1]},{f[2]})" for f in self.faces)
            lines.append(f"Faces: F={{{f_str}}}")

        if self.cochain_0:
            lines.append("Cochain-0 (Potentials):")
            for k in sorted(self.cochain_0.keys()):
                lines.append(f"  {k} = {self.cochain_0[k]}")

        if self.cochain_1:
            lines.append("Cochain-1 (Circulation):")
            for k in sorted(self.cochain_1.keys()):
                lines.append(f"  {k} = {self.cochain_1[k]}")

        if self.cochain_2:
            lines.append("Cochain-2 (Curvature Defect):")
            for k in sorted(self.cochain_2.keys()):
                lines.append(f"  {k} = {self.cochain_2[k]}")

        lines.append("Spans:")
        for span in self.spans:
            lines.append(f"  {span.slot} [{span.role} @ {span.simplex}]: {span.text}")

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
            "vertex_count": len(self.vertices),
            "edge_count": len(self.edges),
            "face_count": len(self.faces),
            "span_count": len(self.spans),
        }
