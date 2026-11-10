"""Frozen reference solver for C050: Equational Theorem Proving with Checkable Rewrite Proofs."""

from typing import Any, Dict

from .countermodel import find_countermodel
from .prover import prove_equational


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Solve an equational theorem proving challenge case."""
    case_id = case.get("case_id", "eq_unknown")
    axioms = case.get("axioms")
    goal = case.get("goal")

    trace = ["C", "R"]

    # 1. Input Validation (OUT_OF_SCOPE check)
    if axioms is None or not isinstance(axioms, list):
        trace.append("M")
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": "Axioms must be a list of equation pairs",
            "trace": trace,
        }

    if goal is None or not isinstance(goal, list) or len(goal) != 2:
        trace.append("M")
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": "Goal must be a 2-element list [s, t]",
            "trace": trace,
        }

    parsed_axioms = []
    for ax_idx, ax in enumerate(axioms):
        if not isinstance(ax, list) or len(ax) != 2:
            trace.append("M")
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": f"Axiom {ax_idx} is not a valid [l, r] pair",
                "trace": trace,
            }
        parsed_axioms.append((ax[0], ax[1]))

    parsed_goal = (goal[0], goal[1])

    trace.append("I")

    # 2. Attempt Proof Search
    res_proof = prove_equational(parsed_axioms, parsed_goal, max_depth=5, max_nodes=2000)
    if res_proof is not None:
        trace.extend(["E", "T"])
        res_proof["case_id"] = case_id
        res_proof["trace"] = trace
        return res_proof

    # 3. Attempt Countermodel Search
    res_cm = find_countermodel(parsed_axioms, parsed_goal, max_size=3)
    if res_cm is not None:
        trace.extend(["E", "T"])
        res_cm["case_id"] = case_id
        res_cm["trace"] = trace
        return res_cm

    trace.append("T")
    return {
        "case_id": case_id,
        "status": "UNKNOWN",
        "code": "CASE_BUDGET_EXHAUSTED",
        "trace": trace,
    }
