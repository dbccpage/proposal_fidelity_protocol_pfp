"""Independent second checker for C053: Bareiss Fraction-Free Matrix Inversion.
Independently verifies rank, row echelon consistency, and dual identity multiplication.

Correction, 2026-09-29: answer entries are parsed by the package's single
canonical-rational parser ("4/1", "0/1", floats and whitespace are refused),
and a SINGULAR determinant must be the string "0".
"""

from fractions import Fraction
from typing import Any, Dict, List, Tuple

from .canonical_rational import parse_canonical_rational


def parse_strict_frac_str(val: Any) -> Fraction:
    return parse_canonical_rational(val)


def parse_input_frac(val: Any) -> Fraction:
    s = str(val).strip()
    if "/" in s:
        p, q = s.split("/", 1)
        return Fraction(int(p), int(q))
    return Fraction(int(s), 1)


def gaussian_rank_and_det(M: List[List[Fraction]]) -> Tuple[int, Fraction]:
    n = len(M)
    mat = [[M[r][c] for c in range(n)] for r in range(n)]
    det = Fraction(1, 1)
    rank = 0
    row = 0
    for col in range(n):
        pivot = row
        while pivot < n and mat[pivot][col] == 0:
            pivot += 1
        if pivot == n:
            continue
        if pivot != row:
            mat[row], mat[pivot] = mat[pivot], mat[row]
            det = -det
        p_val = mat[row][col]
        det *= p_val
        rank += 1
        for i in range(row + 1, n):
            factor = mat[i][col] / p_val
            for j in range(col, n):
                mat[i][j] -= factor * mat[row][j]
        row += 1
    if rank < n:
        det = Fraction(0, 1)
    return rank, det


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(result, dict) or not isinstance(case, dict):
        return False, "Case and result must be dictionaries"
    if result.get("case_id") != case.get("case_id"):
        return False, "Mismatched case_id"

    # Input validation
    matrix_raw = case.get("matrix")
    if not isinstance(matrix_raw, list) or len(matrix_raw) == 0:
        if result.get("status") == "OUT_OF_SCOPE":
            return True, "Valid OUT_OF_SCOPE for empty matrix"
        return False, "Expected OUT_OF_SCOPE"

    n = len(matrix_raw)
    is_malformed = False
    for r in matrix_raw:
        if not isinstance(r, list) or len(r) != n:
            is_malformed = True
            break
        for val in r:
            try:
                parse_input_frac(val)
            except Exception:
                is_malformed = True
                break
        if is_malformed:
            break

    if is_malformed:
        if result.get("status") == "OUT_OF_SCOPE":
            return True, "Valid OUT_OF_SCOPE for malformed input"
        return False, "Expected OUT_OF_SCOPE for non-square or invalid matrix"

    if result.get("status") != "SOLVED":
        return False, f"Expected SOLVED, got {result.get('status')}"

    A = [[parse_input_frac(matrix_raw[r][c]) for c in range(n)] for r in range(n)]
    indep_rank, indep_det = gaussian_rank_and_det(A)

    kind = result.get("kind")
    if kind == "INVERTIBLE":
        if indep_rank < n:
            return (
                False,
                f"Solver claimed INVERTIBLE but matrix is singular (rank {indep_rank} < {n})",
            )
        try:
            det_val = parse_strict_frac_str(result.get("det"))
        except Exception:
            return False, "Invalid determinant string"
        if det_val != indep_det:
            return False, f"Determinant mismatch: solver={det_val}, independent={indep_det}"

        inv_raw = result.get("inverse")
        adj_raw = result.get("adjugate")
        if not isinstance(inv_raw, list) or not isinstance(adj_raw, list):
            return False, "Inverse or adjugate is not a list"
        if len(inv_raw) != n or len(adj_raw) != n:
            return False, f"Dimension mismatch: expected {n} rows"

        try:
            inv: List[List[Fraction]] = []
            for r in inv_raw:
                if not isinstance(r, list) or len(r) != n:
                    return False, "Inverse row length mismatch"
                inv.append([parse_strict_frac_str(val) for val in r])

            adj: List[List[Fraction]] = []
            for r in adj_raw:
                if not isinstance(r, list) or len(r) != n:
                    return False, "Adjugate row length mismatch"
                adj.append([parse_strict_frac_str(val) for val in r])
        except Exception as e:
            return False, f"Parse error in inverse or adjugate: {e}"

        # Independent product checks
        for r in range(n):
            for c in range(n):
                dot_inv = sum(inv[r][k] * A[k][c] for k in range(n))
                exp_inv = Fraction(1, 1) if r == c else Fraction(0, 1)
                if dot_inv != exp_inv:
                    return False, f"inv * A != I at ({r}, {c})"

                if adj[r][c] != inv[r][c] * det_val:
                    return False, f"adj != det * inv at ({r}, {c})"

        return True, f"Independent verification passed: full rank {n}, det={det_val}"

    elif kind == "SINGULAR":
        if indep_rank == n:
            return False, f"Solver claimed SINGULAR but matrix is invertible (full rank {n})"
        if result.get("det") != "0":
            return False, "Singular matrix must have det='0'"
        null_v = result.get("null_vector")
        if not isinstance(null_v, list) or len(null_v) != n:
            return False, "Invalid null_vector dimension"
        try:
            v = [parse_strict_frac_str(x) for x in null_v]
        except Exception as e:
            return False, f"Invalid entry in null_vector: {e}"
        if all(x == 0 for x in v):
            return False, "Zero null_vector is invalid"
        for r in range(n):
            dot = sum(A[r][c] * v[c] for c in range(n))
            if dot != 0:
                return False, f"A * null_vector != 0 at row {r}"
        return True, f"Independent verification passed: singular rank {indep_rank} < {n}"

    return False, f"Unknown kind: {kind}"
