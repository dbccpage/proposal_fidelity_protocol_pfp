"""Constraint graph admission and connected components.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:graph:v1
"""

from __future__ import annotations

import pytest

from pfp_lab.core.admission import AdmissionError
from pfp_lab.core.graph import MAX_EDGES, MAX_VERTICES, MAX_WEIGHT, ConstraintGraph, Edge


def triangle() -> ConstraintGraph:
    return ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))


def test_edge_key_and_lookup() -> None:
    graph = triangle()
    assert graph.edges[1].key == ("b", "c")
    assert graph.edge("b", "c") == Edge("b", "c", 2)
    assert graph.edge("c", "b") is None
    assert graph.has_vertex("a")
    assert not graph.has_vertex("z")


@pytest.mark.parametrize(
    ("source", "target", "weight", "message"),
    [
        ("a", "a", 1, "self-loop"),
        ("a", "b", 0, "between 1 and"),
        ("a", "b", MAX_WEIGHT + 1, "between 1 and"),
        ("a", "b", True, "must be an integer"),
        ("a b", "c", 1, "edge source"),
        ("a", "", 1, "edge target"),
    ],
)
def test_edge_refusals(source: str, target: str, weight: int, message: str) -> None:
    with pytest.raises(AdmissionError, match=message):
        Edge(source, target, weight)


def test_edge_accepts_weight_bounds() -> None:
    assert Edge("a", "b", 1).weight == 1
    assert Edge("a", "b", MAX_WEIGHT).weight == MAX_WEIGHT


def test_graph_refusals() -> None:
    with pytest.raises(AdmissionError, match="1 to"):
        ConstraintGraph((), ())
    with pytest.raises(AdmissionError, match="1 to"):
        ConstraintGraph(tuple(f"v{i}" for i in range(MAX_VERTICES + 1)), ())
    with pytest.raises(AdmissionError, match="duplicate vertex"):
        ConstraintGraph(("a", "a"), ())
    with pytest.raises(AdmissionError, match="leaves the declared carrier"):
        ConstraintGraph(("a",), (Edge("a", "b", 1),))
    with pytest.raises(AdmissionError, match="leaves the declared carrier"):
        ConstraintGraph(("b",), (Edge("a", "b", 1),))
    with pytest.raises(AdmissionError, match="duplicate directed edge"):
        ConstraintGraph(("a", "b"), (Edge("a", "b", 1), Edge("a", "b", 2)))
    with pytest.raises(AdmissionError, match="vertices must be a tuple"):
        ConstraintGraph(["a"], ())  # type: ignore[arg-type]
    with pytest.raises(AdmissionError, match="edges must be a tuple"):
        ConstraintGraph(("a",), [])  # type: ignore[arg-type]
    with pytest.raises(AdmissionError, match="Edge values"):
        ConstraintGraph(("a", "b"), (("a", "b", 1),))  # type: ignore[arg-type]
    with pytest.raises(AdmissionError, match="vertex"):
        ConstraintGraph(("a", "no spaces"), ())


def test_graph_size_bounds() -> None:
    names = tuple(f"v{i}" for i in range(MAX_VERTICES))
    assert len(ConstraintGraph(names, ()).vertices) == MAX_VERTICES
    pairs = [(a, b) for a in names[:5] for b in names[:5] if a != b]
    edges = tuple(Edge(a, b, 1) for a, b in pairs[: MAX_EDGES + 1])
    assert len(ConstraintGraph(names, edges[:MAX_EDGES]).edges) == MAX_EDGES
    with pytest.raises(AdmissionError, match="at most"):
        ConstraintGraph(names, edges)


def test_opposite_edges_are_distinct() -> None:
    graph = ConstraintGraph(("a", "b"), (Edge("a", "b", 1), Edge("b", "a", 1)))
    assert graph.components() == (("a", "b"),)


def test_components() -> None:
    graph = ConstraintGraph(
        ("c", "a", "x", "b", "lonely", "y"),
        (Edge("a", "b", 1), Edge("c", "b", 1), Edge("y", "x", 1)),
    )
    assert graph.components() == (("a", "b", "c"), ("x", "y"), ("lonely",))


def test_documented_limits() -> None:
    # The contract documents 12 vertices, 16 edges and weights 1 to 1000.
    assert (MAX_VERTICES, MAX_EDGES, MAX_WEIGHT) == (12, 16, 1000)


def test_values_are_frozen() -> None:
    import dataclasses

    graph = triangle()
    with pytest.raises(dataclasses.FrozenInstanceError):
        graph.vertices = ()  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        graph.edges[0].weight = 5  # type: ignore[misc]
