"""Mutation tests for C035 Dual Checkers.

Asserts that both Checker 1 (Jacobi-Character Evaluator) and Checker 2 (Matrix Inversion Verifier)
reject 100% of the 48 hostile corrupted certificates without throwing unhandled exceptions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers.jacobi_character_checker import (
    verify_jacobi_character_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers.matrix_inversion_checker import (
    verify_matrix_inversion_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"
MUTATION_FILES = sorted(MUTATIONS_DIR.glob("*.json"))


def test_mutation_suite_inventory():
    """Asserts that at least 45 hostile mutations are present (48 total)."""
    assert len(MUTATION_FILES) >= 45, f"Expected at least 45 mutations, found {len(MUTATION_FILES)}"
    assert len(MUTATION_FILES) == 48, f"Expected exactly 48 mutations, found {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("result")
    desc = data.get("description", mut_path.stem)

    ok1, msg1 = verify_jacobi_character_certificate(case, corrupted_result)
    ok2, msg2 = verify_matrix_inversion_certificate(case, corrupted_result)

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
        corrupted_result = data.get("result")

        ok1, _ = verify_jacobi_character_certificate(case, corrupted_result)
        ok2, _ = verify_matrix_inversion_certificate(case, corrupted_result)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == total, f"Checker 1 kill rate: {killed_c1}/{total}"
    assert killed_c2 == total, f"Checker 2 kill rate: {killed_c2}/{total}"
