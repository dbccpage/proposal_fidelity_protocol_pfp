"""Exact Integer Smith Normal Form (SNF) with Unimodular Transformation Matrices.

Given an m x n integer matrix A, computes:
- Diagonal matrix D of size m x n with entries d_1 | d_2 | ... | d_r >= 1 on diagonal (all others 0)
- Unimodular m x m integer matrix U and its inverse U_inv (U * U_inv = I_m)
- Unimodular n x n integer matrix V and its inverse V_inv (V * V_inv = I_n)
such that U * A * V = D.

AuthorityEffect: None.
"""

from __future__ import annotations


def identity_matrix(n: int) -> list[list[int]]:
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def mat_mul(A: list[list[int]], B: list[list[int]]) -> list[list[int]]:
    if not A or not B:
        return []
    m = len(A)
    k = len(A[0])
    n = len(B[0])
    res = [[0 for _ in range(n)] for _ in range(m)]
    for i in range(m):
        for p in range(k):
            if A[i][p] != 0:
                for j in range(n):
                    res[i][j] += A[i][p] * B[p][j]
    return res


def compute_smith_normal_form(
    A_in: list[list[int]],
) -> tuple[list[int], list[list[int]], list[list[int]], list[list[int]], list[list[int]]]:
    """Computes the Smith Normal Form of integer matrix A_in.

    Returns:
        (diagonal_invariants, U, U_inv, V, V_inv)
        where diagonal_invariants = [d_1, d_2, ..., d_r] with d_i > 0 and d_i | d_{i+1},
        U * A * V = diag(d_1, ..., d_r, 0, ..., 0),
        U * U_inv = I_m,
        V * V_inv = I_n.
    """
    m = len(A_in)
    if m == 0:
        return [], [], [], [], []
    n = len(A_in[0])
    if n == 0:
        return [], identity_matrix(m), identity_matrix(m), [], []

    A = [list(row) for row in A_in]
    U = identity_matrix(m)
    U_inv = identity_matrix(m)
    V = identity_matrix(n)
    V_inv = identity_matrix(n)

    # Helper row and col elementary operations with exact inverse maintenance
    def swap_rows(r1: int, r2: int):
        if r1 == r2:
            return
        A[r1], A[r2] = A[r2], A[r1]
        U[r1], U[r2] = U[r2], U[r1]
        # For inverse: swapping rows in U corresponds to swapping cols in U_inv
        for i in range(m):
            U_inv[i][r1], U_inv[i][r2] = U_inv[i][r2], U_inv[i][r1]

    def swap_cols(c1: int, c2: int):
        if c1 == c2:
            return
        for i in range(m):
            A[i][c1], A[i][c2] = A[i][c2], A[i][c1]
        for i in range(n):
            V[i][c1], V[i][c2] = V[i][c2], V[i][c1]
        # For inverse: swapping cols in V corresponds to swapping rows in V_inv
        V_inv[c1], V_inv[c2] = V_inv[c2], V_inv[c1]

    def add_row_mul(target_r: int, src_r: int, mul: int):
        if mul == 0:
            return
        for j in range(n):
            A[target_r][j] += mul * A[src_r][j]
        for j in range(m):
            U[target_r][j] += mul * U[src_r][j]
        # Inverse: U_inv * U = I -> when U has row target_r += mul * src_r,
        # U_inv has col src_r -= mul * target_r
        for i in range(m):
            U_inv[i][src_r] -= mul * U_inv[i][target_r]

    def add_col_mul(target_c: int, src_c: int, mul: int):
        if mul == 0:
            return
        for i in range(m):
            A[i][target_c] += mul * A[i][src_c]
        for i in range(n):
            V[i][target_c] += mul * V[i][src_c]
        # Inverse: V_inv has row src_c -= mul * target_c
        for j in range(n):
            V_inv[src_c][j] -= mul * V_inv[target_c][j]

    def scale_row(r: int, s: int):
        if s == 1:
            return
        if s != -1:
            raise ValueError("Only scaling by +-1 preserves unimodularity over Z")
        for j in range(n):
            A[r][j] *= -1
        for j in range(m):
            U[r][j] *= -1
        for i in range(m):
            U_inv[i][r] *= -1

    def scale_col(c: int, s: int):
        if s == 1:
            return
        if s != -1:
            raise ValueError("Only scaling by +-1 preserves unimodularity over Z")
        for i in range(m):
            A[i][c] *= -1
        for i in range(n):
            V[i][c] *= -1
        for j in range(n):
            V_inv[c][j] *= -1

    pivot = 0
    min_dim = min(m, n)

    while pivot < min_dim:
        # Step 1: Find non-zero entry with minimal absolute value in submatrix A[pivot:, pivot:]
        while True:
            min_val = None
            min_r, min_c = -1, -1
            for r in range(pivot, m):
                for c in range(pivot, n):
                    val = abs(A[r][c])
                    if val != 0:
                        if min_val is None or val < min_val:
                            min_val = val
                            min_r, min_c = r, c

            if min_val is None:
                # Submatrix is all zeros!
                break

            # Move minimal entry to pivot position
            swap_rows(pivot, min_r)
            swap_cols(pivot, min_c)

            if A[pivot][pivot] < 0:
                scale_row(pivot, -1)

            p_val = A[pivot][pivot]

            # Step 2: Eliminate entries in pivot column
            col_cleared = True
            for r in range(pivot + 1, m):
                if A[r][pivot] != 0:
                    q = A[r][pivot] // p_val
                    add_row_mul(r, pivot, -q)
                    if A[r][pivot] != 0:
                        col_cleared = False
                        break
            if not col_cleared:
                continue

            # Step 3: Eliminate entries in pivot row
            row_cleared = True
            for c in range(pivot + 1, n):
                if A[pivot][c] != 0:
                    q = A[pivot][c] // p_val
                    add_col_mul(c, pivot, -q)
                    if A[pivot][c] != 0:
                        row_cleared = False
                        break
            if not row_cleared:
                continue

            # Step 4: Check divisibility across remaining submatrix A[pivot+1:, pivot+1:]
            divisibility_satisfied = True
            for r in range(pivot + 1, m):
                for c in range(pivot + 1, n):
                    if A[r][c] % p_val != 0:
                        # Add row r to pivot row, restart elimination
                        add_row_mul(pivot, r, 1)
                        divisibility_satisfied = False
                        break
                if not divisibility_satisfied:
                    break

            if divisibility_satisfied:
                # Pivot is clean and divides all remaining entries
                break

        if min_val is None:
            # Submatrix all zeros, we are done
            break

        pivot += 1

    # Invariants are the non-zero diagonal entries
    invariants = []
    for i in range(pivot):
        d = A[i][i]
        if d < 0:
            scale_row(i, -1)
            d = -d
        if d != 0:
            invariants.append(d)

    # Final check of divisibility chain
    for i in range(len(invariants) - 1):
        if invariants[i + 1] % invariants[i] != 0:
            raise RuntimeError(
                f"SNF divisibility failed: {invariants[i]} does not divide {invariants[i + 1]}"
            )

    return invariants, U, U_inv, V, V_inv
