"""Independent controls and countermodels; written proofs quantify beyond them."""

from fractions import Fraction as Q
from itertools import combinations

import pytest
from observed_transport import (
    Arrow,
    Cell,
    LinearReport,
    ObservedObject,
    block_lift,
    gauge_loop,
    l1_norm,
    metric_holonomy,
    observed_compositors,
    path_error,
    path_product,
)
from operator_incidence_dga import Cochain
from operator_incidence_examples import chain_carrier, fixture
from sympy import ImmutableMatrix as M
from sympy import eye, zeros


def test_heterogeneous_corner_cup_deletion_and_selector_are_faithful():
    c = chain_carrier((2, 1, 3, 2, 1))
    for degree in range(5):
        f = fixture(c, degree, 7)
        for chain, value in f.values.items():
            lifted = block_lift(c, chain[0], chain[-1], value)
            row, col = sum(c.dimensions[: chain[0]]), sum(c.dimensions[: chain[-1]])
            assert lifted[row : row + value.rows, col : col + value.cols] == value
        for chain, value in f.b().values.items():
            direct = sum(
                (
                    (-1) ** i
                    * block_lift(c, chain[0], chain[-1], f.values[chain[:i] + chain[i + 1 :]])
                    for i in range(1, len(chain) - 1)
                ),
                zeros(sum(c.dimensions)),
            )
            assert direct == block_lift(c, chain[0], chain[-1], value)
        for other_degree in range(5 - degree):
            g = fixture(c, other_degree, 13)
            for chain, value in f.cup(g).values.items():
                assert block_lift(c, chain[0], chain[-1], value) == (
                    block_lift(c, chain[0], chain[degree], f.values[chain[: degree + 1]])
                    * block_lift(c, chain[degree], chain[-1], g.values[chain[degree:]])
                )
    r = fixture(c, 1)
    for chain, k in r.curvature().values.items():
        x, _, z = chain
        assert block_lift(c, x, z, k) * block_lift(c, z, z, eye(c.dimensions[z])) == block_lift(
            c, x, z, k
        )
        e = dict(Cochain.zero(c, 0).values)
        e[(z,)] = eye(c.dimensions[z])
        assert Cochain(c, 0, e).d(r).d(r).values[chain] == k
    with pytest.raises(ValueError):
        block_lift(c, 0, 1, eye(2))


def test_minimal_question_report_unique_descent_and_functorial_composition():
    source = LinearReport(M([[1, 2, 0], [2, 4, 0], [0, 0, 3]]))
    target = LinearReport(M([[1, 0]]))
    final = LinearReport(M([[2, 0]]))
    assert source.basis.rows == source.questions.rank() == 2
    x, y = M([4, 1, 7]), M([2, 2, 7])
    assert source.questions * x == source.questions * y
    assert source.basis * x == source.basis * y
    assert source.decoder * source.basis == source.questions
    t, s = M([[1, 2, 0], [0, 0, 1]]), M([[3, 0], [7, 2]])
    dt, ds = source.descend(target, t), target.descend(final, s)
    assert dt * source.basis == target.basis * t
    assert source.descend(final, s * t) == ds * dt
    assert dt == target.basis * t * source.section
    # An independently reconstructed representative has exactly the same answers.
    assert source.questions * source.section * source.basis * x == source.questions * x
    assert LinearReport(zeros(2, 3)).basis.shape == (0, 3)
    with pytest.raises(ValueError):
        target.descend(target, M([[1, 1], [0, 1]]))


def object3(identifier="x", full=False):
    return ObservedObject(identifier, LinearReport(eye(3) if full else M([[1, 0, 0]])))


def test_typed_2cells_mixed_horizontal_term_interchange_and_visible_refusals():
    o = object3()
    f0, g0 = Arrow.identity(o), Arrow.identity(o)
    f1 = Arrow(o, o, M([[1, 0, 0], [0, 1, 1], [0, 0, 1]]))
    f2 = Arrow(o, o, M([[1, 0, 0], [0, 2, 1], [0, 1, 1]]))
    g1 = Arrow(o, o, M([[1, 0, 0], [0, 1, 0], [0, 1, 1]]))
    g2 = Arrow(o, o, M([[1, 0, 0], [0, 3, 0], [0, 1, 2]]))
    a, b = Cell(f0, f1), Cell(g0, g1)
    horizontal = b.horizontal_after(a)
    assert b.difference * a.difference != zeros(3)
    assert (
        horizontal.difference
        == g0.operator * a.difference + b.difference * f0.operator + b.difference * a.difference
    )
    assert horizontal.difference != g0.operator * a.difference + b.difference * f0.operator
    a2, b2 = Cell(f1, f2), Cell(g1, g2)
    assert horizontal.then(b2.horizontal_after(a2)) == b.then(b2).horizontal_after(a.then(a2))
    assert Cell(f0, f0).then(a) == a == a.then(Cell(f1, f1))
    with pytest.raises(ValueError):
        a.then(b)
    with pytest.raises(ValueError):
        Arrow(o, o, M([[1, 1, 0], [0, 1, 0], [0, 0, 1]]))
    with pytest.raises(ValueError):
        Arrow.identity(object3("other")).after(f0)
    full = object3(full=True)
    with pytest.raises(ValueError):
        Cell(Arrow.identity(full), Arrow(full, full, f1.operator))


