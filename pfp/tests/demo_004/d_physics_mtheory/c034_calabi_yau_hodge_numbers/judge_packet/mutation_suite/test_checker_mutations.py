"""Mutation tests for C034 Dual Checkers.

Asserts that both Checker 1 (Facet Point Bounding-Box) and Checker 2 (Dual Mirror Affine HNF)
reject 100% of the 52 hostile corrupted certificates without throwing unhandled exceptions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.affine_hnf_checker import (
    verify_affine_hnf_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.facet_point_checker import (
    verify_facet_point_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"
MUTATION_FILES = sorted(MUTATIONS_DIR.glob("*.json"))


def test_mutation_suite_inventory():
    """Asserts that at least 50 hostile mutations are present (52 total)."""
    assert len(MUTATION_FILES) >= 50, (
        f"Expected at least 50 mutation files, found {len(MUTATION_FILES)}"
    )
    assert len(MUTATION_FILES) == 52, (
        f"Expected exactly 52 mutation files, found {len(MUTATION_FILES)}"
    )


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts that both checkers reject the mutation cleanly without throwing exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("corrupted_result") or data.get("result")
    desc = data.get("description", mut_path.stem)

    ok1, msg1 = verify_facet_point_certificate(case, corrupted_result)
    ok2, msg2 = verify_affine_hnf_certificate(case, corrupted_result)

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

        ok1, _ = verify_facet_point_certificate(case, corrupted_result)
        ok2, _ = verify_affine_hnf_certificate(case, corrupted_result)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == total, f"Checker 1 kill rate: {killed_c1}/{total}"
    assert killed_c2 == total, f"Checker 2 kill rate: {killed_c2}/{total}"
