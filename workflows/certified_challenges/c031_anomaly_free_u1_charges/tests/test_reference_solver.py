"""Tests validating C031 reference solver, Diophantine U(1) engine, and DDC tracer.

AuthorityEffect: None.
"""

from __future__ import annotations

from c031_anomaly_free_u1_charges.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
)
from c031_anomaly_free_u1_charges.reference_solver.diophantine_u1 import (
    canonical_representative,
    complete_chiral_u1,
    enumerate_chiral_u1,
    is_chiral,
    is_primitive,
    solve_pair,
)
from c031_anomaly_free_u1_charges.reference_solver.solver import (
    solve,
    solve_with_trace,
)


def test_n3_n4_non_existence_identity():
    """Validates that for n=3 and n=4, no chiral anomaly-free U(1) spectra exist for any bound."""
    for bound in [3, 5, 10, 12]:
        # n=3
        sol_n3 = enumerate_chiral_u1(3, bound)
        assert sol_n3 == [], f"Expected no chiral solutions for n=3, bound={bound}"

        res_n3 = solve({"id": f"enum_n3_b{bound}", "query": "enumerate", "n": 3, "bound": bound})
        assert res_n3["status"] == "SOLVED"
        assert res_n3["count"] == 0
        assert res_n3["solutions"] == []

        # n=4
        sol_n4 = enumerate_chiral_u1(4, bound)
        assert sol_n4 == [], f"Expected no chiral solutions for n=4, bound={bound}"

        res_n4 = solve({"id": f"enum_n4_b{bound}", "query": "enumerate", "n": 4, "bound": bound})
        assert res_n4["status"] == "SOLVED"
        assert res_n4["count"] == 0
        assert res_n4["solutions"] == []


def test_n5_enumeration_exact_counts():
    """Validates exact analytical enumeration counts and canonical forms for n=5."""
    # Bound 9: exactly 1 solution
    sols_b9 = enumerate_chiral_u1(5, 9)
    assert len(sols_b9) == 1
    s9 = sols_b9[0]
    assert s9 == [-9, -5, -1, 7, 8]
    assert sum(s9) == 0
    assert sum(x**3 for x in s9) == 0
    assert is_primitive(s9) is True
    assert is_chiral(s9) is True
    assert canonical_representative(s9) == s9

    # Bound 10: exactly 2 solutions
    sols_b10 = enumerate_chiral_u1(5, 10)
    assert len(sols_b10) == 2
    assert sols_b10[0] == [-10, -4, -2, 7, 9]
    assert sols_b10[1] == [-9, -5, -1, 7, 8]
    for sol in sols_b10:
        assert sum(sol) == 0
        assert sum(x**3 for x in sol) == 0
        assert is_primitive(sol) is True
        assert is_chiral(sol) is True
        assert canonical_representative(sol) == sol

    # Bound 12: exactly 2 solutions
    sols_b12 = enumerate_chiral_u1(5, 12)
    assert len(sols_b12) == 2


def test_n6_enumeration_exact_counts():
    """Validates exact analytical enumeration counts and canonical forms for n=6."""
    # Bound 5: exactly 1 solution
    sols_b5 = enumerate_chiral_u1(6, 5)
    assert len(sols_b5) == 1
    s5 = sols_b5[0]
    assert s5 == [-5, -1, -1, -1, 4, 4]
    assert sum(s5) == 0
    assert sum(x**3 for x in s5) == 0
    assert is_primitive(s5) is True
    assert is_chiral(s5) is True
    assert canonical_representative(s5) == s5

    # Bound 6: exactly 2 solutions
    sols_b6 = enumerate_chiral_u1(6, 6)
    assert len(sols_b6) == 2
    for sol in sols_b6:
        assert sum(sol) == 0
        assert sum(x**3 for x in sol) == 0
        assert is_primitive(sol) is True
        assert is_chiral(sol) is True
        assert canonical_representative(sol) == sol

    # Bound 10: exactly 2 solutions
    sols_b10 = enumerate_chiral_u1(6, 10)
    assert len(sols_b10) == 2


def test_solve_pair_quadratic_resolvent():
    """Validates O(1) quadratic resolvent solve_pair for integer charge pairs."""
    # Pair with sum = 4, cubic sum = 28 in [-10, 10] -> (1, 3) since 1+3=4, 1^3+3^3=28
    pairs = solve_pair(4, 28, -10, 10)
    assert pairs == [(1, 3)]

    # Pair with sum = 0, cubic sum = 0 in [-10, 10] -> gives non-zero charges (x, -x)
    pairs_zero = solve_pair(0, 0, -5, 5)
    assert (-1, 1) in pairs_zero

    # Incompatible sum and cubic sum (no real or integer solution)
    assert solve_pair(4, 30, -10, 10) == []
    assert solve_pair(5, 100, -10, 10) == []


