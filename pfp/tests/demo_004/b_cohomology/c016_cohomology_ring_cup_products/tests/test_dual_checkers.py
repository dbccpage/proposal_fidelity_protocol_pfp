"""Test dual checkers agreement on cup product certificates."""

from __future__ import annotations

import json
import pathlib

from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.algebraic_cup_checker import (
    check_algebraic_cup_certificate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.independent_checker import (
    check_independent_cup_products,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.solver import (
    solve,
)

C016_DIR = pathlib.Path(__file__).parent.parent
BASE_DIR = C016_DIR / "judge_packet" / "cases" / "base"
POISONED_DIR = C016_DIR / "judge_packet" / "cases" / "poisoned"


def test_checkers_consensus_on_base_cases():
    base_files = sorted(BASE_DIR.glob("base_*.json"))[:4]
    for bf in base_files:
        case = json.loads(bf.read_text(encoding="utf-8"))
        res, tracer = solve(case)
        assert res["status"] == "SOLVED"

        ok1, reason1 = check_algebraic_cup_certificate(case, res)
        ok2, reason2 = check_independent_cup_products(case, res)
        assert ok1, f"Algebraic checker failed on {bf.name}: {reason1}"
        assert ok2, f"Independent checker failed on {bf.name}: {reason2}"

        ok_dual, reason_dual, _ = evaluate_dual(case, res)
        assert ok_dual, f"Dual eval failed on {bf.name}: {reason_dual}"


def test_checkers_reject_fabricated_betti_mismatch_degree():
    case = json.loads((POISONED_DIR / "pois_03.json").read_text(encoding="utf-8"))
    result, _ = solve(case)
    result["witness"]["degree"] = "999"

    ok_dual, reason_dual, details = evaluate_dual(case, result)

    assert not ok_dual
    assert not details["algebraic_checker"]["passed"]
    assert not details["independent_checker"]["passed"]
