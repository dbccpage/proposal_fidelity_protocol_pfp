"""Test reference solver logic and DDC trace."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.b_cohomology.c018_signed_graph_frustration_index.reference_solver.solver import (
    solve,
)


def test_solver_balanced_triangle():
    case = {
        "id": "t_bal",
        "vertices": ["0", "1", "2"],
        "edges": [["0", "1", 1], ["1", "2", 1], ["2", "0", 1]],
    }
    res, tracer = solve(case)
    assert res["status"] == "SOLVED"
    assert res["l"] == "0"
    letters = [s.letter for s in tracer.trace]
    assert "C" in letters and "T" in letters


def test_solver_all_negative_k4():
    case = {
        "id": "t_k4",
        "vertices": ["0", "1", "2", "3"],
        "edges": [
            ["0", "1", -1],
            ["0", "2", -1],
            ["0", "3", -1],
            ["1", "2", -1],
            ["1", "3", -1],
            ["2", "3", -1],
        ],
    }
    res, tracer = solve(case)
    assert res["status"] == "SOLVED"
    assert res["l"] == "2"
    assert res["lower_bound"]["kind"] == "exhaustive"


def test_solver_self_loop_out_of_scope():
    case = {"id": "t_loop", "vertices": ["0", "1"], "edges": [["0", "0", 1], ["0", "1", 1]]}
    res, tracer = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["reason"] == "SELF_LOOP"


def test_solver_unknown_for_large_dense_graph():
    # Dense graph with 25 vertices and random edges
    import random

    rng = random.Random(42)
    v_list = [str(i) for i in range(25)]
    e_list = []
    for i in range(25):
        for j in range(i + 1, 25):
            if rng.random() < 0.4:
                e_list.append([str(i), str(j), -1 if rng.random() < 0.5 else 1])
    case = {"id": "t_large_rand", "vertices": v_list, "edges": e_list}
    res, tracer = solve(case)
    assert res["status"] in ("SOLVED", "UNKNOWN")
    if res["status"] == "UNKNOWN":
        assert res["refusal"] == "OPTIMALITY_UNCERTIFIED"
        assert int(res["lower"]) <= int(res["upper"])
