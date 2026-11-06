"""
Independent Second Checker for Challenge C054.
Constructed with an alternate rational solver engine to independently determine
system consistency, ground truth rank, and certify solver witnesses.

Correction, 2026-09-29: answer entries use the package's single canonical
rational parser; the 0 x 0 system is checked like any other instead of
accepting any SOLVED reply; index lists must hold integers.
"""

from fractions import Fraction
from typing import Any, Dict, List, Tuple

from .canonical_rational import parse_canonical_rational


def _parse_f_strict(val: Any) -> Fraction:
    return parse_canonical_rational(val)


def _ints_in_range(values: Any, length: int, bound: int) -> bool:
    return (
        isinstance(values, list)
        and len(values) == length
        and all(type(v) is int and 0 <= v < bound for v in values)
        and len(set(values)) == length
    )


def _parse_f_lenient(val: Any) -> Fraction:
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        val = val.strip()
        if "/" in val:
            p = val.split("/")
            return Fraction(int(p[0]), int(p[1]))
        return Fraction(int(val), 1)
    raise ValueError(f"Bad entry: {val}")


def independent_rref_rank(matrix: List[List[Fraction]]) -> Tuple[int, List[int]]:
    if not matrix or not matrix[0]:
        return 0, []
    m = len(matrix)
    n = len(matrix[0])
    A = [list(row) for row in matrix]
    pivots = []
    r = 0
    for c in range(n):
        if r >= m:
            break
        piv = None
        for i in range(r, m):
            if A[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        A[r], A[piv] = A[piv], A[r]
        pv = A[r][c]
        A[r] = [x / pv for x in A[r]]
        for i in range(m):
            if i != r and A[i][c] != 0:
                f = A[i][c]
                A[i] = [A[i][k] - f * A[r][k] for k in range(n)]
        pivots.append(c)
        r += 1
    return len(pivots), pivots


def independent_det(M: List[List[Fraction]]) -> Fraction:
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
        pv = A[col][col]
        det *= pv
        for r in range(col + 1, n):
            if A[r][col] != 0:
                factor = A[r][col] / pv
                for c in range(col + 1, n):
                    A[r][c] -= factor * A[col][c]
    return det


def independent_check(case: Dict[str, Any], result: Any) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a JSON object"
    try:
        if result.get("case_id") != case.get("case_id"):
            return False, "Case ID mismatch"
        status = result.get("status")

        A_raw = case.get("A")
        b_raw = case.get("b")

        # Validate case syntax
        if not isinstance(A_raw, list) or not isinstance(b_raw, list):
            return (
                (True, "Valid rejection")
                if status == "OUT_OF_SCOPE"
                else (False, "Should be OUT_OF_SCOPE")
            )

        m = len(A_raw)
        if m > 0 and not isinstance(A_raw[0], list):
            return (
                (True, "Valid rejection")
                if status == "OUT_OF_SCOPE"
                else (False, "Should be OUT_OF_SCOPE")
            )
        n = len(A_raw[0]) if m > 0 else 0
        if any(not isinstance(row, list) or len(row) != n for row in A_raw) or len(b_raw) != m:
            return (
                (True, "Valid rejection")
                if status == "OUT_OF_SCOPE"
                else (False, "Should be OUT_OF_SCOPE")
            )

        try:
            A = [[_parse_f_lenient(c) for c in row] for row in A_raw]
            b = [_parse_f_lenient(x) for x in b_raw]
        except Exception:
            return (
                (True, "Valid rejection")
                if status == "OUT_OF_SCOPE"
                else (False, "Should be OUT_OF_SCOPE")
            )

        if status == "OUT_OF_SCOPE":
            return False, "Case was valid but solver claimed OUT_OF_SCOPE"

        if status != "SOLVED":
            return False, f"Unexpected status: {status}"

        # Ground truth consistency via RREF
        rank_A, _ = independent_rref_rank(A)
        aug = [A[i] + [b[i]] for i in range(m)]
        rank_aug, _ = independent_rref_rank(aug)
        is_truly_consistent = rank_A == rank_aug

        kind = result.get("kind")
        if is_truly_consistent and kind != "CONSISTENT":
            return False, f"Ground truth is CONSISTENT, but solver claimed {kind}"
        if not is_truly_consistent and kind != "INCONSISTENT":
            return False, f"Ground truth is INCONSISTENT, but solver claimed {kind}"

        if kind == "INCONSISTENT":
            y_raw = result.get("y")
            if not isinstance(y_raw, list) or len(y_raw) != m:
                return False, "y dimension mismatch"
            try:
                y = [_parse_f_strict(v) for v in y_raw]
            except Exception as e:
                return False, f"Invalid y format: {e}"

            # y^T A == 0
            for j in range(n):
                if sum(y[i] * A[i][j] for i in range(m)) != 0:
                    return False, f"y^T A != 0 at col {j}"
            # y^T b != 0
            if sum(y[i] * b[i] for i in range(m)) == 0:
                return False, "y^T b == 0"
            return True, "Independent check passed for INCONSISTENT"

        if kind == "CONSISTENT":
            x_raw = result.get("x")
            if not isinstance(x_raw, list) or len(x_raw) != n:
                return False, "x dimension mismatch"
            try:
                x = [_parse_f_strict(v) for v in x_raw]
            except Exception as e:
                return False, f"Invalid x format: {e}"

            # A x == b
            for i in range(m):
                if sum(A[i][j] * x[j] for j in range(n)) != b[i]:
                    return False, f"A x != b at row {i}"

            claimed_rank = result.get("rank")
            if type(claimed_rank) is not int or claimed_rank != rank_A:
                return False, f"Rank mismatch: ground truth={rank_A}, solver={claimed_rank}"

            # Check rank rows and cols
            rank_rows = result.get("rank_rows")
            rank_cols = result.get("rank_cols")
            if not _ints_in_range(rank_rows, rank_A, m) or not _ints_in_range(rank_cols, rank_A, n):
                return False, "rank_rows/rank_cols must be distinct in-range integer indices"

            minor_A = [[A[r][c] for c in rank_cols] for r in rank_rows]
            if independent_det(minor_A) == 0:
                return False, "rank minor singular"

            # Check null basis dimension
            nb = result.get("null_basis")
            expected_null_dim = n - rank_A
            if not isinstance(nb, list) or len(nb) != expected_null_dim:
                return False, f"Null basis size mismatch: expected {expected_null_dim}"

            parsed_nb = []
            for idx, v_raw in enumerate(nb):
                if not isinstance(v_raw, list) or len(v_raw) != n:
                    return False, f"Null basis vector {idx} invalid length"
                try:
                    v = [_parse_f_strict(entry) for entry in v_raw]
                except Exception as e:
                    return False, f"Null basis vector {idx} format error: {e}"
                for i in range(m):
                    if sum(A[i][j] * v[j] for j in range(n)) != 0:
                        return False, f"Null basis vector {idx} not in kernel at row {i}"
                parsed_nb.append(v)

            # Check null_rows
            null_rows = result.get("null_rows")
            if not _ints_in_range(null_rows, expected_null_dim, n):
                return False, "null_rows must be distinct in-range integer indices"

            minor_N = [
                [parsed_nb[col_idx][r] for col_idx in range(expected_null_dim)] for r in null_rows
            ]
            if independent_det(minor_N) == 0:
                return False, "null rows minor singular"

            return True, "Independent check passed for CONSISTENT"

        return False, f"Invalid kind: {kind}"
    except Exception as exc:
        return False, f"Independent checker exception: {exc}"
