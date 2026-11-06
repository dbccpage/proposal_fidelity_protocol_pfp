# AuthorityEffect: None.
"""
Exact linear algebra over F_2 for C028.

Provides:
1. Matrix inversion over F_2 via Gauss-Jordan elimination.
2. Kernel vector extraction for singular matrices.
"""

from __future__ import annotations

from typing import List, Optional, Tuple


def invert_matrix_f2(
    M: List[List[int]],
) -> Tuple[bool, Optional[List[List[int]]], Optional[List[int]]]:
    """
    Inverts an N x N matrix M over F_2.
    Returns:
        (is_invertible, M_inverse, kernel_vector_if_singular)
    """
    N = len(M)
    aug = [list(row) + [1 if i == j else 0 for j in range(N)] for i, row in enumerate(M)]


    for col in range(N):
        piv = None
        for r in range(col, N):
            if aug[r][col] == 1:
                piv = r
                break

        if piv is None:
            # Singular matrix: find non-zero vector in kernel
            # Use back-substitution on columns up to col
            v = [0] * N
            v[col] = 1
            for r in range(col - 1, -1, -1):
                # aug[r][r] * v[r] + sum_{c > r} aug[r][c] * v[c] = 0
                s = sum(aug[r][c] * v[c] for c in range(r + 1, N)) % 2
                v[r] = s
            return False, None, v

        if piv != col:
            aug[col], aug[piv] = aug[piv], aug[col]

        # Eliminate other rows
        for r in range(N):
            if r != col and aug[r][col] == 1:
                for c in range(2 * N):
                    aug[r][c] ^= aug[col][c]

    M_inv = [row[N:] for row in aug]
    return True, M_inv, None
