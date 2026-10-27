"""Test dual checkers agreement on C020 examples."""

from __future__ import annotations

import json
from pathlib import Path

from c020_spectral_sequence_double_complex.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c020_spectral_sequence_double_complex.reference_solver.solver import (
    solve,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "participant_packet" / "examples"
CASES_DIR = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"


def test_dual_checkers_on_all_examples():
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 16

    for ef in example_files:
        with ef.open(encoding="utf-8") as f:
            case = json.load(f)
        cert = solve(case)
        ok, reason, details = evaluate_dual(case, cert)
        assert ok, f"Dual check failed on {ef.name}: {reason}"


def test_dual_checkers_reject_fabricated_out_of_scope_generator():
    case_path = EXAMPLES_DIR / "c020_ex08_out_of_scope_noncommuting.json"
    with case_path.open(encoding="utf-8") as file_handle:
        case = json.load(file_handle)
    cert = solve(case)
    cert["witness"]["generator"] = "999,999:999"

    ok, reason, details = evaluate_dual(case, cert)

    assert not ok
    assert details["exact"]["verdict"] == "FAIL"
    assert details["independent"]["verdict"] == "FAIL"


def test_out_of_scope_witness_names_actual_nonzero_generator():
    case_path = CASES_DIR / "c020_poison_03_noncommuting.json"
    with case_path.open(encoding="utf-8") as file_handle:
        case = json.load(file_handle)

    cert = solve(case)
    assert cert["witness"]["generator"] == "2,0:1"
    ok, reason, _ = evaluate_dual(case, cert)
    assert ok, reason
