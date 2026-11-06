"""F2 Linear Algebra and Symplectic Pauli Arithmetic for C039.

Implements pure Python stdlib F2 matrix reduction, nullspace computation,
subspace quotient extension, matrix inversion, and symplectic Pauli formatting
using bitwise integer operations.

AuthorityEffect: None.
"""

from __future__ import annotations


def popcount(n: int) -> int:
    """Computes the number of set bits in integer n."""
    return n.bit_count()


def f2_rank(rows: list[int], num_cols: int) -> int:
    """Computes the rank of a matrix over F2 given as integer bitmasks."""
    reduced_rows, _ = f2_rref(rows, num_cols)
    return len(reduced_rows)


def f2_rref(rows: list[int], num_cols: int) -> tuple[list[int], list[int]]:
    """Computes the Reduced Row Echelon Form (RREF) of a matrix over F2.

    Returns:
        (pivot_rows, pivot_cols) where pivot_rows are the reduced non-zero rows
        and pivot_cols are the 0-indexed column indices of the leading 1s.
    """
    matrix = [r for r in rows if r != 0]
    pivot_cols: list[int] = []
    pivot_rows: list[int] = []

    for c in range(num_cols):
        pivot_idx = None
        for i in range(len(pivot_rows), len(matrix)):
            if (matrix[i] >> c) & 1:
                pivot_idx = i
                break
        if pivot_idx is None:
            continue

        curr_pos = len(pivot_rows)
        matrix[curr_pos], matrix[pivot_idx] = matrix[pivot_idx], matrix[curr_pos]
        pivot_val = matrix[curr_pos]
        pivot_cols.append(c)
        pivot_rows.append(pivot_val)

        # Eliminate bit c from all other rows
        for i in range(len(matrix)):
            if i != curr_pos and ((matrix[i] >> c) & 1):
                matrix[i] ^= pivot_val

    return matrix[: len(pivot_cols)], pivot_cols


def f2_nullspace(rows: list[int], num_cols: int) -> list[int]:
    """Computes a basis for the nullspace (kernel) of a matrix over F2.

    Returns:
        List of integer bitmasks forming a basis for {v in F2^num_cols : M v = 0}.
    """
    pivot_rows, pivot_cols = f2_rref(rows, num_cols)
    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(num_cols) if c not in pivot_set]

    # Map each pivot col to its pivot row
    pivot_row_map = {col: pivot_rows[i] for i, col in enumerate(pivot_cols)}

    basis: list[int] = []
    for f in free_cols:
        vec = 1 << f
        for p_col, p_row in pivot_row_map.items():
            if (p_row >> f) & 1:
                vec |= 1 << p_col
        basis.append(vec)

    return basis


def f2_extend_basis(
    subspace_basis: list[int],
    candidate_vectors: list[int],
    num_cols: int,
) -> tuple[list[int], list[int]]:
    """Selects candidate vectors that extend subspace_basis to span a larger space.

    Returns:
        (quotient_representatives, full_extended_basis)
        where quotient_representatives are elements of candidate_vectors that are
        linearly independent modulo span(subspace_basis).
    """
    # Build initial echelon basis for the subspace using a single RREF
    reduced_rows, pivot_cols = f2_rref(subspace_basis, num_cols)
    basis_dict: dict[int, int] = {col: row for col, row in zip(pivot_cols, reduced_rows)}
    pivot_list: list[int] = sorted(basis_dict.keys())

    quotient_reps: list[int] = []

    for cand in candidate_vectors:
        rem = cand
        for p_col in pivot_list:
            if (rem >> p_col) & 1:
                rem ^= basis_dict[p_col]

        if rem != 0:
            # Linearly independent modulo current span!
            quotient_reps.append(cand)
            lead = (rem & -rem).bit_length() - 1

            # Eliminate lead from existing basis rows
            for k in list(basis_dict.keys()):
                if (basis_dict[k] >> lead) & 1:
                    basis_dict[k] ^= rem
            basis_dict[lead] = rem
            pivot_list = sorted(basis_dict.keys())

    return quotient_reps, list(basis_dict.values())


def f2_invert_matrix(matrix_rows: list[int], n: int) -> list[int]:
    """Inverts an n x n invertible matrix over F2.

    matrix_rows: list of n integers, where row i has bits 0..n-1.
    Returns:
        list of n integers representing rows of M^{-1}.
    """
    if n == 0:
        return []

    # Augment with identity matrix at bit positions n .. 2n-1
    aug = []
    for i in range(n):
        row_val = (matrix_rows[i] & ((1 << n) - 1)) | (1 << (n + i))
        aug.append(row_val)

    for c in range(n):
        pivot_idx = None
        for i in range(c, n):
            if (aug[i] >> c) & 1:
                pivot_idx = i
                break
        if pivot_idx is None:
            raise ValueError("Matrix is not invertible over F2")

        aug[c], aug[pivot_idx] = aug[pivot_idx], aug[c]
        pivot_val = aug[c]

        for i in range(n):
            if i != c and ((aug[i] >> c) & 1):
                aug[i] ^= pivot_val

    # Extract right n x n block
    inv_rows = [(aug[i] >> n) & ((1 << n) - 1) for i in range(n)]
    return inv_rows


def format_pauli_string(bitmask: int, pauli_char: str, length: int) -> str:
    """Formats an integer bitmask as a Pauli string of given length ('I' or pauli_char)."""
    chars = []
    for e in range(length):
        if (bitmask >> e) & 1:
            chars.append(pauli_char)
        else:
            chars.append("I")
    return "".join(chars)
