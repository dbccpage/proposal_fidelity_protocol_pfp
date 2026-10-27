"""Dual Evaluator for C015: Persistent Homology Barcodes.

Evaluates both Checker 1 (algebraic certificate) and Checker 2 (independent reduction).
Both must pass for consensus.
"""

from __future__ import annotations

from typing import Any

from .f2_algebraic_checker import check_algebraic_certificate
from .independent_checker import check_independent_persistence


def evaluate_dual(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    ok1, reason1 = check_algebraic_certificate(case, result)
    ok2, reason2 = check_independent_persistence(case, result)

    details = {
        "algebraic_checker": {"passed": ok1, "reason": reason1},
        "independent_checker": {"passed": ok2, "reason": reason2},
    }

    if ok1 and ok2:
        return True, "Dual consensus achieved (both checkers passed)", details
    return False, f"Dual check failed: C1={reason1} | C2={reason2}", details
