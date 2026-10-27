"""Dual Evaluator for C019: Combines Checker 1 and Checker 2."""

from __future__ import annotations

from typing import Any

from .h2_obstruction_checker import check_h2_certificate
from .independent_checker import check_independent_h2


def evaluate_dual(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    ok1, reason1 = check_h2_certificate(case, result)
    ok2, reason2 = check_independent_h2(case, result)

    details = {
        "checker1_passed": ok1,
        "checker1_reason": reason1,
        "checker2_passed": ok2,
        "checker2_reason": reason2,
    }

    if ok1 and ok2:
        return True, "Both checkers passed", details
    elif not ok1:
        return False, f"Checker 1 rejected: {reason1}", details
    else:
        return False, f"Checker 2 rejected: {reason2}", details
