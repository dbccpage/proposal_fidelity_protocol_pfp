"""Exact checker for C050: Equational Theorem Proving with Checkable Rewrite Proofs.
Validates step-by-step equational rewrite chains and finite countermodels.
"""

from typing import Any, Dict, Tuple

from ..reference_solver.countermodel import check_countermodel
from ..reference_solver.terms import rewrite_step


def is_malformed_case(case: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if case input has invalid syntax."""
    axioms = case.get("axioms")
    if not isinstance(axioms, list):
        return True, "Axioms must be a list"
    for idx, ax in enumerate(axioms):
        if not isinstance(ax, list) or len(ax) != 2:
            return True, f"Axiom {idx} is not a valid 2-element list [l, r]"
    goal = case.get("goal")
    if not isinstance(goal, list) or len(goal) != 2:
        return True, "Goal must be a 2-element list [s, t]"
    return False, "Case syntax is valid"


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify candidate solution for C050."""
    if not isinstance(result, dict):
        return False, "Result must be a JSON object"

    case_id = case.get("case_id")
    if result.get("case_id") != case_id:
        return False, f"Case ID mismatch: expected {case_id}, got {result.get('case_id')}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    malformed, malformed_msg = is_malformed_case(case)

    # 1. OUT_OF_SCOPE check
    if status == "OUT_OF_SCOPE":
        if malformed:
            return True, f"Valid OUT_OF_SCOPE verified: {malformed_msg}"
        return False, "Case has valid syntax, cannot be OUT_OF_SCOPE"

    if malformed:
        return (
            False,
            f"Case has malformed syntax ({malformed_msg}), solver should have returned OUT_OF_SCOPE",
        )

    if status == "UNKNOWN":
        return False, "Solver failed with UNKNOWN"

    kind = result.get("kind")
    if kind not in ("PROOF", "COUNTERMODEL"):
        return False, f"Invalid kind for SOLVED: {kind}"

    axioms = [(ax[0], ax[1]) for ax in case["axioms"]]
    goal = (case["goal"][0], case["goal"][1])

    # 2. PROOF Verification
    if kind == "PROOF":
        steps = result.get("steps")
        if not isinstance(steps, list):
            return False, "PROOF requires a list of rewrite steps"

        curr = goal[0]

        for s_idx, step in enumerate(steps):
            if not isinstance(step, dict):
                return False, f"Step {s_idx} must be a dictionary"

            ax_idx = step.get("axiom")
            direction = step.get("dir")
            pos = step.get("pos")
            subst = step.get("subst")
            expected_res = step.get("result")

            if ax_idx is None or not isinstance(ax_idx, int) or not (0 <= ax_idx < len(axioms)):
                return False, f"Step {s_idx}: invalid axiom index {ax_idx}"
            if direction not in ("lr", "rl"):
                return False, f"Step {s_idx}: invalid direction {direction}"
            if not isinstance(pos, list) or not all(isinstance(p, int) for p in pos):
                return False, f"Step {s_idx}: invalid position path {pos}"
            if not isinstance(subst, dict):
                return False, f"Step {s_idx}: invalid substitution mapping {subst}"

            ok, next_term, err_msg = rewrite_step(curr, axioms[ax_idx], direction, pos, subst)
            if not ok:
                return False, f"Step {s_idx} failed: {err_msg}"

            if next_term != expected_res:
                return (
                    False,
                    f"Step {s_idx}: step result {expected_res} does not match computed rewrite {next_term}",
                )

            curr = next_term

        if curr != goal[1]:
            return (
                False,
                f"Proof incomplete: rewrite chain ended at {curr}, expected goal rhs {goal[1]}",
            )

        return True, f"Valid rewrite proof of {len(steps)} steps verified"

    # 3. COUNTERMODEL Verification
    if kind == "COUNTERMODEL":
        size = result.get("size")
        tables = result.get("tables")
        assignment = result.get("assignment")

        if size is None or not isinstance(size, int):
            return False, "COUNTERMODEL requires integer size"
        if tables is None or not isinstance(tables, dict):
            return False, "COUNTERMODEL requires tables dictionary"
        if assignment is None or not isinstance(assignment, dict):
            return False, "COUNTERMODEL requires assignment dictionary"

        ok, msg = check_countermodel(axioms, goal, size, tables, assignment)
        if not ok:
            return False, f"Countermodel verification failed: {msg}"

        return True, f"Valid countermodel of size {size} verified: {msg}"

    return False, f"Unhandled kind {kind}"
