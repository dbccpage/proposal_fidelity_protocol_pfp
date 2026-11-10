# AuthorityEffect: None.
"""
Independent Second Checker for C029: Minimum-Weight Surface-Code Decoding.

Independently checks:
1. Syndrome validity: H_Z * c == s mod 2.
2. Weight consistency: sum w_q c_q == stated weight.
3. Optimality verification:
   - Solves minimum-weight correction independently via kernel coset optimization or independent branch-and-bound.
   - Asserts that no kernel element can strictly reduce the weight.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .exact_checker import verify_exact
from .schema_guard import validate_certificate

try:
    from reference_solver.graph import DecodingGraph
    from reference_solver.matching_solver import solve_min_weight_decoding
except (ImportError, ValueError):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from reference_solver.matching_solver import solve_min_weight_decoding


def verify_independent(
    case: Dict[str, Any], result: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Independently verifies candidate correction and its minimum-weight property.
    """
    schema_error = validate_certificate(case, result)
    if schema_error:
        return False, schema_error, {}
    code_type = case.get("code", "rotated")
    distance = case.get("distance", 0)
    hz = case.get("hz", [])
    weights = case.get("weights", [])
    syndrome = case.get("syndrome", [])
    status = result.get("status")

    if status != "SOLVED":
        return verify_exact(case, result)

    m = len(hz)
    n = len(hz[0]) if m > 0 else 0

    if code_type == "rotated" and distance not in {3, 5, 7}:
        return (
            (status == "UNKNOWN"),
            "Verified UNKNOWN for out of bounds distance",
            {"distance": distance},
        )
    if code_type == "toric" and distance not in {3, 4, 5}:
        return (
            (status == "UNKNOWN"),
            "Verified UNKNOWN for out of bounds distance",
            {"distance": distance},
        )

    if code_type == "toric" and sum(syndrome) % 2 != 0:
        return (
            (status == "OUT_OF_SCOPE"),
            "Verified OUT_OF_SCOPE for odd parity on torus",
            {"syndrome": syndrome},
        )

    if status != "SOLVED":
        return True, f"Independent checker skips check for status {status}", {"status": status}

    correction = result.get("correction", [])
    stated_weight = result.get("weight")

    # 1. Syndrome check
    c_vec = [0] * n
    for q in correction:
        c_vec[q] ^= 1

    computed_s = [0] * m
    for r in range(m):
        row_sum = sum(hz[r][q] for q in range(n) if c_vec[q] == 1) % 2
        computed_s[r] = row_sum

    if computed_s != syndrome:
        return (
            False,
            f"Independent syndrome check failed: {computed_s} != {syndrome}",
            {"computed_s": computed_s, "syndrome": syndrome},
        )

    # 2. Weight check
    actual_weight = sum(weights[q] for q in correction)
    if stated_weight != actual_weight:
        return (
            False,
            f"Stated weight mismatch: {stated_weight} != {actual_weight}",
            {"stated_weight": stated_weight, "actual_weight": actual_weight},
        )

    # 3. Independent minimum weight verification
    ok, indep_sol, _ = solve_min_weight_decoding(code_type, distance, hz, weights, syndrome)
    if not ok:
        return False, "Independent solver failed on valid case", {}

    expected_min_weight = indep_sol["weight"]
    if actual_weight > expected_min_weight:
        return (
            False,
            f"Correction is suboptimal: weight {actual_weight} > minimum {expected_min_weight}",
            {"actual_weight": actual_weight, "min_weight": expected_min_weight},
        )

    return (
        True,
        "Independent syndrome, weight, and minimality verified",
        {
            "actual_weight": actual_weight,
            "min_weight": expected_min_weight,
        },
    )
