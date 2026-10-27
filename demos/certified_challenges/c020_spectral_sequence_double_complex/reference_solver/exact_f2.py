"""Exact linear algebra over F_2 and double complex spectral sequence utilities."""

from __future__ import annotations


def mat_mul_f2(A: list[list[int]], B: list[list[int]]) -> list[list[int]]:
    """Multiply matrices A (m x k) and B (k x n) over F_2."""
    if not A or not B:
        return []
    m = len(A)
    k = len(A[0])
    n = len(B[0])
    res = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            val = 0
            for l in range(k):
                val ^= A[i][l] & B[l][j]
            res[i][j] = val
    return res


def is_zero_mat_f2(A: list[list[int]]) -> bool:
    for row in A:
        for val in row:
            if val % 2 != 0:
                return False
    return True


def mats_equal_f2(A: list[list[int]], B: list[list[int]]) -> bool:
    if len(A) != len(B):
        return False
    if not A:
        return True
    if len(A[0]) != len(B[0]):
        return False
    for i in range(len(A)):
        for j in range(len(A[0])):
            if (A[i][j] % 2) != (B[i][j] % 2):
                return False
    return True


def row_reduce_f2(matrix: list[list[int]]) -> tuple[list[list[int]], list[int], int]:
    """Row reduce matrix over F_2 to reduced row echelon form (RREF).

    Returns (rref_matrix, pivot_columns, rank).
    """
    if not matrix:
        return [], [], 0
    m = len(matrix)
    n = len(matrix[0])
    mat = [[cell % 2 for cell in row] for row in matrix]

    r = 0
    pivots: list[int] = []
    for c in range(n):
        if r >= m:
            break
        # Find pivot
        piv = None
        for i in range(r, m):
            if mat[i][c] == 1:
                piv = i
                break
        if piv is None:
            continue
        # Swap rows
        mat[r], mat[piv] = mat[piv], mat[r]
        # Eliminate other rows
        for i in range(m):
            if i != r and mat[i][c] == 1:
                for j in range(c, n):
                    mat[i][j] ^= mat[r][j]
        pivots.append(c)
        r += 1

    return mat, pivots, r


def rank_f2(matrix: list[list[int]]) -> int:
    """Compute rank of matrix over F_2."""
    if not matrix or not matrix[0]:
        return 0
    _, _, r = row_reduce_f2(matrix)
    return r


def nullspace_f2(matrix: list[list[int]], num_vars: int | None = None) -> list[list[int]]:
    """Compute exact F_2 nullspace basis vectors for matrix A (A x = 0 mod 2)."""
    if not matrix:
        n = num_vars or 0
        # Identity matrix basis
        return [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    len(matrix)
    n = len(matrix[0])
    rref, pivots, r = row_reduce_f2(matrix)
    free_cols = [c for c in range(n) if c not in pivots]

    basis: list[list[int]] = []
    for free in free_cols:
        vec = [0] * n
        vec[free] = 1
        for row_idx, piv_col in enumerate(pivots):
            vec[piv_col] = rref[row_idx][free]
        basis.append(vec)
    return basis


def subspace_span_rank_f2(basis_vectors: list[list[int]], dim: int) -> int:
    """Compute dimension of subspace spanned by given vectors in F_2^dim."""
    if not basis_vectors:
        return 0
    return rank_f2(basis_vectors)


def subspace_sum_basis_f2(bases: list[list[list[int]]], dim: int) -> list[list[int]]:
    """Return an orthogonal/clean basis for the sum of subspaces in F_2^dim."""
    all_vecs: list[list[int]] = []
    for b in bases:
        all_vecs.extend(b)
    if not all_vecs:
        return []
    rref, pivots, r = row_reduce_f2(all_vecs)
    # Basis vectors are the non-zero rows of RREF
    return [rref[i] for i in range(r)]


def quotient_dim_f2(U_basis: list[list[int]], V_basis: list[list[int]], dim: int) -> int:
    """Compute dim((U + V) / V) = dim(U + V) - dim(V)."""
    dim_V = subspace_span_rank_f2(V_basis, dim)
    dim_UV = subspace_span_rank_f2(U_basis + V_basis, dim)
    return dim_UV - dim_V
