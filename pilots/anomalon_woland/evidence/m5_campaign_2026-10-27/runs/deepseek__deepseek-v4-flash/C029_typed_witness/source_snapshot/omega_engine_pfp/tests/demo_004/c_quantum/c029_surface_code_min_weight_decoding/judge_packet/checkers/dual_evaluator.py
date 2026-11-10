# AuthorityEffect: None.
"""
Dual Evaluator for C029: Minimum-Weight Surface-Code Decoding.

Combines Exact Checker and Independent Checker, enforcing 100% agreement.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

try:
    from .exact_checker import verify_exact
    from .independent_checker import verify_independent
except (ImportError, ValueError):
    try:
        from judge_packet.checkers.exact_checker import verify_exact
        from judge_packet.checkers.independent_checker import verify_independent
    except (ImportError, ValueError):
        from exact_checker import verify_exact
        from independent_checker import verify_independent


def evaluate_dual(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates candidate answer with dual independent checkers.
    Requires 100% agreement.
    """
    try:
        exact_pass, exact_msg, exact_det = verify_exact(case, answer)
        indep_pass, indep_msg, indep_det = verify_independent(case, answer)
    except Exception as exc:
        reason = f"CHECKER_EXCEPTION: {type(exc).__name__}: {exc}"
        return False, reason, {"error": reason}

    details = {
        "exact_checker": {"passed": exact_pass, "message": exact_msg, "details": exact_det},
        "independent_checker": {"passed": indep_pass, "message": indep_msg, "details": indep_det},
    }

    if exact_pass != indep_pass:
        return (
            False,
            f"DUAL CHECKER DISAGREEMENT: exact={exact_pass} ({exact_msg}), independent={indep_pass} ({indep_msg})",
            details,
        )

    if not exact_pass:
        return False, f"REJECTED: {exact_msg}", details

    return True, f"DUAL CONSENSUS: {exact_msg}", details
