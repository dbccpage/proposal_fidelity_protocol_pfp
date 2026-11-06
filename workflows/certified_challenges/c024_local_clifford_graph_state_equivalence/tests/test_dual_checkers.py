"""Tests for Dual Checkers in C024."""

from __future__ import annotations

import c024_local_clifford_graph_state_equivalence.judge_packet.checkers.exact_checker as exact_checker_module
import pytest
from c024_local_clifford_graph_state_equivalence.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)


def test_dual_evaluator_valid_equivalent():
    case = {
        "id": "c024_case_p4",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]],
    }
    answer = {
        "id": "c024_case_p4",
        "status": "SOLVED",
        "equivalent": True,
        "sequence": [1],
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is True


def test_dual_evaluator_wrong_sequence():
    case = {
        "id": "c024_case_p4",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]],
    }
    answer = {
        "id": "c024_case_p4",
        "status": "SOLVED",
        "equivalent": True,
        "sequence": [2],  # Wrong vertex
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is False


def test_dual_evaluator_valid_cut_rank():
    case = {
        "id": "c024_case_neq",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1]],
    }
    answer = {
        "id": "c024_case_neq",
        "status": "SOLVED",
        "equivalent": False,
        "witness": {
            "kind": "cut_rank",
            "subset": [0, 2],
            "rank_g": 2,
            "rank_g_prime": 1,
        },
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is True


def test_dual_evaluator_invalid_cut_rank():
    case = {
        "id": "c024_case_neq",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1]],
    }
    answer = {
        "id": "c024_case_neq",
        "status": "SOLVED",
        "equivalent": False,
        "witness": {
            "kind": "cut_rank",
            "subset": [0],
            "rank_g": 1,
            "rank_g_prime": 1,  # Equal ranks do not separate!
        },
    }
    passed, detail, meta = evaluate_dual(case, answer)
    assert passed is False


def test_dual_evaluator_accepts_typed_budget_unknown(monkeypatch: pytest.MonkeyPatch):
    case = {
        "id": "c024_case_budget",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]],
    }
    answer = {
        "id": "c024_case_budget",
        "status": "UNKNOWN",
        "refusal_code": "ORBIT_SEARCH_BUDGET_EXHAUSTED",
        "witness": {
            "kind": "orbit_search_budget_exhausted",
            "states_visited": 25000,
            "max_orbit_states": 25000,
        },
    }
    monkeypatch.setattr(exact_checker_module, "ref_solve", lambda _case: answer)

    passed, detail, meta = evaluate_dual(case, answer)

    assert passed is True
    assert meta["exact"]["verdict"] == "PASS"
    assert meta["independent"]["verdict"] == "PASS"


def test_dual_evaluator_rejects_unknown_that_asserts_false(monkeypatch: pytest.MonkeyPatch):
    case = {
        "id": "c024_case_budget",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]],
    }
    expected = {
        "id": "c024_case_budget",
        "status": "UNKNOWN",
        "refusal_code": "ORBIT_SEARCH_BUDGET_EXHAUSTED",
        "witness": {
            "kind": "orbit_search_budget_exhausted",
            "states_visited": 25000,
            "max_orbit_states": 25000,
        },
    }
    forged = dict(expected, equivalent=False)
    monkeypatch.setattr(exact_checker_module, "ref_solve", lambda _case: expected)

    passed, detail, meta = evaluate_dual(case, forged)

    assert passed is False
    assert meta["exact"]["verdict"] == "FAIL"
    assert meta["independent"]["verdict"] == "FAIL"
