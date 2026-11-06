"""Regression test for R008-04: a relational CUT may not omit a declared edge.

Before this check, `step_cut(proposed_claims=...)` scored omitted edges as zero
claims, so an empty or partial proposal could reach Phi_1 = 0 and be labelled
ExactRepair. The governor now refuses such a proposal with IncompleteProposal and
leaves its state unchanged. A complete proposal of exact values is scored as before.
"""

from fractions import Fraction

import pytest

from l1_symbol_game_governor import ConstraintGraph, Edge, L1SymbolGameGovernor

ASSERTED = {("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}


def _session():
    graph = ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 2)),
    )
    gov = L1SymbolGameGovernor(graph)
    for (u, v), value in ASSERTED.items():
        gov.step_assert(u, v, value)
    return gov


@pytest.mark.parametrize(
    "proposal",
    [
        {},
        {("a", "b"): Fraction(-2), ("b", "c"): Fraction(1)},
        {("a", "b"): Fraction(0), ("b", "c"): Fraction(0)},
    ],
    ids=["empty", "omits-one-edge", "zeroes-two-omits-one"],
)
def test_cut_omitting_a_declared_edge_is_refused(proposal):
    gov = _session()
    verdict = gov.step_cut(proposed_claims=proposal)
    assert verdict.admitted is False
    assert verdict.status == "IncompleteProposal"
    assert "omits declared edges" in verdict.details
    assert verdict.defect_before == verdict.defect_after == Fraction(3)
    assert gov.edge_claims == ASSERTED
    assert gov.primary_obstruction() == Fraction(3)


@pytest.mark.parametrize("bad_value", [0.5, True], ids=["float", "bool"])
def test_cut_with_a_non_exact_value_is_refused(bad_value):
    gov = _session()
    proposal = {("a", "b"): bad_value, ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}
    verdict = gov.step_cut(proposed_claims=proposal)
    assert verdict.admitted is False
    assert verdict.status == "IncompleteProposal"
    assert "non-exact values" in verdict.details
    assert gov.edge_claims == ASSERTED


def test_complete_explicit_proposal_is_still_scored():
    """Explicit values for every edge are judged by the arithmetic, as before.

    Zeroing every claim explicitly satisfies the graph check; acceptance does not
    make the replaced claims factually correct.
    """
    gov = _session()
    zeros = {("a", "b"): Fraction(0), ("b", "c"): Fraction(0), ("c", "a"): Fraction(0)}
    verdict = gov.step_cut(proposed_claims=zeros)
    assert verdict.admitted is True
    assert verdict.status == "ExactRepair"
    assert verdict.defect_before == Fraction(3)
    assert verdict.defect_after == Fraction(0)
