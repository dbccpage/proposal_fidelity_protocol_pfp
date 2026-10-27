"""Basis-change no-go, conditional flat completion, and countermodels."""
import pytest
from operator_incidence_dga import Cochain, OperatorCarrier, PathDependent, flat_cover_extension
from operator_incidence_examples import chain_carrier, fixture
from sympy import ImmutableMatrix, Rational, eye


def gauge(c):
    gs, hs = [], []
    for x, dim in enumerate(c.dimensions):
        g, h = eye(dim), eye(dim)
        if dim == 1:
            g[0, 0], h[0, 0] = 2, Rational(1, 2)
        else:
            g[0, 1], h[0, 1] = x + 1, -(x + 1)
        gs.append(ImmutableMatrix(g))
        hs.append(ImmutableMatrix(h))
    return gs, hs


@pytest.mark.parametrize("degree", range(4))
def test_vertex_gauge_intertwines_all_operations_and_retains_nonzero_curvature(degree):
    c = chain_carrier((2, 1, 3, 2, 1, 2))
    a, f = fixture(c, 1), fixture(c, degree, 11)
    g, h = gauge(c)
    ag, fg = a.gauge(g, h), f.gauge(g, h)
    assert ag.curvature() == a.curvature().gauge(g, h)
    assert not ag.curvature().is_zero()
    assert ag.gauge(h, g) == a
    assert f.d(a).gauge(g, h) == fg.d(ag)
    assert f.b().gauge(g, h) == fg.b()
    assert f.cup(a).gauge(g, h) == fg.cup(ag)


def diamond():
    return OperatorCarrier((1,) * 4, frozenset(((0, 1), (0, 2), (0, 3), (1, 3), (2, 3))))


def covers(last_denominator):
    return {edge: ImmutableMatrix([[Rational(1, d)]]) for edge, d in
            [((0, 1), 2), ((1, 3), 2), ((0, 2), 2), ((2, 3), last_denominator)]}


def test_unique_flat_cover_extension_and_path_obstruction():
    c = diamond()
    flat = flat_cover_extension(c, covers(2))
    assert flat.values[(0, 3)] == ImmutableMatrix([[Rational(1, 4)]])
    assert flat.curvature().is_zero()
    with pytest.raises(PathDependent) as caught:
        flat_cover_extension(c, covers(3))
    assert caught.value.endpoints == (0, 3)
    assert set(caught.value.paths) == {(0, 1, 3), (0, 2, 3)}
    assert Rational(1, 4) != Rational(1, 6)


def test_cover_replacement_is_distinct_from_gauge_rectification():
    c = diamond()
    flat = flat_cover_extension(c, covers(2))
    values = dict(flat.values)
    values[(0, 3)] = ImmutableMatrix([[0]])
    curved = Cochain(c, 1, values)
    g, h = gauge(c)
    assert not curved.curvature().is_zero()
    assert not curved.gauge(g, h).curvature().is_zero()
    assert flat.gauge(g, h).curvature().is_zero()
    assert flat_cover_extension(c, {edge: curved.values[edge] for edge in c.covers()}) == flat


def test_conditional_normal_form_needs_mixed_terms():
    c = chain_carrier((2,) * 5)
    a = fixture(c, 1)
    flat = flat_cover_extension(c, {edge: a.values[edge] for edge in c.covers()})
    residual = a.add(flat, -1)
    assert all(residual.values[edge].is_zero_matrix for edge in c.covers())
    expansion = flat.cup(residual).add(residual.cup(flat)).add(residual.cup(residual)).add(residual.b())
    assert a.curvature() == expansion
    assert not flat.cup(residual).is_zero()
    assert not residual.cup(flat).is_zero()


def test_cover_and_inverse_failures_are_not_flatness_certificates():
    c = diamond()
    for malformed in [dict(list(covers(2).items())[:-1]), {**covers(2), (0, 3): eye(1)}]:
        with pytest.raises(ValueError):
            flat_cover_extension(c, malformed)
    flat = flat_cover_extension(c, covers(2))
    g, h = gauge(c)
    h[0] = eye(1)
    with pytest.raises(ValueError):
        flat.gauge(g, h)
    with pytest.raises(ValueError):
        flat.gauge([], [])
    with pytest.raises(ValueError):
        flat.gauge([ImmutableMatrix([[0]])] * 4, [eye(1)] * 4)


@pytest.mark.parametrize("t", [Rational(0), Rational(1, 4), Rational(1, 2), Rational(3, 4), Rational(1)])
def test_l1_minimizers_do_not_define_a_canonical_gauge(t):
    assert abs(1 - t) + abs(t) == 1
    # Global lower bound for any real t follows from |1-t|+|t| >= |1|.


def test_two_incomparable_vertices_have_no_flat_extension_obligation():
    c = OperatorCarrier((1, 2), frozenset())
    flat = flat_cover_extension(c, {})
    assert flat.degree == 1 and not flat.values and flat.curvature().is_zero()


def test_flat_cover_extension_compares_saturated_paths_of_different_lengths():
    c = OperatorCarrier((1,) * 5, frozenset(
        ((0, 1), (1, 2), (2, 4), (0, 2), (1, 4), (0, 4), (0, 3), (3, 4))))
    maps = {edge: ImmutableMatrix([[Rational(edge[0] + 1, edge[1] + 1)]]) for edge in c.covers()}
    flat = flat_cover_extension(c, maps)
    assert flat.values[(0, 4)] == ImmutableMatrix([[Rational(1, 5)]])
    assert flat.curvature().is_zero()
    maps[(3, 4)] = ImmutableMatrix([[Rational(3, 5)]])
    with pytest.raises(PathDependent) as caught:
        flat_cover_extension(c, maps)
    assert caught.value.endpoints == (0, 4)
    assert set(caught.value.paths) == {(0, 1, 2, 4), (0, 3, 4)}
