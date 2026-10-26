"""Pydantic v2 and domain models for Packets and Sealed Envelopes.

Implements RFC 8785 canonical JSON hashing and sealed packet envelopes.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator


def canonical_json_bytes(data: Any) -> bytes:
    """RFC 8785 style canonical JSON bytes (deterministic key sorting, no whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_canonical_hex(data: Any) -> str:
    """Computes SHA-256 over canonical JSON representation."""
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


class PacketEnvelope(BaseModel):
    """Content-addressed machine-verifiable syntactic packet envelope (RFC 8785)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_id: StrictStr = Field(min_length=1)
    version: StrictStr = Field(default="2.0.0")
    task_data: Dict[str, Any]
    protected_boundary: StrictStr = Field(min_length=1)
    budget: StrictInt = Field(ge=0)
    candidate_payload: Dict[str, Any]
    witness_data: Optional[Dict[str, Any]] = None
    envelope_hash: StrictStr = Field(default="")
    authority_effect: StrictStr = Field(default="None")

    @model_validator(mode="after")
    def compute_and_verify_hash(self) -> PacketEnvelope:
        if self.authority_effect != "None":
            raise ValueError("PacketEnvelope authority_effect must be 'None'")
        d = {
            "schema_id": self.schema_id,
            "version": self.version,
            "task_data": self.task_data,
            "protected_boundary": self.protected_boundary,
            "budget": self.budget,
            "candidate_payload": self.candidate_payload,
            "witness_data": self.witness_data,
            "authority_effect": "None",
        }
        computed = sha256_canonical_hex(d)
        if not self.envelope_hash:
            object.__setattr__(self, "envelope_hash", computed)
        elif self.envelope_hash != computed:
            raise ValueError(f"Envelope hash mismatch: given {self.envelope_hash}, computed {computed}")
        return self


class PacketVerificationReceipt(BaseModel):
    """Receipt emitted after evaluating a packet envelope."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    packet_hash: StrictStr = Field(min_length=1)
    is_admissible: StrictBool
    refusal_code: Optional[StrictStr] = None
    reason: Optional[StrictStr] = None
    evaluator_id: StrictStr = Field(min_length=1)
    authority_effect: StrictStr = Field(default="None")
