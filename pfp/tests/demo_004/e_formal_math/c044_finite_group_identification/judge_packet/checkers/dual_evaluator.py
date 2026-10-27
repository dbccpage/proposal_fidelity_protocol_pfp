# AuthorityEffect: None.
"""
Dual Evaluator for C044 Finite Group Identification.
Runs exact checker and independent checker and fails closed on disagreement.
"""

from typing import Any, Dict, Tuple

from pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.judge_packet.checkers.exact_checker import (
    check_exact,
)
from pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.judge_packet.checkers.independent_checker import (
    independent_check,
)


def evaluate_dual(case: dict, answer: dict) -> Tuple[bool, str, Dict[str, Any]]:
    ok_exact, msg_exact = check_exact(case, answer)
    ok_indep, msg_indep = independent_check(case, answer)

    disagree = ok_exact != ok_indep
    receipt = {
        "exact_pass": ok_exact,
        "exact_msg": msg_exact,
        "independent_pass": ok_indep,
        "independent_msg": msg_indep,
        "checkers_agree": not disagree,
    }

    if disagree:
        return False, f"DUAL CHECKER DISAGREEMENT: exact={ok_exact} vs indep={ok_indep}", receipt

    if not ok_exact:
        return False, f"REJECTED: {msg_exact}", receipt

    return True, f"ACCEPTED: {msg_exact}", receipt
