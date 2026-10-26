"""Defect, Phi_1 and P_S: worked values and generator-checked properties.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:obstruction:v1
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pfp_lab.core.admission import AdmissionError, BudgetExceededError, ErrorCode
from pfp_lab.core.graph import ConstraintGraph, Edge
from pfp_lab.core.obstruction import (
    SearchBudget,
    check_claims,
    edge_residual,
    obstruction,
    project,
    section_defect,
)
from pfp_lab.tests.strategies import claims_for, graphs, sections_for

F = Fraction
TRIANGLE = ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))
ONES = {("a", "b"): F(1), ("b", "c"): F(1), ("c", "a"): F(1)}


def test_edge_residual_reads_absent_values_as_zero() -> None:
    item = TRIANGLE.edges[0]
    assert edge_residual(item, {}, {}) == 0
    assert edge_residual(item, {("a", "b"): F(5)}, {"b": F(2)}) == 3
    assert edge_residual(item, {("a", "b"): F(5)}, {"a": F(2)}) == 7


def test_paper_005_triangle_values() -> None:
    # Paper 005, Section 4: holonomy 1 + 1 + 1 = 3; the cheapest edge (weight 1) absorbs it.
    zero = {"a": F(0), "b": F(0), "c": F(0)}
    assert section_defect(TRIANGLE, ONES, zero) == 6
    value, potential = obstruction(TRIANGLE, ONES)
    assert value == 3
    assert section_defect(TRIANGLE, ONES, potential) == 3
    repaired = {("a", "b"): F(-2), ("b", "c"): F(1), ("c", "a"): F(1)}
    assert obstruction(TRIANGLE, repaired)[0] == 0
    raised = {("a", "b"): F(5), ("b", "c"): F(0), ("c", "a"): F(0)}
    assert obstruction(TRIANGLE, raised)[0] == 5


def test_hand_checked_path_graph() -> None:
    # A tree carries no cycle, so every claim set is a coboundary.
    path = ConstraintGraph(("x", "y", "z"), (Edge("x", "y", 7), Edge("y", "z", 9)))
    claims = {("x", "y"): F(2, 3), ("y", "z"): F(-5)}
    value, potential = obstruction(path, claims)
    assert value == 0
    assert potential == {"x": 0, "y": F(2, 3), "z": F(-13, 3)}


def test_isolated_vertex_and_empty_graph() -> None:
    single = ConstraintGraph(("solo",), ())
    assert obstruction(single, {}) == (0, {"solo": 0})
    assert project(single, {}, {"solo": F(4)}) == {"solo": F(4)}


def test_check_claims_refusals() -> None:
    with pytest.raises(AdmissionError, match="undeclared edge"):
        check_claims(TRIANGLE, {("b", "a"): F(1)})
    with pytest.raises(AdmissionError, match="exact Fraction"):
        check_claims(TRIANGLE, {("a", "b"): 1})  # type: ignore[dict-item]
    with pytest.raises(AdmissionError, match="exact Fraction"):
        check_claims(TRIANGLE, {("a", "b"): True})  # type: ignore[dict-item]


@pytest.mark.parametrize("steps", [0, -1, True, 1.5])
def test_budget_must_be_positive_integer(steps: object) -> None:
    with pytest.raises(AdmissionError, match="positive integer"):
        SearchBudget(steps)  # type: ignore[arg-type]


def test_budget_counts_down_then_refuses() -> None:
    budget = SearchBudget(2)
    budget.charge()
    budget.charge()
    assert budget.remaining == 0
    with pytest.raises(BudgetExceededError) as caught:
        budget.charge()
    assert caught.value.code is ErrorCode.BUDGET_EXCEEDED


def test_obstruction_stops_at_its_budget() -> None:
    with pytest.raises(BudgetExceededError):
        obstruction(TRIANGLE, ONES, budget=3)
    assert obstruction(TRIANGLE, ONES, budget=50)[0] == 3


@given(st.data())
def test_phi_is_a_lower_bound_attained_by_its_potential(data: st.DataObject) -> None:
    graph = data.draw(graphs())
    claims = data.draw(claims_for(graph))
    section = data.draw(sections_for(graph))
    value, potential = obstruction(graph, claims)
    assert value >= 0
    assert section_defect(graph, claims, potential) == value
    assert value <= section_defect(graph, claims, section)


@given(st.data())
def test_projection_is_idempotent_and_optimal(data: st.DataObject) -> None:
    graph = data.draw(graphs())
    claims = data.draw(claims_for(graph))
    section = data.draw(sections_for(graph))
    once = project(graph, claims, section)
    twice = project(graph, claims, once)
    assert section_defect(graph, claims, once) == obstruction(graph, claims)[0]
    assert section_defect(graph, claims, twice) == section_defect(graph, claims, once)
    differences = {item.key: once[item.target] - once[item.source] for item in graph.edges}
    assert differences == {item.key: twice[item.target] - twice[item.source] for item in graph.edges}


@given(st.data())
def test_obstruction_is_gauge_invariant_and_additive(data: st.DataObject) -> None:
    graph = data.draw(graphs())
    claims = data.draw(claims_for(graph, complete=True))
    shift = data.draw(sections_for(graph))
    shifted = {item.key: claims[item.key] + shift[item.target] - shift[item.source] for item in graph.edges}
    assert obstruction(graph, shifted)[0] == obstruction(graph, claims)[0]
    doubled = {key: 2 * value for key, value in claims.items()}
    assert obstruction(graph, doubled)[0] == 2 * obstruction(graph, claims)[0]


def test_components_add() -> None:
    graph = ConstraintGraph(
        ("a", "b", "c", "x", "y", "z"),
        tuple(Edge(u, v, 1) for u, v in [("a", "b"), ("b", "c"), ("c", "a"), ("x", "y"), ("y", "z"), ("z", "x")]),
    )
    left = {("a", "b"): F(1), ("b", "c"): F(1), ("c", "a"): F(1)}
    right = {("x", "y"): F(2), ("y", "z"): F(0), ("z", "x"): F(0)}
    assert obstruction(graph, left)[0] == 3
    assert obstruction(graph, right)[0] == 2
    assert obstruction(graph, {**left, **right})[0] == 5
