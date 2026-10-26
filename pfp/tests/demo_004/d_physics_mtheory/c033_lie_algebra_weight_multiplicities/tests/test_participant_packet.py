"""Tests for C033 Participant Packet.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.governance.budget_gate import (
    BudgetGate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"


def test_participant_packet_files_exist():
    """Asserts that TASK.md, accounting.json, and runner.py exist."""
    assert (PARTICIPANT_DIR / "TASK.md").is_file(), "TASK.md missing"
    assert (PARTICIPANT_DIR / "accounting.json").is_file(), "accounting.json missing"
    assert (PARTICIPANT_DIR / "runner.py").is_file(), "runner.py missing"


def test_accounting_json_conforms_to_tier_t2():
    """Asserts that accounting.json adheres strictly to Tier T2 constraints ($0.50 ceiling, $0.05 target, <= 70B)."""
    cfg = json.loads((PARTICIPANT_DIR / "accounting.json").read_text(encoding="utf-8"))
    gate = BudgetGate()
    audit = gate.audit_accounting_config(cfg)
    assert audit["valid"], f"accounting.json failed Tier T2 audit: {audit['violations']}"


def test_public_examples_inventory_and_execution():
    """Asserts that exactly 12 public examples exist and are solved with 100% agreement."""
    ex_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(ex_files) == 12, f"Expected 12 public examples, found {len(ex_files)}"

    for ef in ex_files:
        data = json.loads(ef.read_text(encoding="utf-8"))
        case_input = data["input"]
        expected = data["expected_output"]
        actual = solve(case_input)
        assert actual == expected, f"Mismatch on {ef.name}: got {actual}, expected {expected}"
