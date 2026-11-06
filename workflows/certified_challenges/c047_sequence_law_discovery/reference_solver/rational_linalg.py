"""Exact rational linear algebra over Fractions for C047.
Provides nullspace computation, Gaussian elimination, and Bareiss determinant.
"""

from fractions import Fraction
from typing import List, Tuple


def rref(matrix: List[List[Fraction]]) -> Tuple[List[List[Fraction]], List[int]]:
    """Compute Row Reduced Echelon Form (RREF) and return (rref_matrix, pivot_cols)."""
    if not matrix or not matrix[0]:
        return [], []
    m = len(matrix)
    n = len(matrix[0])
    A = [[Fraction(val) for val in row] for row in matrix]

    pivot_cols = []
    r = 0
    for c in range(n):
        if r >= m:
            break
        # Find pivot
        pivot_row = -1
        for i in range(r, m):
            if A[i][c] != 0:
                pivot_row = i
                break
        if pivot_row == -1:
            continue

        # Swap rows
        A[r], A[pivot_row] = A[pivot_row], A[r]

        # Normalize pivot row
        pv = A[r][c]
        for j in range(c, n):
            A[r][j] /= pv

        # Eliminate other rows
        for i in range(m):
            if i != r and A[i][c] != 0:
                factor = A[i][c]
                for j in range(c, n):
                    A[i][j] -= factor * A[r][j]
        pivot_cols.append(c)
        r += 1

    return A, pivot_cols


def nullspace(matrix: List[List[Fraction]]) -> List[List[Fraction]]:
    """Compute a basis of the nullspace (kernel) of matrix: M * v = 0.
    Returns list of basis vectors.
    """
    if not matrix or not matrix[0]:
        return []
    len(matrix)
    n = len(matrix[0])
    R, pivot_cols = rref(matrix)

    free_cols = [c for c in range(n) if c not in pivot_cols]
    basis = []

    for free in free_cols:
        vec = [Fraction(0)] * n
        vec[free] = Fraction(1)
        for r_idx, piv in enumerate(pivot_cols):
            vec[piv] = -R[r_idx][free]
        basis.append(vec)

    return basis


def bareiss_determinant(matrix: List[List[Fraction]]) -> Fraction:
    """Exact fraction-free determinant via Bareiss algorithm for Fraction matrix."""
    n = len(matrix)
    if n == 0:
        return Fraction(1)
    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square")
    if n == 1:
        return Fraction(matrix[0][0])
    if n == 2:
        return Fraction(matrix[0][0]) * Fraction(matrix[1][1]) - Fraction(matrix[0][1]) * Fraction(
            matrix[1][0]
        )

    M = [[Fraction(val) for val in row] for row in matrix]
    sign = 1
    prev_pivot = Fraction(1)

    for k in range(n - 1):
        # Pivot selection
        if M[k][k] == 0:
            swap_row = -1
            for i in range(k + 1, n):
                if M[i][k] != 0:
                    swap_row = i
                    break
            if swap_row == -1:
                return Fraction(0)
            M[k], M[swap_row] = M[swap_row], M[k]
            sign = -sign

        d_k = M[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                val = M[i][j] * d_k - M[i][k] * M[k][j]
                if k > 0:
                    M[i][j] = val / prev_pivot
                else:
                    M[i][j] = val
        prev_pivot = d_k

    return Fraction(sign) * M[n - 1][n - 1]
