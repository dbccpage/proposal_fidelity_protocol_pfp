"""Mutation Suite Tests for C012 Judge Packet Dual Checkers.

Asserts that both Checker 1 (Exact Algebraic & Coboundary Certifier) and
Checker 2 (Independent Echelon & Dual Dimension Certifier) detect and reject
100% of injected corrupted certificates with zero false passes and zero unhandled crashes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c012_cellular_sheaf_h0_h1.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_algebraic_checker import (
    verify_algebraic_certificate,
)
from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_echelon_checker import (
    verify_echelon_certificate,
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

    # 1. Test Checker 1 (Exact Algebraic & Coboundary Certifier)
    ok1, msg1 = verify_algebraic_certificate(case, corrupted_result)

    # 2. Test Checker 2 (Independent Echelon & Dual Dimension Certifier)
    ok2, msg2 = verify_echelon_certificate(case, corrupted_result)

    # 3. Both checkers must reject the corrupted certificate independently
    assert not ok1, f"Checker 1 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg1}"
    assert not ok2, f"Checker 2 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg2}"

    # 4. In dual evaluator, verdict must be FAIL
    eval_res = evaluate_dual(case, corrupted_result)
    assert eval_res["verdict"] == "FAIL", (
        f"Mutation {mut_path.name} ({desc}) was NOT killed by dual evaluator! "
        f"Verdict: {eval_res['verdict']}, Checker1: {ok1} ({msg1}), Checker2: {ok2} ({msg2})"
    )


def test_mutation_payloads_are_pairwise_distinct():
    """Padding with copies overstated coverage (2026-09-29 correction removed them)."""
    payloads = [
        json.dumps([data["case"], data["corrupted_result"]], sort_keys=True)
        for data in (json.loads(p.read_text(encoding="utf-8")) for p in MUTATION_FILES)
    ]
    assert len(payloads) == len(set(payloads)) == 51
