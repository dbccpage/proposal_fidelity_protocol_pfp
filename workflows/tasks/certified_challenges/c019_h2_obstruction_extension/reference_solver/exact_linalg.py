"""Exact rational linear algebra over Q and Z for C019."""

from __future__ import annotations

from fractions import Fraction
from typing import Any


def parse_rational(val: Any) -> Fraction:
    if isinstance(val, (int, Fraction)):
        return Fraction(val)
    if isinstance(val, str):
        if "." in val:
            raise ValueError(f"Float string detected: {val}")
        return Fraction(val)
    raise ValueError(f"Unsupported rational format: {val}")


def format_rational(frac: Fraction) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def nullspace_rational(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    """Compute exact rational nullspace basis of matrix A (A x = 0)."""
    if not matrix:
        return []
    m = len(matrix)
    n = len(matrix[0])
    # Augmented matrix copy
    mat = [[Fraction(cell) for cell in row] for row in matrix]

    pivot_cols = []
    r = 0
    for c in range(n):
        if r >= m:
            break
        # Find pivot
        piv = None
        for i in range(r, m):
            if mat[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        # Swap rows
        mat[r], mat[piv] = mat[piv], mat[r]
        # Normalize pivot row
        lead = mat[r][c]
        mat[r] = [val / lead for val in mat[r]]
        # Eliminate column
        for i in range(m):
            if i != r and mat[i][c] != 0:
                factor = mat[i][c]
                mat[i] = [mat[i][j] - factor * mat[r][j] for j in range(n)]
        pivot_cols.append(c)
        r += 1

    free_cols = [c for c in range(n) if c not in pivot_cols]
    basis = []
    for free in free_cols:
        vec = [Fraction(0)] * n
        vec[free] = Fraction(1)
        for row_idx, piv_col in enumerate(pivot_cols):
            vec[piv_col] = -mat[row_idx][free]
        basis.append(vec)
    return basis


def solve_linear_rational(A: list[list[Fraction]], b: list[Fraction]) -> list[Fraction] | None:
    """Solve A x = b over Q. Return particular solution or None if inconsistent."""
    m = len(A)
    n = len(A[0]) if m > 0 else 0
    aug = [[Fraction(cell) for cell in A[i]] + [Fraction(b[i])] for i in range(m)]

    r = 0
    pivots = []
    for c in range(n):
        if r >= m:
            break
        piv = None
        for i in range(r, m):
            if aug[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        aug[r], aug[piv] = aug[piv], aug[r]
        lead = aug[r][c]
        aug[r] = [val / lead for val in aug[r]]
        for i in range(m):
            if i != r and aug[i][c] != 0:
                factor = aug[i][c]
                aug[i] = [aug[i][j] - factor * aug[r][j] for j in range(n + 1)]
        pivots.append((r, c))
        r += 1

    # Check consistency
    for i in range(r, m):
        if aug[i][n] != 0:
            return None  # Inconsistent

    x = [Fraction(0)] * n
    for row, col in pivots:
        x[col] = aug[row][n]
    return x
