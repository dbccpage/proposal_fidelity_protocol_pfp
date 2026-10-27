"""
packet_codec.py
===============

Unified Immutable Packet Codec and Sealing Kernel for Symbol Game envelopes.

AuthorityEffect: None. Finite cryptographic and deterministic verification only.
"""

from __future__ import annotations

import copy
import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Any, ClassVar, Mapping, Tuple

from .exceptions import SymbolGameValidationError
from .shared_kernel.canonical import canonical_bytes


def _normalize_unicode(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        normalized: dict[Any, Any] = {}
        for key, item in value.items():
            normalized_key = _normalize_unicode(key)
            if normalized_key in normalized:
                raise SymbolGameValidationError(
                    "unicode normalization collapses two keys to "
                    f"{normalized_key!r}"
                )
            normalized[normalized_key] = _normalize_unicode(item)
        return normalized
    if isinstance(value, list):
        return [_normalize_unicode(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_unicode(item) for item in value)
    return value


def canonical_json_bytes(obj: Any) -> bytes:
    """Digest bytes from the domain canonical encoder.

    Unknown objects are refused. These are tagged canonical bytes, not RFC 8785.
    """
    return canonical_bytes(_normalize_unicode(obj))


def compute_sha256(data: bytes | str) -> str:
    """Computes pure SHA-256 hex digest."""
    b = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True, slots=True)
class PacketCodec:
    """Deep codec value object for sealing and verifying symbol game envelopes."""

    SCHEMA_VERSION: ClassVar[str] = "2.0.0"
    schema_version: str = "2.0.0"

    @classmethod
    def seal(
        cls,
        payload: Mapping[str, Any],
        packet_family: str,
        *,
        payload_schema: str | None = None,
        parent_id: str | None = None,
        carrier_id: str | None = None,
    ) -> dict[str, Any]:
        """Seals an arbitrary payload dictionary into a deterministic PacketEnvelopeV2 record."""
        payload_bytes = canonical_json_bytes(payload)
        payload_sha256 = compute_sha256(payload_bytes)

        envelope_data: dict[str, Any] = {
            "schema_version": cls.SCHEMA_VERSION,
            "packet_family": packet_family,
            "payload_schema": payload_schema or f"core.symbol-game.{packet_family}.v1",
            "payload_sha256": payload_sha256,
            "payload": copy.deepcopy(payload),
            "authority_effect": "None",
        }
        if parent_id is not None:
            envelope_data["parent_id"] = parent_id
        if carrier_id is not None:
            envelope_data["carrier_id"] = carrier_id

        envelope_bytes = canonical_json_bytes(envelope_data)
        envelope_data["envelope_sha256"] = compute_sha256(envelope_bytes)
        return envelope_data

    @classmethod
    def verify(cls, envelope: Mapping[str, Any]) -> Tuple[bool, str, str]:
        """Verifies envelope integrity, payload hash bijection, and authority invariants.

        Returns (is_valid, computed_payload_sha256, detail_message).
        """
        if "payload" not in envelope or "payload_sha256" not in envelope:
            raise SymbolGameValidationError(
                "Envelope missing required 'payload' or 'payload_sha256' fields"
            )

        payload = envelope["payload"]
        declared_sha = envelope["payload_sha256"]
        actual_bytes = canonical_json_bytes(payload)
        actual_sha = compute_sha256(actual_bytes)

        if declared_sha != actual_sha:
            return (
                False,
                actual_sha,
                f"Payload SHA-256 mismatch: declared={declared_sha}, actual={actual_sha}",
            )

        authority = envelope.get("authority_effect", "None")
        if authority != "None":
            return (
                False,
                actual_sha,
                f"Prohibited authority effect: {authority} (must be 'None')",
            )

        declared_envelope_sha = envelope.get("envelope_sha256")
        unsigned = {
            key: value for key, value in envelope.items() if key != "envelope_sha256"
        }
        recomputed_envelope_sha = compute_sha256(canonical_json_bytes(unsigned))
        if declared_envelope_sha != recomputed_envelope_sha:
            return (
                False,
                actual_sha,
                "Envelope SHA-256 mismatch: "
                f"declared={declared_envelope_sha}, actual={recomputed_envelope_sha}",
            )

        return (True, actual_sha, "OK")
