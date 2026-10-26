"""Test dual checkers agreement and independent verification."""

from __future__ import annotations

import json
import pathlib

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c015_persistent_homology_barcodes.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c015_persistent_homology_barcodes.judge_packet.checkers.f2_algebraic_checker import (
    check_algebraic_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c015_persistent_homology_barcodes.judge_packet.checkers.independent_checker import (
    check_independent_persistence,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c015_persistent_homology_barcodes.reference_solver.solver import (
    solve,
)

C015_DIR = pathlib.Path(__file__).parent.parent
BASE_DIR = C015_DIR / "judge_packet" / "cases" / "base"


def test_checkers_consensus_on_base_cases():
    base_files = sorted(BASE_DIR.glob("base_*.json"))[:5]
    for bf in base_files:
        case = json.loads(bf.read_text(encoding="utf-8"))
        res, tracer = solve(case)
        assert res["status"] == "SOLVED"

        ok1, reason1 = check_algebraic_certificate(case, res)
        ok2, reason2 = check_independent_persistence(case, res)
        assert ok1, f"Algebraic checker failed on {bf.name}: {reason1}"
        assert ok2, f"Independent checker failed on {bf.name}: {reason2}"

        ok_dual, reason_dual, _ = evaluate_dual(case, res)
        assert ok_dual, f"Dual eval failed on {bf.name}: {reason_dual}"
