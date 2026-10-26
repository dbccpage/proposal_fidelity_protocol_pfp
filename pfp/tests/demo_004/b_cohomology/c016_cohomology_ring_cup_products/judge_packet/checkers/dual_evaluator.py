"""Dual Evaluator for C016: Cohomology Ring Cup Products.

Combines Checker 1 (algebraic certificate checker) and Checker 2 (independent cup product evaluator).
"""

from __future__ import annotations

from typing import Any

from .algebraic_cup_checker import check_algebraic_cup_certificate
from .independent_checker import check_independent_cup_products


def evaluate_dual(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    ok1, reason1 = check_algebraic_cup_certificate(case, result)
    ok2, reason2 = check_independent_cup_products(case, result)

    details = {
        "algebraic_checker": {"passed": ok1, "reason": reason1},
        "independent_checker": {"passed": ok2, "reason": reason2},
    }

    if ok1 and ok2:
        return True, "Dual consensus achieved (both checkers passed)", details
    return False, f"Dual check failed: C1={reason1} | C2={reason2}", details
