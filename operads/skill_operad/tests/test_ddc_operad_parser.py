"""Unit tests for DdcOperadParser.

Verifies:
1. Ingestion of hash-chained DDC action records.
2. Enforcement of DDC candidate runtime laws (alphabet, terminal absorption, monotonicity).
3. Mapping of DDC runes {C, R, E, I, Λ, D, M, T} into typed ColoredOp operad morphisms.
4. Exact rational residual contraction calculation.
5. Registration into ColouredOperad multicategory registry.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest
from omega_engine_operads.skill_operad.coloured_operad import ColouredOperad
from omega_engine_operads.skill_operad.ddc_operad_parser import (
    DdcOperadParser,
    OperadCompositionReceipt,
)


def _build_synthetic_tape(steps_payload: list[dict]) -> list[dict]:
    """Helper creating a cryptographically valid hash-chained DDC tape."""
    tape = []
    head: str | None = None
    for seq, payload in enumerate(steps_payload):
        sorted_payload = {
            k: payload[k] for k in sorted(payload.keys(), key=lambda key: key.encode("utf-8"))
        }
        material = json.dumps(
            {"sequence": seq, "parent_sha256": head, "payload": sorted_payload},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        rec_sha = hashlib.sha256(material).hexdigest()
        tape.append({
            "sequence": seq,
            "parent_sha256": head,
            "payload": sorted_payload,
            "record_sha256": rec_sha,
        })
        head = rec_sha
    return tape


def test_ddc_operad_parser_exact_contraction(tmp_path: Path) -> None:
    tape_records = _build_synthetic_tape([
        {
            "letter": "C",
            "before_class": "Uninitialized",
            "after_class": "CarrierExposed",
            "carrier_hash": "carrier_1",
            "phi_1": "1/2",
            "gamma_2": "0",
        },
        {
            "letter": "R",
            "before_class": "CarrierExposed",
            "after_class": "ResidualProjected",
            "carrier_hash": "carrier_1",
            "phi_1": "1/2",
            "gamma_2": "0",
        },
        {
            "letter": "E",
            "before_class": "ResidualProjected",
            "after_class": "ExactRepaired",
            "carrier_hash": "carrier_1",
            "phi_1": "0",
            "gamma_2": "0",
        },
        {
            "letter": "I",
            "before_class": "ExactRepaired",
            "after_class": "Integrated",
            "carrier_hash": "carrier_1",
            "phi_1": "0",
            "gamma_2": "0",
        },
        {
            "letter": "T",
            "before_class": "Integrated",
            "after_class": "Terminalized",
            "carrier_hash": "carrier_1",
            "phi_1": "0",
            "gamma_2": "0",
        },
    ])

    run_dir = tmp_path / "runs" / "test_exact_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    ddc_file = run_dir / "ddc.jsonl"
    with open(ddc_file, "w", encoding="utf-8") as f:
        for r in tape_records:
            f.write(json.dumps(r) + "\n")

    parser = DdcOperadParser(run_dir)
    res = parser.parse()
    assert res.is_ok, f"Parser failed: {res.unwrap_err()}"
    receipt = res.unwrap()

    assert receipt.step_count == 5
    assert receipt.tape_str == "C.R.E.I.T"
    assert receipt.hash_chain_valid is True
    assert receipt.ddc_laws_valid is True
    assert receipt.law_violations == ()
    assert receipt.initial_residual == "1/2"
    assert receipt.terminal_residual == "0"
    assert receipt.residual_delta == "-1/2"
    assert receipt.residual_effect == "exact"
    assert receipt.authority_effect == "None"

    # Test registration into ColouredOperad
    operad = ColouredOperad("TestDdcOperad")
    reg_res = parser.register_in_operad(operad)
    assert reg_res["operations_registered"] == 5
    assert reg_res["compositions_registered"] >= 1
    assert "State" in operad.colours
    assert "Receipt" in operad.colours


def test_ddc_operad_parser_broken_hash_chain() -> None:
    tape_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1"},
        {"letter": "R", "carrier_hash": "c1"},
    ])
    # Corrupt parent_sha256 of step 1
    tape_records[1]["parent_sha256"] = "bad" * 16

    parser = DdcOperadParser(tape_records)
    res = parser.parse()
    assert res.is_err
    refusal = res.unwrap_err()
    assert refusal.code == "HASH_CHAIN_BROKEN"


def test_ddc_operad_parser_detects_terminal_absorbing_violation() -> None:
    # Step after T
    tape_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1"},
        {"letter": "T", "carrier_hash": "c1"},
        {"letter": "R", "carrier_hash": "c1"},
    ])
    parser = DdcOperadParser(tape_records)
    res = parser.parse()
    assert res.is_ok
    receipt = res.unwrap()
    assert receipt.ddc_laws_valid is False
    assert any("TerminalAbsorbing" in v for v in receipt.law_violations)


def test_ddc_operad_parser_detects_non_monotonic_repair() -> None:
    tape_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1/4"},
        {"letter": "E", "carrier_hash": "c1", "phi_1": "3/4"},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "3/4"},
    ])
    parser = DdcOperadParser(tape_records)
    res = parser.parse()
    assert res.is_ok
    receipt = res.unwrap()
    assert receipt.ddc_laws_valid is False
    assert any("ExactRepairIncreasedPhi1" in v for v in receipt.law_violations)


def test_ddc_operad_parser_string_buffer_and_export(tmp_path: Path) -> None:
    tape_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1/2", "gamma_2": "0"},
        {"letter": "R", "carrier_hash": "c1", "phi_1": "1/2", "gamma_2": "0"},
        {"letter": "E", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0"},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0"},
    ])
    tape_jsonl = "\n".join(json.dumps(r) for r in tape_records) + "\n"

    parser = DdcOperadParser(tape_jsonl)
    res = parser.parse()
    assert res.is_ok
    receipt = res.unwrap()
    assert receipt.residual_effect == "exact"
    assert receipt.tape_str == "C.R.E.T"

    # Test export_evidence_receipt
    receipt_out = tmp_path / "receipts" / "my_operad_receipt.json"
    exp_res = parser.export_evidence_receipt(receipt_out)
    assert exp_res.is_ok
    assert receipt_out.is_file()
    saved = json.loads(receipt_out.read_text(encoding="utf-8"))
    assert saved["residual_effect"] == "exact"
    assert saved["step_count"] == 4
    assert saved["hash_chain_valid"] is True
