"""Dual Evaluator for C011 (Cycle-Rank Ladder: Minimum-L1 Coboundary Repair).

Coordinates Checker 1 (Exact LP Dual Circulation Certifier) and
Checker 2 (Exact Primal Potential & Coboundary Certifier).
Enforces 100% agreement between both independent checkers.
Trips CHECKER_DISAGREEMENT if the checkers produce contradictory verdicts.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .circulation_checker import verify_circulation_certificate
    from .potential_checker import verify_potential_certificate
except (ImportError, ValueError):
    try:
        from c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.circulation_checker import verify_circulation_certificate
        from c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.potential_checker import verify_potential_certificate
    except (ImportError, ValueError):
        from c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.circulation_checker import (
            verify_circulation_certificate,
        )
        from c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.potential_checker import (
            verify_potential_certificate,
        )


class CheckerDisagreementError(Exception):
    """Raised when Checker 1 and Checker 2 disagree on a certificate."""


def evaluate_dual(case: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluates both Checker 1 and Checker 2 on a case and result.

    Returns dict with keys:
    - verdict: 'PASS' | 'FAIL' | 'CHECKER_DISAGREEMENT'
    - case_id: str
    - agreement: bool
    - checker1: {'valid': bool, 'message': str}
    - checker2: {'valid': bool, 'message': str}
    """
    case_id = (
        str(case.get("id") or "unknown_case") if isinstance(case, Mapping) else "malformed_case"
    )

    ok1, msg1 = verify_circulation_certificate(case, result)
    ok2, msg2 = verify_potential_certificate(case, result)

    agreement = ok1 == ok2
    if ok1 and ok2:
        verdict = "PASS"
    elif (not ok1) and (not ok2):
        verdict = "FAIL"
    else:
        verdict = "CHECKER_DISAGREEMENT"

    return {
        "verdict": verdict,
        "case_id": case_id,
        "agreement": agreement,
        "checker1": {"valid": ok1, "message": msg1},
        "checker2": {"valid": ok2, "message": msg2},
    }


def assert_dual_agreement(case: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluates dual checkers and asserts that they agree.

    Raises CheckerDisagreementError on disagreement.
    Returns the evaluation summary.
    """
    eval_res = evaluate_dual(case, result)
    if not eval_res["agreement"]:
        raise CheckerDisagreementError(
            f"Checker disagreement on case {eval_res['case_id']}: "
            f"Checker 1 returned {eval_res['checker1']['valid']} ({eval_res['checker1']['message']}), "
            f"Checker 2 returned {eval_res['checker2']['valid']} ({eval_res['checker2']['message']})"
        )
    return eval_res
