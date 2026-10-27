"""Dual Evaluator for C012 (Cellular Sheaf Cohomology H^0 and H^1).

Coordinates Checker 1 (Exact Algebraic) and Checker 2 (Independent Echelon),
asserting 100% agreement and raising CheckerDisagreementError fail-closed
upon any divergence.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .sheaf_algebraic_checker import verify_algebraic_certificate
    from .sheaf_echelon_checker import verify_echelon_certificate
except (ImportError, ValueError):
    try:
        from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_algebraic_checker import verify_algebraic_certificate
        from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_echelon_checker import verify_echelon_certificate
    except (ImportError, ValueError):
        from sheaf_algebraic_checker import verify_algebraic_certificate
        from sheaf_echelon_checker import verify_echelon_certificate


class CheckerDisagreementError(Exception):
    """Raised fail-closed when Checker 1 and Checker 2 produce divergent verdicts."""


def evaluate_dual(case: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluates case against both Checker 1 and Checker 2, reporting concordance."""
    case_id = (
        str(case.get("id") or case.get("case_id") or "unknown_case")
        if isinstance(case, Mapping)
        else "malformed_case"
    )

    ok1, msg1 = verify_algebraic_certificate(case, result)
    ok2, msg2 = verify_echelon_certificate(case, result)

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
        "authority_effect": "None",
    }


def assert_dual_agreement(case: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluates dual checkers and raises CheckerDisagreementError if they diverge."""
    eval_res = evaluate_dual(case, result)
    if not eval_res["agreement"]:
        raise CheckerDisagreementError(
            f"Checker disagreement on case {eval_res['case_id']}: "
            f"Checker 1 returned {eval_res['checker1']['valid']} ({eval_res['checker1']['message']}), "
            f"Checker 2 returned {eval_res['checker2']['valid']} ({eval_res['checker2']['message']})"
        )
    return eval_res
