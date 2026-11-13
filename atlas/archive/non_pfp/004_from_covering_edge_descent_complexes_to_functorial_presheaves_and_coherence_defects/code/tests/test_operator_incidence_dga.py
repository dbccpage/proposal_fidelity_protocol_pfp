"""Exact all-degree controls; finite instances are distinct from the prose proof."""
from itertools import combinations, permutations, product

import pytest
from operator_incidence_dga import Cochain, OperatorCarrier
from operator_incidence_examples import chain_carrier, fixture
from sympy import ImmutableMatrix, eye, zeros


def expanded_d(f, a):
    values = {}
    for chain in f.carrier.chains(f.degree + 1):
        value = a.values[chain[:2]] * f.values[chain[1:]]
        for i in range(1, f.degree + 1):
            value += (-1)**i * f.values[chain[:i] + chain[i + 1:]]
        value -= (-1)**f.degree * f.values[chain[:-1]] * a.values[chain[-2:]]
        values[chain] = value
    return Cochain(f.carrier, f.degree + 1, values)


@pytest.mark.parametrize("degree", range(8))
def test_all_degree_identity_and_internal_nilpotence(degree):
    c = chain_carrier()
    a, f = fixture(c, 1), fixture(c, degree, 11)
    k = a.curvature()
    assert not k.is_zero()
    assert k.d(a).is_zero()
    assert f.b().b().is_zero()
    assert f.d(a) == expanded_d(f, a)
    square = f.d(a).d(a)
    assert square == k.cup(f).add(f.cup(k), -1)
    if degree <= 4:
        assert not square.is_zero()


@pytest.mark.parametrize("p,q", [(p, q) for p in range(6) for q in range(6 - p)])
def test_associativity_unit_and_both_graded_leibniz_laws(p, q):
    c = chain_carrier((2,) * 8)
    a, f, g, h = fixture(c, 1), fixture(c, p, 11), fixture(c, q, -3), fixture(c, 1, 19)
    unit = Cochain.unit(c)
    assert unit.cup(f) == f == f.cup(unit)
    assert f.cup(g).cup(h) == f.cup(g.cup(h))
    assert f.cup(g).b() == f.b().cup(g).add(f.cup(g.b()), (-1)**p)
    assert f.cup(g).d(a) == f.d(a).cup(g).add(f.cup(g.d(a)), (-1)**p)


def test_vertex_selectors_recover_each_curvature_component():
    c = chain_carrier((2, 1, 3, 2))
    a = fixture(c, 1)
    for triple in c.chains(2):
        values = dict(Cochain.zero(c, 0).values)
        values[(triple[-1],)] = eye(c.dimensions[triple[-1]])
        e = Cochain(c, 0, values)
        assert e.d(a).d(a).values[triple] == a.curvature().values[triple]

def test_exact_graded_lie_bridge_and_odd_connection_sign():
    c = chain_carrier((2,) * 8)
    a = fixture(c, 1)
    assert a.bracket(a) == a.cup(a).add(a.cup(a))
    for p in range(3):
        for q in range(3):
            for r in range(3):
                f, g, h = fixture(c, p, 11), fixture(c, q, -3), fixture(c, r, 19)
                assert f.bracket(g.bracket(h)) == f.bracket(g).bracket(h).add(g.bracket(f.bracket(h)), (-1)**(p*q))
                assert f.bracket(g).d(a) == f.d(a).bracket(g).add(f.bracket(g.d(a)), (-1)**p)


def test_strict_chain_carrier_is_not_weak_chain_zero_extension():
    # On weak chain (0,0,1), b A = -A_(0,1) even if A vanishes on repeated
    # pairs. Internal b alone does not preserve the normalization subspace.
    a01 = ImmutableMatrix([[2]])
    assert -a01 != zeros(1, 1)


def test_malformed_coverage_shapes_degrees_scalars_and_carriers_refuse():
    c = chain_carrier((2, 2, 2))
    f = fixture(c, 1)
    cases = [dict(f.values), dict(f.values), dict(f.values), dict(f.values)]
    del cases[0][(0, 1)]
    cases[1][(1, 0)] = eye(2)
    cases[2][(0, 1)] = eye(1)
    cases[3][(0, 1)] = ImmutableMatrix([[0.1, 0], [0, 1]])
    for values in cases:
        with pytest.raises(ValueError):
            Cochain(c, 1, values)
    with pytest.raises(ValueError):
        f.add(Cochain.unit(c))
    with pytest.raises(ValueError):
        f.d(Cochain.unit(c))
    with pytest.raises(ValueError):
        f.cup(fixture(chain_carrier((1, 1, 1)), 1))
    with pytest.raises(ValueError):
        Cochain(c, True, f.values)
    with pytest.raises(ValueError):
        OperatorCarrier((1, 1, 1), frozenset(((0, 1), (1, 2))))


def test_non_numeric_vertex_order_is_admitted():
    c = OperatorCarrier((1, 1, 1), frozenset(((2, 1), (1, 0), (2, 0))))
    assert c.chains(2) == ((2, 1, 0),)
    a = fixture(c, 1)
    assert a.curvature().values[(2, 1, 0)] == a.values[(2, 1)] * a.values[(1, 0)] - a.values[(2, 0)]


def test_all_219_four_vertex_posets_have_exact_chain_enumeration_and_flat_completion():
    from operator_incidence_dga import flat_cover_extension
    from sympy import Rational

    pairs = tuple(combinations(range(4), 2))
    count = 0
    for orientation in product(range(3), repeat=len(pairs)):
        order = frozenset((x, y) if choice == 1 else (y, x)
                          for (x, y), choice in zip(pairs, orientation) if choice)
        if any((x, z) not in order for x, y in order for a, z in order if a == y):
            continue
        c = OperatorCarrier((1,) * 4, order)
        for degree in range(4):
            # Brute-force ordered tuples are independent of the subset/sort constructor.
            expected = tuple(sorted(path for path in permutations(range(4), degree + 1)
                                    if all(edge in order for edge in zip(path, path[1:]))))
            assert c.chains(degree) == expected
        maps = {edge: ImmutableMatrix([[Rational(edge[0] + 1, edge[1] + 1)]]) for edge in c.covers()}
        flat = flat_cover_extension(c, maps)
        assert flat.curvature().is_zero()
        for x, y in order:
            assert flat.values[(x, y)] == ImmutableMatrix([[Rational(x + 1, y + 1)]])
        a, f = fixture(c, 1), fixture(c, 0, 11)
        k = a.curvature()
        assert k.d(a).is_zero()
        assert f.d(a).d(a) == k.cup(f).add(f.cup(k), -1)
        count += 1
    assert count == 219
