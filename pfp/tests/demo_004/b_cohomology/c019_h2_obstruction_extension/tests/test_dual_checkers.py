"""Test dual checker agreement."""

from __future__ import annotations

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.judge_packet.checkers.h2_obstruction_checker import (
    check_h2_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.judge_packet.checkers.independent_checker import (
    check_independent_h2,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.reference_solver.solver import (
    solve,
)


def test_dual_checkers_agree():
    case = {
        "id": "t_zero",
        "vertices": ["v0", "v1", "v2"],
        "edges": ["e01", "e12", "e02"],
        "faces": ["f0"],
        "d1": {"e01": {"v0": -1, "v1": 1}, "e12": {"v1": -1, "v2": 1}, "e02": {"v0": -1, "v2": 1}},
        "d2": {"f0": {"e01": 1, "e12": 1, "e02": -1}},
        "mode": "Q",
        "B": {"f0": "0"},
        "weights": {"f0": "1"},
    }
    res, _ = solve(case)
    ok1, _ = check_h2_certificate(case, res)
    ok2, _ = check_independent_h2(case, res)
    assert ok1 == ok2 is True
