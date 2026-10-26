# AuthorityEffect: None.
"""
Dual Evaluator for C030: Tensor-Network Contraction Order Under a Cost Bound.

Runs both ExactChecker and IndependentChecker and asserts 100% consensus.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

try:
    from .exact_checker import verify_exact
    from .independent_checker import verify_independent
except (ImportError, ValueError):
    from exact_checker import verify_exact
    from independent_checker import verify_independent


def evaluate_dual(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates both checkers on (case, answer) and requires full consensus.
    """
    try:
        exact_ok, exact_msg, exact_det = verify_exact(case, answer)
        indep_ok, indep_msg, indep_det = verify_independent(case, answer)
    except Exception as exc:
        reason = f"CHECKER_EXCEPTION: {type(exc).__name__}: {exc}"
        return False, reason, {"error": reason}

    if exact_ok != indep_ok:
        return (
            False,
            (
                f"DUAL CHECKER DISAGREEMENT: exact={exact_ok} ({exact_msg}), "
                f"independent={indep_ok} ({indep_msg})"
            ),
            {
                "exact": exact_det,
                "independent": indep_det,
            },
        )

    if not exact_ok:
        return False, f"Both checkers rejected answer: {exact_msg}", exact_det

    return True, f"Dual consensus passed: {exact_msg}", exact_det
