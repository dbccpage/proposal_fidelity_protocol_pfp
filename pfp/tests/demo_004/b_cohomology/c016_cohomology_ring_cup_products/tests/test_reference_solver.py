"""Test reference solver bounds, degree validations, and refusals."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.solver import (
    solve,
)


def test_invalid_degrees_sum_gt_4():
    case = {
        "id": "deg_sum_gt_4",
        "X": {"maximal_simplices": [[0, 1, 2]]},
        "Y": {"maximal_simplices": [[0, 1, 2]]},
        "deg_p": 3,
        "deg_q": 2,
    }
    res, tracer = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "INVALID_DEGREES"


def test_dimension_out_of_bounds_simplex():
    case = {
        "id": "dim_gt_4",
        "X": {"maximal_simplices": [[0, 1, 2, 3, 4, 5]]},
        "Y": {"maximal_simplices": [[0, 1, 2]]},
        "deg_p": 1,
        "deg_q": 1,
    }
    res, tracer = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "MALFORMED_INPUT"


def test_out_of_scope_betti_mismatch():
    case = {
        "id": "betti_diff",
        "X": {"maximal_simplices": [[0, 1], [1, 2], [2, 0]]},  # S1: b1=1
        "Y": {"maximal_simplices": [[0, 1, 2]]},  # triangle 2-simplex: contractible, b1=0
        "deg_p": 1,
        "deg_q": 0,
    }
    res, tracer = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["reason"] == "BETTI_MISMATCH"
    assert res["witness"]["degree"] == "1"
