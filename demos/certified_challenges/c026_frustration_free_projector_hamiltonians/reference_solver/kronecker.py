# AuthorityEffect: None.
"""
Exact Kronecker extension of local operator terms to full Hilbert space.

Maps a local matrix on a subset of sites S to an operator on the full space
H = H_0 (x) ... (x) H_{n-1} according to canonical row-major computational basis ordering.
"""

from __future__ import annotations

from typing import List

from .gaussian_rational import GaussianRat


def compute_strides(dims: List[int]) -> List[int]:
    """Compute row-major strides for a list of dimensions."""
    strides = [1] * len(dims)
    for i in range(len(dims) - 2, -1, -1):
        strides[i] = strides[i + 1] * dims[i + 1]
    return strides


def index_to_coords(flat_idx: int, dims: List[int], strides: List[int]) -> List[int]:
    """Convert flat index to multi-index coordinates."""
    coords = [0] * len(dims)
    rem = flat_idx
    for i, s in enumerate(strides):
        coords[i] = rem // s
        rem %= s
    return coords


def coords_to_index(coords: List[int], strides: List[int]) -> int:
    """Convert multi-index coordinates to flat index."""
    return sum(c * s for c, s in zip(coords, strides))


def extend_local_matrix(
    local_dims: List[int],
    support: List[int],
    local_matrix: List[List[GaussianRat]],
) -> List[List[GaussianRat]]:
    """
    Extend a local matrix acting on support sites S to full D x D matrix P (x) I.
    """
    len(local_dims)
    total_d = 1
    for d in local_dims:
        total_d *= d

    global_strides = compute_strides(local_dims)

    support_dims = [local_dims[s] for s in support]
    local_strides = compute_strides(support_dims)
    local_d = 1
    for d in support_dims:
        local_d *= d

    if len(local_matrix) != local_d or any(len(row) != local_d for row in local_matrix):
        raise ValueError(
            f"Local matrix shape mismatch: expected {local_d}x{local_d}, got {len(local_matrix)}x{len(local_matrix[0]) if local_matrix else 0}"
        )

    # Initialize D x D zero matrix
    extended = [[GaussianRat.zero() for _ in range(total_d)] for _ in range(total_d)]

    # Loop over all global row states x and global col states y
    # Optimization: iterate over row states x, and for y, vary only coordinates in support
    for x_idx in range(total_d):
        x_coords = index_to_coords(x_idx, local_dims, global_strides)
        x_local_coords = [x_coords[s] for s in support]
        x_local_idx = coords_to_index(x_local_coords, local_strides)

        # y coordinates must match x outside support
        # We vary y_local_coords over all possible local states
        y_coords = list(x_coords)
        for y_local_idx in range(local_d):
            val = local_matrix[x_local_idx][y_local_idx]
            if not val.is_zero():
                y_local_coords = index_to_coords(y_local_idx, support_dims, local_strides)
                for s_pos, s_site in enumerate(support):
                    y_coords[s_site] = y_local_coords[s_pos]
                y_idx = coords_to_index(y_coords, global_strides)
                extended[x_idx][y_idx] = val

    return extended
