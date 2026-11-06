# AuthorityEffect: None.
"""Tests for Exact Checker, Independent Checker, and Dual Evaluator."""

from c025_mub_prime_power_exact.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c025_mub_prime_power_exact.judge_packet.checkers.exact_checker import (
    verify_exact,
)
from c025_mub_prime_power_exact.judge_packet.checkers.independent_checker import (
    verify_independent,
)
from c025_mub_prime_power_exact.reference_solver.solver import (
    solve,
)


def test_dual_checkers_valid_cases():
    test_cases = [
        {"case_id": "test_d2", "dimension": 2, "num_bases": 3},
        {"case_id": "test_d3", "dimension": 3, "num_bases": 4},
        {"case_id": "test_d4", "dimension": 4, "num_bases": 5},
        {"case_id": "test_d5", "dimension": 5, "num_bases": 6},
        {"case_id": "test_d7", "dimension": 7, "num_bases": 8},
        {"case_id": "test_d8", "dimension": 8, "num_bases": 9},
        {"case_id": "test_d9", "dimension": 9, "num_bases": 10},
        {"case_id": "test_d6_k3", "dimension": 6, "num_bases": 3},
        {"case_id": "test_d10_k3", "dimension": 10, "num_bases": 3},
    ]
    for case in test_cases:
        ans = solve(case)
        passed, msg, _ = evaluate_dual(case, ans)
        assert passed, f"Dual evaluation failed for {case['case_id']}: {msg}"


def test_dual_checkers_refusal_cases():
    # d=6, k=4 open problem
    case_open = {"case_id": "open_6", "dimension": 6, "num_bases": 4}
    ans_open = solve(case_open)
    p_exact, _, _ = verify_exact(case_open, ans_open)
    p_indep, _, _ = verify_independent(case_open, ans_open)
    assert p_exact and p_indep
    p_dual, msg, _ = evaluate_dual(case_open, ans_open)
    assert p_dual

    # out of scope k > d + 1
    case_oos = {"case_id": "oos_3", "dimension": 3, "num_bases": 5}
    ans_oos = solve(case_oos)
    p_exact, _, _ = verify_exact(case_oos, ans_oos)
    p_indep, _, _ = verify_independent(case_oos, ans_oos)
    assert p_exact and p_indep
    p_dual, msg, _ = evaluate_dual(case_oos, ans_oos)
    assert p_dual
