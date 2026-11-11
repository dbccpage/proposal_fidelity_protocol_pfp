"""Exact helpers: rank test, cochain residuals, seal chain, mutation score."""
from __future__ import annotations

from fractions import Fraction
from itertools import product

from pfp_core.workflow_families.exact import (
    Graph,
    classify_linear,
    commitment,
    det,
    mutation_score,
    rank,
    seal_chain,
)


def test_rank_over_q_and_gf2():
    assert rank([[1, 2], [2, 4]]) == 1
    assert rank([[1, 1], [1, -1]]) == 2
    assert rank([[1, 1], [1, -1]], modulus=2) == 1


def test_classify_linear_rouche_capelli():
    assert classify_linear([[1, 1], [1, -1]], [3, 1]).solution == (Fraction(2), Fraction(1))
    assert classify_linear([[1, 1], [2, 2]], [3, 7]).status == 'inconsistent'
    assert classify_linear([[1, 1], [2, 2]], [3, 6]).status == 'underdetermined'


def test_det_is_exact():
    assert det([[2, 1], [1, 1]]) == 1
    assert det([[Fraction(1, 2), 0], [0, 4]]) == 2


def test_fundamental_cycles_annihilate_every_coboundary():
    g = Graph.of([[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [1, 3]])
    assert g.cycle_rank == 3
    for values in product(range(-2, 3), repeat=4):
        c = g.coboundary(dict(enumerate(values)))
        assert all(g.cycle_sum(c, cyc) == 0 for cyc in g.fundamental_cycles())
        assert g.is_exact(c) and g.phi1(c) == 0


def test_residual_detects_a_cycle_obstruction():
    g = Graph.of([[0, 1], [1, 2], [2, 0]])
    c = [1, 1, 1]  # cycle sum 3, not a coboundary over Q
    assert not g.is_exact(c) and g.phi1(c) == 3
    assert g.is_exact([1, 1, 0], modulus=2)


def test_seal_chain_breaks_every_later_link():
    a = seal_chain('seed', [1, 2, 3])
    b = seal_chain('seed', [1, 9, 3])
    assert a[:2] == b[:2] and all(x != y for x, y in zip(a[2:], b[2:], strict=True))
    assert commitment('s', {'x': 1}) != commitment('t', {'x': 1})


def test_mutation_score_counts_kills_and_false_rejections():
    score = mutation_score(lambda x: x % 2 == 0, [0, 2, 4], [1, 3, 'boom'])
    assert score.sound and score.kill_rate == 1
