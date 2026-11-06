"""
Exact Checker for Challenge C054: Exact Linear Systems with Inconsistency Witnesses.
Validates exact algebraic identities:
- Inconsistency: y^T A = 0 and y^T b != 0
- Consistency: A x = b, A N = 0, det A[R, K] != 0, det N[J, :] != 0, rank + dim(N) = n
- Strict canonical fraction string verification.

Correction, 2026-09-29: answer entries use the package's single canonical
rational parser ("4/1", "0/1", floats and whitespace are refused); a reply that
is not a JSON object, or index lists holding strings, Booleans or floats, are
typed rejections instead of exceptions.
"""

from fractions import Fraction
from typing import Any, Dict, List, Tuple

from .canonical_rational import parse_canonical_rational


def parse_fraction_strict(val: Any) -> Fraction:
    return parse_canonical_rational(val)


def _index_list_problem(values: Any, length: int, bound: int, name: str) -> str:
    if not isinstance(values, list) or len(values) != length:
        return f"{name} must be a list of length {length}"
    if any(type(v) is not int for v in values):
        return f"{name} entries must be integers (not strings, Booleans or floats)"
    if len(set(values)) != length:
        return f"{name} contains duplicates"
    if any(v < 0 or v >= bound for v in values):
        return f"{name} index out of bounds"
    return ""


def parse_matrix_lenient(A_raw: Any) -> Tuple[bool, List[List[Fraction]], int, int, str]:
    if not isinstance(A_raw, list):
        return False, [], 0, 0, "A is not a list"
    m = len(A_raw)
    if m == 0:
        return True, [], 0, 0, ""
    if not isinstance(A_raw[0], list):
        return False, [], 0, 0, "Row 0 is not a list"
    n = len(A_raw[0])
    A: List[List[Fraction]] = []
    for r_idx, row in enumerate(A_raw):
        if not isinstance(row, list) or len(row) != n:
            return False, [], 0, 0, f"Row {r_idx} length mismatch"
        row_fracs = []
        for cell in row:
            try:
                if isinstance(cell, int):
                    row_fracs.append(Fraction(cell, 1))
                elif isinstance(cell, str):
                    if "/" in cell:
                        p = cell.split("/")
                        row_fracs.append(Fraction(int(p[0]), int(p[1])))
                    else:
                        row_fracs.append(Fraction(int(cell), 1))
                else:
                    return False, [], 0, 0, f"Non-numeric cell at row {r_idx}: {cell}"
            except Exception as e:
                return False, [], 0, 0, f"Parse error at row {r_idx}: {e}"
        A.append(row_fracs)
    return True, A, m, n, ""


def compute_minor_det(M: List[List[Fraction]]) -> Fraction:
    n = len(M)
    if n == 0:
        return Fraction(1, 1)
    A = [list(row) for row in M]
    det = Fraction(1, 1)
    for col in range(n):
        piv = -1
        for r in range(col, n):
            if A[r][col] != 0:
                piv = r
                break
        if piv == -1:
            return Fraction(0, 1)
        if piv != col:
            A[col], A[piv] = A[piv], A[col]
            det = -det
        pivot_val = A[col][col]
        det *= pivot_val
        for r in range(col + 1, n):
            if A[r][col] != 0:
                factor = A[r][col] / pivot_val
                for c in range(col + 1, n):
                    A[r][c] -= factor * A[col][c]
    return det


