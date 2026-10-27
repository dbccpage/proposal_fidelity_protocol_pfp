"""Tests for Cut-Rank Invariant over F_2 (C024)."""

from __future__ import annotations

from c024_local_clifford_graph_state_equivalence.reference_solver.cut_rank import (
    cut_rank,
    find_cut_rank_separation,
    rank_f2,
)
from c024_local_clifford_graph_state_equivalence.reference_solver.graph import (
    SimpleGraph,
)


def test_rank_f2():
    mat = [
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 0],
    ]
    # Row 0 + Row 1 = Row 2 over F_2 -> rank 2
    assert rank_f2(mat) == 2


def test_cut_rank_invariance():
    # P4: 0-1-2-3
    g = SimpleGraph(4, [[0, 1], [1, 2], [2, 3]])
    gp = g.local_complementation(1)

    # For EVERY subset A of {0, 1, 2, 3}, cut_rank(g, A) == cut_rank(gp, A)
    for mask in range(16):
        subset = [i for i in range(4) if (mask & (1 << i))]
        assert cut_rank(g, subset) == cut_rank(gp, subset)


def test_cut_rank_separation():
    # Non-equivalent graphs
    g1 = SimpleGraph(4, [[0, 1], [1, 2], [2, 3]])
    g2 = SimpleGraph(4, [[0, 1], [2, 3]])  # 2 disjoint edges

    sep = find_cut_rank_separation(g1, g2)
    assert sep is not None
    assert sep["kind"] == "cut_rank"
    assert sep["rank_g"] != sep["rank_g_prime"]
