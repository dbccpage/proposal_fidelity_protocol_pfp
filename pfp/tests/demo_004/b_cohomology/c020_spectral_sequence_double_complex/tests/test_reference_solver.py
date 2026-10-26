"""Test C020 reference solver on public examples."""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.reference_solver.solver import (
    solve,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "participant_packet" / "examples"


def test_worked_example_columns():
    with (EXAMPLES_DIR / "c020_ex01_worked_columns.json").open(encoding="utf-8") as f:
        case = json.load(f)
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["filtration"] == "columns"
    assert res["E2"] == {"2,0": "1", "0,1": "1"}
    assert res["differentials"] == [{"r": "2", "from": "2,0", "rank": "1"}]
    assert res["Einf"] == {}
    assert res["tot_homology"] == {}


def test_worked_example_rows():
    with (EXAMPLES_DIR / "c020_ex02_worked_rows.json").open(encoding="utf-8") as f:
        case = json.load(f)
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["filtration"] == "rows"
    assert res["E2"] == {}
    assert res["differentials"] == []
    assert res["Einf"] == {}
    assert res["tot_homology"] == {}


def test_out_of_scope_cases():
    with (EXAMPLES_DIR / "c020_ex08_out_of_scope_noncommuting.json").open(encoding="utf-8") as f:
        case = json.load(f)
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["reason"] == "DH_DV_NOT_COMMUTING"
