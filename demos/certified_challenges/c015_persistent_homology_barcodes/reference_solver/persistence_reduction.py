"""Persistent Homology Matrix Reduction over F2.

Implements the standard persistent homology reduction algorithm (Edelsbrunner et al. 2002).
Tracks column operations in V so that R = D * V.
Extracts index persistence pairs, essential classes, and rational value barcodes.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .sparse_f2_algebra import xor_columns


def reduce_boundary_matrix(
    D_cols: list[set[int]], n: int
) -> tuple[dict[int, set[int]], dict[int, set[int]], dict[int, int]]:
    """Reduce boundary matrix D into R = D * V by column additions over F2.

    Returns:
    - R_cols: dictionary of columns of R that differ from D_cols
    - V_cols: dictionary of columns of V that differ from unit vector {j}
    - low_map: mapping col -> low(col) for all nonzero columns of R
    """
    R: list[set[int]] = [set(col) for col in D_cols]
    V: list[set[int]] = [{j} for j in range(n)]

    low_to_col: dict[int, int] = {}
    low_map: dict[int, int] = {}

    for j in range(n):
        while R[j]:
            low_j = max(R[j])
            if low_j in low_to_col:
                k = low_to_col[low_j]
                R[j] = xor_columns(R[j], R[k])
                V[j] = xor_columns(V[j], V[k])
            else:
                low_to_col[low_j] = j
                low_map[j] = low_j
                break

    # Extract modified columns for compact serialization
    modified_R: dict[int, set[int]] = {}
    modified_V: dict[int, set[int]] = {}

    for j in range(n):
        if R[j] != D_cols[j]:
            modified_R[j] = R[j]
        if V[j] != {j}:
            modified_V[j] = V[j]

    return modified_R, modified_V, low_map


def extract_pairing_and_barcodes(
    simplices: list[dict[str, Any]],
    low_map: dict[int, int],
    n: int,
    R_cols: dict[int, set[int]] | None = None,
    D_cols: list[set[int]] | None = None,
) -> tuple[list[list[str]], list[str], dict[str, list[list[str]]]]:
    """Extract persistence pairs, essential classes, and value barcodes.

    - A column j with low(j) = i yields pair (i, j).
      Degree is dim(simplex_i).
      Interval is [val(simplex_i), val(simplex_j)).
      Zero-length intervals (val(simplex_i) == val(simplex_j)) are retained in pairs
      but dropped from value barcode.
    - An index i that is not in low_map.values() and whose column in R is empty
      is an essential class born at i with interval [val(simplex_i), inf).
    """
    paired_births = set(low_map.values())
    pairs: list[list[str]] = []
    essential: list[str] = []
    barcode: dict[str, list[list[str]]] = {}

    # Initialize empty barcode lists for dims 0, 1, 2, 3
    max_dim = 0
    for s in simplices:
        dim = int(s["dim"])
        if dim > max_dim:
            max_dim = dim
    for d in range(max_dim + 1):
        barcode[str(d)] = []

    # 1. Persistence pairs
    # Sort pairs by birth index, then death index
    sorted_pairs = sorted([(i, j) for j, i in low_map.items()], key=lambda p: (p[0], p[1]))
    for i, j in sorted_pairs:
        pairs.append([str(i), str(j)])
        s_i = simplices[i]
        s_j = simplices[j]
        deg = int(s_i["dim"])
        val_i = Fraction(s_i["val"])
        val_j = Fraction(s_j["val"])
        if val_i != val_j:
            barcode[str(deg)].append([str(val_i), str(val_j)])

    # 2. Essential classes
    # Essential i is not in low_map.values() AND R[:, i] is empty.
    # Note: If i is not in low_map, that means R[:, i] is zero (if it was non-zero it would be in low_map).
    for i in range(n):
        if i not in paired_births:
            # Check column i of R is indeed 0
            if R_cols is not None and D_cols is not None:
                col_i = R_cols.get(i, D_cols[i])
                if col_i:
                    # Column i is not zero and not in low_map: shouldn't happen in valid reduction
                    continue
            essential.append(str(i))
            s_i = simplices[i]
            deg = int(s_i["dim"])
            val_i = Fraction(s_i["val"])
            barcode[str(deg)].append([str(val_i), "inf"])

    # Sort barcodes canonically: by start value, then end value ("inf" sorted last)
    def bar_key(interval: list[str]) -> tuple[Fraction, Fraction]:
        start = Fraction(interval[0])
        end = Fraction(10**9, 1) if interval[1] == "inf" else Fraction(interval[1])
        return (start, end)

    for deg_str in barcode:
        barcode[deg_str].sort(key=bar_key)

    return pairs, essential, barcode
