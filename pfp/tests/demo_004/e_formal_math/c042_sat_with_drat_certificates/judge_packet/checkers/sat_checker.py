# AuthorityEffect: None.
"""
Problem-level SAT Checker for C042.
Directly verifies problem-level certificates without reference to solver traces.
Enforces strict int type discipline: type(v) is int (rejects bool True/False).
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.family_solvers import (
    check_problem_solution,
)


def check_sat_submission(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Checks a SAT solution certificate against problem case."""
    sol = answer.get("solution")
    if not isinstance(sol, dict):
        return False, "SAT answer missing 'solution' dict", {}

    ok, msg = check_problem_solution(case, sol)
    if not ok:
        return False, f"Problem solution check failed: {msg}", {}

    return True, f"Problem solution verified: {msg}", {"solution_valid": True}
