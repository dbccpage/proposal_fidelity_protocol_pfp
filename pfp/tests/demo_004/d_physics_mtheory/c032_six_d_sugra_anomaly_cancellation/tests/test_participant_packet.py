"""Tests for C032 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"


def test_task_md_exists_and_declares_bounds():
    """TASK.md must exist and specify mathematical anomaly conditions."""
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"
    content = task_file.read_text(encoding="utf-8")
    assert "H - V + 29T = 273" in content
    assert "B_{\\text{adj}} = \\sum_R x_R B^R" in content or "B_adj = sum_R x_R B^R" in content
    assert "a \\cdot a = 9 - T" in content or "a . a = 9 - T" in content
    assert "AuthorityEffect" in content and "None" in content


def test_accounting_json_specifies_tier_t3():
    """accounting.json must declare Tier T3 bounds and zero fallbacks."""
    accounting_file = PARTICIPANT_DIR / "accounting.json"
    assert accounting_file.is_file(), "accounting.json must exist in participant_packet"
    data = json.loads(accounting_file.read_text(encoding="utf-8"))
    assert data.get("tier") == "T3"
    assert data.get("cost_ceiling_usd") == 1.00
    assert data.get("target_cost_usd") == 0.05
    assert data.get("model_ceiling_parameters") == 70_000_000_000
    assert data.get("allow_fallbacks") is False


def test_examples_exist_and_match_solver():
    """All 10 canonical example files must match reference solver output exactly."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 10, f"Expected 10 examples, found {len(example_files)}"

    for ef in example_files:
        data = json.loads(ef.read_text(encoding="utf-8"))
        case = data["case"]
        expected = data["expected_output"]
        actual = solve(case)

        assert actual.get("status") == expected.get("status"), (
            f"Status mismatch in {ef.name}: actual {actual.get('status')} != expected {expected.get('status')}"
        )
        if actual.get("status") == "SOLVED":
            assert actual.get("verdict") == expected.get("verdict"), (
                f"Verdict mismatch in {ef.name}: actual {actual.get('verdict')} != expected {expected.get('verdict')}"
            )
            assert actual.get("H") == expected.get("H")
            assert actual.get("V") == expected.get("V")
            assert actual.get("T") == expected.get("T")
