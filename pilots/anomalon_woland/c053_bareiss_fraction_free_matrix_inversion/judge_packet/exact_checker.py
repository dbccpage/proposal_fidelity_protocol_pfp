"""Exact algebraic certificate checker for C053: Bareiss Fraction-Free Matrix Inversion.

Correction, 2026-09-29: the determinant is now pinned to det(A), computed here
by fraction-free Bareiss elimination. Before, A = I with det "5", adjugate 5I
and inverse I passed, because A adj(A) = det I and inv = adj / det hold for
any scalar det. Answer entries must be canonical rationals ("4", not "4/1").
"""

from fractions import Fraction
from typing import Any, Dict, List, Tuple

from .canonical_rational import parse_canonical_rational


def parse_strict_frac_str(val: Any) -> Fraction:
    return parse_canonical_rational(val)


def bareiss_determinant(A: List[List[Fraction]]) -> Fraction:
    """det(A) by fraction-free Bareiss elimination on integers (rows scaled by their LCD)."""
    n = len(A)
    scale = Fraction(1)
    M: List[List[int]] = []
    for row in A:
        lcd = 1
        for x in row:
            lcd = lcd * x.denominator // _gcd(lcd, x.denominator)
        scale /= lcd
        M.append([int(x * lcd) for x in row])
    sign = 1
    prev = 1
    for k in range(n - 1):
        if M[k][k] == 0:
            swap = next((r for r in range(k + 1, n) if M[r][k] != 0), None)
            if swap is None:
                return Fraction(0)
            M[k], M[swap] = M[swap], M[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                M[i][j] = (M[i][j] * M[k][k] - M[i][k] * M[k][j]) // prev
        prev = M[k][k]
    return scale * sign * M[n - 1][n - 1]


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def parse_input_frac(val: Any) -> Fraction:
    s = str(val).strip()
    if "/" in s:
        p, q = s.split("/", 1)
        return Fraction(int(p), int(q))
    return Fraction(int(s), 1)


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(result, dict) or not isinstance(case, dict):
        return False, "Case and result must be dictionaries"

    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"Mismatched case_id: expected {case.get('case_id')}, got {result.get('case_id')}",
        )

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    # Check if input case is out of scope / malformed
    is_malformed = False
    malformed_reason = ""
    matrix_raw = case.get("matrix")
    if not isinstance(matrix_raw, list) or len(matrix_raw) == 0:
        is_malformed = True
        malformed_reason = "EMPTY_OR_NON_LIST_MATRIX"
    else:
        n = len(matrix_raw)
        for r_idx, row in enumerate(matrix_raw):
            if not isinstance(row, list) or len(row) != n:
                is_malformed = True
                malformed_reason = "NOT_SQUARE"
                break
            for c_idx, val in enumerate(row):
                try:
                    parse_input_frac(val)
                except Exception:
                    is_malformed = True
                    malformed_reason = "NON_NUMERIC_ENTRY"
                    break
            if is_malformed:
                break

    if is_malformed:
        if status == "OUT_OF_SCOPE":
            return True, f"Correctly rejected out-of-scope case: {malformed_reason}"
        return (
            False,
            f"Case was malformed ({malformed_reason}), but solver returned status={status}",
        )

    if status == "OUT_OF_SCOPE":
        return False, "Solver claimed OUT_OF_SCOPE on a valid square matrix"

    if status == "UNKNOWN":
        return False, "Solver returned UNKNOWN status"

    kind = result.get("kind")
    if kind not in ("INVERTIBLE", "SINGULAR"):
        return False, f"Invalid kind: {kind}"

    n = len(matrix_raw)
    A = [[parse_input_frac(val) for val in row] for row in matrix_raw]

    if kind == "INVERTIBLE":
        if "det" not in result or "adjugate" not in result or "inverse" not in result:
            return False, "Missing mandatory fields for INVERTIBLE ('det', 'adjugate', 'inverse')"

        try:
            det_val = parse_strict_frac_str(result["det"])
        except Exception as e:
            return False, f"Invalid determinant format: {e}"

        if det_val == 0:
            return False, "Determinant cannot be zero for INVERTIBLE kind"
        true_det = bareiss_determinant(A)
        if det_val != true_det:
            return False, f"Determinant mismatch: claimed {det_val}, det(A) = {true_det}"

        adj_raw = result["adjugate"]
        inv_raw = result["inverse"]

        if not isinstance(adj_raw, list) or len(adj_raw) != n:
            return False, f"Adjugate matrix row count mismatch: expected {n}"
        if not isinstance(inv_raw, list) or len(inv_raw) != n:
            return False, f"Inverse matrix row count mismatch: expected {n}"

        # Parse adjugate and inverse
        try:
            adj: List[List[Fraction]] = []
            for r_idx, row in enumerate(adj_raw):
                if not isinstance(row, list) or len(row) != n:
                    return False, f"Adjugate row {r_idx} length mismatch: expected {n}"
                adj.append([parse_strict_frac_str(val) for val in row])

            inv: List[List[Fraction]] = []
            for r_idx, row in enumerate(inv_raw):
                if not isinstance(row, list) or len(row) != n:
                    return False, f"Inverse row {r_idx} length mismatch: expected {n}"
                inv.append([parse_strict_frac_str(val) for val in row])
        except Exception as e:
            return False, f"Invalid entry format in adjugate or inverse: {e}"

        # Verify 1: A * adj(A) == det(A) * I
        for r in range(n):
            for c in range(n):
                dot = sum(A[r][k] * adj[k][c] for k in range(n))
                expected = det_val if r == c else Fraction(0, 1)
                if dot != expected:
                    return (
                        False,
                        f"A * adj(A) violated at ({r}, {c}): dot={dot}, expected={expected}",
                    )

        # Verify 2: adj(A) * A == det(A) * I
        for r in range(n):
            for c in range(n):
                dot = sum(adj[r][k] * A[k][c] for k in range(n))
                expected = det_val if r == c else Fraction(0, 1)
                if dot != expected:
                    return (
                        False,
                        f"adj(A) * A violated at ({r}, {c}): dot={dot}, expected={expected}",
                    )

        # Verify 3: A * A^(-1) == I
        for r in range(n):
            for c in range(n):
                dot = sum(A[r][k] * inv[k][c] for k in range(n))
                expected = Fraction(1, 1) if r == c else Fraction(0, 1)
                if dot != expected:
                    return (
                        False,
                        f"A * A^(-1) violated at ({r}, {c}): dot={dot}, expected={expected}",
                    )

        # Verify 4: inv[r][c] == adj[r][c] / det
        for r in range(n):
            for c in range(n):
                if inv[r][c] != adj[r][c] / det_val:
                    return False, f"Relation inv = adj/det violated at ({r}, {c})"

        return (
            True,
            f"Verified exact invertible certificate: det={det_val}, A*adj(A)=det*I, A*inv=I",
        )

    elif kind == "SINGULAR":
        if "det" not in result or "null_vector" not in result:
            return False, "Missing mandatory fields for SINGULAR ('det', 'null_vector')"

        try:
            det_val = parse_strict_frac_str(result["det"])
        except Exception as e:
            return False, f"Invalid determinant format for SINGULAR: {e}"

        if det_val != 0:
            return False, f"Determinant must be zero for SINGULAR kind, got {det_val}"

        null_vec_raw = result["null_vector"]
        if not isinstance(null_vec_raw, list):
            return False, "null_vector must be a list"
        if len(null_vec_raw) != n:
            return (
                False,
                f"null_vector dimension mismatch: expected length {n}, got {len(null_vec_raw)}",
            )

        try:
            v = [parse_strict_frac_str(val) for val in null_vec_raw]
        except Exception as e:
            return False, f"Invalid entry format in null_vector: {e}"

        # Check non-triviality: v != 0
        if all(val == 0 for val in v):
            return False, "null_vector cannot be the all-zero vector"

        # Verify A * v == 0
        for r in range(n):
            dot = sum(A[r][c] * v[c] for c in range(n))
            if dot != 0:
                return False, f"A * null_vector != 0 at row {r}: dot={dot}"

        return True, "Verified exact singular certificate: det=0, A*null_vector=0 with v != 0"

    return False, f"Unhandled kind: {kind}"
