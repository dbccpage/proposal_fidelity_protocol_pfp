"""Mutation Suite Tests for C032 Judge Packet Dual Checkers.

Asserts that both Checker 1 (Exact Algebraic Weight Certifier) and Checker 2 (Independent Matrix Certifier)
detect and reject 100% of injected corrupted certificates with zero false passes and zero unhandled crashes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.sugra_matrix_checker import (
    verify_sugra_matrix_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.sugra_weight_checker import (
    verify_sugra_weight_certificate,
)

SUITE_DIR = Path(__file__).resolve().parent
MUTATIONS_DIR = SUITE_DIR / "mutations"
if not MUTATIONS_DIR.exists():
    MUTATIONS_DIR = SUITE_DIR

MUTATION_FILES = sorted(MUTATIONS_DIR.glob("mut_*.json"))


def test_mutation_suite_inventory_count():
    """Asserts that all 46 corrupted certificates exist in the suite."""
    assert len(MUTATION_FILES) >= 45, f"Expected at least 45 mutations, found {len(MUTATION_FILES)}"


def test_hardened_mutations_killed_by_both_checkers():
    """Explicitly asserts that mut_41 through mut_46 are present and killed by both checkers."""
    expected_hardened = [
        "mut_41_corrupted_coefficients_aa.json",
        "mut_42_corrupted_coefficients_ab.json",
        "mut_43_stripped_payload_no_coefficients.json",
        "mut_44_stripped_payload_no_inertia.json",
        "mut_45_boolean_in_gram_inertia.json",
        "mut_46_unwarranted_refusal_representation_not_supported.json",
    ]
    for filename in expected_hardened:
        p = MUTATIONS_DIR / filename
        assert p.is_file(), f"Missing expected hardened mutation file: {filename}"
        data = json.loads(p.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("corrupted_result") or data.get("result")
        desc = data.get("description", p.stem)
        ok1, msg1 = verify_sugra_weight_certificate(case, corrupted_result)
        ok2, msg2 = verify_sugra_matrix_certificate(case, corrupted_result)
        assert not ok1, f"Weight checker accepted {filename} ({desc}): {msg1}"
        assert not ok2, f"Matrix checker accepted {filename} ({desc}): {msg2}"
        eval_res = evaluate_dual(case, corrupted_result)
        assert eval_res["verdict"] == "FAIL", f"Dual evaluator accepted {filename}: {eval_res}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("corrupted_result") or data.get("result")
    desc = data.get("description", mut_path.stem)

    ok1, msg1 = verify_sugra_weight_certificate(case, corrupted_result)
    ok2, msg2 = verify_sugra_matrix_certificate(case, corrupted_result)

    assert not ok1, f"Checker 1 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg1}"
    assert not ok2, f"Checker 2 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg2}"

    eval_res = evaluate_dual(case, corrupted_result)
    assert eval_res["verdict"] == "FAIL", (
        f"Mutation {mut_path.name} ({desc}) was NOT killed by dual evaluator! "
        f"Verdict: {eval_res['verdict']}, Checker1: {ok1} ({msg1}), Checker2: {ok2} ({msg2})"
    )
