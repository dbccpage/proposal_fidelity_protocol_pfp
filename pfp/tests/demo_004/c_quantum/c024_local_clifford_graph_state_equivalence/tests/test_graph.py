"""Tests for SimpleGraph and Local Complementation (C024)."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.graph import (
    SimpleGraph,
    validate_simple_graph,
)


def test_graph_validation():
    # Valid graph
    ok, defect = validate_simple_graph(4, [[0, 1], [1, 2], [2, 3]])
    assert ok is True
    assert defect is None

    # Invalid: self loop
    ok, defect = validate_simple_graph(4, [[0, 0], [1, 2]])
    assert ok is False
    assert defect["kind"] == "self_loop"

    # Invalid: duplicate edge
    ok, defect = validate_simple_graph(4, [[0, 1], [1, 0]])
    assert ok is False
    assert defect["kind"] == "duplicate_edge"

    # Invalid: vertex out of bounds
    ok, defect = validate_simple_graph(4, [[0, 4]])
    assert ok is False
    assert defect["kind"] == "vertex_out_of_bounds"

    # Invalid: num_vertices out of bounds
    ok, defect = validate_simple_graph(17, [[0, 1]])
    assert ok is False
    assert defect["kind"] == "num_vertices_out_of_bounds"


def test_local_complementation_involution():
    # (G * v) * v = G
    edges = [[0, 1], [1, 2], [2, 3], [0, 3]]
    g = SimpleGraph(4, edges)
    for v in range(4):
        g_prime = g.local_complementation(v)
        g_double = g_prime.local_complementation(v)
        assert g == g_double


def test_star_to_complete_graph():
    # Star S5 with center 0 -> local complementation at 0 produces complete graph K5
    s5_edges = [[0, 1], [0, 2], [0, 3], [0, 4]]
    star = SimpleGraph(5, s5_edges)
    k5 = star.local_complementation(0)

    # Every pair in K5 should be an edge
    for u in range(5):
        for v in range(u + 1, 5):
            assert k5.has_edge(u, v) is True


def test_isolated_vertex_complementation():
    # G with isolated vertex 3
    edges = [[0, 1], [1, 2]]
    g = SimpleGraph(4, edges)
    # Complementation at isolated vertex does nothing
    assert g.local_complementation(3) == g
