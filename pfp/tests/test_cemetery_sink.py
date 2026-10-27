"""Targeted Examiner Tests for CemeterySink and Tail-Truncation Rejection.

Methodology:
1. Invariant: Mathematical and architectural invariants (hash-chain, immutability, exact-type eq).
2. Break: Negative controls, adversarial perturbations, stealth tail-truncation, bit-flips.
3. Witness: Cryptographic receipts, sorted-key JSON determinism, cold-restart state reconstruction.
4. Mutation: Explicit verification that intentional mutations trigger fail-closed test failures.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import pytest

from pfp.domain.entities.cemetery_entry import CemeteryEntry, TailReceipt
from pfp.domain.exact.q import Q
from pfp.domain.exceptions import (
    LedgerIntegrityError,
    LedgerTruncationError,
)
from pfp.domain.ports.ports import CemeterySinkPort
from pfp.infrastructure.persistence.cemetery_sink import (
    GENESIS_DIGEST,
    CemeterySink,
)


@dataclass(frozen=True)
class MockCemeteryEntryImposter:
    """Imposter with identical fields to test exact-type equality rejection."""

    entry_index: int
    timestamp_utc: str
    turn_envelope: dict
    refusal_reason: str
    prompt_parameters: dict
    cochain_projection: dict
    prev_digest: str
    entry_digest: str
    authority_effect: str = "None"


# ==============================================================================
# 1. INVARIANT TESTS
# ==============================================================================

def test_cemetery_entry_value_object_exact_type_equality() -> None:
    """Invariant: CemeteryEntry enforces exact-type equality and composite hash."""
    e1 = CemeteryEntry(
        entry_index=0,
        timestamp_utc="2026-09-26T00:00:00Z",
        turn_envelope={"packet_id": "p0", "step": 1},
        refusal_reason="NON_CONTRACTIVE_DESCENT",
        prompt_parameters={"temperature": 0.0, "tokens": ["tok1"]},
        cochain_projection={"phi1": "1/2", "gamma2": "1"},
        prev_digest="genesis",
        entry_digest="d0",
        authority_effect="None",
    )
    e2 = CemeteryEntry(
        entry_index=0,
        timestamp_utc="2026-09-26T00:00:00Z",
        turn_envelope={"packet_id": "p0", "step": 1},
        refusal_reason="NON_CONTRACTIVE_DESCENT",
        prompt_parameters={"temperature": 0.0, "tokens": ["tok1"]},
        cochain_projection={"phi1": "1/2", "gamma2": "1"},
        prev_digest="genesis",
        entry_digest="d0",
        authority_effect="None",
    )
    imposter = MockCemeteryEntryImposter(
        entry_index=0,
        timestamp_utc="2026-09-26T00:00:00Z",
        turn_envelope={"packet_id": "p0", "step": 1},
        refusal_reason="NON_CONTRACTIVE_DESCENT",
        prompt_parameters={"temperature": 0.0, "tokens": ["tok1"]},
        cochain_projection={"phi1": "1/2", "gamma2": "1"},
        prev_digest="genesis",
        entry_digest="d0",
        authority_effect="None",
    )

    assert e1 == e2
    assert hash(e1) == hash(e2)
    assert e1 != imposter
    assert not (e1 == imposter)


def test_tail_receipt_value_object_exact_type_equality() -> None:
    """Invariant: TailReceipt enforces exact-type equality and schema binding."""
    r1 = TailReceipt(entry_count=5, head_digest="d5", receipt_sha256="sha5")
    r2 = TailReceipt(entry_count=5, head_digest="d5", receipt_sha256="sha5")

    @dataclass(frozen=True)
    class ReceiptImposter:
        entry_count: int
        head_digest: str
        receipt_sha256: str
        schema: str = "core.symbol-game.cemetery-receipt.v1"
        authority_effect: str = "None"

    imp = ReceiptImposter(entry_count=5, head_digest="d5", receipt_sha256="sha5")
    assert r1 == r2
    assert hash(r1) == hash(r2)
    assert r1 != imp


def test_cemetery_sink_protocol_compliance(tmp_path: Path) -> None:
    """Invariant: CemeterySink is an instance of CemeterySinkPort."""
    sink = CemeterySink(tmp_path / "cemetery.jsonl")
    assert isinstance(sink, CemeterySinkPort)


def test_append_only_hash_chain_continuity(tmp_path: Path) -> None:
    """Invariant: Every recorded refusal links cryptographically to the prior digest."""
    sink = CemeterySink(tmp_path / "cemetery.jsonl")
    assert sink.tail_digest() == GENESIS_DIGEST

    e0 = sink.record_refusal(
        turn_envelope={"step": 1},
        refusal_reason="CYCLE_OBSTRUCTION",
        prompt_parameters={"candidate": "gamma_0"},
        cochain_projection={"phi1": "1", "gamma2": "2"},
    )
    assert e0.entry_index == 0
    assert e0.prev_digest == GENESIS_DIGEST
    assert sink.tail_digest() == e0.entry_digest

    e1 = sink.record_refusal(
        turn_envelope={"step": 2},
        refusal_reason="ENERGY_DIVERGENCE",
        prompt_parameters={"candidate": "gamma_1"},
        cochain_projection={"phi1": "3", "gamma2": "1"},
    )
    assert e1.entry_index == 1
    assert e1.prev_digest == e0.entry_digest
    assert sink.tail_digest() == e1.entry_digest

    e2 = sink.record_refusal(
        turn_envelope={"step": 3},
        refusal_reason="AUTHORITY_LEAK",
        prompt_parameters={"candidate": "gamma_2"},
        cochain_projection={"phi1": "0", "gamma2": "1"},
    )
    assert e2.entry_index == 2
    assert e2.prev_digest == e1.entry_digest
    assert sink.tail_digest() == e2.entry_digest

    entries = sink.get_entries()
    assert len(entries) == 3
    assert entries[0] == e0
    assert entries[1] == e1
    assert entries[2] == e2


def test_zero_data_loss_full_prompt_and_cochain_capture(tmp_path: Path) -> None:
    """Invariant: Zero Data-Loss guarantees full raw prompt tokens and cochain deltas are preserved."""
    ledger_file = tmp_path / "zero_loss.jsonl"
    sink = CemeterySink(ledger_file)

    raw_tokens = ["SYSTEM: descent", "USER: candidate", "ASSISTANT: hallucination_123"]
    cochain = {"delta_phi1": "-1/2", "delta_gamma2": "0", "active_obstructions": ["h1", "h2"]}

    entry = sink.record_refusal(
        turn_envelope={"turn_id": "t-007", "actor": "proposer"},
        refusal_reason="HALLUCINATION_FRAME_BREAK",
        prompt_parameters={"raw_tokens": raw_tokens, "temperature": 0.7},
        cochain_projection=cochain,
    )

    assert entry.prompt_parameters["raw_tokens"] == raw_tokens
    assert entry.cochain_projection == cochain

    # Verify on-disk persistence contains exact tokens
    lines = [json.loads(l) for l in ledger_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 2  # Line 0 Header + Line 1 Entry
    assert lines[1]["prompt_parameters"]["raw_tokens"] == raw_tokens
    assert lines[1]["cochain_projection"] == cochain


# ==============================================================================
# 2. BREAK TESTS (NEGATIVE CONTROLS & ADVERSARIAL PERTURBATIONS)
# ==============================================================================

def test_cold_restart_tail_truncation_rejection(tmp_path: Path) -> None:
    """Break: An attacker deletes the last entry from the ledger; cold restart fails closed."""
    ledger_file = tmp_path / "tampered.jsonl"
    sink = CemeterySink(ledger_file)

    for i in range(5):
        sink.record_refusal(
            turn_envelope={"step": i},
            refusal_reason=f"REFUSAL_{i}",
            prompt_parameters={"idx": i},
            cochain_projection={"phi1": str(i)},
        )

    # Simulate stealth tail-truncation attack: delete the last line (entry 4)
    lines = [l for l in ledger_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 6  # Header + 5 entries
    truncated_lines = lines[:-1]  # Header + 4 entries
    ledger_file.write_text("\n".join(truncated_lines) + "\n", encoding="utf-8")

    # Cold restart must detect missing 5th entry and raise LedgerTruncationError
    with pytest.raises(LedgerTruncationError) as exc_info:
        CemeterySink(ledger_file)
    assert "Tail truncation detected" in str(exc_info.value)


def test_intermediate_bit_flip_tamper_detection(tmp_path: Path) -> None:
    """Break: Modifying a single character in historical entries triggers LedgerIntegrityError."""
    ledger_file = tmp_path / "bit_flip.jsonl"
    sink = CemeterySink(ledger_file)

    for i in range(4):
        sink.record_refusal(
            turn_envelope={"step": i},
            refusal_reason=f"REFUSAL_{i}",
            prompt_parameters={"i": i},
            cochain_projection={"phi": "0"},
        )

    lines = [l for l in ledger_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Tamper with record 2 (index 1): change a refusal reason
    entry_2 = json.loads(lines[2])
    entry_2["refusal_reason"] = "TAMPERED_REASON"
    lines[2] = json.dumps(entry_2, sort_keys=True, separators=(",", ":"))
    ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityError) as exc_info:
        CemeterySink(ledger_file)
    assert "Bit-flip or record tampering detected" in str(exc_info.value)


def test_spurious_entry_append_without_header_update(tmp_path: Path) -> None:
    """Break: Appending extra records without updating Header entry_count is refused."""
    ledger_file = tmp_path / "spurious.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal(turn_envelope={"step": 0}, refusal_reason="REF_0")

    # Add extra line to disk without updating header
    extra_line = json.dumps({
        "record_type": "ENTRY",
        "entry_index": 1,
        "timestamp_utc": "2026-09-26T00:00:00Z",
        "turn_envelope": {},
        "refusal_reason": "INJECTED",
        "prompt_parameters": {},
        "cochain_projection": {},
        "prev_digest": sink.tail_digest(),
        "entry_digest": "fake",
        "authority_effect": "None",
    })
    with open(ledger_file, "a", encoding="utf-8") as f:
        f.write(extra_line + "\n")

    with pytest.raises(LedgerIntegrityError) as exc_info:
        CemeterySink(ledger_file)
    assert "Spurious entries detected" in str(exc_info.value)


def test_empty_ledger_file_rejection(tmp_path: Path) -> None:
    """Break: Completely empty ledger file raises LedgerTruncationError."""
    ledger_file = tmp_path / "empty.jsonl"
    ledger_file.write_text("", encoding="utf-8")

    with pytest.raises(LedgerTruncationError) as exc_info:
        CemeterySink(ledger_file)
    assert "Empty ledger file" in str(exc_info.value)


def test_corrupt_header_rejection(tmp_path: Path) -> None:
    """Break: Non-HEADER line 0 raises LedgerIntegrityError."""
    ledger_file = tmp_path / "bad_header.jsonl"
    ledger_file.write_text("NOT_JSON\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityError) as exc_info:
        CemeterySink(ledger_file)
    assert "Corrupt HEADER JSON" in str(exc_info.value)


def test_utf8_bom_rejection(tmp_path: Path) -> None:
    """Break: File containing UTF-8 BOM is rejected under byte-level cleanliness rule."""
    ledger_file = tmp_path / "bom.jsonl"
    ledger_file.write_bytes(b"\xef\xbb\xbf" + json.dumps({"record_type": "HEADER"}).encode("utf-8") + b"\n")

    with pytest.raises(LedgerIntegrityError) as exc_info:
        CemeterySink(ledger_file)
    assert "BOM detected" in str(exc_info.value)


def test_cemetery_entry_authority_leak_refusal() -> None:
    """Break: Attempting to mint AuthorityEffect other than 'None' raises ValueError."""
    with pytest.raises(ValueError, match="AuthorityEffect must be 'None'"):
        CemeteryEntry(
            entry_index=0,
            timestamp_utc="2026-09-26T00:00:00Z",
            turn_envelope={},
            refusal_reason="TEST",
            prompt_parameters={},
            cochain_projection={},
            prev_digest="genesis",
            entry_digest="d0",
            authority_effect="PROMOTED",  # FORBIDDEN
        )


# ==============================================================================
# 3. WITNESS TESTS
# ==============================================================================

def test_multi_session_cold_restart_replay(tmp_path: Path) -> None:
    """Witness: State is faithfully recovered across multi-session process cold restarts."""
    ledger_file = tmp_path / "cold_restart.jsonl"

    # Session 1: Record 3 refusals
    s1 = CemeterySink(ledger_file)
    s1.record_refusal({"s": 1}, "R1", {"p": 1}, {"c": 1})
    s1.record_refusal({"s": 2}, "R2", {"p": 2}, {"c": 2})
    s1.record_refusal({"s": 3}, "R3", {"p": 3}, {"c": 3})
    receipt_1 = s1.emit_tail_receipt()
    tail_1 = s1.tail_digest()

    # Session 2: Cold restart from disk
    s2 = CemeterySink(ledger_file)
    assert s2.tail_digest() == tail_1
    assert len(s2.get_entries()) == 3
    assert s2.verify_integrity() is True

    # Continue appending in Session 2
    s2.record_refusal({"s": 4}, "R4", {"p": 4}, {"c": 4})
    assert len(s2.get_entries()) == 4
    receipt_2 = s2.emit_tail_receipt()
    assert receipt_2.entry_count == 4
    assert receipt_2.receipt_sha256 != receipt_1.receipt_sha256

    # Session 3: Cold restart again
    s3 = CemeterySink(ledger_file)
    assert len(s3.get_entries()) == 4
    assert s3.verify_integrity() is True


def test_sorted_key_profile_byte_determinism(tmp_path: Path) -> None:
    """Witness: Re-serializing entries produces byte-for-byte deterministic output."""
    ledger_file = tmp_path / "determinism.jsonl"
    sink = CemeterySink(ledger_file)

    sink.record_refusal(
        turn_envelope={"b": 2, "a": 1},
        refusal_reason="ORDER_TEST",
        prompt_parameters={"z": 26, "a": 1},
        cochain_projection={"y": "yes", "x": "no"},
    )
    first_bytes = ledger_file.read_bytes()

    # Cold reload and re-verify
    reloaded = CemeterySink(ledger_file)
    reloaded._write_file()
    second_bytes = ledger_file.read_bytes()

    assert first_bytes == second_bytes
    assert b"\r" not in first_bytes  # Pure LF invariant
    assert not first_bytes.startswith(b"\xef\xbb\xbf")  # Zero BOM


# ==============================================================================
# 4. MUTATION TESTS (STRICT EXAMINER MUTATION VERIFICATION)
# ==============================================================================

def test_mutation_check_tail_truncation_detection_cannot_be_bypassed(tmp_path: Path) -> None:
    """Mutation: Asserting that tail truncation check is strictly fail-closed."""
    ledger_file = tmp_path / "mut_trunc.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal({"step": 0}, "R0")
    sink.record_refusal({"step": 1}, "R1")

    # Manually truncate
    lines = [l for l in ledger_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    ledger_file.write_text(lines[0] + "\n" + lines[1] + "\n", encoding="utf-8")  # Omit entry 1

    # Verify that truncation cannot be silently ignored
    with pytest.raises(LedgerTruncationError):
        CemeterySink(ledger_file)


def test_cemetery_sink_exact_rational_cochain_serialization(tmp_path: Path) -> None:
    """Invariant: CemeterySink serializes Fraction and Q in cochain_projection without error."""
    ledger_file = tmp_path / "exact_serialization.jsonl"
    sink = CemeterySink(ledger_file)

    entry = sink.record_refusal(
        turn_envelope={"step": 1, "packet_id": "pkt_exact"},
        refusal_reason="TEST_EXACT_TYPES",
        prompt_parameters={"temp": 0, "alpha": Fraction(1, 4)},
        cochain_projection={"phi1": Fraction(1, 2), "gamma2": Q(1, 1)},
    )
    assert entry.cochain_projection["phi1"] == "1/2"
    assert entry.cochain_projection["gamma2"] == "1/1"

    # Reload and verify disk integrity
    reloaded = CemeterySink(ledger_file)
    assert len(reloaded.get_entries()) == 1
    assert reloaded.verify_integrity() is True
    loaded_entry = reloaded.get_entries()[0]
    assert loaded_entry.cochain_projection["phi1"] == "1/2"
    assert loaded_entry.cochain_projection["gamma2"] == "1/1"


def test_mutation_check_authority_effect_tamper_detection(tmp_path: Path) -> None:
    """Mutation: On-disk mutation of authority_effect to non-None raises LedgerIntegrityError."""
    ledger_file = tmp_path / "mut_auth.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal({"step": 1}, "REFUSAL_1")

    lines = ledger_file.read_text(encoding="utf-8").splitlines()
    entry_dict = json.loads(lines[1])
    entry_dict["authority_effect"] = "PROMOTED"
    lines[1] = json.dumps(entry_dict)
    ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityError, match="AuthorityEffect 'None'"):
        CemeterySink(ledger_file)


def test_mutation_check_extra_key_injection_detection(tmp_path: Path) -> None:
    """Mutation: On-disk injection of arbitrary extra keys raises LedgerIntegrityError."""
    ledger_file = tmp_path / "mut_extra_keys.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal({"step": 1}, "REFUSAL_1")

    lines = ledger_file.read_text(encoding="utf-8").splitlines()
    entry_dict = json.loads(lines[1])
    entry_dict["malicious_injected_key"] = "payload"
    lines[1] = json.dumps(entry_dict)
    ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityError, match="keys do not match schema"):
        CemeterySink(ledger_file)


def test_corrupt_utf8_encoding_raises_ledger_integrity_error(tmp_path: Path) -> None:
    """Mutation: Invalid non-UTF8 bytes in ledger file raises LedgerIntegrityError."""
    ledger_file = tmp_path / "corrupt_utf8.jsonl"
    ledger_file.write_bytes(b"\xff\xfe\x00\x00")

    with pytest.raises(LedgerIntegrityError, match="Corrupt UTF-8 encoding"):
        CemeterySink(ledger_file)


def test_boolean_counts_are_not_integers(tmp_path: Path) -> None:
    """JSON true is a bool. It must not count as entry 1."""
    with pytest.raises(ValueError, match="entry_count"):
        TailReceipt(entry_count=True, head_digest="d", receipt_sha256="s")
    with pytest.raises(ValueError, match="entry_index"):
        CemeteryEntry(
            entry_index=True,
            timestamp_utc="t",
            turn_envelope={},
            refusal_reason="refused",
            prompt_parameters={},
            cochain_projection={},
            prev_digest="p",
            entry_digest="e",
        )

    ledger_file = tmp_path / "bool_count.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal({"step": 1}, "REFUSAL_1")
    lines = ledger_file.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    header["entry_count"] = True
    lines[0] = json.dumps(header)
    ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(LedgerIntegrityError, match="entry_count"):
        CemeterySink(ledger_file)


# ==============================================================================
# 5. FLOAT AND NaN REFUSAL IN DIGESTED PAYLOADS (O-05)
# ==============================================================================


def _reject_constant(token: str) -> None:
    raise AssertionError(f"ledger bytes contain the non-JSON constant {token}")


@pytest.mark.parametrize("value", [0.5, float("nan"), float("inf"), -0.0])
def test_digest_encoder_refuses_floats_and_nan(value: float) -> None:
    """Counterexample: the old encoder digested ``{"t": NaN}`` as the bytes ``NaN``."""
    from pfp.domain.exceptions import CanonicalizationError
    from pfp.infrastructure.persistence.cemetery_sink import (
        _canonical_json_bytes,
    )

    with pytest.raises(CanonicalizationError):
        _canonical_json_bytes({"prompt_parameters": {"temperature": value}})
    with pytest.raises(CanonicalizationError):
        _canonical_json_bytes({"cochain": [1, [value]]})


def test_float_inputs_are_recorded_exactly_without_json_floats(tmp_path: Path) -> None:
    """A refused turn carrying floats is still recorded, bit for bit, as tagged hex."""
    from pfp.infrastructure.persistence.cemetery_sink import FLOAT_TAG

    ledger_file = tmp_path / "floats.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal(
        turn_envelope={"turn_id": "t-float"},
        refusal_reason="REFUSED_FLOAT_REPLY",
        prompt_parameters={"temperature": 0.7, "bad": float("nan")},
        cochain_projection={"residual": [float("inf"), Fraction(1, 3)]},
    )
    text = ledger_file.read_text(encoding="utf-8")
    assert "NaN" not in text and "Infinity" not in text
    entry = json.loads(text.splitlines()[1], parse_constant=_reject_constant)
    temperature = entry["prompt_parameters"]["temperature"]
    assert temperature == {FLOAT_TAG: (0.7).hex()}
    assert float.fromhex(temperature[FLOAT_TAG]) == 0.7
    assert entry["prompt_parameters"]["bad"] == {FLOAT_TAG: "nan"}
    assert entry["cochain_projection"]["residual"] == [{FLOAT_TAG: "inf"}, "1/3"]
    assert CemeterySink(ledger_file).verify_integrity() is True


def test_loader_refuses_a_ledger_whose_digested_payload_holds_a_float(tmp_path: Path) -> None:
    """Counterexample: a ledger whose entry was digested over a JSON float loaded as valid."""
    import hashlib

    ledger_file = tmp_path / "legacy_float.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal({"turn_id": "t"}, "R")
    header_line, entry_line = ledger_file.read_text(encoding="utf-8").splitlines()
    entry = json.loads(entry_line)
    entry["prompt_parameters"] = {"temperature": 0.5}
    body = {key: value for key, value in entry.items() if key != "entry_digest"}
    body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    entry["entry_digest"] = hashlib.sha256(body_bytes.encode("utf-8")).hexdigest()
    header = json.loads(header_line)
    header["head_digest"] = entry["entry_digest"]
    compact = {"sort_keys": True, "separators": (",", ":"), "ensure_ascii": False}
    ledger_file.write_text(
        json.dumps(header, **compact) + "\n" + json.dumps(entry, **compact) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(LedgerIntegrityError, match="not canonical"):
        CemeterySink(ledger_file)


def test_loader_refuses_nan_constants(tmp_path: Path) -> None:
    ledger_file = tmp_path / "nan.jsonl"
    sink = CemeterySink(ledger_file)
    sink.record_refusal({"turn_id": "t"}, "R")
    header_line, entry_line = ledger_file.read_text(encoding="utf-8").splitlines()
    entry_line = entry_line.replace('"turn_id":"t"', '"turn_id":NaN')
    ledger_file.write_text(header_line + "\n" + entry_line + "\n", encoding="utf-8")
    with pytest.raises(LedgerIntegrityError, match="NaN"):
        CemeterySink(ledger_file)
