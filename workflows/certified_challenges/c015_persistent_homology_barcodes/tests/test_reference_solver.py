"""Test reference solver behavior, bounds checks, and refusal codes."""

from __future__ import annotations

from c015_persistent_homology_barcodes.reference_solver.solver import (
    solve,
)


def test_simplex_count_out_of_bounds():
    huge_case = {
        "id": "huge_simplices",
        "simplices": [{"dim": 0, "vertices": [i], "val": "0"} for i in range(2005)],
    }
    res, tracer = solve(huge_case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "SIMPLEX_COUNT_OUT_OF_BOUNDS"


def test_dimension_out_of_bounds():
    dim4_case = {
        "id": "dim4_simplex",
        "simplices": [
            {"dim": 0, "vertices": [0], "val": "0"},
            {"dim": 0, "vertices": [1], "val": "0"},
            {"dim": 0, "vertices": [2], "val": "0"},
            {"dim": 0, "vertices": [3], "val": "0"},
            {"dim": 0, "vertices": [4], "val": "0"},
            {"dim": 4, "vertices": [0, 1, 2, 3, 4], "val": "1"},
        ],
    }
    res, tracer = solve(dim4_case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "DIMENSION_OUT_OF_BOUNDS"


def test_non_monotonic_filtration():
    non_mono = {
        "id": "non_mono",
        "simplices": [
            {"dim": 0, "vertices": [0], "val": "1"},
            {"dim": 0, "vertices": [1], "val": "0"},
            {"dim": 1, "vertices": [0, 1], "val": "2"},
        ],
    }
    res, tracer = solve(non_mono)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "NON_MONOTONIC_FILTRATION"


def test_out_of_scope_face_violation():
    bad_order = {
        "id": "bad_order",
        "simplices": [
            {"dim": 0, "vertices": [0], "val": "0"},
            {"dim": 1, "vertices": [0, 1], "val": "1"},  # vertex 1 missing earlier!
        ],
    }
    res, tracer = solve(bad_order)
    assert res["status"] == "OUT_OF_SCOPE"
    assert "witness" in res
    assert res["witness"]["missing_earlier_face"] == "[1]"


def test_malformed_input_missing_simplices():
    res, tracer = solve({"id": "malformed"})
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "MALFORMED_INPUT"
