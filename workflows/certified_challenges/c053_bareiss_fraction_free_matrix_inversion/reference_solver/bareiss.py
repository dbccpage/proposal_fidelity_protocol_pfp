"""Bareiss Fraction-Free Algorithm for exact Determinants, Adjugates, and Inverses."""

from fractions import Fraction
from typing import List, Optional


def parse_fraction(val: str) -> Fraction:
    val = str(val).strip()
    if "/" in val:
        num, den = val.split("/", 1)
        return Fraction(int(num), int(den))
    return Fraction(int(val), 1)


def format_fraction(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def bareiss_determinant(matrix: List[List[Fraction]]) -> Fraction:
    """Exact Bareiss fraction-free determinant algorithm."""
    n = len(matrix)
    if n == 0:
        return Fraction(1, 1)
    if n == 1:
        return matrix[0][0]

    # Clear common denominator to work with pure integers
    # Find lcm of all denominators
    from math import gcd

    def lcm(a, b):
        return (a * b) // gcd(a, b)

    total_lcm = 1
    for row in matrix:
        for val in row:
            total_lcm = lcm(total_lcm, val.denominator)

    int_mat = [[int(val * total_lcm) for val in row] for row in matrix]

    sign = 1
    prev_pivot = 1

    for k in range(n - 1):
        # Pivot search
        pivot_row = k
        while pivot_row < n and int_mat[pivot_row][k] == 0:
            pivot_row += 1

        if pivot_row == n:
            return Fraction(0, 1)

        if pivot_row != k:
            int_mat[k], int_mat[pivot_row] = int_mat[pivot_row], int_mat[k]
            sign = -sign

        pivot = int_mat[k][k]

        for i in range(k + 1, n):
            for j in range(k + 1, n):
                num = pivot * int_mat[i][j] - int_mat[i][k] * int_mat[k][j]
                # Exact integer division guaranteed by Bareiss theorem
                int_mat[i][j] = num // prev_pivot

        prev_pivot = pivot

    int_det = sign * int_mat[n - 1][n - 1]
    return Fraction(int_det, total_lcm**n)


def compute_adjugate(matrix: List[List[Fraction]]) -> List[List[Fraction]]:
    """Compute adjugate matrix via exact cofactors."""
    n = len(matrix)
    if n == 1:
        return [[Fraction(1, 1)]]

    adj = [[Fraction(0, 1)] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            # Minor M_{i, j} by removing row i and col j
            minor = [[matrix[r][c] for c in range(n) if c != j] for r in range(n) if r != i]
            det_minor = bareiss_determinant(minor)
            sign = 1 if (i + j) % 2 == 0 else -1
            # Note adjugate is TRANSPOSE of cofactor matrix: adj[j][i] = (-1)^(i+j) * det(minor)
            adj[j][i] = sign * det_minor

    return adj


def find_null_vector(matrix: List[List[Fraction]]) -> Optional[List[Fraction]]:
    """Find a non-zero right null vector v in Q^n such that A v = 0 via Gaussian elimination."""
    n = len(matrix)
    if n == 0:
        return None

    # Augmented matrix copy
    M = [[matrix[r][c] for c in range(n)] for r in range(n)]

    col = 0
    pivot_cols = []

    for r in range(n):
        if col >= n:
            break
        # Find non-zero pivot
        p_row = r
        while p_row < n and M[p_row][col] == 0:
            p_row += 1
        if p_row == n:
            col += 1
            # Retry row r with next column
            # decrement r to retry
            r -= 1
            continue

        M[r], M[p_row] = M[p_row], M[r]
        pivot_val = M[r][col]

        # Normalize row
        for c in range(col, n):
            M[r][c] = M[r][c] / pivot_val

        # Eliminate other rows
        for other_r in range(n):
            if other_r != r and M[other_r][col] != 0:
                factor = M[other_r][col]
                for c in range(col, n):
                    M[other_r][c] -= factor * M[r][c]

        pivot_cols.append(col)
        col += 1

    free_cols = [c for c in range(n) if c not in pivot_cols]
    if not free_cols:
        return None  # Full rank, trivial kernel only

    # Take first free variable = 1, others = 0
    f_col = free_cols[0]
    v = [Fraction(0, 1)] * n
    v[f_col] = Fraction(1, 1)

    for r, p_col in enumerate(pivot_cols):
        v[p_col] = -M[r][f_col]

    # Clear denominators to return canonical integer vector
    from math import gcd

    def lcm(a, b):
        return (a * b) // gcd(a, b)

    den_lcm = 1
    for val in v:
        den_lcm = lcm(den_lcm, val.denominator)
    v_int = [val * den_lcm for val in v]

    # Simplify by overall gcd
    overall_gcd = 0
    for val in v_int:
        overall_gcd = gcd(overall_gcd, abs(val.numerator))
    if overall_gcd > 1:
        v_int = [val / overall_gcd for val in v_int]

    return v_int
