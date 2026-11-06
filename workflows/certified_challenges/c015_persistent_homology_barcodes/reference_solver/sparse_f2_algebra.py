"""Sparse F2 Linear Algebra for Persistent Homology Matrix Reduction.

Columns are represented as sets of integer row indices (where entry is 1 in F2).
Matrix addition is set symmetric difference (XOR).
Matrix multiplication D * V over F2:
  (D * V)_j = sum_{k in V_j} D_k (mod 2) = XOR_{k in V_j} D_k.
"""

from __future__ import annotations


def xor_columns(col1: set[int], col2: set[int]) -> set[int]:
    """Add two sparse F2 column vectors (symmetric difference)."""
    return col1 ^ col2


def is_upper_unitriangular(V_cols: dict[int, set[int]], n: int) -> tuple[bool, str]:
    """Verify that V is an n x n upper unitriangular matrix over F2.

    Unlisted columns default to standard unit vectors {j}.
    For each column j in 0..n-1:
    - V[j, j] == 1 (i.e. j in V_cols[j])
    - For all i in V_cols[j], i <= j (no entries below diagonal)
    """
    for j in range(n):
        col = V_cols.get(j, {j})
        if j not in col:
            return False, f"Diagonal entry V[{j}, {j}] is not 1"
        for i in col:
            if i > j:
                return False, f"Entry below diagonal: V[{i}, {j}] is nonzero"
            if i < 0:
                return False, f"Invalid negative row index {i} in column {j}"
    return True, "V is upper unitriangular"


def verify_sparse_f2_product(
    D_cols: list[set[int]],
    V_cols: dict[int, set[int]],
    R_cols: dict[int, set[int]],
    n: int,
) -> tuple[bool, str]:
    """Verify that D * V = R over F2 for all columns 0..n-1.

    Unlisted columns of V default to {j}.
    Unlisted columns of R default to D_cols[j].
    """
    for j in range(n):
        v_col = V_cols.get(j, {j})
        expected_r = set()
        for k in v_col:
            if k >= len(D_cols):
                return False, f"Index {k} in V[{j}] exceeds boundary matrix size {len(D_cols)}"
            expected_r ^= D_cols[k]

        actual_r = R_cols.get(j, D_cols[j] if j < len(D_cols) else set())
        if expected_r != actual_r:
            return (
                False,
                f"Column {j} mismatch: D*V[:, {j}] = {sorted(expected_r)}, but R[:, {j}] = {sorted(actual_r)}",
            )
    return True, "D * V = R over F2 holds for all columns"


def is_reduced(
    R_cols: dict[int, set[int]],
    D_cols: list[set[int]],
    n: int,
) -> tuple[bool, str, dict[int, int]]:
    """Check that R is a reduced boundary matrix over F2.

    A matrix R is reduced if no two nonzero columns have the same lowest row index (low(j)).
    Returns (is_reduced_flag, reason, low_map) where low_map maps col -> low(col).
    """
    low_to_col: dict[int, int] = {}
    low_map: dict[int, int] = {}

    for j in range(n):
        col = R_cols.get(j, D_cols[j] if j < len(D_cols) else set())
        if col:
            low_j = max(col)
            low_map[j] = low_j
            if low_j in low_to_col:
                other_col = low_to_col[low_j]
                return (
                    False,
                    f"Collision in R: columns {other_col} and {j} both have lowest row {low_j}",
                    {},
                )
            low_to_col[low_j] = j

    return True, "R is reduced", low_map
