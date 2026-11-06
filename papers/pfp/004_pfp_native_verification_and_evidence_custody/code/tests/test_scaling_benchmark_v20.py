"""
Native adapter and retired benchmark contract tests.
Reference: Paper 032 (PO-032).
"""

from fractions import Fraction

import pytest

from l1_symbol_game_governor import (
    Cochain1,
    ConstraintGraph,
    Edge,
    compute_phi1,
)
from scaling_benchmark_v20 import (
    run_scaling_benchmark,
    solve_phi1_lp_exact_basis,
)


def test_legacy_solver_alias_preserves_native_cycle_result():
    """Both names call one governor function; this is an API compatibility check.

    That function asks the pinned native calculator first and falls back to exact
    Python enumeration when the native call raises (see docs/completion_supplement.md).
    """
    # 3-cycle with weights 1, 2, 3
    vertices = ("A", "B", "C")
    edges = (Edge("A", "B", weight=1), Edge("B", "C", weight=2), Edge("C", "A", weight=3))
    graph = ConstraintGraph(vertices=vertices, edges=edges)
    claims = Cochain1({
        ("A", "B"): Fraction(1),
        ("B", "C"): Fraction(1),
        ("C", "A"): Fraction(1),
    })

    phi1_enum, gauge_enum = compute_phi1(graph, claims)
    phi1_lp, gauge_lp = solve_phi1_lp_exact_basis(graph, claims)

    assert phi1_lp == phi1_enum == Fraction(3)
    # Verify exact rational type
    assert isinstance(phi1_lp, Fraction)
    for v, val in gauge_lp.items():
        assert isinstance(val, Fraction)


def test_retired_speedup_comparison_refuses():
    """One solver exposed through two names cannot measure an independent speedup."""
    with pytest.raises(RuntimeError, match="BENCHMARK_RETIRED"):
        run_scaling_benchmark(vertex_counts=(4, 6, 10, 20, 50), seed=123)


def test_lp_edge_cases_and_trivial_graphs():
    """Tests trivial single vertex and tree graphs."""
    g_trivial = ConstraintGraph(vertices=("A",), edges=())
    phi_triv, gauge_triv = solve_phi1_lp_exact_basis(g_trivial, Cochain1({}))
    assert phi_triv == Fraction(0)
    assert gauge_triv == {"A": Fraction(0)}

    # Tree of 4 vertices: Phi_1 must be exactly 0
    tree_g = ConstraintGraph(
        vertices=("A", "B", "C", "D"),
        edges=(Edge("A", "B"), Edge("B", "C"), Edge("C", "D")),
    )
    tree_claims = Cochain1({
        ("A", "B"): Fraction(3, 2),
        ("B", "C"): Fraction(-5),
        ("C", "D"): Fraction(7, 3),
    })
    phi_tree, gauge_tree = solve_phi1_lp_exact_basis(tree_g, tree_claims)
    assert phi_tree == Fraction(0)
    assert gauge_tree["B"] - gauge_tree["A"] == Fraction(3, 2)
    assert gauge_tree["C"] - gauge_tree["B"] == Fraction(-5)
    assert gauge_tree["D"] - gauge_tree["C"] == Fraction(7, 3)


def test_lp_exact_certificate_preserves_large_rational_denominator():
    """The exact path must not truncate rational inputs to a fixed denominator."""
    graph = ConstraintGraph(vertices=("A", "B"), edges=(Edge("A", "B"),))
    claim = Fraction(1, 10001)

    phi1, gauge = solve_phi1_lp_exact_basis(
        graph,
        Cochain1({("A", "B"): claim}),
    )

    assert phi1 == Fraction(0)
    assert gauge["B"] - gauge["A"] == claim
