"""Exact checker for C048: Ternary Quadratic Forms.
Validates integer rational points and local Hilbert symbol obstruction certificates.
"""

from typing import Any, Dict, Tuple

from ..reference_solver.factorization import is_prime
from ..reference_solver.hilbert_symbol import hilbert_symbol


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify candidate solution for C048 ternary quadratic form."""
    if not isinstance(result, dict):
        return False, "Result must be a JSON object"

    case_id = case.get("case_id")
    if result.get("case_id") != case_id:
        return False, f"Case ID mismatch: expected {case_id}, got {result.get('case_id')}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    # 1. OUT_OF_SCOPE check
    if status == "OUT_OF_SCOPE":
        # Must witness non-integer coefficient
        raw_vals = [case.get("a"), case.get("b"), case.get("c")]
        has_non_int = False
        for rv in raw_vals:
            try:
                int(str(rv))
            except (ValueError, TypeError):
                has_non_int = True
                break
        if not has_non_int:
            return False, "Coefficients are valid integers, cannot be OUT_OF_SCOPE"
        return True, "Valid OUT_OF_SCOPE verified"

    # If status is SOLVED, verify input coefficients are valid integers
    try:
        a = int(str(case["a"]))
        b = int(str(case["b"]))
        c = int(str(case["c"]))
    except (ValueError, TypeError):
        return (
            False,
            "Case contains non-integer coefficient, solver should have returned OUT_OF_SCOPE",
        )

    if status == "UNKNOWN":
        return False, "Solver failed with UNKNOWN"

    kind = result.get("kind")
    if kind not in ("RATIONAL_POINT", "LOCAL_OBSTRUCTION"):
        return False, f"Invalid kind for SOLVED: {kind}"

    # 2. RATIONAL_POINT verification
    if kind == "RATIONAL_POINT":
        x_str = result.get("x")
        y_str = result.get("y")
        z_str = result.get("z")

        if x_str is None or y_str is None or z_str is None:
            return False, "RATIONAL_POINT requires x, y, and z coordinates"

        if isinstance(x_str, bool) or isinstance(y_str, bool) or isinstance(z_str, bool):
            return False, "Coordinates must not be booleans"

        try:
            x = int(str(x_str))
            y = int(str(y_str))
            z = int(str(z_str))
        except (ValueError, TypeError):
            return False, "Coordinates must be integer strings"

        if x == 0 and y == 0 and z == 0:
            return False, "Trivial zero solution (0, 0, 0) is invalid"

        eval_val = a * x**2 + b * y**2 + c * z**2
        if eval_val != 0:
            return False, f"Equation violated: a*x^2 + b*y^2 + c*z^2 = {eval_val} != 0"

        return True, f"Valid RATIONAL_POINT verified: ({x}, {y}, {z})"

    # 3. LOCAL_OBSTRUCTION verification
    if kind == "LOCAL_OBSTRUCTION":
        place_str = result.get("place")
        if not place_str:
            return False, "LOCAL_OBSTRUCTION requires place"

        # Edge case: zero coefficients admit trivial points, no obstruction possible
        if a == 0 or b == 0 or c == 0:
            return (
                False,
                "Form with zero coefficient has non-trivial rational points, cannot be obstructed",
            )

        u = -a * c
        w = -b * c

        if place_str == "inf":
            if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
                return True, "Valid LOCAL_OBSTRUCTION at inf (definite sign)"
            if u < 0 and w < 0:
                return True, "Valid LOCAL_OBSTRUCTION at inf (Hilbert symbol -1)"
            return False, "Form is indefinite and has real points, inf is not an obstruction"

        try:
            p = int(str(place_str))
        except (ValueError, TypeError):
            return False, f"Invalid place identifier: {place_str}"

        if p < 2:
            return False, f"Place must be >= 2, got {p}"

        if not is_prime(p):
            return False, f"Claimed place {p} is composite, must be prime"

        sym = hilbert_symbol(u, w, p)
        if sym != -1:
            return False, f"Hilbert symbol (-ac, -bc)_{p} is {sym}, not -1"

        return True, f"Valid LOCAL_OBSTRUCTION verified at place {p}"

    return False, f"Unknown kind: {kind}"
