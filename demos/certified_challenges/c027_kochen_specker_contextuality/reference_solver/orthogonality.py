# AuthorityEffect: None.
"""
Exact orthogonality graph and context enumeration for C027.

Computes exact dot products in Q(sqrt(2)) and enumerates all complete
contexts (maximal cliques of mutually orthogonal rays of size d in {3, 4}).
"""

from __future__ import annotations

from typing import List, Set, Tuple

try:
    from .quad_field import QuadRat
except (ImportError, ValueError):
    try:
        from c027_kochen_specker_contextuality.reference_solver.quad_field import QuadRat
    except (ImportError, ValueError):
        from quad_field import QuadRat


def dot_product(u: List[QuadRat], v: List[QuadRat]) -> QuadRat:
    """Computes exact dot product sum_k u_k * v_k in Q(sqrt(2))."""
    res = QuadRat.zero()
    for uk, vk in zip(u, v):
        res = res + (uk * vk)
    return res


def compute_orthogonality_graph(
    rays: List[List[QuadRat]],
) -> Tuple[List[Set[int]], List[Tuple[int, int]]]:
    """
    Computes adjacency sets and edge list of the orthogonality graph.
    Two rays i != j are orthogonal iff u_i . u_j == 0 in Q(sqrt(2)).
    """
    n = len(rays)
    adj: List[Set[int]] = [set() for _ in range(n)]
    edges: List[Tuple[int, int]] = []

    for i in range(n):
        for j in range(i + 1, n):
            dp = dot_product(rays[i], rays[j])
            if dp.is_zero():
                adj[i].add(j)
                adj[j].add(i)
                edges.append((i, j))

    return adj, edges


def enumerate_contexts(
    dimension: int,
    rays: List[List[QuadRat]],
    adj: List[Set[int]],
) -> List[List[int]]:
    """
    Enumerates all complete orthogonal bases (contexts of size d)
    drawn from the canonical rays.
    """
    n = len(rays)
    contexts: List[List[int]] = []

    if dimension == 3:
        for i in range(n):
            adj_i = adj[i]
            for j in sorted(adj_i):
                if j <= i:
                    continue
                # Mutual neighbors k > j
                common = adj_i.intersection(adj[j])
                for k in sorted(common):
                    if k > j:
                        contexts.append([i, j, k])

    elif dimension == 4:
        for i in range(n):
            adj_i = adj[i]
            for j in sorted(adj_i):
                if j <= i:
                    continue
                common_ij = adj_i.intersection(adj[j])
                for k in sorted(common_ij):
                    if k <= j:
                        continue
                    common_ijk = common_ij.intersection(adj[k])
                    for idx_l in sorted(common_ijk):
                        if idx_l > k:
                            contexts.append([i, j, k, idx_l])

    return contexts
