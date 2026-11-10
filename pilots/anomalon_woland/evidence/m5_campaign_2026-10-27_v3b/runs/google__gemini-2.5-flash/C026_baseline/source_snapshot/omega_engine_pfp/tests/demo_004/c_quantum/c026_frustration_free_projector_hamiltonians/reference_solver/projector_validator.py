# AuthorityEffect: None.
r"""
Projector validation for C026 terms.

Checks Hermiticity (P^\dagger = P) and Idempotence (P^2 = P) in exact Q(i) arithmetic.
Identifies first offending entry [row, col] on failure.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .gaussian_rational import GaussianRat


def validate_projector(
    matrix: List[List[GaussianRat]],
) -> Tuple[bool, Optional[str], Optional[List[int]]]:
    r"""
    Validates that a square matrix over Q(i) is an orthogonal projector:
    1. Hermiticity: P^\dagger = P
    2. Idempotence: P^2 = P
    Returns (is_valid, failure_reason, offending_entry).
    """
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        return False, "non_square", [0, 0]

    # 1. Check Hermiticity: P[j][k] == P[k][j]^*
    for j in range(n):
        for k in range(j, n):
            if matrix[j][k] != matrix[k][j].conjugate():
                return False, "not_hermitian", [j, k]

    # 2. Check Idempotence: P^2 == P
    for j in range(n):
        for k in range(n):
            prod_jk = GaussianRat.zero()
            for l in range(n):
                prod_jk = prod_jk + (matrix[j][l] * matrix[l][k])
            if prod_jk != matrix[j][k]:
                return False, "not_idempotent", [j, k]

    return True, None, None