def test_observer_sensitive_lax_compositors_units_and_full_pentagon():
    c = chain_carrier((3,) * 5)
    values = {
        (x, z): M([[1, 0, 0], [x + 1, 1 + z, x + z + 1], [z, 1, 2 + x]]) for x, z in c.strict_order
    }
    r = Cochain(c, 1, values)
    arrows, cells = observed_compositors(r, [M([[1, 0, 0]])] * 5)
    assert not r.curvature().is_zero()
    for (x, y, z), cell in cells.items():
        assert cell.difference == -r.curvature().values[x, y, z]
    for x, y, z, w in combinations(range(5), 4):
        left = (
            cells[x, y, z].horizontal_after(Cell(arrows[z, w], arrows[z, w])).then(cells[x, z, w])
        )
        right = (
            Cell(arrows[x, y], arrows[x, y]).horizontal_after(cells[y, z, w]).then(cells[x, y, w])
        )
        assert left == right
    a, b, d, e = (arrows[i, i + 1] for i in range(4))
    parenthesizations = [
        a.after(b).after(d).after(e),
        a.after(b.after(d)).after(e),
        a.after(b).after(d.after(e)),
        a.after(b.after(d).after(e)),
        a.after(b.after(d.after(e))),
    ]
    assert all(p == parenthesizations[0] for p in parenthesizations)
    comparisons = [Cell(p, arrows[0, 4]) for p in parenthesizations]
    assert all(cell == comparisons[0] for cell in comparisons)
    for arrow in arrows.values():
        assert Arrow.identity(arrow.target).after(arrow) == arrow
        assert arrow.after(Arrow.identity(arrow.source)) == arrow
    with pytest.raises(ValueError):
        observed_compositors(r, [eye(3)] * 5)


@pytest.mark.parametrize("length", [1, 2, 5, 16])
def test_path_bound_is_sharp_and_unweighted_local_budget_is_insufficient(length):
    residual, terms, bound = path_error([M([2])] * length, [M([1])] * length)
    assert residual == M([2**length - 1]) and bound == 2**length - 1
    assert sum(terms, zeros(1)) == residual
    amplified, _, paid = path_error([M([1]), M([100])], [M([0]), M([100])])
    assert l1_norm(amplified) == paid == 100
    assert sum(l1_norm(a - b) for a, b in zip([M([1]), M([100])], [M([0]), M([100])])) == 1


def test_noncommuting_heterogeneous_paths_and_malformed_profiles():
    a = [M([[1, 2], [3, 4], [5, 6]]), M([[2, 0, 1]]), M([[3], [7]])]
    b = [M([[1, 0], [0, 1], [0, 0]]), M([[1, 2, 3]]), M([[2], [1]])]
    residual, _, bound = path_error(a, b)
    assert residual == path_product(a, 2) - path_product(b, 2)
    assert l1_norm(residual) <= bound
    for x, y in [
        ([], []),
        ([eye(2)], [eye(3)]),
        ([eye(2)], [eye(2), eye(2)]),
        ([eye(2), eye(3)], [eye(2), eye(3)]),
    ]:
        with pytest.raises(ValueError):
            path_error(x, y)


def metric_star(cosines):
    hinge, cycle = (0, 1, 2), tuple(range(3, 3 + len(cosines)))
    edges = {}
    for i, c in enumerate(cosines):
        ids = hinge + (cycle[i], cycle[(i + 1) % len(cycle)])
        for a, b in combinations(range(5), 2):
            edges[tuple(sorted((ids[a], ids[b])))] = (
                Q(1) if a == 0 else Q(2) - 2 * c if (a, b) == (3, 4) else Q(2)
            )
    return hinge, cycle, edges


def test_metric_to_angle_gluing_gauge_basepoint_and_winding_countermodel():
    links, rotations, w, _ = metric_holonomy(
        *metric_star([Q(3, 5), Q(0), Q(-3, 5), Q(5, 13)]), Q(1, 100000)
    )
    assert tuple((Q(c), Q(s)) for c, s in rotations) == (
        (Q(3, 5), Q(4, 5)),
        (Q(0), Q(1)),
        (Q(-3, 5), Q(4, 5)),
        (Q(5, 13), Q(12, 13)),
    )
    frames = []
    for i in range(4):
        g = eye(4)
        a, b = i % 2, 2 + i % 2
        g[a, a] = g[b, b] = Q(3, 5)
        g[a, b] = Q(-4, 5)
        g[b, a] = Q(4, 5)
        frames.append(M(g))
    for base in range(4):
        assert gauge_loop(links, frames, base) == frames[base] * w * frames[base].T
    _, _, flat, d0 = metric_holonomy(*metric_star([Q(0)] * 4), Q(1, 100000))
    _, _, winding, d8 = metric_holonomy(*metric_star([Q(0)] * 8), Q(1, 100000))
    assert flat == winding == eye(4)
    assert d0.lo <= 0 <= d0.hi and d8.hi < -6
    with pytest.raises(ValueError):
        metric_holonomy(*metric_star([Q(1, 2)] * 4), Q(1, 10000))
    with pytest.raises(ValueError):
        gauge_loop(links, [2 * eye(4)] * 4, 0)


def test_additive_operator_bianchi_does_not_force_metric_loop_identity():
    links, _, w, d = metric_holonomy(*metric_star([Q(0)] * 3), Q(1, 10000))
    late, early = links[2] * links[1], links[0]
    c = chain_carrier((4,) * 4)
    r = Cochain(
        c,
        1,
        {
            (0, 1): late,
            (1, 2): early,
            (0, 2): eye(4),
            (2, 3): eye(4),
            (1, 3): early,
            (0, 3): eye(4),
        },
    )
    k = r.curvature()
    assert k.values[0, 1, 2] == w - eye(4)
    assert not k.is_zero() and k.d(r).is_zero()
    assert len(k.d(r).values) == 1  # nonempty quadruple check
    assert w != eye(4) and d.lo > 0