def test_complete_chiral_u1_solvable_cases():
    """Validates completion of partial fixed charges into full chiral spectra."""
    # n=5, fixed=[-9, -5], bound=10 (from ex06)
    comp1 = complete_chiral_u1(5, 10, [-9, -5])
    assert comp1 is not None
    full1 = [-9, -5] + comp1
    assert len(full1) == 5
    assert sum(full1) == 0
    assert sum(x**3 for x in full1) == 0
    assert is_primitive(full1) is True
    assert is_chiral(full1) is True

    # n=6, fixed=[-5, -1, -1, 4], bound=10 (from base_comp_01)
    comp2 = complete_chiral_u1(6, 10, [-5, -1, -1, 4])
    assert comp2 is not None
    full2 = [-5, -1, -1, 4] + comp2
    assert len(full2) == 6
    assert sum(full2) == 0
    assert sum(x**3 for x in full2) == 0
    assert is_primitive(full2) is True
    assert is_chiral(full2) is True

    # n=7, fixed=[5, -8, 2], bound=10 (from ex07)
    comp3 = complete_chiral_u1(7, 10, [5, -8, 2])
    assert comp3 is not None
    full3 = [5, -8, 2] + comp3
    assert len(full3) == 7
    assert sum(full3) == 0
    assert sum(x**3 for x in full3) == 0
    assert is_primitive(full3) is True
    assert is_chiral(full3) is True

    # Large bound Q=100000 with spectator pairs (from base_comp_18)
    fixed_large = [-100000, -20000, -20000, -20000, 80000, 80000, 1, -1, 2, -2]
    comp_large = complete_chiral_u1(12, 100000, fixed_large)
    assert comp_large is not None
    full_large = fixed_large + comp_large
    assert len(full_large) == 12
    assert sum(full_large) == 0
    assert sum(x**3 for x in full_large) == 0
    assert is_primitive(full_large) is True
    assert is_chiral(full_large) is True


def test_complete_chiral_u1_no_completion_refusal():
    """Validates certified non-existence of completions."""
    # Impossible completion with vector-like traps
    comp_no = complete_chiral_u1(6, 10, [-5, 5])
    assert comp_no is None

    res_no = solve(
        {
            "id": "comp_n6_vec_trap",
            "query": "complete",
            "n": 6,
            "bound": 10,
            "fixed": [-5, 5],
        }
    )
    assert res_no["status"] == "SOLVED"
    assert res_no["completion"] is None
    assert res_no["claim"] == "NO_COMPLETION"


def test_out_of_scope_witnesses():
    """Validates structured OUT_OF_SCOPE parameter domain violation witnesses."""
    # 1. Fixed charge exceeds bound
    res1 = solve(
        {
            "id": "oos_exceed",
            "query": "complete",
            "n": 6,
            "bound": 10,
            "fixed": [15, 2],
        }
    )
    assert res1["status"] == "OUT_OF_SCOPE"
    assert res1["witness"]["kind"] == "fixed_charge_exceeds_bound"
    assert res1["witness"]["charge"] == 15
    assert res1["witness"]["bound"] == 10

    # 2. Fixed charge is zero
    res2 = solve(
        {
            "id": "oos_zero",
            "query": "complete",
            "n": 6,
            "bound": 10,
            "fixed": [0, 2],
        }
    )
    assert res2["status"] == "OUT_OF_SCOPE"
    assert res2["witness"]["kind"] == "fixed_charge_zero"
    assert res2["witness"]["charge"] == 0

    # 3. Too many fixed charges (m >= n)
    res3 = solve(
        {
            "id": "oos_too_many",
            "query": "complete",
            "n": 4,
            "bound": 10,
            "fixed": [1, 2, 3, 4],
        }
    )
    assert res3["status"] == "OUT_OF_SCOPE"
    assert res3["witness"]["kind"] == "too_many_fixed_charges"


def test_closed_refusal_codes():
    """Validates closed UNKNOWN refusal codes for structural/boundary errors."""
    # 1. N_OUT_OF_BOUNDS
    res1 = solve({"id": "ref_n_low", "query": "enumerate", "n": 0, "bound": 10})
    assert res1["status"] == "UNKNOWN"
    assert res1["refusal_code"] == "N_OUT_OF_BOUNDS"

    res1_high = solve({"id": "ref_n_high", "query": "enumerate", "n": 15, "bound": 10})
    assert res1_high["status"] == "UNKNOWN"
    assert res1_high["refusal_code"] == "N_OUT_OF_BOUNDS"

    # 2. BOUND_OUT_OF_BOUNDS
    res2 = solve({"id": "ref_b_low", "query": "enumerate", "n": 5, "bound": 0})
    assert res2["status"] == "UNKNOWN"
    assert res2["refusal_code"] == "BOUND_OUT_OF_BOUNDS"

    # 3. MALFORMED_QUERY_TYPE
    res3 = solve({"id": "ref_query", "query": "unsupported_action", "n": 5, "bound": 10})
    assert res3["status"] == "UNKNOWN"
    assert res3["refusal_code"] == "MALFORMED_QUERY_TYPE"

    # 4. MALFORMED_CASE_STRUCTURE
    res4 = solve("not_a_dictionary")
    assert res4["status"] == "UNKNOWN"
    assert res4["refusal_code"] == "MALFORMED_CASE_STRUCTURE"


def test_ddc_tracer_hash_chaining():
    """Validates DDC 8-letter trace transitions and SHA-256 parent hash chaining."""
    case = {"id": "trace_test", "query": "enumerate", "n": 5, "bound": 9}
    res, tracer = solve_with_trace(case)
    assert res["status"] == "SOLVED"
    assert len(tracer.steps) >= 5

    for s in tracer.steps:
        assert s["letter"] in VALID_DDC_LETTERS

    ok, msg = tracer.verify_integrity()
    assert ok is True
    assert msg == "VALID_CHAIN"
