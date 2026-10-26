"""
Dual Evaluator for C043 Ramsey & Van der Waerden Constructions.
Runs both checkers and verifies 100% agreement.
"""

from typing import Any, Dict, Tuple

from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.judge_packet.checkers.independent_checker import (
    check_independent,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.judge_packet.checkers.ramsey_vdw_checker import (
    check as check_primary,
)


def evaluate_dual(case: dict, answer: dict) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates answer against both checkers.
    Fails closed if the checkers disagree.
    """
    p_ok, p_msg = check_primary(case, answer)
    i_ok, i_msg = check_independent(case, answer)

    disagreement = p_ok != i_ok
    receipt = {
        "primary_pass": p_ok,
        "primary_msg": p_msg,
        "independent_pass": i_ok,
        "independent_msg": i_msg,
        "checkers_agree": not disagreement,
        "abstained": answer.get("status") == "UNKNOWN" if isinstance(answer, dict) else False,
    }

    if disagreement:
        return (
            False,
            f"DUAL CHECKER DISAGREEMENT: primary={p_ok} ({p_msg}) vs independent={i_ok} ({i_msg})",
            receipt,
        )

    if not p_ok:
        return False, f"REJECTED: {p_msg}", receipt

    return True, f"ACCEPTED: {p_msg}", receipt
