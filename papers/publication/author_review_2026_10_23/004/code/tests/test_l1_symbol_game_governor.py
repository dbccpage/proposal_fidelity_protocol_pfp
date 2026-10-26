"""
Tests for L1 Symbol Game Governor (P_S^2 = P_S and Monotonic Defect Descent).
Reference: Paper 032 (PO-032).
"""

from fractions import Fraction

import pytest

from l1_symbol_game_governor import (
    Cochain1,
    ConstraintGraph,
    Edge,
    L1SymbolGameGovernor,
    boundary_operator_c1_to_c0,
    compute_coboundary,
    compute_phi1,
)


def test_edge_irreflexivity():
    """Self-loops violate irreflexivity and must be refused."""
    with pytest.raises(ValueError, match="violates irreflexivity"):
        Edge(u="A", v="A")


def test_simplicial_boundary_operator():
    """partial_1(u -> v) = v - u."""
    b = boundary_operator_c1_to_c0("A", "B")
    assert b == {"B": 1, "A": -1}


def test_coboundary_operator():
    """(d_0 s)(u, v) = s(v) - s(u)."""
    section = {"A": Fraction(2), "B": Fraction(5)}
    edges = [Edge("A", "B")]
    coboundary = compute_coboundary(section, edges)
    assert coboundary.get("A", "B") == Fraction(3)


def test_zero_defect_characterization():
    """Theorem 4.2: ||Phi_1(c_0)||_1 = 0 iff delta c_0 = W_E."""
    vertices = ("A", "B", "C")
    edges = (Edge("A", "B"), Edge("B", "C"), Edge("C", "A"))
    graph = ConstraintGraph(vertices=vertices, edges=edges)

    # Consistent cycle: A->B = 1, B->C = 2, C->A = -3
    consistent_claims = Cochain1({
        ("A", "B"): Fraction(1),
        ("B", "C"): Fraction(2),
        ("C", "A"): Fraction(-3),
    })
    phi1_val, gauge = compute_phi1(graph, consistent_claims)
    assert phi1_val == Fraction(0)
    assert gauge["B"] - gauge["A"] == Fraction(1)
    assert gauge["C"] - gauge["B"] == Fraction(2)
    assert gauge["A"] - gauge["C"] == Fraction(-3)


def test_inconsistent_cycle_exact_defect():
    """Inconsistent cycle: sum around loop = 1 + 1 + 1 = 3 != 0. Defect must be positive."""
    vertices = ("A", "B", "C")
    edges = (Edge("A", "B"), Edge("B", "C"), Edge("C", "A"))
    graph = ConstraintGraph(vertices=vertices, edges=edges)
    inconsistent_claims = Cochain1({
        ("A", "B"): Fraction(1),
        ("B", "C"): Fraction(1),
        ("C", "A"): Fraction(1),
    })
    phi1_val, _ = compute_phi1(graph, inconsistent_claims)
    assert phi1_val > Fraction(0)
    assert isinstance(phi1_val, Fraction)


def test_idempotent_projection_governor():
    """Verifies P_S(P_S(s)) = P_S(s) using governor.verify_idempotence()."""
    vertices = ("A", "B", "C")
    edges = (Edge("A", "B"), Edge("B", "C"), Edge("C", "A"))
    graph = ConstraintGraph(vertices=vertices, edges=edges)
    governor = L1SymbolGameGovernor(graph=graph)

    governor.step_assert("A", "B", Fraction(1))
    governor.step_assert("B", "C", Fraction(2))
    governor.step_assert("C", "A", Fraction(-3))

    test_section = {"A": Fraction(0), "B": Fraction(0), "C": Fraction(0)}
    assert governor.verify_idempotence(test_section) is True


def test_monotonic_defect_descent_on_repairs():
    """The host refuses any proposal that increases L1 defect."""
    vertices = ("A", "B")
    edges = (Edge("A", "B"),)
    graph = ConstraintGraph(vertices=vertices, edges=edges)
    governor = L1SymbolGameGovernor(graph=graph)

    # Initial assertion creates defect against zero section
    governor.step_assert("A", "B", Fraction(5))
    defect_before = governor.section_defect()
    assert defect_before == Fraction(5)

    # Admissible cut reducing defect to 0
    verdict_admit = governor.step_cut(proposed_section={"A": Fraction(0), "B": Fraction(5)})
    assert verdict_admit.admitted is True
    assert verdict_admit.status == "ExactRepair"
    assert governor.section_defect() == Fraction(0)

    # Inadmissible cut that would increase defect from 0 to 10 is refused
    verdict_refuse = governor.step_cut(proposed_section={"A": Fraction(0), "B": Fraction(-5)})
    assert verdict_refuse.admitted is False
    assert verdict_refuse.status == "DefectIncrease"


def test_assert_monotonicity_and_provisional_mode():
    """Assert move with enforce_monotonicity refuses defect increase and rolls back."""
    vertices = ("A", "B", "C")
    edges = (Edge("A", "B", Fraction(1)), Edge("B", "C", Fraction(1)), Edge("C", "A", Fraction(1)))
    graph = ConstraintGraph(vertices=vertices, edges=edges)
    governor = L1SymbolGameGovernor(graph=graph)

    # Initially zero claims and zero section => defect 0
    assert governor.section_defect() == Fraction(0)

    # An assertion that creates defect 1 is refused when enforce_monotonicity=True
    v_refused = governor.step_assert("A", "B", Fraction(1), enforce_monotonicity=True)
    assert v_refused.admitted is False
    assert v_refused.status == "DefectIncrease"
    assert (("A", "B") not in governor.edge_claims)

    # When marked provisional, it is admitted with ProvisionalAssert status
    v_prov = governor.step_assert("A", "B", Fraction(1), provisional=True)
    assert v_prov.admitted is True
    assert v_prov.status == "ProvisionalAssert"
    assert governor.edge_claims[("A", "B")] == Fraction(1)
