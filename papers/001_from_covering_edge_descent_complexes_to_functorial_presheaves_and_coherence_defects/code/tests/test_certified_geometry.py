from fractions import Fraction as Q

import pytest
from certified_geometry import atan_interval, deficit, dihedral, pi_interval, root_interval


def star(n, orthogonal=False):
    hinge, cycle = (0, 1, 2), tuple(range(3, 3 + n))
    edges = {}
    for i in range(n):
        s = hinge + (cycle[i], cycle[(i + 1) % n])
        for a in range(5):
            for b in range(a + 1, 5):
                x, y = sorted((s[a], s[b]))
                edges[x, y] = Q(2 if orthogonal and x != 0 else 1)
    return hinge, cycle, edges


@pytest.mark.parametrize("x", [Q(0), Q(1, 7), Q(2), Q(144, 49), Q(10000, 3)])
def test_independent_bisection_root_brackets(x):
    bound = root_interval(x, Q(1, 10000))
    assert bound.lo**2 <= x <= bound.hi**2
    assert bound.width <= Q(1, 10000)


def test_independent_euler_pi_and_atan_identities():
    eps = Q(1, 100000000)
    pi = pi_interval(eps)
    assert Q(31415926, 10000000) < pi.lo < pi.hi < Q(31415927, 10000000)
    assert pi.width <= eps
    for x in (Q(0), Q(1, 239), Q(1, 2), Q(3, 4), Q(1), Q(2), Q(10000)):
        a, b = atan_interval(x, eps), atan_interval(-x, eps)
        assert a.width <= eps and b.lo == -a.hi and b.hi == -a.lo
    one = atan_interval(Q(1), eps)
    assert one.lo <= pi.hi / 4 and pi.lo / 4 <= one.hi


def test_regular_and_obtuse_geometric_angles_are_metric_bound():
    squared = [[Q(i != j) for j in range(5)] for i in range(5)]
    a, normal = dihedral(squared, Q(1, 1000000))
    assert normal == (Q(2, 3), Q(2, 3), Q(1, 6))
    assert Q(1318, 1000) < a.lo < a.hi < Q(1319, 1000)
    assert a.width <= Q(1, 1000000)
    # Gram diag=1; its two normal vectors have dot=-1/2.
    squared = [
        [
            Q(0) if i == j else Q(1) if i == 0 or j == 0 else Q(3) if {i, j} == {3, 4} else Q(2)
            for j in range(5)
        ]
        for i in range(5)
    ]
    angle, normal = dihedral(squared, Q(1, 100000))
    assert normal == (Q(1), Q(1), Q(-1, 2))
    pi = pi_interval(Q(1, 100000))
    assert angle.lo <= 2 * pi.hi / 3 and 2 * pi.lo / 3 <= angle.hi
    assert angle.width <= Q(1, 100000)


@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_closed_metric_star_has_verified_deficit_sign(n):
    bound = deficit(*star(n), Q(1, 100000))
    assert bound.width <= Q(1, 100000)
    assert bound.lo > 0 if n <= 4 else bound.hi < 0


def test_flat_zero_is_retained_without_a_fabricated_separation_promise():
    bound = deficit(*star(4, True), Q(1, 1000000))
    assert bound.lo <= 0 <= bound.hi and bound.width <= Q(1, 1000000)


def test_bad_metric_coverage_precision_and_inexact_data_are_refused():
    hinge, cycle, edges = star(4)
    with pytest.raises(ValueError):
        deficit(hinge, (), {}, Q(1, 10))
    del edges[0, 1]
    with pytest.raises(ValueError):
        deficit(hinge, cycle, edges, Q(1, 10))
    with pytest.raises(ValueError):
        atan_interval(Q(1), Q(0))
    with pytest.raises(ValueError):
        atan_interval(1.0, Q(1, 10))
    with pytest.raises(ValueError):
        root_interval(Q(-1), Q(1, 10))
    squared = [[Q(i != j) for j in range(5)] for i in range(5)]
    squared[1][2] = squared[2][1] = Q(100)
    with pytest.raises(ValueError):
        dihedral(squared, Q(1, 10))
