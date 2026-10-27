"""Tests for Dual Checkers in C023 (Exact Row-wise simulation and Independent Unitary/Backward checker)."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)


def test_dual_evaluator_valid_case():
    case = {
        "id": "cnot_case",
        "num_qubits": 2,
        "gate_budget": 5,
        "images": {
            "X0": "+XX",
            "X1": "+IX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    answer = {
        "id": "cnot_case",
        "status": "SOLVED",
        "circuit": [["CNOT", 0, 1]],
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is True
    assert meta["exact"]["verdict"] == "PASS"
    assert meta["independent"]["verdict"] == "PASS"


def test_dual_evaluator_budget_exceeded():
    case = {
        "id": "cnot_case",
        "num_qubits": 2,
        "gate_budget": 0,
        "images": {
            "X0": "+XX",
            "X1": "+IX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    answer = {
        "id": "cnot_case",
        "status": "SOLVED",
        "circuit": [["CNOT", 0, 1]],
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is False
    assert "budget" in detail.lower()


def test_dual_evaluator_wrong_circuit():
    case = {
        "id": "cnot_case",
        "num_qubits": 2,
        "gate_budget": 5,
        "images": {
            "X0": "+XX",
            "X1": "+IX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    answer = {
        "id": "cnot_case",
        "status": "SOLVED",
        "circuit": [["H", 0]],  # Wrong gate
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is False


def test_dual_evaluator_out_of_scope_witness():
    case = {
        "id": "bad_case",
        "num_qubits": 2,
        "gate_budget": 5,
        "images": {
            "X0": "+XX",
            "X1": "+XX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    answer = {
        "id": "bad_case",
        "status": "OUT_OF_SCOPE",
        "witness": {
            "pair": ["X1", "Z0"],
            "expected": "commute",
            "actual": "anticommute",
        },
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is True