def check_exact(case: Dict[str, Any], result: Any) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, f"Result must be a JSON object, got {type(result).__name__}"
    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"Case ID mismatch: expected {case.get('case_id')}, got {result.get('case_id')}",
        )

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    valid_A, A, m, n, err_A = parse_matrix_lenient(case.get("A"))
    b_raw = case.get("b")
    valid_b = isinstance(b_raw, list) and len(b_raw) == m
    if valid_b:
        try:
            b = [
                Fraction(int(x.split("/")[0]), int(x.split("/")[1]))
                if "/" in str(x)
                else Fraction(int(x), 1)
                for x in b_raw
            ]
        except Exception:
            valid_b = False
            b = []
    else:
        b = []

    is_truly_valid = valid_A and valid_b

    if status == "OUT_OF_SCOPE":
        if is_truly_valid:
            return False, "Solver claimed OUT_OF_SCOPE on a valid linear system"
        witness = result.get("witness")
        if not isinstance(witness, dict) or "reason" not in witness:
            return False, "Missing witness.reason for OUT_OF_SCOPE"
        return True, "Valid OUT_OF_SCOPE"

    if not is_truly_valid:
        return False, f"Expected OUT_OF_SCOPE, but solver returned {status}"

    kind = result.get("kind")
    if kind not in ("CONSISTENT", "INCONSISTENT"):
        return False, f"Invalid kind: {kind}"

    if kind == "INCONSISTENT":
        y_raw = result.get("y")
        if not isinstance(y_raw, list) or len(y_raw) != m:
            return (
                False,
                f"Invalid y vector length: expected {m}, got {len(y_raw) if isinstance(y_raw, list) else type(y_raw)}",
            )
        try:
            y = [parse_fraction_strict(entry) for entry in y_raw]
        except Exception as e:
            return False, f"Invalid fraction string in y: {e}"

        # Check y^T A == 0
        for j in range(n):
            col_dot = sum(y[i] * A[i][j] for i in range(m))
            if col_dot != 0:
                return False, f"y^T A != 0 at col {j}: dot = {col_dot}"

        # Check y^T b != 0
        b_dot = sum(y[i] * b[i] for i in range(m))
        if b_dot == 0:
            return False, "y^T b == 0; y fails to witness inconsistency"

        return True, "Valid INCONSISTENT witness"

    if kind == "CONSISTENT":
        x_raw = result.get("x")
        if not isinstance(x_raw, list) or len(x_raw) != n:
            return (
                False,
                f"Invalid x vector length: expected {n}, got {len(x_raw) if isinstance(x_raw, list) else type(x_raw)}",
            )
        try:
            x = [parse_fraction_strict(entry) for entry in x_raw]
        except Exception as e:
            return False, f"Invalid fraction string in x: {e}"

        # Check A x == b
        for i in range(m):
            row_dot = sum(A[i][j] * x[j] for j in range(n))
            if row_dot != b[i]:
                return False, f"A x != b at row {i}: got {row_dot}, expected {b[i]}"

        # Check rank
        rank = result.get("rank")
        if type(rank) is not int or rank < 0 or rank > min(m, n):
            return False, f"Invalid rank: {rank}"

        # Check rank_rows and rank_cols
        rank_rows = result.get("rank_rows")
        rank_cols = result.get("rank_cols")
        problem = _index_list_problem(rank_rows, rank, m, "rank_rows") or _index_list_problem(
            rank_cols, rank, n, "rank_cols"
        )
        if problem:
            return False, problem

        # Check minor A[R, K] determinant
        minor_A = [[A[r][c] for c in rank_cols] for r in rank_rows]
        det_A_minor = compute_minor_det(minor_A)
        if det_A_minor == 0:
            return False, "Rank certificate minor A[R, K] is singular (det=0)"

        # Check null_basis
        null_basis_raw = result.get("null_basis")
        expected_null_dim = n - rank
        if not isinstance(null_basis_raw, list) or len(null_basis_raw) != expected_null_dim:
            return (
                False,
                f"null_basis length mismatch: expected {expected_null_dim}, got {len(null_basis_raw) if isinstance(null_basis_raw, list) else type(null_basis_raw)}",
            )

        null_basis: List[List[Fraction]] = []
        for vec_idx, vec_raw in enumerate(null_basis_raw):
            if not isinstance(vec_raw, list) or len(vec_raw) != n:
                return False, f"null_basis vector {vec_idx} length mismatch: expected {n}"
            try:
                vec = [parse_fraction_strict(entry) for entry in vec_raw]
                null_basis.append(vec)
            except Exception as e:
                return False, f"Invalid fraction string in null_basis vector {vec_idx}: {e}"

        # Check A N == 0
        for vec_idx, vec in enumerate(null_basis):
            for i in range(m):
                dot = sum(A[i][j] * vec[j] for j in range(n))
                if dot != 0:
                    return False, f"A * null_basis[{vec_idx}] != 0 at row {i}: dot = {dot}"

        # Check null_rows minor
        null_rows = result.get("null_rows")
        problem = _index_list_problem(null_rows, expected_null_dim, n, "null_rows")
        if problem:
            return False, problem

        # Minor N[J, :] where null_basis is list of columns
        minor_N = [
            [null_basis[col_idx][r] for col_idx in range(expected_null_dim)] for r in null_rows
        ]
        det_N_minor = compute_minor_det(minor_N)
        if det_N_minor == 0:
            return False, "Null basis certificate minor N[J, :] is singular (det=0)"

        return True, "Valid CONSISTENT certificate"

    return False, f"Unhandled kind: {kind}"
