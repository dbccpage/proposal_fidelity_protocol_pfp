"""Cut-Rank Invariant Computation and Separation Search over F_2 for C024.

AuthorityEffect: None.
"""

from __future__ import annotations

import itertools
from typing import Any

try:
    from .graph import SimpleGraph
except (ImportError, ValueError):
    try:
        from reference_solver.graph import SimpleGraph
    except (ImportError, ValueError):
        from graph import SimpleGraph


def rank_f2(matrix: list[list[int]]) -> int:
    """Computes exact row-rank of binary matrix over F_2 via Gaussian elimination."""
    if not matrix or not matrix[0]:
        return 0

    rows = [row[:] for row in matrix]
    num_rows = len(rows)
    num_cols = len(rows[0])

    rank = 0
    col = 0
    for r in range(num_rows):
        if col >= num_cols:
            break

        # Find pivot in current column
        pivot = -1
        for i in range(r, num_rows):
            if rows[i][col] == 1:
                pivot = i
                break

        if pivot == -1:
            # No pivot in this column, advance column
            col += 1
            # Retry same row r with next column
            while col < num_cols:
                for i in range(r, num_rows):
                    if rows[i][col] == 1:
                        pivot = i
                        break
                if pivot != -1:
                    break
                col += 1
            if pivot == -1:
                break

        # Swap pivot row into place
        rows[r], rows[pivot] = rows[pivot], rows[r]

        # Eliminate other rows below
        for i in range(r + 1, num_rows):
            if rows[i][col] == 1:
                for c in range(col, num_cols):
                    rows[i][c] ^= rows[r][c]

        rank += 1
        col += 1

    return rank


def cut_rank(g: SimpleGraph, subset: list[int] | set[int]) -> int:
    r"""Computes the cut-rank rho_G(A) = rank_{F_2}(Gamma[A, V \ A]).

    The cut-rank is invariant under local complementation (Bouchet 1991, Oum 2005).
    """
    n = g.n
    set_a = set(subset)
    set_b = [v for v in range(n) if v not in set_a]

    if not set_a or not set_b:
        return 0

    list_a = sorted(set_a)
    submat = [[g.adj[u][v] for v in set_b] for u in list_a]
    return rank_f2(submat)


def find_cut_rank_separation(
    g1: SimpleGraph,
    g2: SimpleGraph,
    max_search_subsets: int = 5000,
) -> dict[str, Any] | None:
    """Searches for a subset A with rho_G(A) != rho_{G'}(A).

    Employs structured search:
    1. Singletons (k=1)
    2. Pairs (k=2)
    3. Graph neighborhoods N(v) in g1 and g2
    4. Triples (k=3)
    5. Combinations up to size n // 2
    """
    n = g1.n
    if n != g2.n:
        return None

    # Helper to check a subset
    def check_subset(s: list[int]) -> dict[str, Any] | None:
        r1 = cut_rank(g1, s)
        r2 = cut_rank(g2, s)
        if r1 != r2:
            return {
                "kind": "cut_rank",
                "subset": sorted(s),
                "rank_g": r1,
                "rank_g_prime": r2,
            }
        return None

    tested_count = 0

    # 1. Singletons
    for i in range(n):
        res = check_subset([i])
        if res:
            return res
        tested_count += 1

    # 2. Pairs
    for i in range(n):
        for j in range(i + 1, n):
            res = check_subset([i, j])
            if res:
                return res
            tested_count += 1
            if tested_count >= max_search_subsets:
                return None

    # 3. Neighborhoods of all vertices in both graphs
    for v in range(n):
        nbrs1 = g1.get_neighbors(v)
        if nbrs1:
            res = check_subset(nbrs1)
            if res:
                return res
        nbrs2 = g2.get_neighbors(v)
        if nbrs2:
            res = check_subset(nbrs2)
            if res:
                return res

    # 4. Triples (k=3)
    if n >= 3:
        for triple in itertools.combinations(range(n), 3):
            res = check_subset(list(triple))
            if res:
                return res
            tested_count += 1
            if tested_count >= max_search_subsets:
                return None

    # 5. Higher order subsets up to n // 2
    for k in range(4, (n // 2) + 1):
        for combo in itertools.combinations(range(n), k):
            res = check_subset(list(combo))
            if res:
                return res
            tested_count += 1
            if tested_count >= max_search_subsets:
                return None

    return None


__all__ = [
    "cut_rank",
    "find_cut_rank_separation",
    "rank_f2",
]
