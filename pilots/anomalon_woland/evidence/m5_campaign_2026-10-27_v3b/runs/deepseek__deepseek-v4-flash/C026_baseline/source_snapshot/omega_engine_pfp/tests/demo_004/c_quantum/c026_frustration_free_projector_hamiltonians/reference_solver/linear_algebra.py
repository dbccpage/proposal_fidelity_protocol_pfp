# AuthorityEffect: None.
"""
Exact linear algebra operations over Q(i) for C026.

Provides exact matrix arithmetic, RREF, kernel basis extraction,
Hermitian matrix inversion, and left-inverse certificate computation.
"""

from __future__ import annotations

from typing import List, Tuple

from .gaussian_rational import GaussianRat


def mat_mul(
    A: List[List[GaussianRat]],
    B: List[List[GaussianRat]],
) -> List[List[GaussianRat]]:
    """Matrix multiplication A * B over Q(i)."""
    R = len(A)
    K = len(B)
    C = len(B[0]) if K > 0 else 0
    res = [[GaussianRat.zero() for _ in range(C)] for _ in range(R)]
    for i in range(R):
        row_A = A[i]
        for k in range(K):
            val_A = row_A[k]
            if val_A.is_zero():
                continue
            row_B = B[k]
            for j in range(C):
                res[i][j] = res[i][j] + (val_A * row_B[j])
    return res


def mat_add(
    A: List[List[GaussianRat]],
    B: List[List[GaussianRat]],
) -> List[List[GaussianRat]]:
    """Matrix addition A + B."""
    R = len(A)
    C = len(A[0]) if R > 0 else 0
    return [[A[r][c] + B[r][c] for c in range(C)] for r in range(R)]


def mat_scale(
    A: List[List[GaussianRat]],
    scalar: GaussianRat,
) -> List[List[GaussianRat]]:
    """Scalar multiplication scalar * A."""
    R = len(A)
    C = len(A[0]) if R > 0 else 0
    return [[A[r][c] * scalar for c in range(C)] for r in range(R)]


def mat_dagger(
    A: List[List[GaussianRat]],
) -> List[List[GaussianRat]]:
    r"""Conjugate transpose A^\dagger."""
    R = len(A)
    C = len(A[0]) if R > 0 else 0
    return [[A[r][c].conjugate() for r in range(R)] for c in range(C)]


def mat_trace(
    A: List[List[GaussianRat]],
) -> GaussianRat:
    """Trace of square matrix A."""
    n = len(A)
    tr = GaussianRat.zero()
    for i in range(n):
        tr = tr + A[i][i]
    return tr


def identity_matrix(n: int) -> List[List[GaussianRat]]:
    """Identity matrix I_n."""
    return [
        [GaussianRat.one() if i == j else GaussianRat.zero() for j in range(n)] for i in range(n)
    ]


def invert_matrix(
    A: List[List[GaussianRat]],
) -> List[List[GaussianRat]]:
    """
    Computes exact inverse of invertible square matrix A via Gauss-Jordan elimination.
    """
    n = len(A)
    aug = [
        [A[i][j] for j in range(n)]
        + [GaussianRat.one() if i == j else GaussianRat.zero() for j in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        pivot_row = None
        for row in range(col, n):
            if not aug[row][col].is_zero():
                pivot_row = row
                break
        if pivot_row is None:
            raise ValueError("Matrix is singular over Q(i)")

        if pivot_row != col:
            aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

        piv = aug[col][col]
        for j in range(col, 2 * n):
            aug[col][j] = aug[col][j] / piv

        for row in range(n):
            if row != col and not aug[row][col].is_zero():
                factor = aug[row][col]
                for j in range(col, 2 * n):
                    aug[row][j] = aug[row][j] - (factor * aug[col][j])

    return [[aug[i][n + j] for j in range(n)] for i in range(n)]


def compute_rref_and_kernel(
    M: List[List[GaussianRat]],
) -> Tuple[List[List[GaussianRat]], int, List[List[GaussianRat]]]:
    """
    Computes Reduced Row Echelon Form (RREF), rank, and exact kernel basis for M.
    Returns (rref_matrix, rank, kernel_basis).
    Kernel basis vectors v satisfy M * v = 0.
    """
    R = len(M)
    C = len(M[0]) if R > 0 else 0
    mat = [[M[r][c] for c in range(C)] for r in range(R)]

    pivot_cols: List[int] = []
    pivot_row = 0

    for col in range(C):
        if pivot_row >= R:
            break
        sel_row = None
        for r in range(pivot_row, R):
            if not mat[r][col].is_zero():
                sel_row = r
                break
        if sel_row is None:
            continue

        if sel_row != pivot_row:
            mat[pivot_row], mat[sel_row] = mat[sel_row], mat[pivot_row]

        piv = mat[pivot_row][col]
        for c in range(col, C):
            mat[pivot_row][c] = mat[pivot_row][c] / piv

        for r in range(R):
            if r != pivot_row and not mat[r][col].is_zero():
                fac = mat[r][col]
                for c in range(col, C):
                    mat[r][c] = mat[r][c] - (fac * mat[pivot_row][c])

        pivot_cols.append(col)
        pivot_row += 1

    rank = len(pivot_cols)
    free_cols = [c for c in range(C) if c not in pivot_cols]

    kernel_basis: List[List[GaussianRat]] = []
    for free_c in free_cols:
        v = [GaussianRat.zero() for _ in range(C)]
        v[free_c] = GaussianRat.one()
        for p_idx, p_col in enumerate(pivot_cols):
            v[p_col] = GaussianRat.zero() - mat[p_idx][free_c]
        kernel_basis.append(v)

    return mat, rank, kernel_basis


def compute_left_inverse(
    M: List[List[GaussianRat]],
) -> List[List[GaussianRat]]:
    r"""
    Computes exact left inverse L of matrix M with full column rank C:
    L = (M^\dagger * M)^{-1} * M^\dagger, such that L * M = I_C.
    """
    M_dag = mat_dagger(M)
    H = mat_mul(M_dag, M)  # C x C
    H_inv = invert_matrix(H)  # C x C
    L = mat_mul(H_inv, M_dag)  # C x R
    return L
