"""Structured Prompt Representation Model.

Characteristics:
- Canonical JSON segment partition with explicit role/slot boundaries.
- Emits RFC 8785 canonical JSON containing "segments" and "source".
- Evaluated on benchmark tasks in results.md (16 trials, 75.0% validation rate, avg 186.9 input tokens, +100.8 tok overhead).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import Field, StrictInt, StrictStr, model_validator

from .common import (
    MAX_PROMPT_BYTES,
    MAX_SEGMENTS,
    BaseRepresentationRecord,
    Digest,
    Role,
    canonical_json_str,
    sha256_digest,
)


class StructuredSegmentBinding(BaseRepresentationRecord):
    """Represents a bounded substring segment with assigned role and slot identifier."""

    slot: Annotated[StrictStr, Field(pattern=r"^s[0-9]+$")]
    role: Role
    text: StrictStr
    start_byte: Optional[Annotated[StrictInt, Field(ge=0)]] = None
    end_byte: Optional[Annotated[StrictInt, Field(gt=0)]] = None

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Emits canonical dict for wire payload serialization."""
        return {
            "role": self.role,
            "slot": self.slot,
            "text": self.text,
        }


class StructuredPayload(BaseRepresentationRecord):
    """The inner JSON structure presented as the wire prompt."""

    source: StrictStr = Field(..., min_length=1)
    segments: Annotated[List[StructuredSegmentBinding], Field(min_length=1, max_length=MAX_SEGMENTS)]

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Emits ordered dictionary matching canonical trials in pilot_output."""
        return {
            "segments": [seg.to_canonical_dict() for seg in self.segments],
            "source": self.source,
        }


class StructuredPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the structured JSON segment prompt representation."""

    source_id: StrictStr = Field(..., min_length=1)
    source_sha256: Digest
    proposal_sha256: Digest
    payload: StructuredPayload
    representation_kind: Literal["structured"] = "structured"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_structure_and_coverage(self) -> StructuredPromptRepresentation:
        source_bytes = self.payload.source.encode("utf-8")
        if len(source_bytes) > MAX_PROMPT_BYTES:
            raise ValueError(f"SOURCE_BYTE_BUDGET_EXCEEDED: {len(source_bytes)} > {MAX_PROMPT_BYTES}")

        computed_source_digest = sha256_digest(source_bytes)
        if computed_source_digest != self.source_sha256:
            raise ValueError(
                f"SOURCE_DIGEST_MISMATCH: declared {self.source_sha256} != computed {computed_source_digest}"
            )

        # Ensure slots are ordered s0, s1, ...
        for idx, seg in enumerate(self.payload.segments):
            expected_slot = f"s{idx}"
            if seg.slot != expected_slot:
                raise ValueError(f"SLOT_ORDER_MISMATCH: segment {idx} has slot '{seg.slot}', expected '{expected_slot}'")

        # Verify task segment presence
        if not any(seg.role == "task" for seg in self.payload.segments):
            raise ValueError("TASK_SEGMENT_REQUIRED: at least one segment must have role='task'")

        # Verify byte span bounds if declared
        if any(seg.start_byte is not None for seg in self.payload.segments):
            curr_pos = 0
            for idx, seg in enumerate(self.payload.segments):
                if seg.start_byte is None or seg.end_byte is None:
                    raise ValueError(f"INCONSISTENT_SPAN_DECLARATION: segment {idx} missing start/end bytes")
                if seg.start_byte != curr_pos or seg.end_byte <= seg.start_byte or seg.end_byte > len(source_bytes):
                    raise ValueError(
                        f"SPAN_GAP_OR_OVERLAP: segment {idx} span [{seg.start_byte}, {seg.end_byte}] invalid at pos {curr_pos}"
                    )
                curr_pos = seg.end_byte
            if curr_pos != len(source_bytes):
                raise ValueError("INCOMPLETE_SPAN_PARTITION: spans do not cover full source byte range")

        return self

    def render(self) -> str:
        """Renders the RFC 8785 canonical JSON prompt wire string."""
        return canonical_json_str(self.payload.to_canonical_dict())

    def prompt_sha256(self) -> str:
        """Returns the SHA-256 digest of the rendered structured wire prompt."""
        return sha256_digest(self.render())

    def to_envelope(self) -> Dict[str, Any]:
        """Serializes the prompt representation metadata envelope."""
        return {
            "source_id": self.source_id,
            "representation_kind": self.representation_kind,
            "source_sha256": self.source_sha256,
            "proposal_sha256": self.proposal_sha256,
            "prompt_sha256": self.prompt_sha256(),
            "authority_effect": self.authority_effect,
            "segment_count": len(self.payload.segments),
            "rendered_prompt": self.render(),
        }

    @classmethod
    def from_source_and_segments(
        cls,
        source_id: str,
        source_text: str,
        proposal_sha256: str,
        segments: List[StructuredSegmentBinding],
    ) -> StructuredPromptRepresentation:
        """Convenience builder computing source digest automatically."""
        source_sha = sha256_digest(source_text.encode("utf-8"))
        payload = StructuredPayload(source=source_text, segments=segments)
        return cls(
            source_id=source_id,
            source_sha256=source_sha,
            proposal_sha256=proposal_sha256,
            payload=payload,
            representation_kind="structured",
            authority_effect="None",
        )
