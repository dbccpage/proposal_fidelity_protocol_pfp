"""Hypothesis strategies for small admitted graphs, claims and sections.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:strategies:v1
"""

from __future__ import annotations

from fractions import Fraction

from hypothesis import strategies as st

from pfp_lab.core.graph import ConstraintGraph, Edge, EdgeKey

NAMES = ("a", "b", "c", "d", "e")


@st.composite
def graphs(draw: st.DrawFn, max_vertices: int = 5, max_edges: int = 7) -> ConstraintGraph:
    count = draw(st.integers(min_value=1, max_value=max_vertices))
    vertices = NAMES[:count]
    pairs = [(u, v) for u in vertices for v in vertices if u != v]
    chosen = draw(st.lists(st.sampled_from(pairs), unique=True, max_size=max_edges)) if pairs else []
    weights = draw(st.lists(st.integers(1, 4), min_size=len(chosen), max_size=len(chosen)))
    edges = tuple(Edge(u, v, w) for (u, v), w in zip(chosen, weights, strict=True))
    return ConstraintGraph(vertices, edges)


small_rationals = st.builds(
    Fraction,
    st.integers(min_value=-6, max_value=6),
    st.integers(min_value=1, max_value=3),
)


@st.composite
def claims_for(draw: st.DrawFn, graph: ConstraintGraph, complete: bool = False) -> dict[EdgeKey, Fraction]:
    keys = [item.key for item in graph.edges]
    if not complete:
        keys = draw(st.lists(st.sampled_from(keys), unique=True)) if keys else []
    return {key: draw(small_rationals) for key in keys}


@st.composite
def sections_for(draw: st.DrawFn, graph: ConstraintGraph) -> dict[str, Fraction]:
    return {name: draw(small_rationals) for name in graph.vertices}
