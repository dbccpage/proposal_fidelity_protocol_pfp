"""Dual Evaluator for C021 (Q40-R Stabilizer Challenge).

Coordinates Checker 1 (Exact Algebraic Symplectic Certifier) and
Checker 2 (Exact Dense Spectral LDL^H Checker over Q[i]).
Enforces 100% agreement between both independent checkers.
Trips CHECKER_DISAGREEMENT if the checkers produce contradictory verdicts.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .algebraic_checker import verify_certificate
    from .spectral_checker import secondary_numeric_check, verify_spectral_optimality
except (ImportError, ValueError):
    try:
        from c021_q40_r.judge_packet.checkers.algebraic_checker import verify_certificate
        from c021_q40_r.judge_packet.checkers.spectral_checker import (
            secondary_numeric_check,
            verify_spectral_optimality,
        )
    except (ImportError, ValueError):
        from c021_q40_r.judge_packet.checkers.algebraic_checker import (
            verify_certificate,
        )
        from c021_q40_r.judge_packet.checkers.spectral_checker import (
            secondary_numeric_check,
            verify_spectral_optimality,
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
    - secondary_numeric: {'valid': bool, 'message': str}
    """
    case_id = (
        str(case.get("id") or "unknown_case") if isinstance(case, Mapping) else "malformed_case"
    )

    ok1, msg1 = verify_certificate(case, result)
    ok2, msg2 = verify_spectral_optimality(case, result)
    ok_num, msg_num = secondary_numeric_check(case, result)

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
        "secondary_numeric": {"valid": ok_num, "message": msg_num},
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
