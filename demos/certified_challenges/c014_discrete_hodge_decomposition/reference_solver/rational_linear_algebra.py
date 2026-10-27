"""Exact Rational Linear Algebra in Pure Python.

Provides fraction-free and exact Gaussian elimination over Q:
- Matrix multiplication, transpose, vector products
- Exact linear system solve A x = b (particular solution)
- Exact nullspace / kernel basis ker(A)
- Exact row reduction / echelon form and rank over Q

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence


def parse_fraction(val: str | int | float | Fraction) -> Fraction:
    """Parses scalar into exact Fraction."""
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        val = val.strip()
        if "/" in val:
            num, den = val.split("/", 1)
            return Fraction(int(num.strip()), int(den.strip()))
        return Fraction(int(val), 1)
    if isinstance(val, float):
        return Fraction(val).limit_denominator(1_000_000)
    raise TypeError(f"Cannot parse value {val!r} as Fraction")


def format_fraction(frac: Fraction) -> str:
    """Formats Fraction into canonical string."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def mat_mul(
    A: Sequence[Sequence[Fraction]], B: Sequence[Sequence[Fraction]]
) -> list[list[Fraction]]:
    """Multiplies two matrices A (m x p) and B (p x n) over Q."""
    if not A or not B:
        return []
    m, p, n = len(A), len(B), len(B[0])
    res = [[Fraction(0, 1) for _ in range(n)] for _ in range(m)]
    for i in range(m):
        for k in range(p):
            if A[i][k] != 0:
                a_ik = A[i][k]
                for j in range(n):
                    res[i][j] += a_ik * B[k][j]
    return res


def mat_vec_mul(A: Sequence[Sequence[Fraction]], x: Sequence[Fraction]) -> list[Fraction]:
    """Multiplies matrix A (m x n) by vector x (n) over Q."""
    if not A:
        return []
    m, n = len(A), len(A[0])
    assert len(x) == n, f"Dimension mismatch: {len(A[0])} != {len(x)}"
    res = [Fraction(0, 1) for _ in range(m)]
    for i in range(m):
        row_sum = Fraction(0, 1)
        for j in range(n):
            if A[i][j] != 0 and x[j] != 0:
                row_sum += A[i][j] * x[j]
        res[i] = row_sum
    return res


def transpose(A: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    """Transposes matrix A (m x n) -> (n x m)."""
    if not A:
        return []
    m, n = len(A), len(A[0])
    return [[A[r][c] for r in range(m)] for c in range(n)]


def rref_and_rank(
    A_in: Sequence[Sequence[Fraction]],
) -> tuple[list[list[Fraction]], list[int], int]:
    """Computes Reduced Row Echelon Form (RREF), pivot columns, and rank over Q."""
    if not A_in or not A_in[0]:
        return [], [], 0
    m = len(A_in)
    n = len(A_in[0])
    A = [[A_in[r][c] for c in range(n)] for r in range(m)]
    pivots: list[int] = []
    r = 0
    for c in range(n):
        if r >= m:
            break
        # Find pivot
        pivot_r = None
        for i in range(r, m):
            if A[i][c] != 0:
                pivot_r = i
                break
        if pivot_r is None:
            continue
        # Swap rows
        A[r], A[pivot_r] = A[pivot_r], A[r]
        # Normalize pivot row
        pv = A[r][c]
        for j in range(c, n):
            A[r][j] /= pv
        # Eliminate in all other rows
        for i in range(m):
            if i != r and A[i][c] != 0:
                factor = A[i][c]
                for j in range(c, n):
                    A[i][j] -= factor * A[r][j]
        pivots.append(c)
        r += 1
    return A, pivots, len(pivots)


def exact_solve(
    A: Sequence[Sequence[Fraction]], b: Sequence[Fraction]
) -> tuple[bool, list[Fraction]]:
    """Finds a particular solution x to A x = b over Q.

    Returns:
        (is_consistent, particular_solution)
    """
    if not A or not A[0]:
        if all(val == 0 for val in b):
            return True, []
        return False, []

    m = len(A)
    n = len(A[0])
    assert len(b) == m, f"Dimension mismatch: A has {m} rows, b has {len(b)} entries"

    # Augmented matrix [A | b]
    aug = [[A[r][c] for c in range(n)] + [b[r]] for r in range(m)]
    r = 0
    pivots: list[int] = []
    for c in range(n):
        if r >= m:
            break
        pivot_r = None
        for i in range(r, m):
            if aug[i][c] != 0:
                pivot_r = i
                break
        if pivot_r is None:
            continue
        aug[r], aug[pivot_r] = aug[pivot_r], aug[r]
        pv = aug[r][c]
        for j in range(c, n + 1):
            aug[r][j] /= pv
        for i in range(m):
            if i != r and aug[i][c] != 0:
                factor = aug[i][c]
                for j in range(c, n + 1):
                    aug[i][j] -= factor * aug[r][j]
        pivots.append(c)
        r += 1

    # Check consistency: any row [0 ... 0 | nonzero] means inconsistent
    for i in range(r, m):
        if aug[i][n] != 0:
            return False, []

    # Build particular solution (non-pivot variables set to 0)
    x = [Fraction(0, 1) for _ in range(n)]
    for row_idx, col_idx in enumerate(pivots):
        x[col_idx] = aug[row_idx][n]

    return True, x


def nullspace_basis(A: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    """Computes an exact basis for the kernel / nullspace ker(A) over Q."""
    if not A or not A[0]:
        return []
    len(A)
    n = len(A[0])
    rref, pivots, rank = rref_and_rank(A)
    pivot_set = set(pivots)
    free_vars = [c for c in range(n) if c not in pivot_set]

    basis: list[list[Fraction]] = []
    for f in free_vars:
        vec = [Fraction(0, 1) for _ in range(n)]
        vec[f] = Fraction(1, 1)
        for r_idx, p_col in enumerate(pivots):
            vec[p_col] = -rref[r_idx][f]
        basis.append(vec)

    return basis
