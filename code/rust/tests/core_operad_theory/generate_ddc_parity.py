#!/usr/bin/env python3
"""Generate frozen golden test fixtures for DDC tape parsing parity in Rust.

Usage: py -3.12 engine/crates_rs/tests/core_operad_theory/generate_ddc_parity.py [--write]

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Add repo root to sys.path
repo_root = Path(__file__).resolve().parents[4]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from operads.skill_operad.ddc_operad_parser import DdcOperadParser


def _build_synthetic_tape(steps_payload: list[dict]) -> list[dict]:
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


def generate_golden_cases() -> dict:
    cases = {}

    # Case 1: Exact Contraction Run (C.R.E.I.T)
    c1_records = _build_synthetic_tape([
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
    parser1 = DdcOperadParser(c1_records)
    res1 = parser1.parse()
    assert res1.is_ok
    receipt1 = res1.unwrap()
    cases["exact_contraction_run"] = {
        "records": c1_records,
        "is_ok": True,
        "expected_receipt": {
            "step_count": receipt1.step_count,
            "tape_str": receipt1.tape_str,
            "hash_chain_valid": receipt1.hash_chain_valid,
            "ddc_laws_valid": receipt1.ddc_laws_valid,
            "law_violations": list(receipt1.law_violations),
            "initial_residual": receipt1.initial_residual,
            "terminal_residual": receipt1.terminal_residual,
            "residual_delta": receipt1.residual_delta,
            "residual_effect": receipt1.residual_effect,
            "authority_effect": receipt1.authority_effect,
        },
    }

    # Case 2: Broken Hash Chain Run
    c2_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1"},
        {"letter": "R", "carrier_hash": "c1"},
    ])
    c2_records[1]["parent_sha256"] = "bad" * 16  # Corrupt parent_sha256 of step 1
    parser2 = DdcOperadParser(c2_records)
    res2 = parser2.parse()
    assert res2.is_err
    refusal2 = res2.unwrap_err()
    cases["broken_hash_chain_run"] = {
        "records": c2_records,
        "is_ok": False,
        "refusal_code": refusal2.code,
    }

    # Case 3: Terminal Absorbing Violation Run (Step after T)
    c3_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1"},
        {"letter": "T", "carrier_hash": "c1"},
        {"letter": "R", "carrier_hash": "c1"},
    ])
    parser3 = DdcOperadParser(c3_records)
    res3 = parser3.parse()
    assert res3.is_ok
    receipt3 = res3.unwrap()
    cases["terminal_absorbing_violation_run"] = {
        "records": c3_records,
        "is_ok": True,
        "expected_receipt": {
            "step_count": receipt3.step_count,
            "tape_str": receipt3.tape_str,
            "hash_chain_valid": receipt3.hash_chain_valid,
            "ddc_laws_valid": receipt3.ddc_laws_valid,
            "law_violations": list(receipt3.law_violations),
        },
    }

    # Case 4: Non-Monotonic Repair Run
    c4_records = _build_synthetic_tape([
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1/4"},
        {"letter": "E", "carrier_hash": "c1", "phi_1": "3/4"},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "3/4"},
    ])
    parser4 = DdcOperadParser(c4_records)
    res4 = parser4.parse()
    assert res4.is_ok
    receipt4 = res4.unwrap()
    cases["non_monotonic_repair_run"] = {
        "records": c4_records,
        "is_ok": True,
        "expected_receipt": {
            "step_count": receipt4.step_count,
            "tape_str": receipt4.tape_str,
            "hash_chain_valid": receipt4.hash_chain_valid,
            "ddc_laws_valid": receipt4.ddc_laws_valid,
            "law_violations": list(receipt4.law_violations),
        },
    }

    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write golden fixtures to disk")
    args = parser.parse_args()

    fixtures_path = Path(__file__).resolve().parent / "fixtures" / "ddc_golden_cases.json"
    cases = generate_golden_cases()
    content = json.dumps(cases, indent=2, sort_keys=True)

    if args.write:
        fixtures_path.parent.mkdir(parents=True, exist_ok=True)
        fixtures_path.write_text(content + "\n", encoding="utf-8")
        print(f"Wrote {len(cases)} golden cases to {fixtures_path}")
        return 0

    if not fixtures_path.exists():
        print(f"Fixture missing: {fixtures_path}. Run with --write to generate.", file=sys.stderr)
        return 1

    existing = fixtures_path.read_text(encoding="utf-8").strip()
    if existing != content.strip():
        print("FAIL: Golden cases diverged. Run with --write to update if intentional.", file=sys.stderr)
        return 1

    print("OK: Golden cases match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
