"""
Reference Solver for Challenge C054: Exact Linear Systems with Inconsistency Witnesses
Exact arbitrary-precision rational Gauss-Jordan elimination with RREF,
nullspace basis extraction, certified rank minors, and inconsistency witnesses.
"""

from fractions import Fraction
from typing import Any, Dict, List


def parse_fraction(val: Any) -> Fraction:
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        val = val.strip()
        if "/" in val:
            parts = val.split("/")
            if len(parts) != 2:
                raise ValueError(f"Malformed fraction string: {val}")
            num = int(parts[0].strip())
            den = int(parts[1].strip())
            if den == 0:
                raise ZeroDivisionError("Fraction denominator cannot be zero")
            return Fraction(num, den)
        return Fraction(int(val), 1)
    raise TypeError(f"Unsupported entry type: {type(val)}")


def format_fraction(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def compute_determinant(M: List[List[Fraction]]) -> Fraction:
    n = len(M)
    if n == 0:
        return Fraction(1, 1)
    if any(len(row) != n for row in M):
        raise ValueError("Matrix must be square to compute determinant")

    # Gaussian elimination for determinant
    A = [list(row) for row in M]
    det = Fraction(1, 1)
    for col in range(n):
        pivot_idx = -1
        for r in range(col, n):
            if A[r][col] != 0:
                pivot_idx = r
                break
        if pivot_idx == -1:
            return Fraction(0, 1)
        if pivot_idx != col:
            A[col], A[pivot_idx] = A[pivot_idx], A[col]
            det = -det
        pivot = A[col][col]
        det *= pivot
        for r in range(col + 1, n):
            if A[r][col] != 0:
                factor = A[r][col] / pivot
                for c in range(col + 1, n):
                    A[r][c] -= factor * A[col][c]
    return det


def solve_linear_system(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("case_id", "unknown")

    # 1. Structural schema validation
    if "A" not in case or "b" not in case:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MISSING_REQUIRED_KEYS"},
        }

    A_raw = case["A"]
    b_raw = case["b"]

    if not isinstance(A_raw, list) or not isinstance(b_raw, list):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_TYPE_NOT_LIST"},
        }

    m = len(A_raw)

    # Edge case: m == 0
    if m == 0:
        if len(b_raw) != 0:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "ROW_COUNT_MISMATCH_WITH_B"},
            }
        # 0 rows, let n be 0 by convention
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "CONSISTENT",
            "x": [],
            "null_basis": [],
            "rank": 0,
            "rank_rows": [],
            "rank_cols": [],
            "null_rows": [],
        }

    # Check row lengths
    if not isinstance(A_raw[0], list):
        return {"case_id": case_id, "status": "OUT_OF_SCOPE", "witness": {"reason": "ROW_NOT_LIST"}}
    n = len(A_raw[0])

    for r_idx, row in enumerate(A_raw):
        if not isinstance(row, list) or len(row) != n:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "ROW_LENGTH_MISMATCH", "row": r_idx},
            }

    if len(b_raw) != m:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "B_LENGTH_MISMATCH", "expected": m, "actual": len(b_raw)},
        }

    # Parse numbers
    try:
        A = [[parse_fraction(cell) for cell in row] for row in A_raw]
        b = [parse_fraction(val) for val in b_raw]
    except Exception as e:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "PARSE_ERROR", "details": str(e)},
        }

    # Edge case: n == 0
    if n == 0:
        if all(val == 0 for val in b):
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "CONSISTENT",
                "x": [],
                "null_basis": [],
                "rank": 0,
                "rank_rows": [],
                "rank_cols": [],
                "null_rows": [],
            }
        else:
            # Inconsistent: find first non-zero entry in b
            y = [Fraction(0, 1)] * m
            for i, val in enumerate(b):
                if val != 0:
                    y[i] = Fraction(1, 1)
                    break
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "INCONSISTENT",
                "y": [format_fraction(v) for v in y],
            }

    # 2. General Gauss-Jordan elimination on augmented matrix [A | b | I_m]
    # Matrix size: m rows, (n + 1 + m) cols
    M_aug: List[List[Fraction]] = []
    for i in range(m):
        row = list(A[i]) + [b[i]] + [Fraction(1, 1) if j == i else Fraction(0, 1) for j in range(m)]
        M_aug.append(row)

    pivot_cols: List[int] = []
    pivot_rows_orig: List[int] = []
    row_mapping = list(range(m))

    curr_row = 0
    for col in range(n):
        if curr_row >= m:
            break
        # Find pivot in column col at or below curr_row
        piv = -1
        for r in range(curr_row, m):
            if M_aug[r][col] != 0:
                piv = r
                break
        if piv == -1:
            continue

        # Swap rows if needed
        if piv != curr_row:
            M_aug[curr_row], M_aug[piv] = M_aug[piv], M_aug[curr_row]
            row_mapping[curr_row], row_mapping[piv] = row_mapping[piv], row_mapping[curr_row]

        pivot_val = M_aug[curr_row][col]
        # Scale pivot row
        for c in range(col, n + 1 + m):
            M_aug[curr_row][c] /= pivot_val

        # Eliminate from all other rows
        for r in range(m):
            if r != curr_row and M_aug[r][col] != 0:
                factor = M_aug[r][col]
                for c in range(col, n + 1 + m):
                    M_aug[r][c] -= factor * M_aug[curr_row][c]

        pivot_cols.append(col)
        pivot_rows_orig.append(row_mapping[curr_row])
        curr_row += 1

    # 3. Check for inconsistency:
    # Any row with all zeros in A-block but non-zero in b-block
    for r in range(curr_row, m):
        if M_aug[r][n] != 0:
            # INCONSISTENT
            # Multiplier vector y is located in columns n+1 to n+m
            y = [M_aug[r][n + 1 + j] for j in range(m)]
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "INCONSISTENT",
                "y": [format_fraction(v) for v in y],
            }

    # 4. System is CONSISTENT
    rank = len(pivot_cols)
    rank_rows = list(pivot_rows_orig)
    rank_cols = list(pivot_cols)

    # Particular solution x
    x = [Fraction(0, 1)] * n
    for r_idx, col in enumerate(pivot_cols):
        x[col] = M_aug[r_idx][n]

    # Nullspace basis N
    free_cols = [c for c in range(n) if c not in pivot_cols]
    null_basis_cols: List[List[Fraction]] = []

    for f_col in free_cols:
        v = [Fraction(0, 1)] * n
        v[f_col] = Fraction(1, 1)
        for r_idx, col in enumerate(pivot_cols):
            v[col] = -M_aug[r_idx][f_col]
        null_basis_cols.append(v)

    # Minor for null_basis is simply rows corresponding to free_cols
    null_rows = list(free_cols)

    # Formatted null basis (list of column vectors)
    formatted_null_basis = [[format_fraction(v[i]) for i in range(n)] for v in null_basis_cols]

    return {
        "case_id": case_id,
        "status": "SOLVED",
        "kind": "CONSISTENT",
        "x": [format_fraction(val) for val in x],
        "null_basis": formatted_null_basis,
        "rank": rank,
        "rank_rows": rank_rows,
        "rank_cols": rank_cols,
        "null_rows": null_rows,
    }
