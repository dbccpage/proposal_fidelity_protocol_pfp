"""E-Graph Normal Form Prompt Representation Model.

Characteristics:
- Equational saturation representation with normal form levels (0NF through 6NF, ENF).
- Groups equivalent syntactic and semantic expressions into disjoint e-classes.
- Binds prompt spans to target e-classes while certifying constraint preservation.
- Derived from Mode 13 confluent relational chase and Gate 03 equational saturation.

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

NormalFormLevel = Literal["0NF", "1NF", "2NF", "3NF", "4NF", "5NF", "6NF", "ENF"]


class EgraphSpanBinding(BaseRepresentationRecord):
    """Represents a prompt span bound to an e-graph equivalence class."""

    slot: Annotated[StrictStr, Field(pattern=r"^s[0-9]+$")]
    role: Role
    eclass_id: Annotated[StrictStr, Field(pattern=r"^e[0-9]+$")]
    text: StrictStr


class EgraphPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the e-graph equational saturation prompt representation."""

    source_id: StrictStr = Field(..., min_length=1)
    source_sha256: Digest
    proposal_sha256: Digest
    normal_form_level: NormalFormLevel = "ENF"
    eclasses: Dict[StrictStr, List[StrictStr]] = Field(
        ...,
        description="Mapping of e-class identifiers (e0, e1, ...) to equivalent term representations.",
    )
    rewrite_rules: List[StrictStr] = Field(
        default_factory=list,
        description="Equational rewrite rules applied during saturation.",
    )
    spans: Annotated[List[EgraphSpanBinding], Field(min_length=1, max_length=MAX_SEGMENTS)]
    representation_kind: Literal["egraph"] = "egraph"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_egraph_invariants(self) -> EgraphPromptRepresentation:
        # Verify e-class format and non-emptiness
        if not self.eclasses:
            raise ValueError("EMPTY_ECLASSES: at least one e-class must be defined")
        for eid, terms in self.eclasses.items():
            if not eid.startswith("e") or not eid[1:].isdigit():
                raise ValueError(f"MALFORMED_ECLASS_ID: '{eid}' must match pattern '^e[0-9]+$'")
            if not terms:
                raise ValueError(f"EMPTY_ECLASS_TERMS: e-class '{eid}' has no equivalent terms")

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

        # Verify all spans reference defined e-classes
        declared_eclasses = set(self.eclasses.keys())
        for span in self.spans:
            if span.eclass_id not in declared_eclasses:
                raise ValueError(
                    f"UNKNOWN_ECLASS_REFERENCE: span '{span.slot}' references undeclared e-class '{span.eclass_id}'"
                )

        return self

    def render(self) -> str:
        """Renders the canonical E-Graph prompt wire text."""
        lines = [
            f"-- E-Graph Saturated Normal Form (level: {self.normal_form_level})",
            f"-- Source ID: {self.source_id} | Hash: {self.source_sha256[:16]}",
            "-- E-Classes:",
        ]
        for eid in sorted(self.eclasses.keys(), key=lambda x: int(x[1:])):
            terms = ", ".join(f'"{t}"' for t in self.eclasses[eid])
            lines.append(f"  {eid} := {{{terms}}}")

        lines.append("-- Bound Spans:")
        for span in self.spans:
            lines.append(f"  {span.slot} [{span.role} -> {span.eclass_id}]: {span.text}")

        if self.rewrite_rules:
            lines.append("-- Saturated Rewrite Rules:")
            for rule in sorted(self.rewrite_rules):
                lines.append(f"  {rule}")

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
            "normal_form_level": self.normal_form_level,
            "eclass_count": len(self.eclasses),
            "span_count": len(self.spans),
            "rewrite_rule_count": len(self.rewrite_rules),
        }
