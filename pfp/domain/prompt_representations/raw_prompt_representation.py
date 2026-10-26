"""Raw Prompt Representation Model.

Characteristics:
- Baseline plain source text without role framing or structural envelope.
- Incurs 0 framing token overhead in empirical evaluations.
- Evaluated on benchmark tasks in results.md (16 trials, 93.8% validation rate, avg 86.1 input tokens).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import Field, StrictStr, model_validator

from .common import (
    MAX_PROMPT_BYTES,
    BaseRepresentationRecord,
    Digest,
    sha256_digest,
)


class RawPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the unpartitioned raw text prompt representation."""

    source_id: StrictStr = Field(
        ...,
        min_length=1,
        description="Canonical identifier of the originating task source (e.g. bench-001-primes).",
    )
    source_text: StrictStr = Field(
        ...,
        min_length=1,
        description="Raw stimulus text without envelope, markdown fences, or role annotations.",
    )
    source_sha256: Digest = Field(
        ...,
        description="Cryptographic SHA-256 digest of the UTF-8 encoded source_text.",
    )
    representation_kind: Literal["raw"] = "raw"
    standard_id: Literal["SPK-001"] = "SPK-001"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_byte_bounds_and_digest(self) -> RawPromptRepresentation:
        raw_bytes = self.source_text.encode("utf-8")
        if len(raw_bytes) > MAX_PROMPT_BYTES:
            raise ValueError(f"SOURCE_BYTE_BUDGET_EXCEEDED: {len(raw_bytes)} > {MAX_PROMPT_BYTES}")
        computed_digest = sha256_digest(raw_bytes)
        if computed_digest != self.source_sha256:
            raise ValueError(
                f"SOURCE_DIGEST_MISMATCH: declared {self.source_sha256} != computed {computed_digest}"
            )
        return self

    def render(self) -> str:
        """Renders the exact wire string presented to the model."""
        return self.source_text

    def prompt_sha256(self) -> str:
        """Returns the SHA-256 digest of the rendered wire prompt."""
        return sha256_digest(self.render())

    def to_envelope(self) -> Dict[str, Any]:
        """Serializes the prompt representation metadata envelope."""
        return {
            "source_id": self.source_id,
            "standard_id": self.standard_id,
            "representation_kind": self.representation_kind,
            "source_sha256": self.source_sha256,
            "prompt_sha256": self.prompt_sha256(),
            "authority_effect": self.authority_effect,
            "rendered_prompt": self.render(),
        }

    @classmethod
    def from_text(cls, source_id: str, source_text: str) -> RawPromptRepresentation:
        """Constructs a RawPromptRepresentation computing digests automatically."""
        computed_sha256 = sha256_digest(source_text.encode("utf-8"))
        return cls(
            source_id=source_id,
            source_text=source_text,
            source_sha256=computed_sha256,
            representation_kind="raw",
            standard_id="SPK-001",
            authority_effect="None",
        )
