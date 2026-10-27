"""Regression checks for the field manual's declared input and evidence boundaries."""

from fractions import Fraction as Q

import pytest

import native_functional
from l1_symbol_game_governor import (
    Cochain1,
    ConstraintGraph,
    Edge,
    L1SymbolGameGovernor,
    compute_phi1,
)
from study_capstone import run_capstone


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)


def _graph():
    return ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))


def _governor():
    governor = L1SymbolGameGovernor(_graph())
    for edge in governor.graph.edges:
        assert governor.step_assert(*edge.key, Q(1)).admitted
    return governor


def _state(governor):
    return dict(governor.edge_claims), dict(governor.section), list(governor.history)


@pytest.mark.parametrize("pair", [("d", "e"), ("a", "c"), ("a", "a")])
def test_offline_scoring_refuses_undeclared_claims(offline, pair):
    with pytest.raises(ValueError, match="absent from declared carrier"):
        compute_phi1(_graph(), Cochain1({pair: Q(9)}))


def test_edge_object_keys_are_scored_after_normalization(offline):
    graph = _graph()
    phi, potential = compute_phi1(graph, Cochain1({edge: Q(1) for edge in graph.edges}))
    assert phi == 3
    assert sum(Q(edge.weight) * abs(1 - (potential[edge.v] - potential[edge.u])) for edge in graph.edges) == 3


@pytest.mark.parametrize("duplicate", ["vertex", "edge"])
def test_scoring_refuses_duplicate_carrier_entries(offline, duplicate):
    graph = _graph()
    vertices = graph.vertices + ("a",) if duplicate == "vertex" else graph.vertices
    edges = graph.edges + (graph.edges[0],) if duplicate == "edge" else graph.edges
    with pytest.raises(ValueError, match="duplicate"):
        compute_phi1(ConstraintGraph(vertices, edges), Cochain1({edge.key: Q(1) for edge in graph.edges}))


@pytest.mark.parametrize("value", [True, False, 0.1])
def test_non_exact_assertion_is_refused_without_state_change(offline, value):
    governor = _governor()
    before = _state(governor)
    verdict = governor.step_assert("a", "b", value)
    assert verdict.status == "IncompleteProposal"
    assert not verdict.admitted
    assert _state(governor) == before


@pytest.mark.parametrize("proposal,status", [
    ({"a": True}, "IncompleteProposal"),
    ({"a": 0.1}, "IncompleteProposal"),
    ({"d": Q(9)}, "CarrierViolation"),
])
def test_section_cut_validates_values_and_carrier(offline, proposal, status):
    governor = _governor()
    before = _state(governor)
    verdict = governor.step_cut(proposed_section=proposal)
    assert verdict.status == status
    assert not verdict.admitted
    assert _state(governor) == before


def test_cut_cannot_silently_ignore_a_second_payload(offline):
    governor = _governor()
    before = _state(governor)
    verdict = governor.step_cut(proposed_section={}, proposed_claims={})
    assert verdict.status == "MoveViolation"
    assert not verdict.admitted
    assert _state(governor) == before


@pytest.mark.parametrize("obligation", [
    "EDGE_MATCH:d,e", "EDGE_MATCH:a,c", "EDGE_MATCH:a", "EDGE_MATCH:a,b,c", "EDGE_MATCH:,",
])
def test_edge_verification_refuses_undeclared_or_malformed_edge(offline, obligation):
    governor = _governor()
    before = _state(governor)
    verdict = governor.step_verify(obligation)
    assert verdict.status == "VerificationFailed"
    assert not verdict.admitted
    assert _state(governor) == before


def test_matching_one_declared_edge_does_not_discharge_global_obstruction(offline):
    governor = _governor()
    verdict = governor.step_cut(proposed_section={"a": Q(0), "b": Q(-2), "c": Q(-1)})
    assert verdict.admitted
    assert governor.step_verify("EDGE_MATCH:b,c").admitted
    assert not governor.step_verify("ZERO_OBSTRUCTION").admitted


def test_zero_obstruction_and_zero_current_defect_are_distinct(offline):
    governor = L1SymbolGameGovernor(_graph())
    for edge, value in zip(governor.graph.edges, (-2, 1, 1)):
        governor.step_assert(*edge.key, Q(value))
    assert governor.primary_obstruction() == 0
    assert governor.section_defect() == 7
    assert governor.step_verify("ZERO_OBSTRUCTION").admitted
    assert not governor.step_verify("ZERO_DEFECT").admitted


def test_native_projection_error_preserves_pre_cut_state(offline, monkeypatch):
    governor = _governor()
    before = _state(governor)
    calls = []

    def calculator(vertices, edges, claims):
        calls.append(dict(claims))
        if len(calls) == 3:
            raise native_functional.NativeFunctionalUnavailable("projection refused")
        return (Q(3) if len(calls) == 1 else Q(0)), {"a": Q(0), "b": Q(-2), "c": Q(-1)}

    monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", "configured-for-boundary-test")
    monkeypatch.setattr(native_functional, "compute_graph_phi1", calculator)
    with pytest.raises(native_functional.NativeFunctionalUnavailable, match="projection refused"):
        governor.step_cut(proposed_claims={("a", "b"): Q(-2), ("b", "c"): Q(1), ("c", "a"): Q(1)})
    assert len(calls) == 3
    assert _state(governor) == before


def test_stationary_score_can_accompany_changed_claims(offline):
    governor = _governor()
    claims = {("a", "b"): Q(2), ("b", "c"): Q(1), ("c", "a"): Q(0)}
    verdict = governor.step_cut(proposed_claims=claims)
    assert verdict.status == "IdempotentStationary"
    assert verdict.admitted
    assert verdict.defect_before == verdict.defect_after == 3
    assert governor.edge_claims == claims


def test_capstone_refusals_repairs_and_snapshot_restore(offline):
    result = run_capstone(verbose=False)
    assert result["calculation_path"] == "python-enumeration"
    assert result["weights"] == (1, 2, 3)
    assert result["original_minimum"] == result["restored_minimum"] == 3
    assert result["refused_state_preserved"]
    assert result["restored_claims"] == {("a", "b"): Q(1), ("b", "c"): Q(1), ("c", "a"): Q(1)}
    assert [row["status"] for row in result["outcomes"]] == [
        "IncompleteProposal", "DefectIncrease", "MonotonicDescent", "ExactRepair", "Verified", "Retracted",
    ]
    assert [row["admitted"] for row in result["outcomes"]] == [False, False, True, True, True, True]
    assert [(row["before"], row["after"]) for row in result["outcomes"][:4]] == [(3, 3), (3, 5), (3, 2), (2, 0)]
    assert result["outcomes"][-1]["metric"] == "D_c"
    assert result["outcomes"][-1]["after"] == 6
