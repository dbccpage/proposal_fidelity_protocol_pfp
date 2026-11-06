"""Test reference solver lattice bounds, boundary options, and refusals."""

from __future__ import annotations

from c017_nonabelian_lattice_holonomy.reference_solver.groups import (
    make_s3,
)
from c017_nonabelian_lattice_holonomy.reference_solver.solver import (
    solve,
)

S3 = make_s3()


def test_lattice_size_out_of_bounds_gt_12():
    case = {"id": "L_gt_12", "L": 15, "M": 3, "boundary": "open", "group": S3, "edges": {}}
    res, tracer = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "LATTICE_SIZE_OUT_OF_BOUNDS"


def test_lattice_size_out_of_bounds_lt_2():
    case = {"id": "M_lt_2", "L": 3, "M": 1, "boundary": "open", "group": S3, "edges": {}}
    res, tracer = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "LATTICE_SIZE_OUT_OF_BOUNDS"


def test_invalid_boundary():
    case = {"id": "bad_bnd", "L": 3, "M": 3, "boundary": "mobius", "group": S3, "edges": {}}
    res, tracer = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal"] == "MALFORMED_INPUT"


def test_out_of_scope_inverse_mismatch():
    case = {
        "id": "inv_mismatch",
        "L": 3,
        "M": 3,
        "boundary": "open",
        "group": S3,
        "edges": {
            "0,0->0,1": "r",
            "0,1->0,0": "s",  # r^-1 is r2!
        },
    }
    res, tracer = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["reason"] == "INVERSE_MISMATCH"
