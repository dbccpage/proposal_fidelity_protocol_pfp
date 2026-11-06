"""Test dual checker agreement."""

from __future__ import annotations

from c018_signed_graph_frustration_index.judge_packet.checkers.frustration_checker import (
    check_frustration_certificate,
)
from c018_signed_graph_frustration_index.judge_packet.checkers.independent_checker import (
    check_independent_frustration,
)
from c018_signed_graph_frustration_index.reference_solver.solver import (
    solve,
)


def test_dual_checkers_agree_on_solved_and_unknown():
    cases = [
        {
            "id": "c1",
            "vertices": ["0", "1", "2"],
            "edges": [["0", "1", 1], ["1", "2", 1], ["2", "0", 1]],
        },
        {
            "id": "c2",
            "vertices": ["0", "1", "2"],
            "edges": [["0", "1", -1], ["1", "2", 1], ["2", "0", 1]],
        },
        {"id": "c3", "vertices": ["0", "0"], "edges": [["0", "0", 1]]},
    ]
    for c in cases:
        res, _ = solve(c)
        ok1, _ = check_frustration_certificate(c, res)
        ok2, _ = check_independent_frustration(c, res)
        assert ok1 == ok2
