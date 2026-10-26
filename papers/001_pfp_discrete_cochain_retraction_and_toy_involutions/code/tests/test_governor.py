"""
Targeted tests for L1SymbolGameGovernor.
"""

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from symbol_game_governor import (
    ConstraintGraph,
    Edge,
    L1SymbolGameGovernor,
    MoveType,
    StepVerdict,
)


def test_edge_and_graph_invariants():
    e1 = Edge("a", "b", weight=1)
    e2 = Edge("a", "b", weight=1)
    e3 = Edge("b", "c", weight=2)

    # Exact-type equality
    assert e1 == e2
    assert e1 != e3
    assert e1 != ("a", "b", 1)  # Rejects cross-type comparison

    # Irreflexivity: self-loops forbidden
    with pytest.raises(ValueError, match="violates irreflexivity"):
        Edge("a", "a", weight=1)

    # Positive weight
    with pytest.raises(ValueError, match="positive integer"):
        Edge("a", "b", weight=0)

    g = ConstraintGraph(("a", "b", "c"), (e1, e3))
    assert g == ConstraintGraph(("a", "b", "c"), (e1, e3))
    assert g != ("a", "b", "c")


def test_governor_monotonic_descent_and_rejection():
    vertices = ("a", "b", "c")
    edges = (
        Edge("a", "b", weight=1),
        Edge("b", "c", weight=2),
        Edge("c", "a", weight=2),
    )
    graph = ConstraintGraph(vertices, edges)
    gov = L1SymbolGameGovernor(graph)

    # Assert edges
    s1 = gov.execute_move(MoveType.ASSERT, {"u": "a", "v": "b", "value": 1})
    assert s1.admitted
    assert s1.verdict == StepVerdict.ASSERTED

    s2 = gov.execute_move(MoveType.ASSERT, {"u": "b", "v": "c", "value": 2})
    assert s2.admitted

    s3 = gov.execute_move(MoveType.ASSERT, {"u": "c", "v": "a", "value": 2})
    assert s3.admitted
    init_defect = gov.compute_section_defect(gov.section)

    # Defect-increasing CUT proposal must be REFUSED
    bad_cut = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": 10, "c": -10}})
    assert not bad_cut.admitted
    assert bad_cut.verdict == StepVerdict.REFUSAL
    assert "DefectIncrease" in bad_cut.feedback

    # Non-moving stationary CUT proposal must be REFUSED
    loop_cut = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": 0, "c": 0}})
    assert not loop_cut.admitted
    assert loop_cut.verdict == StepVerdict.REFUSAL
    assert "IdempotentStationaryLoop" in loop_cut.feedback

    # Gradient-consistent section CUT must descend
    phi1, best_pot = gov.compute_phi_1()
    good_cut = gov.execute_move(MoveType.CUT, {"potentials": {k: int(v) for k, v in best_pot.items()}})
    assert good_cut.admitted
    assert good_cut.defect <= init_defect


def test_governor_exact_verification():
    vertices = ("a", "b", "c")
    edges = (
        Edge("a", "b", weight=1),
        Edge("b", "c", weight=1),
        Edge("c", "a", weight=1),
    )
    graph = ConstraintGraph(vertices, edges)
    # Gradient-consistent: (0->1: 1, 1->2: 2, 2->0: -3)
    gov = L1SymbolGameGovernor(graph, initial_claims={("a", "b"): 1, ("b", "c"): 2, ("c", "a"): -3})

    # Prior to potential assignment: defect > 0, verify must fail
    v_premature = gov.execute_move(MoveType.VERIFY, {})
    assert not v_premature.admitted
    assert v_premature.verdict == StepVerdict.REFUSAL

    # Set exact potential: s(a)=0, s(b)=1, s(c)=3
    cut = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": 1, "c": 3}})
    assert cut.admitted
    assert cut.defect == 0

    # Verify now succeeds
    v_exact = gov.execute_move(MoveType.VERIFY, {})
    assert v_exact.admitted
    assert v_exact.verdict == StepVerdict.EXACT
    assert "ZERO_OBSTRUCTION confirmed" in v_exact.feedback


def test_fractional_string_cut_keeps_half_and_positive_optimum_is_hold():
    vertices = ("a", "b", "c")
    edges = (
        Edge("a", "b", weight=1),
        Edge("b", "c", weight=2),
        Edge("c", "a", weight=2),
    )
    graph = ConstraintGraph(vertices, edges)
    claims = {("a", "b"): 1, ("b", "c"): Fraction(1, 2), ("c", "a"): 2}
    exact = L1SymbolGameGovernor(graph, initial_claims=claims)
    admitted = exact.execute_move(
        MoveType.CUT, {"potentials": {"a": "0", "b": "-5/2", "c": "-2"}}
    )
    assert admitted.admitted
    assert admitted.defect == Fraction(7, 2)
    assert admitted.verdict == StepVerdict.HOLD

    truncated = L1SymbolGameGovernor(graph, initial_claims=claims)
    widened = truncated.execute_move(
        MoveType.CUT, {"potentials": {"a": 0, "b": -2, "c": -2}}
    )
    assert widened.admitted
    assert widened.defect == 4

    demo1 = L1SymbolGameGovernor(graph)
    demo1.execute_move(MoveType.ASSERT, {"u": "a", "v": "b", "value": 1})
    demo1.execute_move(MoveType.ASSERT, {"u": "b", "v": "c", "value": 2})
    demo1.execute_move(MoveType.ASSERT, {"u": "c", "v": "a", "value": 2})
    _phi1, best_pot = demo1.compute_phi_1()
    held = demo1.execute_move(
        MoveType.CUT, {"potentials": {k: str(v) for k, v in best_pot.items()}}
    )
    assert held.admitted
    assert held.defect == 5
    assert held.verdict == StepVerdict.HOLD
