"""Mutation Suite Tests for C011 Judge Packet Dual Checkers.

Asserts that both Checker 1 (Exact LP Dual Circulation) and Checker 2 (Exact Primal Potential)
detect and reject 100% of injected corrupted certificates with zero false passes
and zero unhandled crashes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.circulation_checker import (
    verify_circulation_certificate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.potential_checker import (
    verify_potential_certificate,
)

SUITE_DIR = Path(__file__).resolve().parent
MUTATIONS_DIR = SUITE_DIR / "mutations"
if not MUTATIONS_DIR.exists():
    MUTATIONS_DIR = SUITE_DIR

MUTATION_FILES = sorted(MUTATIONS_DIR.glob("mut_*.json"))


def test_mutation_suite_inventory_count():
    """Asserts that all 38+ corrupted certificates exist in the suite."""
    assert len(MUTATION_FILES) >= 38, f"Expected at least 38 mutations, found {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("corrupted_result") or data.get("result")
    desc = data.get("description", mut_path.stem)

    # 1. Test Checker 1 (Exact LP Dual Circulation)
    ok1, msg1 = verify_circulation_certificate(case, corrupted_result)

    # 2. Test Checker 2 (Exact Primal Potential & Coboundary)
    ok2, msg2 = verify_potential_certificate(case, corrupted_result)

    # 3. Both checkers must reject the corrupted certificate independently
    assert not ok1, f"Checker 1 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg1}"
    assert not ok2, f"Checker 2 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg2}"

    # 4. In dual evaluator, verdict must be FAIL
    eval_res = evaluate_dual(case, corrupted_result)
    assert eval_res["verdict"] == "FAIL", (
        f"Mutation {mut_path.name} ({desc}) was NOT killed by dual evaluator! "
        f"Verdict: {eval_res['verdict']}, Checker1: {ok1} ({msg1}), Checker2: {ok2} ({msg2})"
    )
