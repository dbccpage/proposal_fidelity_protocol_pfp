"""Exact counterexamples and admission regressions from the 2026-10-02 review."""

from fractions import Fraction

import pytest

from covering_edge_poset import FinitePoset
from curvature_cochain import compute_curvature_operator, is_flat_system
from curved_bicomplex import decompose_normal_form
from exact import exact_equal
from exactsym import Matrix
from quantum_sheaf_contextuality import (
    EmpiricalModel, build_bell_sheaf_system, solve_cech_contextuality_obstruction,
)
from restriction_system import RestrictionMap, RestrictionSystem


def scalar_system(poset, values):
    return RestrictionSystem(poset, {node: 1 for node in poset.elements},
                             [RestrictionMap(c, a, Matrix([[value]]))
                              for (a, c), value in values.items()])


@pytest.mark.parametrize("values", [(1, 2), (2, 1), (1, 1)])
def test_duplicate_restrictions_are_refused_instead_of_overwritten(values):
    poset = FinitePoset(["a", "b"], [("a", "b")])
    with pytest.raises(ValueError, match="duplicate restriction"):
        RestrictionSystem(poset, {"a": 1, "b": 1},
                          [RestrictionMap("b", "a", Matrix([[v]])) for v in values])


def test_nonidentity_self_restriction_is_refused():
    poset = FinitePoset(["a"], [])
    with pytest.raises(ValueError, match="must be the identity"):
        scalar_system(poset, {("a", "a"): 2})
    assert exact_equal(scalar_system(poset, {("a", "a"): 1}).get_restriction("a", "a").matrix,
                       Matrix.eye(1))


def test_unknown_and_reflexive_nodes_do_not_create_cover_or_identity_witnesses():
    poset = FinitePoset(["a", "b"], [("a", "b")])
    system = scalar_system(poset, {("a", "b"): 1})
    assert poset.is_covering("a", "a") is False
    assert poset.is_covering("ghost", "ghost") is False
    assert poset.saturated_chains("ghost", "ghost") == []
    assert system.has_restriction("ghost", "ghost") is False
    with pytest.raises(KeyError, match="not a declared comparable pair"):
        system.get_restriction("ghost", "ghost")


@pytest.mark.parametrize("chain", [[], ["ghost"]])
def test_chain_composition_requires_declared_nonempty_chain(chain):
    poset = FinitePoset(["a"], [])
    with pytest.raises(ValueError, match="chain"):
        scalar_system(poset, {}).chain_composite(chain)


def test_master_normal_form_requires_commuting_cover_paths():
    poset = FinitePoset(["a", "x", "y", "d"],
                        [("a", "x"), ("x", "d"), ("a", "y"), ("y", "d")])
    system = scalar_system(poset, {("a", "x"): Fraction(1, 2), ("x", "d"): Fraction(1, 2),
                                   ("a", "y"): Fraction(1, 3), ("y", "d"): Fraction(1, 2),
                                   ("a", "d"): 0})
    assert system.chain_composite(["a", "x", "d"])[0, 0] == Fraction(1, 4)
    assert system.chain_composite(["a", "y", "d"])[0, 0] == Fraction(1, 6)
    with pytest.raises(ValueError, match="Path A hypothesis violated"):
        decompose_normal_form(system)


def test_master_normal_form_decomposition_on_commuting_covers():
    poset = FinitePoset(["a", "b", "c"], [("a", "b"), ("b", "c")])
    system = scalar_system(poset, {("a", "b"): Fraction(1, 2), ("b", "c"): Fraction(1, 2),
                                   ("a", "c"): 0})
    result = decompose_normal_form(system)
    assert is_flat_system(result.flat_background)
    for pair in poset.comparable_pairs():
        a, c = pair.lower, pair.upper
        assert exact_equal(result.flat_background.get_restriction(a, c).matrix + result.correction[(a, c)],
                           system.get_restriction(a, c).matrix)
    for edge in poset.covering_edges:
        assert exact_equal(result.correction[(edge.lower, edge.upper)], Matrix.zeros(1, 1))
    assert exact_equal(compute_curvature_operator(system, "a", "b", "c").matrix,
                       -result.correction[("a", "c")])


def test_normal_form_curvature_keeps_mixed_terms_on_longer_triples():
    poset = FinitePoset(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("c", "d")])
    system = scalar_system(poset, {("a", "b"): Fraction(1, 2), ("b", "c"): Fraction(1, 2),
                                   ("c", "d"): Fraction(1, 2), ("a", "c"): Fraction(1, 3),
                                   ("b", "d"): Fraction(1, 3), ("a", "d"): Fraction(1, 10)})
    result = decompose_normal_form(system)
    a = result.correction
    hat = result.flat_background
    curvature = compute_curvature_operator(system, "a", "b", "d").matrix
    expected = (hat.get_restriction("a", "b").matrix * a[("b", "d")]
                + a[("a", "b")] * hat.get_restriction("b", "d").matrix
                + a[("a", "b")] * a[("b", "d")] - a[("a", "d")])
    assert curvature[0, 0] == Fraction(1, 15)
    assert exact_equal(curvature, expected)
    assert not exact_equal(curvature, -a[("a", "d")])


def test_flat_bell_restrictions_do_not_imply_global_probability_extension():
    system = build_bell_sheaf_system()
    assert is_flat_system(system)
    receipt = solve_cech_contextuality_obstruction(EmpiricalModel.pr_box())
    assert receipt.is_contextual
    assert receipt.obstruction_distance == 2
    assert receipt.duality_gap == 0


def test_algebraic_contextuality_rational_enclosure():
    lower, upper = Fraction(828, 1000), Fraction(829, 1000)
    assert (1 + lower / 2) ** 2 == Fraction(499849, 250000) < 2
    assert (1 + upper / 2) ** 2 == Fraction(8003241, 4000000) > 2
    assert upper - lower == Fraction(1, 1000)
    # An interval shifted above the target fails the exact lower-endpoint check.
    assert not (1 + upper / 2) ** 2 < 2
