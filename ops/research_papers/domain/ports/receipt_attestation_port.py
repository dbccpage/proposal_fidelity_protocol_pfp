"""Protocol for Cryptographic Receipt Attestation and Merkle Tape Commitments."""

from __future__ import annotations

from typing import Any, Protocol, Tuple


class ReceiptAttestationPort(Protocol):
    """Protocol for cryptographic hashing, RFC 8785 serialization, and Merkle tape commitments."""

    def canonicalize_json(self, payload: Any) -> bytes:
        """Serializes payload to RFC 8785 canonical JSON bytes (ordinal key sorting, UTF-8)."""
        ...

    def compute_digest(self, data: bytes) -> str:
        """Computes content digest (Blake3 / SHA-256 hex string)."""
        ...

    def append_merkle_tape(self, tape_id: str, entry_bytes: bytes) -> Tuple[int, str]:
        """Appends entry to append-only Merkle tape, returning (entry_index, head_digest)."""
        ...

    def verify_tape_integrity(self, tape_id: str) -> bool:
        """Verifies hash chain integrity and absence of tail truncation."""
        ...
