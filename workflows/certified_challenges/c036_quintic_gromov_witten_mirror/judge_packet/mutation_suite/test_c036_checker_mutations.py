"""Hostile Mutation Kill-Rate Verification Suite for Challenge C036.

Asserts that both Checker 1 (Hypergeometric Mirror Evaluator) and
Checker 2 (Picard-Fuchs Recurrence Verifier) reject 100% of the 48 hostile
mutations without unhandled exceptions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c036_quintic_gromov_witten_mirror.judge_packet.checkers.hypergeometric_mirror_checker import (
    verify_hypergeometric_mirror_certificate,
)
from c036_quintic_gromov_witten_mirror.judge_packet.checkers.picard_fuchs_recurrence_checker import (
    verify_picard_fuchs_recurrence_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"
MUTATION_FILES = sorted(MUTATIONS_DIR.glob("*.json"))


def test_mutation_suite_inventory():
    """Asserts that at least 45 hostile mutations are present (exactly 48 total)."""
    assert len(MUTATION_FILES) >= 45, f"Expected >= 45 mutations, found {len(MUTATION_FILES)}"
    assert len(MUTATION_FILES) == 48, f"Expected exactly 48 mutations, found {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_dual_checkers_reject_mutation(mut_path: Path):
    """Asserts both checkers cleanly reject the corrupted certificate without exceptions."""
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case = data["case"]
    corrupted_result = data.get("result")
    desc = data.get("description", mut_path.stem)

    ok1, msg1 = verify_hypergeometric_mirror_certificate(case, corrupted_result)
    ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, corrupted_result)

    assert not ok1, f"Checker 1 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg1}"
    assert not ok2, f"Checker 2 unexpectedly accepted mutation {mut_path.name} ({desc}): {msg2}"


def test_mutation_kill_rate_summary():
    """Asserts a verified 100% kill rate across both independent checkers."""
    killed_c1 = 0
    killed_c2 = 0
    total = len(MUTATION_FILES)

    for mut_path in MUTATION_FILES:
        data = json.loads(mut_path.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("result")

        ok1, _ = verify_hypergeometric_mirror_certificate(case, corrupted_result)
        ok2, _ = verify_picard_fuchs_recurrence_certificate(case, corrupted_result)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == total, f"Checker 1 kill rate: {killed_c1}/{total}"
    assert killed_c2 == total, f"Checker 2 kill rate: {killed_c2}/{total}"
