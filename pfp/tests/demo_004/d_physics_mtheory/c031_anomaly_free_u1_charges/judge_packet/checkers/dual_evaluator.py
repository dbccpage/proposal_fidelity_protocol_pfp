"""Dual Evaluator & Agreement Enforcer for C031.

Coordinates Checker 1 (Exact Algebraic Certifier) and Checker 2 (Independent MITM Engine),
asserting 100% agreement between both checkers.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .u1_algebraic_checker import verify_chiral_u1_certificate
from .u1_mitm_checker import verify_mitm_certificate


class CheckerDisagreementError(Exception):
    """Raised when Checker 1 and Checker 2 produce contradictory verdicts."""


def evaluate_dual(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
    ground_truth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Runs Checker 1 and Checker 2 and verifies agreement with defense-in-depth status tracking."""
    ok1, msg1 = verify_chiral_u1_certificate(case, result, ground_truth=ground_truth)
    ok2, msg2 = verify_mitm_certificate(case, result, ground_truth=ground_truth)

    agreement = ok1 == ok2
    if ok1 and ok2:
        verdict = "PASS"
    elif (not ok1) and (not ok2):
        verdict = "FAIL"
    else:
        verdict = "CHECKER_DISAGREEMENT"

    case_id = str(case.get("id") or case.get("case_id") or "unknown")
    status = str(result.get("status", "UNKNOWN"))
    is_refusal = status in {"UNKNOWN", "OUT_OF_SCOPE"}
    valid_refusal = is_refusal and ok1 and ok2
    solved = (status == "SOLVED") and ok1 and ok2

    return {
        "verdict": verdict,
        "case_id": case_id,
        "agreement": agreement,
        "status": status,
        "is_refusal": is_refusal,
        "valid_refusal": valid_refusal,
        "solved": solved,
        "checker1": {"valid": ok1, "message": msg1},
        "checker2": {"valid": ok2, "message": msg2},
    }


def assert_dual_agreement(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
    ground_truth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluates dual checkers and asserts agreement fail-closed.

    Raises CheckerDisagreementError if Checker 1 and Checker 2 diverge.
    """
    eval_res = evaluate_dual(case, result, ground_truth=ground_truth)
    if not eval_res["agreement"]:
        cid = eval_res["case_id"]
        c1_val = eval_res["checker1"]["valid"]
        c1_msg = eval_res["checker1"]["message"]
        c2_val = eval_res["checker2"]["valid"]
        c2_msg = eval_res["checker2"]["message"]
        raise CheckerDisagreementError(
            f"Checker divergence on case {cid!r}: "
            f"Checker 1 returned {c1_val} ({c1_msg}), "
            f"Checker 2 returned {c2_val} ({c2_msg})"
        )
    return eval_res
