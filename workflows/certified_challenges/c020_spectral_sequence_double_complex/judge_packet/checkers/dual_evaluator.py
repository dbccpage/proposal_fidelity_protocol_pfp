"""Dual evaluator combining exact and independent checkers for C020."""

from __future__ import annotations

from typing import Any

from .exact_checker import check_certificate as exact_check
from .independent_checker import independent_check_certificate as indep_check


def evaluate_dual(case: dict[str, Any], cert: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    res1 = exact_check(case, cert)
    res2 = indep_check(case, cert)

    ok1 = res1.get("verdict") == "PASS"
    ok2 = res2.get("verdict") == "PASS"

    if ok1 and ok2:
        return True, "PASSED_BOTH_CHECKERS", {"exact": res1, "independent": res2}

    reasons = []
    if not ok1:
        reasons.append(f"Exact: {res1.get('reason')}")
    if not ok2:
        reasons.append(f"Independent: {res2.get('reason')}")

    return False, " | ".join(reasons), {"exact": res1, "independent": res2}
