import pytest
from loss_curvature import norms, path_separation, question_loss
from operator_incidence_dga import Cochain, OperatorCarrier
from sympy import ImmutableMatrix as M
from sympy import Rational as Q
from sympy import eye, zeros


def test_stochastic_flat_projection_erases_protected_question():
    p = M([[Q(1, 2), Q(1, 2), 0], [Q(1, 2), Q(1, 2), 0], [0, 0, 1]])
    assert p * p == p == p.T
    assert all(x >= 0 for x in p)
    assert all(sum(p[:, j]) == 1 for j in range(3))
    assert norms(p)[0] == 1
    assert question_loss(p, M([1, 0, 0]), M([0, 1, 0]), M([[1, 0, 0]])) == (True, 1)
    carrier = OperatorCarrier((3, 3, 3), frozenset({(0, 1), (1, 2), (0, 2)}))
    r = Cochain(carrier, 1, {edge: p for edge in carrier.chains(1)})
    assert r.curvature().is_zero()
    e = Cochain.unit(carrier)
    assert e.d(r).d(r).is_zero()
    with pytest.raises(ValueError, match="separation"):
        path_separation(p * p, p, M([1, -1, 0]), M([[1, 0, 0]]), Q(1))


def test_supplied_qubit_dephasing_has_same_information_curvature_separation():
    p = M.diag(1, 0, 0, 1)
    plus = M([[Q(1, 2), Q(1, 2)], [Q(1, 2), Q(1, 2)]])
    minus = M([[Q(1, 2), -Q(1, 2)], [-Q(1, 2), Q(1, 2)]])
    for rho in (plus, minus):
        assert rho * rho == rho and rho.trace() == 1
        assert sorted(rho.eigenvals()) == [0, 1]
    assert p * p - p == zeros(4)
    assert question_loss(p, M(list(plus)), M(list(minus)), M([[0, 1, 1, 0]])) == (True, 2)
    p0, p1 = M.diag(1, 0), M.diag(0, 1)
    assert p0.T * p0 + p1.T * p1 == eye(2)
    assert p0 * plus * p0 + p1 * plus * p1 == eye(2) / 2


@pytest.mark.parametrize("scale", [Q(1, 100), Q(1), Q(7)])
def test_sharp_bound_is_scale_sensitive(scale):
    c = path_separation(M([[scale]]), M([[0]]), M([2]), M([[3]]), 6 * scale)
    assert c.induced_floor == c.entry_floor == c.induced_norm == c.entry_norm == scale


def test_rectangular_bounds_and_duplicate_records_do_not_amplify_norm():
    b = M([[2, -1, 0], [0, 3, 1]])
    c = path_separation(b, zeros(2, 3), M([1, -2, 1]), M([[2, -1]]), Q(13))
    assert c.separation == 13
    assert c.induced_norm >= c.induced_floor
    assert c.entry_norm >= c.entry_floor
    witnesses = [c] * 12
    assert all(w.induced_norm == 4 for w in witnesses)


@pytest.mark.parametrize(
    "b,r,d,q,eta",
    [
        (M([[1]]), M([[1]]), M([1]), M([[1]]), Q(1)),
        (M([[1]]), M([[0]]), M([0]), M([[1]]), Q(1)),
        (M([[1]]), M([[0]]), M([1]), M([[0]]), Q(1)),
        (M([[1]]), M([[0]]), M([1]), M([[1]]), Q(0)),
        (M([[1]]), M([[0]]), M([1]), M([[1]]), True),
        (M([[1.0]]), M([[0]]), M([1]), M([[1]]), Q(1)),
        (M([[1, 0]]), M([[0]]), M([1]), M([[1]]), Q(1)),
    ],
)
def test_false_separation_premises_are_refused(b, r, d, q, eta):
    with pytest.raises(ValueError):
        path_separation(b, r, d, q, eta)
