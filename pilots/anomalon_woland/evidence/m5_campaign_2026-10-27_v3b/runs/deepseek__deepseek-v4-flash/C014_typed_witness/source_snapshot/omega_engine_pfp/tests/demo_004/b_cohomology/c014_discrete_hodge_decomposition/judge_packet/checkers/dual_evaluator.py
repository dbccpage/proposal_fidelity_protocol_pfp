"""Dual Evaluator for C014 Judge Packet.

Runs both Checker 1 (Exact Algebraic & Orthogonality Certifier) and
Checker 2 (Independent Elimination & Betti 1 Certifier)
and verifies 100% agreement between both checks.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from .hodge_algebraic_checker import verify_algebraic_certificate
from .hodge_elimination_checker import verify_elimination_certificate


def evaluate_dual(case: Any, result: Any) -> dict[str, Any]:
    """Evaluates case and candidate result through both independent checkers."""
    case_id = (
        str(case.get("id") or case.get("case_id") or "unnamed_case")
        if isinstance(case, dict)
        else "unnamed_case"
    )

    # 1. Run Checker 1
    ok1, msg1 = verify_algebraic_certificate(case, result)

    # 2. Run Checker 2
    ok2, msg2 = verify_elimination_certificate(case, result)

    # 3. Enforce 100% agreement
    agreement = ok1 == ok2
    verdict = "PASS" if (ok1 and ok2) else "FAIL"

    return {
        "verdict": verdict,
        "case_id": case_id,
        "agreement": agreement,
        "checker1": {"valid": ok1, "message": msg1},
        "checker2": {"valid": ok2, "message": msg2},
        "authority_effect": "None",
    }


def assert_dual_agreement(case: Any, result: Any) -> dict[str, Any]:
    """Asserts that both checkers pass and agree 100% on case and result."""
    eval_res = evaluate_dual(case, result)
    assert eval_res["agreement"] is True, (
        f"Checker disagreement on {eval_res['case_id']}: "
        f"Checker1={eval_res['checker1']}, Checker2={eval_res['checker2']}"
    )
    assert eval_res["verdict"] == "PASS", (
        f"Dual evaluation failed on {eval_res['case_id']}: "
        f"Checker1={eval_res['checker1']}, Checker2={eval_res['checker2']}"
    )
    return eval_res
