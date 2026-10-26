"""CemeteryEntry and TailReceipt domain Value Objects for append-only DAG logging.

Under the Symbol Game Zero Data-Loss Invariant, every refused candidate proposal,
hallucination, or typed refusal (M) is permanently committed to CemeterySink
with full raw prompt vectors, cochain projections, and cryptographic tail-truncation receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CemeteryEntry:
    """Immutable entry in the append-only CemeterySink ledger."""

    entry_index: int
    timestamp_utc: str
    turn_envelope: Mapping[str, Any]
    refusal_reason: str
    prompt_parameters: Mapping[str, Any]
    cochain_projection: Mapping[str, Any]
    prev_digest: str
    entry_digest: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError(f"AuthorityEffect must be 'None', got {self.authority_effect!r}")
        if type(self.entry_index) is not int or self.entry_index < 0:
            raise ValueError("entry_index must be a non-negative int")
        if not isinstance(self.refusal_reason, str) or not self.refusal_reason:
            raise ValueError("refusal_reason must be a non-empty string")
        if not isinstance(self.prev_digest, str):
            raise ValueError("prev_digest must be a string")
        if not isinstance(self.entry_digest, str):
            raise ValueError("entry_digest must be a string")
        if not isinstance(self.turn_envelope, (dict, Mapping)):
            raise TypeError("turn_envelope must be a Mapping")
        if not isinstance(self.prompt_parameters, (dict, Mapping)):
            raise TypeError("prompt_parameters must be a Mapping")
        if not isinstance(self.cochain_projection, (dict, Mapping)):
            raise TypeError("cochain_projection must be a Mapping")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.entry_index == other.entry_index
            and self.timestamp_utc == other.timestamp_utc
            and self.turn_envelope == other.turn_envelope
            and self.refusal_reason == other.refusal_reason
            and self.prompt_parameters == other.prompt_parameters
            and self.cochain_projection == other.cochain_projection
            and self.prev_digest == other.prev_digest
            and self.entry_digest == other.entry_digest
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.entry_index,
            self.entry_digest,
            self.prev_digest,
            self.refusal_reason,
        ))

    def to_dict(self) -> dict[str, Any]:
        """Produce deterministic dictionary for canonical JSON serialization."""
        return {
            "record_type": "ENTRY",
            "entry_index": self.entry_index,
            "timestamp_utc": self.timestamp_utc,
            "turn_envelope": dict(self.turn_envelope),
            "refusal_reason": self.refusal_reason,
            "prompt_parameters": dict(self.prompt_parameters),
            "cochain_projection": dict(self.cochain_projection),
            "prev_digest": self.prev_digest,
            "entry_digest": self.entry_digest,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class TailReceipt:
    """Cryptographic tail-truncation receipt verifying the head of the CemeterySink ledger."""

    entry_count: int
    head_digest: str
    receipt_sha256: str
    schema: str = "omega.symbol-game.cemetery-receipt.v1"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError(f"AuthorityEffect must be 'None', got {self.authority_effect!r}")
        if type(self.entry_count) is not int or self.entry_count < 0:
            raise ValueError("entry_count must be a non-negative int")
        if not isinstance(self.head_digest, str):
            raise ValueError("head_digest must be a string")
        if not isinstance(self.receipt_sha256, str):
            raise ValueError("receipt_sha256 must be a string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.entry_count == other.entry_count
            and self.head_digest == other.head_digest
            and self.receipt_sha256 == other.receipt_sha256
            and self.schema == other.schema
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((type(self), self.entry_count, self.head_digest, self.receipt_sha256))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "entry_count": self.entry_count,
            "head_digest": self.head_digest,
            "receipt_sha256": self.receipt_sha256,
            "authority_effect": self.authority_effect,
        }


__all__ = [
    "CemeteryEntry",
    "TailReceipt",
]
