"""Exact rational linear algebra over Q using fractions.Fraction."""

from __future__ import annotations

from fractions import Fraction


def row_reduce(matrix: list[list[Fraction]]) -> tuple[list[list[Fraction]], list[int], int]:
    """Gaussian elimination to row echelon form over Q.

    Returns (echelon_matrix, pivot_columns, rank).
    """
    if not matrix or not matrix[0]:
        return [], [], 0

    m = len(matrix)
    n = len(matrix[0])
    mat = [[val for val in row] for row in matrix]

    pivot_cols: list[int] = []
    curr_row = 0

    for col in range(n):
        if curr_row >= m:
            break
        pivot_idx = None
        for r in range(curr_row, m):
            if mat[r][col] != 0:
                pivot_idx = r
                break
        if pivot_idx is None:
            continue

        mat[curr_row], mat[pivot_idx] = mat[pivot_idx], mat[curr_row]
        pivot_val = mat[curr_row][col]

        # Normalize pivot row
        for c in range(col, n):
            mat[curr_row][c] /= pivot_val

        # Eliminate below and above for RREF
        for r in range(m):
            if r != curr_row and mat[r][col] != 0:
                factor = mat[r][col]
                for c in range(col, n):
                    mat[r][c] -= factor * mat[curr_row][c]

        pivot_cols.append(col)
        curr_row += 1

    return mat, pivot_cols, curr_row


def exact_rank(matrix: list[list[Fraction]]) -> int:
    if not matrix or not matrix[0]:
        return 0
    _, _, rank = row_reduce(matrix)
    return rank


def nullspace_basis(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    """Compute exact basis for the kernel / nullspace of matrix {x : A x = 0}."""
    if not matrix or not matrix[0]:
        return []
    len(matrix)
    n = len(matrix[0])
    rref, pivot_cols, rank = row_reduce(matrix)

    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(n) if c not in pivot_set]

    basis: list[list[Fraction]] = []
    for free_var in free_cols:
        vec = [Fraction(0, 1) for _ in range(n)]
        vec[free_var] = Fraction(1, 1)
        for r, p_col in enumerate(pivot_cols):
            vec[p_col] = -rref[r][free_var]
        basis.append(vec)
    return basis


def exact_solve(matrix: list[list[Fraction]], b: list[Fraction]) -> list[Fraction] | None:
    """Find a particular solution x to A x = b over Q, or None if inconsistent."""
    m = len(matrix)
    n = len(matrix[0]) if m > 0 else 0
    if m == 0 or n == 0:
        return None

    augmented = [matrix[r] + [b[r]] for r in range(m)]
    rref, pivot_cols, rank = row_reduce(augmented)

    # Check consistency: if last column is a pivot column, no solution
    if n in pivot_cols:
        return None

    x = [Fraction(0, 1) for _ in range(n)]
    for r, p_col in enumerate(pivot_cols):
        if p_col < n:
            x[p_col] = rref[r][n]
    return x
