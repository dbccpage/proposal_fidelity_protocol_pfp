"""Deterministic codec adapter for the Epistemic Quarantine Ledger.

Enforces:
1. RFC 8785 Canonical JSON & Byte-Level Determinism.
2. Explicit Head Record Binding (thanatos-append-only-log-truncation-auditor).
3. Cryptographic SHA-256 Hash Chain Integrity.
4. Permanent Quarantine Law (FW-SCOPE, Stage 10 floor).
5. UTF-8 Cleanliness without BOM (\xef\xbb\xbf).
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from omega_engine_pfp.domain.mssn_research.grammar.entities import EpistemicQuarantineLedger
from omega_engine_pfp.domain.mssn_research.grammar.errors import (
    GrammarDomainError,
    LedgerIntegrityError,
    LedgerSerializationError,
    LedgerTruncationError,
    ScopeBoundaryViolationError,
)
from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    HostFenceAudit,
    PontryaginKillFlags,
    QuarantinedShadowPacket,
)
from omega_engine_pfp.domain.mssn_research.packets.value_objects import RefusalCode
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel


def canonical_json_bytes(obj: Any) -> bytes:
    """Encode an object to RFC 8785 Canonical JSON bytes in UTF-8."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    """Compute standard hex SHA-256 digest over byte payload."""
    return sha256(data).hexdigest()


def packet_to_dict(packet: QuarantinedShadowPacket) -> dict[str, Any]:
    """Convert a QuarantinedShadowPacket into a deterministic dictionary representation."""
    return {
        "assertion_flags": {
            "flag_alpha": packet.assertion_flags.flag_alpha,
            "flag_pi": packet.assertion_flags.flag_pi,
            "flag_u1": packet.assertion_flags.flag_u1,
            "flag_zn": packet.assertion_flags.flag_zn,
        },
        "evidence_bound": packet.evidence_bound,
        "fence_audit": {
            "check_alpha": packet.fence_audit.check_alpha,
            "check_pi": packet.fence_audit.check_pi,
            "check_u1": packet.fence_audit.check_u1,
            "check_zn": packet.fence_audit.check_zn,
            "quarantine_verdict": packet.fence_audit.quarantine_verdict,
        },
        "raw_transcript": list(packet.raw_transcript),
        "shadow_type": packet.shadow_type,
        "target_theorem": packet.target_theorem,
    }


def dict_to_packet(d: dict[str, Any]) -> Result[QuarantinedShadowPacket, GrammarDomainError]:
    """Reconstruct a QuarantinedShadowPacket from a validated dictionary representation."""
    try:
        flags_d = d["assertion_flags"]
        flags = PontryaginKillFlags(
            flag_pi=bool(flags_d.get("flag_pi", False)),
            flag_u1=bool(flags_d.get("flag_u1", False)),
            flag_zn=bool(flags_d.get("flag_zn", False)),
            flag_alpha=bool(flags_d.get("flag_alpha", False)),
        )
        audit_d = d["fence_audit"]
        audit = HostFenceAudit(
            check_pi=bool(audit_d.get("check_pi", True)),
            check_u1=bool(audit_d.get("check_u1", True)),
            check_zn=bool(audit_d.get("check_zn", True)),
            check_alpha=bool(audit_d.get("check_alpha", True)),
            quarantine_verdict=bool(audit_d.get("quarantine_verdict", True)),
        )
        transcript = tuple(str(x) for x in d.get("raw_transcript", []))
        return Ok(
            QuarantinedShadowPacket(
                target_theorem=str(d["target_theorem"]),
                assertion_flags=flags,
                fence_audit=audit,
                shadow_type=str(d["shadow_type"]),
                evidence_bound=str(d["evidence_bound"]),
                raw_transcript=transcript,
            )
        )
    except (KeyError, TypeError, ValueError) as exc:
        return Refusal(
            LedgerSerializationError(
                code=RefusalCode.MALFORMED_PACKET,
                message=f"Failed to parse QuarantinedShadowPacket fields from dict: {exc}",
            )
        )


def serialize_ledger_to_jsonl(ledger: EpistemicQuarantineLedger) -> str:
    """Serialize an EpistemicQuarantineLedger to deterministic RFC 8785 canonical JSON-L.

    Line 0: HEADER record binding total entry count, head digest, schema version, and stage level.
    Lines 1..N: ENTRY records in a cryptographic SHA-256 hash chain with prev_digest pointers.
    """
    entry_lines: list[dict[str, Any]] = []
    prev_digest = "genesis"

    for idx, packet in enumerate(ledger.entries):
        pkt_dict = packet_to_dict(packet)
        payload = {
            "entry_index": idx,
            "packet": pkt_dict,
            "prev_digest": prev_digest,
            "record_type": "ENTRY",
        }
        entry_digest = sha256_digest(canonical_json_bytes(payload))
        entry_record = {
            "entry_digest": entry_digest,
            "entry_index": idx,
            "packet": pkt_dict,
            "prev_digest": prev_digest,
            "record_type": "ENTRY",
        }
        entry_lines.append(entry_record)
        prev_digest = entry_digest

    head_digest = prev_digest  # "genesis" if empty, else last entry's digest

    header_record = {
        "entry_count": len(ledger.entries),
        "head_digest": head_digest,
        "ledger_id": ledger.ledger_id,
        "record_type": "HEADER",
        "schema_version": "v1",
        "stage_level": ledger.stage_level.level,
    }

    all_records = [header_record, *entry_lines]
    lines = [canonical_json_bytes(r).decode("utf-8") for r in all_records]
    return "\n".join(lines) + "\n"


_MAX_JSONL_CHARACTERS = 16 * 1024 * 1024
_MAX_RECORD_CHARACTERS = 1024 * 1024
_MAX_LEDGER_ENTRIES = 100_000


def deserialize_ledger_from_jsonl(
    jsonl_text: str,
) -> Result[EpistemicQuarantineLedger, GrammarDomainError]:
    """Parse and verify bounded JSON-L without trusting self-declared evidence."""
    lines_result = _bounded_records(jsonl_text)
    if lines_result.is_err():
        return lines_result
    raw_lines = lines_result.unwrap()
    header_result = _parse_header(raw_lines[0])
    if header_result.is_err():
        return header_result
    header = header_result.unwrap()
    count_result = _verify_record_count(header["entry_count"], len(raw_lines) - 1)
    if count_result.is_err():
        return count_result
    entries_result = _verify_entries(raw_lines[1:])
    if entries_result.is_err():
        return entries_result
    packets, computed_head = entries_result.unwrap()
    if header["head_digest"] != computed_head:
        return Refusal(
            _integrity_error(
                f"Head digest mismatch: header bound '{header['head_digest']}', but chain computed '{computed_head}'"
            )
        )
    return Ok(
        EpistemicQuarantineLedger(
            ledger_id=header["ledger_id"],
            stage_level=StageLevel(header["stage_level"]),
            entries=packets,
        )
    )


def _bounded_records(jsonl_text: str) -> Result[list[str], GrammarDomainError]:
    if not isinstance(jsonl_text, str):
        return Refusal(_serialization_error("Ledger content must be text"))
    if not jsonl_text.strip():
        return Refusal(_truncation_error("Empty ledger content; missing required HEADER record"))
    if len(jsonl_text) > _MAX_JSONL_CHARACTERS:
        return Refusal(_serialization_error("Ledger content exceeds 16 MiB character limit"))
    records = [line.strip() for line in jsonl_text.splitlines() if line.strip()]
    if not records:
        return Refusal(_truncation_error("No records found in ledger content"))
    if len(records) - 1 > _MAX_LEDGER_ENTRIES:
        return Refusal(_serialization_error("Ledger entry count exceeds 100000 record limit"))
    if any(len(record) > _MAX_RECORD_CHARACTERS for record in records):
        return Refusal(_serialization_error("Ledger record exceeds 1 MiB character limit"))
    return Ok(records)


def _parse_header(raw_header: str) -> Result[dict[str, Any], GrammarDomainError]:
    parsed = _parse_json_object(raw_header, "header")
    if parsed.is_err():
        return parsed
    header = parsed.unwrap()
    checks = (
        (
            header.get("record_type") == "HEADER",
            "First record must be a valid HEADER with record_type='HEADER'",
        ),
        (header.get("schema_version") == "v1", "Header schema_version must be 'v1'"),
        (
            isinstance(header.get("ledger_id"), str) and bool(header.get("ledger_id")),
            "Header missing valid ledger_id",
        ),
        (type(header.get("stage_level")) is int, "Header missing integer stage_level"),
        (
            type(header.get("entry_count")) is int and header.get("entry_count", -1) >= 0,
            "Header missing non-negative integer entry_count",
        ),
        (isinstance(header.get("head_digest"), str), "Header missing string head_digest"),
    )
    invalid = next((message for valid, message in checks if not valid), None)
    if invalid is not None:
        return Refusal(_serialization_error(invalid))
    if header["stage_level"] < 10:
        return Refusal(
            ScopeBoundaryViolationError(
                code=RefusalCode.NONCONSERVATIVE_LIFT,
                message=(
                    "Permanent Quarantine Law violation: ledger stage floor must be >= 10, "
                    f"got Stage {header['stage_level']} (FW-SCOPE)"
                ),
            )
        )
    return Ok(header)


def _verify_record_count(declared: int, actual: int) -> Result[bool, GrammarDomainError]:
    if actual < declared:
        return Refusal(
            _truncation_error(
                f"Tail truncation detected: header declared {declared} entries, but found only {actual} entries "
                f"(missing {declared - actual} records)"
            )
        )
    if actual > declared:
        return Refusal(
            _truncation_error(
                f"Log extension detected beyond declared head: header declared {declared} entries, but found {actual} entries"
            )
        )
    return Ok(True)


def _verify_entries(
    raw_entries: list[str],
) -> Result[tuple[tuple[QuarantinedShadowPacket, ...], str], GrammarDomainError]:
    packets: list[QuarantinedShadowPacket] = []
    expected_previous = "genesis"
    for index, raw_entry in enumerate(raw_entries):
        verified = _verify_entry(raw_entry, index, expected_previous)
        if verified.is_err():
            return verified
        packet, expected_previous = verified.unwrap()
        packets.append(packet)
    return Ok((tuple(packets), expected_previous))


def _verify_entry(
    raw_entry: str,
    index: int,
    expected_previous: str,
) -> Result[tuple[QuarantinedShadowPacket, str], GrammarDomainError]:
    parsed = _parse_json_object(raw_entry, f"entry line {index + 1}")
    if parsed.is_err():
        return parsed
    entry = parsed.unwrap()
    shape_result = _verify_entry_shape(entry, index, expected_previous)
    if shape_result.is_err():
        return shape_result
    packet_dict, claimed_digest = shape_result.unwrap()
    payload = {
        "entry_index": index,
        "packet": packet_dict,
        "prev_digest": expected_previous,
        "record_type": "ENTRY",
    }
    recomputed = sha256_digest(canonical_json_bytes(payload))
    if recomputed != claimed_digest:
        return Refusal(
            _integrity_error(
                f"Record tampering detected at entry {index}: declared digest '{claimed_digest}' != recomputed digest '{recomputed}'"
            )
        )
    packet_result = dict_to_packet(packet_dict)
    if packet_result.is_err():
        return packet_result
    return Ok((packet_result.unwrap(), claimed_digest))


def _verify_entry_shape(
    entry: dict[str, Any],
    index: int,
    expected_previous: str,
) -> Result[tuple[dict[str, Any], str], GrammarDomainError]:
    if entry.get("record_type") != "ENTRY":
        return Refusal(
            _serialization_error(f"Record at line {index + 1} must have record_type='ENTRY'")
        )
    if entry.get("entry_index") != index:
        return Refusal(
            _integrity_error(
                f"Entry index discontinuity at line {index + 1}: expected {index}, got {entry.get('entry_index')}"
            )
        )
    if entry.get("prev_digest") != expected_previous:
        return Refusal(
            _integrity_error(
                f"Hash chain break at entry {index}: declared prev_digest '{entry.get('prev_digest')}' "
                f"!= expected '{expected_previous}'"
            )
        )
    claimed = entry.get("entry_digest")
    packet = entry.get("packet")
    if not isinstance(claimed, str):
        return Refusal(_serialization_error(f"Entry {index} missing string entry_digest"))
    if not isinstance(packet, dict):
        return Refusal(_serialization_error(f"Entry {index} missing packet dictionary payload"))
    return Ok((packet, claimed))


def _parse_json_object(raw: str, label: str) -> Result[dict[str, Any], GrammarDomainError]:
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        return Refusal(_serialization_error(f"Failed to parse {label} JSON: {exc}"))
    if not isinstance(parsed, dict):
        return Refusal(_serialization_error(f"{label.capitalize()} must be a JSON object"))
    return Ok(parsed)


def _serialization_error(message: str) -> LedgerSerializationError:
    return LedgerSerializationError(code=RefusalCode.MALFORMED_PACKET, message=message)


def _integrity_error(message: str) -> LedgerIntegrityError:
    return LedgerIntegrityError(code=RefusalCode.HOST_VERIFICATION_REQUIRED, message=message)


def _truncation_error(message: str) -> LedgerTruncationError:
    return LedgerTruncationError(code=RefusalCode.HOST_VERIFICATION_REQUIRED, message=message)
