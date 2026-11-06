"""Tests for Orbit Search and Solver Entry Point (C024)."""

from __future__ import annotations

import c024_local_clifford_graph_state_equivalence.reference_solver.solver as solver_module
import pytest
from c024_local_clifford_graph_state_equivalence.reference_solver.graph import (
    SimpleGraph,
)
from c024_local_clifford_graph_state_equivalence.reference_solver.orbit_search import (
    decide_local_equivalence,
)
from c024_local_clifford_graph_state_equivalence.reference_solver.solver import (
    solve,
)


def test_orbit_search_equivalent():
    g = SimpleGraph(4, [[0, 1], [1, 2], [2, 3]])
    gp = g.local_complementation(1)

    equiv, seq, wit = decide_local_equivalence(g, gp)
    assert equiv is True
    assert seq is not None

    # Replay sequence
    curr = g.copy()
    for v in seq:
        curr = curr.local_complementation(v)
    assert curr == gp


def test_orbit_search_non_equivalent():
    g1 = SimpleGraph(4, [[0, 1], [1, 2], [2, 3]])
    g2 = SimpleGraph(4, [[0, 1], [0, 3], [1, 2], [2, 3]])

    equiv, seq, wit = decide_local_equivalence(g1, g2)
    assert equiv is False
    assert wit is not None


def test_orbit_search_budget_exhaustion_is_unknown_not_false():
    g = SimpleGraph(4, [[0, 1], [1, 2], [2, 3]])
    gp = g.local_complementation(1)

    equiv, seq, wit = decide_local_equivalence(g, gp, max_orbit_states=2)

    assert equiv is None
    assert seq is None
    assert wit == {
        "kind": "orbit_search_budget_exhausted",
        "states_visited": 2,
        "max_orbit_states": 2,
    }


def test_solver_maps_budget_exhaustion_to_typed_unknown(monkeypatch: pytest.MonkeyPatch):
    witness = {
        "kind": "orbit_search_budget_exhausted",
        "states_visited": 25000,
        "max_orbit_states": 25000,
    }
    monkeypatch.setattr(
        solver_module,
        "decide_local_equivalence",
        lambda _g, _gp: (None, None, witness),
    )
    case = {
        "id": "test_budget",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]],
    }

    result = solver_module.solve(case)

    assert result == {
        "id": "test_budget",
        "status": "UNKNOWN",
        "refusal_code": "ORBIT_SEARCH_BUDGET_EXHAUSTED",
        "witness": witness,
    }


def test_solve_interface():
    case = {
        "id": "test_p4",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["equivalent"] is True
    assert res["sequence"] == [1]
