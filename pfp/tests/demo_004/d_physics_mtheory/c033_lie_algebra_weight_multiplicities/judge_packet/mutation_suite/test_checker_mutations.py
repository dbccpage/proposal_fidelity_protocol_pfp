"""Mutation tests for C033 Dual Checkers.

Asserts that both Checker 1 (Freudenthal) and Checker 2 (Kostant) reject 100%
of the hostile corrupted certificates without throwing unhandled exceptions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.judge_packet.checkers.freudenthal_checker import (
    verify_freudenthal_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.judge_packet.checkers.kostant_checker import (
    verify_kostant_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"
MUTATION_FILES = sorted(MUTATIONS_DIR.glob("*.json"))


def test_mutation_suite_inventory():
    """Asserts that at least 45 hostile mutations are present."""
    assert len(MUTATION_FILES) >= 45, (
        f"Expected at least 45 mutation files, found {len(MUTATION_FILES)}"
    )


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("corrupted_result") or data.get("result")
    desc = data.get("description", mut_path.stem)

    ok1, msg1 = verify_freudenthal_certificate(case, corrupted_result)
    ok2, msg2 = verify_kostant_certificate(case, corrupted_result)

    assert not ok1, f"Checker 1 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg1}"
    assert not ok2, f"Checker 2 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg2}"


def test_mutation_kill_rate_summary():
    """Asserts a 100% kill rate across the full mutation suite."""
    killed_c1 = 0
    killed_c2 = 0
    total = len(MUTATION_FILES)

    for mut_path in MUTATION_FILES:
        data = json.loads(mut_path.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("corrupted_result") or data.get("result")

        ok1, _ = verify_freudenthal_certificate(case, corrupted_result)
        ok2, _ = verify_kostant_certificate(case, corrupted_result)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == total, f"Checker 1 kill rate: {killed_c1}/{total}"
    assert killed_c2 == total, f"Checker 2 kill rate: {killed_c2}/{total}"
