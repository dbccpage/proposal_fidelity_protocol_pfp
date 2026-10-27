"""Test dual checkers agreement on holonomy and gauge certificates."""

from __future__ import annotations

import json
import pathlib

from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.judge_packet.checkers.algebraic_holonomy_checker import (
    check_algebraic_holonomy_certificate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.judge_packet.checkers.independent_checker import (
    check_independent_holonomy,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.reference_solver.solver import (
    solve,
)

C017_DIR = pathlib.Path(__file__).parent.parent
BASE_DIR = C017_DIR / "judge_packet" / "cases" / "base"


def test_checkers_consensus_on_base_cases():
    base_files = sorted(BASE_DIR.glob("base_*.json"))[:6]
    for bf in base_files:
        case = json.loads(bf.read_text(encoding="utf-8"))
        res, tracer = solve(case)
        assert res["status"] == "SOLVED"

        ok1, reason1 = check_algebraic_holonomy_certificate(case, res)
        ok2, reason2 = check_independent_holonomy(case, res)
        assert ok1, f"Algebraic checker failed on {bf.name}: {reason1}"
        assert ok2, f"Independent checker failed on {bf.name}: {reason2}"

        ok_dual, reason_dual, _ = evaluate_dual(case, res)
        assert ok_dual, f"Dual eval failed on {bf.name}: {reason_dual}"
