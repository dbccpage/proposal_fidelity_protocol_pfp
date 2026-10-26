"""Test reference solver logic and DDC trace."""

from __future__ import annotations

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.reference_solver.solver import (
    solve,
)


def test_solver_demo6_hollow_tetrahedron_obstructed():
    import json
    import pathlib

    ex_path = pathlib.Path(__file__).parent.parent / "participant_packet" / "examples" / "ex01.json"
    case = json.loads(ex_path.read_text(encoding="utf-8"))
    res, tracer = solve(case)
    assert res["status"] == "SOLVED"
    assert res["mode"] == "Q"
    assert res["verdict"] == "OBSTRUCTED"
    assert res["phi2"] == "1"


def test_solver_non_nilpotent_boundary_out_of_scope():
    case = {
        "id": "t_bad",
        "vertices": ["v0", "v1"],
        "edges": ["e0"],
        "faces": ["f0"],
        "d1": {"e0": {"v0": 1, "v1": -1}},
        "d2": {"f0": {"e0": 1}},  # d1 * d2 != 0!
        "mode": "Q",
        "B": {"f0": "1"},
        "weights": {"f0": "1"},
    }
    res, tracer = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["reason"] == "BOUNDARY_NOT_NILPOTENT"
