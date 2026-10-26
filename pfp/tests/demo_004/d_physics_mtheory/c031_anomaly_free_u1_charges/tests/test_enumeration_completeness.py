"""C031: an enumeration must be checked for completeness for every n, not only n <= 8.

Counterexample named by this test: for n = 9 or 10 (within the declared enumerate bounds
n <= 10, Q <= 12) both checkers skipped the completeness comparison when no ground truth
was passed, so the constant answer {"count": 0, "solutions": []} passed.
"""

from __future__ import annotations

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.u1_algebraic_checker import (
    verify_chiral_u1_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.u1_mitm_checker import (
    _mitm_enumerate,
    verify_mitm_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.reference_solver.solver import (
    solve,
)

CHECKERS = (verify_chiral_u1_certificate, verify_mitm_certificate)


def _case(n: int, bound: int) -> dict[str, object]:
    return {"case_id": f"enum_{n}_{bound}", "query": "enumerate", "n": n, "bound": bound}


@pytest.mark.parametrize(("n", "bound"), [(9, 5), (10, 5), (9, 12)])
def test_empty_enumeration_rejected_above_n8(n: int, bound: int) -> None:
    case = _case(n, bound)
    assert _mitm_enumerate(n, bound), "the counterexample needs a non-empty solution set"
    empty = {"id": case["case_id"], "status": "SOLVED", "count": 0, "solutions": []}
    for checker in CHECKERS:
        ok, msg = checker(case, empty)
        assert ok is False, msg
    assert evaluate_dual(case, empty)["verdict"] == "FAIL"


@pytest.mark.parametrize(("n", "bound"), [(9, 5), (10, 5)])
def test_reference_enumeration_accepted_above_n8(n: int, bound: int) -> None:
    case = _case(n, bound)
    result = solve(case)
    assert result["status"] == "SOLVED"
    for checker in CHECKERS:
        ok, msg = checker(case, result)
        assert ok is True, msg


@pytest.mark.parametrize("checker", CHECKERS)
def test_truncated_enumeration_rejected(checker) -> None:
    case = _case(9, 5)
    result = solve(case)
    truncated = dict(result)
    truncated["solutions"] = result["solutions"][:-1]
    truncated["count"] = len(truncated["solutions"])
    ok, msg = checker(case, truncated)
    assert ok is False, msg


@pytest.mark.parametrize("checker", CHECKERS)
def test_enumeration_outside_declared_bounds_fails_closed(checker) -> None:
    case = _case(11, 5)
    empty = {"id": case["case_id"], "status": "SOLVED", "count": 0, "solutions": []}
    ok, msg = checker(case, empty)
    assert ok is False, msg


@pytest.mark.parametrize("checker", CHECKERS)
def test_malformed_ground_truth_fails_closed(checker) -> None:
    case = _case(9, 5)
    empty = {"id": case["case_id"], "status": "SOLVED", "count": 0, "solutions": []}
    ok, msg = checker(case, empty, ground_truth={})
    assert ok is False, msg
