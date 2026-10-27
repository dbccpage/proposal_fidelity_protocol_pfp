"""Hostile Mutation Suite Tests for C023 Judge Packet Dual Checkers.

Asserts that both Checker 1 (Exact Row-Wise Tableau Simulation) and
Checker 2 (Dense Spectral / Backward Propagation) detect and reject 100% of injected
corrupted certificates with zero false passes and zero crashes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)

SUITE_DIR = Path(__file__).resolve().parent
MUTATIONS_DIR = SUITE_DIR / "mutations"
MUTATION_FILES = sorted(MUTATIONS_DIR.glob("mut_*.json"))


def test_mutation_suite_inventory_count():
    """Asserts that at least 40 hostile mutations exist in the suite."""
    assert len(MUTATION_FILES) >= 40, f"Expected at least 40 mutations, found {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that the checkers reject the mutation cleanly without throwing unhandled exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    cert = data["certificate"]
    desc = data.get("description", mut_path.stem)

    ok, reason, details = evaluate_dual(case, cert)
    assert not ok, f"Dual evaluator falsely PASSED mutation {mut_path.name} ({desc}): {reason}"
