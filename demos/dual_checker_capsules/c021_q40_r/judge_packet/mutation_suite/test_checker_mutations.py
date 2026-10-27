"""Mutation Suite Tests for C021 Judge Packet Dual Checkers.

Asserts that both Checker 1 (Exact Algebraic) and Checker 2 (Dense Spectral LDL^H)
detect and reject 100% of injected corrupted certificates with zero false passes
and zero crashes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c021_q40_r.judge_packet.checkers.algebraic_checker import (
    verify_certificate,
)
from c021_q40_r.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c021_q40_r.judge_packet.checkers.spectral_checker import (
    verify_spectral_optimality,
)

SUITE_DIR = Path(__file__).resolve().parent
MUTATIONS_DIR = SUITE_DIR / "mutations"
if not MUTATIONS_DIR.exists():
    MUTATIONS_DIR = SUITE_DIR

MUTATION_FILES = sorted(MUTATIONS_DIR.glob("mut_*.json"))


def test_mutation_suite_inventory_count():
    """Asserts that at least 30 corrupted certificates exist in the suite."""
    assert len(MUTATION_FILES) >= 30, f"Expected at least 30 mutations, found {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data["corrupted_result"]
    desc = data.get("description", mut_path.stem)

    # 1. Test Checker 1 (Exact Algebraic)
    ok1, msg1 = verify_certificate(case, corrupted_result)
    assert not ok1, f"Checker 1 falsely PASSED mutation {mut_path.name} ({desc}): {msg1}"
    assert msg1.startswith("FAIL:"), f"Checker 1 error message must start with FAIL:, got: {msg1}"

    # 2. Test Checker 2 (Exact Dense Spectral LDL^H)
    ok2, msg2 = verify_spectral_optimality(case, corrupted_result)
    assert not ok2, f"Checker 2 falsely PASSED mutation {mut_path.name} ({desc}): {msg2}"
    assert msg2.startswith("FAIL:"), f"Checker 2 error message must start with FAIL:, got: {msg2}"

    # 3. Test Dual Evaluator
    eval_res = evaluate_dual(case, corrupted_result)
    assert eval_res["verdict"] == "FAIL", (
        f"Dual evaluator verdict was {eval_res['verdict']} on {mut_path.name}"
    )
    assert eval_res["agreement"] is True, f"Checkers disagreed on mutation {mut_path.name}"
