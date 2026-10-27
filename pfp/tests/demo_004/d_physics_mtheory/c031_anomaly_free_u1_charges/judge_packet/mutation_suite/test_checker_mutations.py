"""Mutation Suite Tests for C031 Judge Packet Dual Checkers.

Asserts that both Checker 1 (Exact Algebraic Certifier) and Checker 2 (Independent MITM Engine)
detect and reject 100% of injected corrupted certificates with zero false passes
and zero unhandled crashes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.u1_algebraic_checker import (
    verify_chiral_u1_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.u1_mitm_checker import (
    verify_mitm_certificate,
)

SUITE_DIR = Path(__file__).resolve().parent
MUTATIONS_DIR = SUITE_DIR / "mutations"
if not MUTATIONS_DIR.exists():
    MUTATIONS_DIR = SUITE_DIR

MUTATION_FILES = sorted(MUTATIONS_DIR.glob("mut_*.json"))


def test_mutation_suite_inventory_count():
    """Asserts that all 42+ (up to 45) corrupted certificates exist in the suite."""
    assert len(MUTATION_FILES) >= 42, f"Expected at least 42 mutations, found {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("corrupted_result") or data.get("result")
    desc = data.get("description", mut_path.stem)

    # 1. Test Checker 1 (Exact Algebraic Certifier)
    ok1, msg1 = verify_chiral_u1_certificate(case, corrupted_result)

    # 2. Test Checker 2 (Meet-in-the-Middle Dual Engine)
    ok2, msg2 = verify_mitm_certificate(case, corrupted_result)

    # 3. Both checkers must reject the corrupted certificate independently
    assert not ok1, f"Checker 1 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg1}"
    assert not ok2, f"Checker 2 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg2}"

    # 4. In dual evaluator, verdict must be FAIL
    eval_res = evaluate_dual(case, corrupted_result)
    assert eval_res["verdict"] == "FAIL", (
        f"Mutation {mut_path.name} ({desc}) was NOT killed by dual evaluator! "
        f"Verdict: {eval_res['verdict']}, Checker1: {ok1} ({msg1}), Checker2: {ok2} ({msg2})"
    )


def test_refusal_mutations_specifically_rejected():
    """Asserts that all unwarranted refusal mutations (status UNKNOWN) are killed with explicit FAIL reasons."""
    refusal_muts = [
        p
        for p in MUTATION_FILES
        if "refusal" in p.stem or p.stem == "mut_30_unknown_unwarranted_refusal"
    ]
    assert len(refusal_muts) >= 7, (
        f"Expected at least 7 refusal mutations, found {len(refusal_muts)}"
    )
    for mut_path in refusal_muts:
        data = json.loads(mut_path.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("corrupted_result") or data.get("result")
        ok1, msg1 = verify_chiral_u1_certificate(case, corrupted_result)
        ok2, msg2 = verify_mitm_certificate(case, corrupted_result)
        eval_res = evaluate_dual(case, corrupted_result)
        assert not ok1, f"Checker 1 accepted refusal mutation {mut_path.name}: {msg1}"
        assert not ok2, f"Checker 2 accepted refusal mutation {mut_path.name}: {msg2}"
        assert msg1.startswith("FAIL:"), f"Checker 1 returned non-FAIL message: {msg1}"
        assert msg2.startswith("FAIL:"), f"Checker 2 returned non-FAIL message: {msg2}"
        assert eval_res["verdict"] == "FAIL", (
            f"DualEvaluator did not mark refusal {mut_path.name} as FAIL"
        )
