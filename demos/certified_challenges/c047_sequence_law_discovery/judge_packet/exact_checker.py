"""Exact checker for C047: Recurrence and Generating-Function Discovery.
Verifies recurrence replay over both given and held-out terms, leading root conditions,
and Bareiss determinant certificates for absence proofs.
"""

from fractions import Fraction
from typing import Any, Dict, Tuple

from ..reference_solver.holonomic_guesser import (
    build_system_matrix,
    leading_poly_has_integer_root_ge,
)
from ..reference_solver.rational_linalg import bareiss_determinant


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Check a candidate solution against the case specification."""
    if not isinstance(result, dict):
        return False, "Result must be a JSON object"

    case_id = case.get("case_id")
    if result.get("case_id") != case_id:
        return False, f"Case ID mismatch: expected {case_id}, got {result.get('case_id')}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    r_max = int(case.get("r_max", 8))
    d_max = int(case.get("d_max", 3))

    # 1. OUT_OF_SCOPE check
    if status == "OUT_OF_SCOPE":
        witness = result.get("witness")
        if not isinstance(witness, dict):
            return False, "OUT_OF_SCOPE requires witness dict"
        if witness.get("reason") != "NON_INTEGER_TERM":
            return False, f"Unexpected witness reason: {witness.get('reason')}"
        idx = witness.get("index")
        if not isinstance(idx, int) or idx < 0 or idx >= len(case.get("terms", [])):
            return False, f"Invalid witness index: {idx}"
        val_str = str(case["terms"][idx])
        try:
            int(val_str)
            return False, f"Witness index {idx} contains valid integer '{val_str}', not invalid"
        except ValueError:
            return True, "Valid OUT_OF_SCOPE witness"

    # 2. Check if case actually contains non-integer terms (if so, SOLVED is invalid)
    has_non_int = False
    for t_str in case.get("terms", []):
        try:
            int(t_str)
        except ValueError:
            has_non_int = True
            break
    if has_non_int:
        return False, "Case contains non-integer term, solver should have returned OUT_OF_SCOPE"

    if status == "UNKNOWN":
        return False, "Solver failed with UNKNOWN"

    kind = result.get("kind")
    if kind not in ("RECURRENCE", "NONE_WITHIN_BOUNDS"):
        return False, f"Invalid kind for SOLVED: {kind}"

    # 3. RECURRENCE check
    if kind == "RECURRENCE":
        polys = result.get("polys")
        if not isinstance(polys, list) or len(polys) < 2:
            return False, "polys must be a list of at least 2 polynomial coefficient lists"

        r = len(polys) - 1
        if r > r_max:
            return False, f"Recurrence order {r} exceeds r_max {r_max}"

        start = result.get("start", 0)
        if not isinstance(start, int) or start < 0:
            return False, f"Invalid start index: {start}"

        for i, p in enumerate(polys):
            if not isinstance(p, list) or len(p) == 0:
                return False, f"polys[{i}] must be a non-empty list of string coefficients"
            deg = len(p) - 1
            if deg > d_max:
                return False, f"Polynomial degree {deg} exceeds d_max {d_max}"
            for c_str in p:
                if not isinstance(c_str, str):
                    return False, f"Polynomial coefficient must be string, got {type(c_str)}"
                try:
                    int(c_str)
                except ValueError:
                    return False, f"Coefficient string '{c_str}' is not an integer"

        # Check leading poly is non-zero
        p_r = polys[-1]
        if all(int(c) == 0 for c in p_r):
            return False, f"Leading polynomial p_{r} cannot be identically zero"

        # Check all polynomials are not trivial all-zero
        if all(all(int(c) == 0 for c in p) for p in polys):
            return False, "All polynomials are zero"

        # Check leading root condition
        if leading_poly_has_integer_root_ge(p_r, start):
            return False, f"Leading polynomial p_{r} has integer root at or beyond start={start}"

        # Replay recurrence over given terms AND held-out terms
        all_terms_raw = list(case.get("terms", [])) + list(case.get("held_out_terms", []))
        all_terms = [Fraction(int(x)) for x in all_terms_raw]
        N_tot = len(all_terms)

        int_polys = [[int(x) for x in p] for p in polys]

        for n in range(start, N_tot - r):
            total = Fraction(0)
            for i in range(r + 1):
                p_val = Fraction(0)
                n_pow = Fraction(1)
                for j in range(len(int_polys[i])):
                    p_val += Fraction(int_polys[i][j]) * n_pow
                    n_pow *= Fraction(n)
                total += p_val * all_terms[n + i]

            if total != 0:
                is_held_out = n >= len(case.get("terms", [])) - r
                tag = "held-out" if is_held_out else "prefix"
                return False, f"Recurrence violated at {tag} index n={n}: total residual is {total}"

        return True, "Valid RECURRENCE certified across all given and held-out terms"

    # 4. NONE_WITHIN_BOUNDS check
    if kind == "NONE_WITHIN_BOUNDS":
        order = result.get("order")
        degree = result.get("degree")
        if order != r_max or degree != d_max:
            return (
                False,
                f"Absence proof must certify bounds ({r_max}, {d_max}), got ({order}, {degree})",
            )

        minor_rows = result.get("minor_rows")
        u = (r_max + 1) * (d_max + 1)
        if not isinstance(minor_rows, list) or len(minor_rows) != u:
            return (
                False,
                f"minor_rows must contain exactly {u} row indices, got {len(minor_rows) if isinstance(minor_rows, list) else type(minor_rows)}",
            )

        if any(not isinstance(r_idx, int) for r_idx in minor_rows):
            return False, "All elements in minor_rows must be integer row indices"

        start_range = result.get("start_range", [0, 0])
        max_start = start_range[1] if isinstance(start_range, list) and len(start_range) >= 2 else 0
        if any(r_idx < max_start for r_idx in minor_rows):
            return False, f"All minor rows must be >= max start {max_start}"

        terms = [Fraction(int(x)) for x in case.get("terms", [])]
        mat, row_indices = build_system_matrix(terms, r_max, d_max, start=0)

        row_map = {idx: row for idx, row in zip(row_indices, mat)}
        minor_matrix = []
        for r_idx in minor_rows:
            if r_idx not in row_map:
                return False, f"Row index {r_idx} is out of bounds for given terms"
            minor_matrix.append(row_map[r_idx])

        det = bareiss_determinant(minor_matrix)
        if det == 0:
            return False, f"Minor matrix at rows {minor_rows} is singular (det = 0)"

        return True, f"Valid NONE_WITHIN_BOUNDS certified (det = {det})"

    return False, f"Unknown kind: {kind}"
