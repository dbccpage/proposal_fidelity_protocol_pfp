"""The tutorial must preserve the native owner and exact input boundary."""
from fractions import Fraction

import pytest

from native_functional import NativeFunctionalUnavailable
from quickstart import (
    Cochain1,
    Edge,
    build_default_meeting_conflict,
    compute_discrete_l1_projection,
    find_spanning_forest_potentials,
)


def test_quickstart_requires_native_pin(monkeypatch):
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_BIN", raising=False)
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_SHA256", raising=False)
    graph, claims = build_default_meeting_conflict().to_graph_and_cochain()
    with pytest.raises(NativeFunctionalUnavailable):
        compute_discrete_l1_projection(graph, claims)


def test_candidate_enumeration_is_retired():
    graph, claims = build_default_meeting_conflict().to_graph_and_cochain()
    with pytest.raises(RuntimeError, match="RUST_FUNCTIONAL_REQUIRED"):
        find_spanning_forest_potentials(graph, claims)


def test_projection_replays_native_and_is_idempotent(native_functional):
    graph, claims = build_default_meeting_conflict().to_graph_and_cochain()
    minimum, potential, projected = compute_discrete_l1_projection(graph, claims)
    assert minimum == Fraction(3)
    assert set(potential) == set(graph.vertices)
    next_minimum, _, reprojected = compute_discrete_l1_projection(graph, projected)
    assert next_minimum == Fraction(0)
    assert reprojected == projected


@pytest.mark.parametrize("bad", [True, float("1")])
def test_approximate_or_boolean_input_is_rejected(bad):
    with pytest.raises(TypeError):
        Edge("a", "b", bad)
    with pytest.raises(TypeError):
        Cochain1({("a", "b"): bad})
