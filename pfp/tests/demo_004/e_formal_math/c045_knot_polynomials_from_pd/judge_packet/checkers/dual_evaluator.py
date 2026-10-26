# AuthorityEffect: None.
"""
Dual Evaluator for C045.
Executes both exact_checker and independent_checker to ensure 100% consensus.
"""

from typing import Any, Dict, Tuple

from .exact_checker import check_exact
from .independent_checker import check_independent


def evaluate_dual(case: Dict[str, Any], ans: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    ok_exact, msg_exact = check_exact(case, ans)
    ok_indep, msg_indep = check_independent(case, ans)

    receipt = {
        "case_id": case.get("case_id"),
        "exact_passed": ok_exact,
        "exact_msg": msg_exact,
        "independent_passed": ok_indep,
        "independent_msg": msg_indep,
        "consensus": (ok_exact and ok_indep),
    }

    if ok_exact and ok_indep:
        return True, f"Consensus PASS: {msg_exact}", receipt
    elif not ok_exact and not ok_indep:
        return False, f"Consensus FAIL: exact: {msg_exact} | independent: {msg_indep}", receipt
    else:
        return (
            False,
            f"Checker DIVERGENCE: exact ({ok_exact}): {msg_exact} | independent ({ok_indep}): {msg_indep}",
            receipt,
        )
