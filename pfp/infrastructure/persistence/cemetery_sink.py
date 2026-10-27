"""CemeterySink: Append-only JSON-L DAG persistence with cryptographic tail-truncation receipts.

Under the Symbol Game Zero Data-Loss Invariant, every refused candidate proposal,
hallucination, or typed refusal (M) is permanently committed to CemeterySink
with full raw prompt vectors, cochain projections, and cryptographic tail-truncation receipts.

Records are written in a sorted-key compact JSON profile (UTF-8, no
whitespace, ``ensure_ascii=False``). This profile is not RFC 8785 (JCS): it
does not implement the JCS number serialization or its UTF-16 key ordering.
Digested payloads contain no binary floating-point numbers and no NaN or
infinity; a float supplied to ``record_refusal`` is kept exactly as the tagged
string ``{"$float_hex": float.hex()}``.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from pfp.domain.entities.cemetery_entry import CemeteryEntry, TailReceipt
from pfp.domain.exceptions import (
    CanonicalizationError,
    LedgerIntegrityError,
    LedgerTruncationError,
)
from pfp.domain.ports.ports import CemeterySinkPort

HEADER_SCHEMA = "core.symbol-game.cemetery-sink.v1"
RECEIPT_SCHEMA = "core.symbol-game.cemetery-receipt.v1"
GENESIS_DIGEST = "genesis"
FLOAT_TAG = "$float_hex"

ALLOWED_ENTRY_KEYS = frozenset({
    "authority_effect",
    "cochain_projection",
    "entry_digest",
    "entry_index",
    "prev_digest",
    "prompt_parameters",
    "record_type",
    "refusal_reason",
    "timestamp_utc",
    "turn_envelope",
})


def _sanitize_for_cemetery(obj: Any) -> Any:
    """Recursively convert Fraction and Q into canonical string representations.

    A float (including NaN and the infinities) becomes ``{"$float_hex": x.hex()}``:
    the refused turn is still recorded, bit for bit, but no binary float
    enters a digested payload.
    """
    if isinstance(obj, Fraction):
        return f"{obj.numerator}/{obj.denominator}"
    if isinstance(obj, float):
        return {FLOAT_TAG: float(obj).hex()}
    if type(obj).__name__ == "Q" or hasattr(obj, "to_canonical_wire"):
        return str(obj)
    if isinstance(obj, Mapping):
        return {str(k): _sanitize_for_cemetery(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_cemetery(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted([_sanitize_for_cemetery(v) for v in obj], key=lambda x: str(x))
    return obj


def _refuse_floats(obj: Any, where: str = "$") -> None:
    """Raise if a binary float appears anywhere in a payload that will be digested."""
    if isinstance(obj, float):
        raise CanonicalizationError(
            f"float {obj!r} at {where} is not admitted in a digested cemetery payload"
        )
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            _refuse_floats(value, f"{where}.{key}")
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            _refuse_floats(value, f"{where}[{index}]")


def _canonical_json_bytes(obj: Any) -> bytes:
    """Encode an object in the sorted-key compact JSON profile, as UTF-8 bytes.

    Keys are sorted, separators carry no whitespace, and non-ASCII text is kept
    as UTF-8. This is not RFC 8785 (JCS). Floats, NaN and the infinities are
    refused with ``CanonicalizationError`` rather than written as JSON numbers.
    """
    _refuse_floats(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _reject_json_constant(token: str) -> Any:
    raise LedgerIntegrityError(f"non-finite JSON constant {token} in ledger file")


def _sha256_hex(data: bytes) -> str:
    """Compute standard hex SHA-256 digest over byte payload."""
    return hashlib.sha256(data).hexdigest()


class CemeterySink(CemeterySinkPort):
    """Append-only JSON-L DAG persistence sink implementing CemeterySinkPort.

    Features:
    1. Sorted-key compact JSON serialization (not RFC 8785), with floats refused.
    2. Explicit Head Record Binding (Line 0 Header).
    3. Cryptographic SHA-256 hash-chaining across all entries.
    4. Bit-flip and interior tamper detection.
    5. Multi-session cold-restart tail-truncation detection (raises LedgerTruncationError).
    6. Cryptographic tail-truncation receipt emission.
    """

    def __init__(self, file_path: str | Path, *, auto_init: bool = True) -> None:
        self.file_path = Path(file_path).resolve()
        self._entries: list[CemeteryEntry] = []
        self._tail_digest: str = GENESIS_DIGEST
        self._genesis_timestamp: str = datetime.now(timezone.utc).isoformat()

        if self.file_path.exists():
            self._load_and_verify()
        elif auto_init:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_file()

    def _entry_payload(
        self,
        *,
        entry_index: int,
        timestamp_utc: str,
        turn_envelope: Mapping[str, Any],
        refusal_reason: str,
        prompt_parameters: Mapping[str, Any],
        cochain_projection: Mapping[str, Any],
        prev_digest: str,
        authority_effect: str = "None",
    ) -> dict[str, Any]:
        """Compute the deterministic dictionary payload for an entry without entry_digest."""
        return {
            "authority_effect": authority_effect,
            "cochain_projection": dict(cochain_projection),
            "entry_index": entry_index,
            "prev_digest": prev_digest,
            "prompt_parameters": dict(prompt_parameters),
            "record_type": "ENTRY",
            "refusal_reason": refusal_reason,
            "timestamp_utc": timestamp_utc,
            "turn_envelope": dict(turn_envelope),
        }

    def _load_and_verify(self) -> None:
        """Parse disk file and cryptographically verify all header and entry records."""
        content_bytes = self.file_path.read_bytes()
        if content_bytes.startswith(b"\xef\xbb\xbf"):
            raise LedgerIntegrityError("BOM detected in ledger file: must be pure UTF-8 without BOM")

        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LedgerIntegrityError("Corrupt UTF-8 encoding in ledger file") from exc

        if not text.strip():
            raise LedgerTruncationError("Empty ledger file; missing required HEADER record")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise LedgerTruncationError("No valid lines found in ledger file")

        # Line 0: HEADER
        try:
            header = json.loads(lines[0], parse_constant=_reject_json_constant)
        except Exception as exc:
            raise LedgerIntegrityError(f"Corrupt HEADER JSON: {exc}") from exc

        if not isinstance(header, dict) or header.get("record_type") != "HEADER":
            raise LedgerIntegrityError("Line 0 must be a HEADER record with record_type='HEADER'")

        if header.get("authority_effect") != "None":
            raise LedgerIntegrityError("Header must carry AuthorityEffect 'None'")

        declared_count = header.get("entry_count")
        if type(declared_count) is not int or declared_count < 0:
            raise LedgerIntegrityError("Header missing non-negative integer entry_count")

        declared_head_digest = header.get("head_digest")
        if not isinstance(declared_head_digest, str):
            raise LedgerIntegrityError("Header missing string head_digest")

        self._genesis_timestamp = str(header.get("genesis_timestamp", datetime.now(timezone.utc).isoformat()))

        # Parse entries
        actual_entries: list[CemeteryEntry] = []
        expected_prev_digest = GENESIS_DIGEST

        entry_lines = lines[1:]
        if len(entry_lines) < declared_count:
            raise LedgerTruncationError(
                f"Tail truncation detected: header declared {declared_count} entries, "
                f"but found only {len(entry_lines)} entries on disk"
            )
        if len(entry_lines) > declared_count:
            raise LedgerIntegrityError(
                f"Spurious entries detected: header declared {declared_count} entries, "
                f"but found {len(entry_lines)} entries on disk"
            )

        for idx, line_str in enumerate(entry_lines):
            try:
                rec = json.loads(line_str, parse_constant=_reject_json_constant)
            except Exception as exc:
                raise LedgerIntegrityError(f"Corrupt JSON at entry index {idx}: {exc}") from exc

            if not isinstance(rec, dict) or rec.get("record_type") != "ENTRY":
                raise LedgerIntegrityError(f"Record at index {idx} must have record_type='ENTRY'")

            if set(rec.keys()) != ALLOWED_ENTRY_KEYS:
                raise LedgerIntegrityError(
                    f"Entry {idx} keys do not match schema: {set(rec.keys())}"
                )

            if rec.get("authority_effect") != "None":
                raise LedgerIntegrityError(
                    f"Entry {idx} must carry AuthorityEffect 'None', got {rec.get('authority_effect')!r}"
                )

            recorded_index = rec.get("entry_index")
            if type(recorded_index) is not int or recorded_index != idx:
                raise LedgerIntegrityError(
                    f"Entry index discontinuity at position {idx}: got {recorded_index!r}"
                )

            prev_dig = rec.get("prev_digest")
            if prev_dig != expected_prev_digest:
                raise LedgerIntegrityError(
                    f"Hash-chain break at entry {idx}: declared prev_digest '{prev_dig}' "
                    f"!= expected '{expected_prev_digest}'"
                )

            claimed_digest = rec.get("entry_digest")
            if not isinstance(claimed_digest, str):
                raise LedgerIntegrityError(f"Entry {idx} missing entry_digest string")

            # Recompute digest over the canonical payload
            turn_envelope = rec.get("turn_envelope", {})
            prompt_parameters = rec.get("prompt_parameters", {})
            cochain_projection = rec.get("cochain_projection", {})
            refusal_reason = str(rec.get("refusal_reason", ""))
            timestamp_utc = str(rec.get("timestamp_utc", ""))
            authority_effect = str(rec.get("authority_effect", "None"))

            payload = self._entry_payload(
                entry_index=idx,
                timestamp_utc=timestamp_utc,
                turn_envelope=turn_envelope,
                refusal_reason=refusal_reason,
                prompt_parameters=prompt_parameters,
                cochain_projection=cochain_projection,
                prev_digest=expected_prev_digest,
                authority_effect=authority_effect,
            )
            try:
                recomputed_digest = _sha256_hex(_canonical_json_bytes(payload))
            except CanonicalizationError as exc:
                raise LedgerIntegrityError(f"Entry {idx} payload is not canonical: {exc}") from exc
            if recomputed_digest != claimed_digest:
                raise LedgerIntegrityError(
                    f"Bit-flip or record tampering detected at entry {idx}: "
                    f"claimed '{claimed_digest}' != recomputed '{recomputed_digest}'"
                )

            entry = CemeteryEntry(
                entry_index=idx,
                timestamp_utc=timestamp_utc,
                turn_envelope=turn_envelope,
                refusal_reason=refusal_reason,
                prompt_parameters=prompt_parameters,
                cochain_projection=cochain_projection,
                prev_digest=expected_prev_digest,
                entry_digest=claimed_digest,
                authority_effect=authority_effect,
            )
            actual_entries.append(entry)
            expected_prev_digest = claimed_digest

        if declared_head_digest != expected_prev_digest:
            raise LedgerTruncationError(
                f"Head digest mismatch: header bound '{declared_head_digest}', "
                f"recomputed head is '{expected_prev_digest}'"
            )

        self._entries = actual_entries
        self._tail_digest = expected_prev_digest

    def _write_file(self) -> None:
        """Atomically persist header and entries as JSON-L in the sorted-key compact profile."""
        header_record = {
            "authority_effect": "None",
            "entry_count": len(self._entries),
            "genesis_timestamp": self._genesis_timestamp,
            "head_digest": self._tail_digest,
            "record_type": "HEADER",
            "schema": HEADER_SCHEMA,
        }
        all_lines = [_canonical_json_bytes(header_record).decode("utf-8")]
        for entry in self._entries:
            all_lines.append(_canonical_json_bytes(entry.to_dict()).decode("utf-8"))

        content = "\n".join(all_lines) + "\n"

        temp_path = self.file_path.with_suffix(".tmp")
        temp_path.write_bytes(content.encode("utf-8"))
        os.replace(temp_path, self.file_path)

    def record_refusal(
        self,
        turn_envelope: Any,
        refusal_reason: str,
        prompt_parameters: Mapping[str, Any] | None = None,
        cochain_projection: Mapping[str, Any] | None = None,
    ) -> CemeteryEntry:
        """Permanently commit a refused candidate turn into the append-only ledger."""
        # Convert envelope to mapping
        if hasattr(turn_envelope, "to_dict"):
            envelope_dict = turn_envelope.to_dict()
        elif hasattr(turn_envelope, "identity_fields"):
            envelope_dict = turn_envelope.identity_fields()
        elif isinstance(turn_envelope, Mapping):
            envelope_dict = dict(turn_envelope)
        elif hasattr(turn_envelope, "__dict__"):
            envelope_dict = {k: v for k, v in turn_envelope.__dict__.items() if not k.startswith("_")}
        else:
            envelope_dict = {"raw": str(turn_envelope)}

        params = dict(prompt_parameters) if prompt_parameters is not None else {}
        projection = dict(cochain_projection) if cochain_projection is not None else {}

        envelope_dict = _sanitize_for_cemetery(envelope_dict)
        params = _sanitize_for_cemetery(params)
        projection = _sanitize_for_cemetery(projection)

        idx = len(self._entries)
        prev_digest = self._tail_digest
        timestamp_utc = datetime.now(timezone.utc).isoformat()

        payload = self._entry_payload(
            entry_index=idx,
            timestamp_utc=timestamp_utc,
            turn_envelope=envelope_dict,
            refusal_reason=refusal_reason,
            prompt_parameters=params,
            cochain_projection=projection,
            prev_digest=prev_digest,
        )
        entry_digest = _sha256_hex(_canonical_json_bytes(payload))

        entry = CemeteryEntry(
            entry_index=idx,
            timestamp_utc=timestamp_utc,
            turn_envelope=envelope_dict,
            refusal_reason=refusal_reason,
            prompt_parameters=params,
            cochain_projection=projection,
            prev_digest=prev_digest,
            entry_digest=entry_digest,
            authority_effect="None",
        )
        self._entries.append(entry)
        self._tail_digest = entry_digest
        self._write_file()
        return entry

    def tail_digest(self) -> str:
        """Return the current SHA-256 hash-chain digest at the head of the ledger."""
        return self._tail_digest

    def verify_integrity(self) -> bool:
        """Verify hash-chain continuity and reject any tail-truncation or interior bit-flips."""
        self._load_and_verify()
        return True

    def emit_tail_receipt(self) -> TailReceipt:
        """Emit a cryptographically sealed tail-truncation receipt."""
        tail_body = {
            "authority_effect": "None",
            "entry_count": len(self._entries),
            "head_digest": self._tail_digest,
            "schema": RECEIPT_SCHEMA,
        }
        receipt_sha256 = _sha256_hex(_canonical_json_bytes(tail_body))
        return TailReceipt(
            entry_count=len(self._entries),
            head_digest=self._tail_digest,
            receipt_sha256=receipt_sha256,
            schema=RECEIPT_SCHEMA,
            authority_effect="None",
        )

    def get_entries(self) -> Sequence[CemeteryEntry]:
        """Return an immutable sequence of all recorded cemetery entries."""
        return tuple(self._entries)


__all__ = [
    "ALLOWED_ENTRY_KEYS",
    "CemeterySink",
    "FLOAT_TAG",
    "GENESIS_DIGEST",
    "HEADER_SCHEMA",
    "RECEIPT_SCHEMA",
]
