"""Tests for C034 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from c034_calabi_yau_hodge_numbers.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
SOLVER_FILE = CHALLENGE_DIR / "reference_solver" / "solver.py"
RUNNER_FILE = PARTICIPANT_DIR / "runner.py"


def test_task_md_exists_and_declares_bounds():
    """TASK.md must exist and declare 4D reflexive polytope bounds and AuthorityEffect: None."""
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"
    content = task_file.read_text(encoding="utf-8")
    assert "AuthorityEffect" in content and "None" in content
    assert "Tier" in content and "T2" in content
    assert "Batyrev" in content
    assert "reflexive" in content
    assert "h11" in content or "h^{1,1}" in content
    assert "h21" in content or "h^{2,1}" in content
    assert "euler" in content or "Euler" in content


def test_accounting_json_specifies_tier_t2():
    """accounting.json must declare Tier T2 bounds, $0.50 ceiling, $0.05 target, and zero fallbacks."""
    accounting_file = PARTICIPANT_DIR / "accounting.json"
    assert accounting_file.is_file(), "accounting.json must exist in participant_packet"
    data = json.loads(accounting_file.read_text(encoding="utf-8"))
    assert data.get("tier") == "T2"
    assert data.get("cost_ceiling_usd") == 0.50
    assert data.get("target_cost_usd") == 0.05
    assert data.get("model_ceiling_parameters") in (70_000_000_000, "70B")
    assert data.get("allow_fallbacks") is False


def test_runner_cli_interface(tmp_path: Path):
    """runner.py must execute correctly from CLI on single case and directory input."""
    example_case = EXAMPLES_DIR / "ex01_quintic_dual.json"
    assert example_case.is_file()

    out_file = tmp_path / "output.json"
    cmd = [
        sys.executable,
        str(RUNNER_FILE),
        "--cases",
        str(example_case),
        "--solver",
        str(SOLVER_FILE),
        "--output",
        str(out_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"runner.py failed: {proc.stderr}"
    assert out_file.is_file(), "Output file not written"

    res_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(res_data, list) and len(res_data) == 1
    assert res_data[0].get("status") == "SOLVED"
    assert res_data[0].get("h11") == 1
    assert res_data[0].get("h21") == 101


def test_canonical_examples_match_reference_solver():
    """All 8 canonical example files must match reference solver output exactly."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 8, f"Expected 8 examples, found {len(example_files)}"

    for ef in example_files:
        data = json.loads(ef.read_text(encoding="utf-8"))
        case = data.get("input", data)
        expected = data.get("expected_output", data.get("output"))
        actual = solve(case)

        assert actual.get("status") == expected.get("status"), (
            f"Status mismatch in {ef.name}: actual {actual.get('status')} != expected {expected.get('status')}"
        )
        if actual.get("status") == "SOLVED":
            assert actual.get("h11") == expected.get("h11"), f"h11 mismatch in {ef.name}"
            assert actual.get("h21") == expected.get("h21"), f"h21 mismatch in {ef.name}"
            assert actual.get("euler") == expected.get("euler"), f"euler mismatch in {ef.name}"
            assert actual.get("face_data", {}).get("l_delta") == expected.get("face_data", {}).get(
                "l_delta"
            )
            assert actual.get("face_data", {}).get("l_delta_star") == expected.get(
                "face_data", {}
            ).get("l_delta_star")
        elif actual.get("status") == "OUT_OF_SCOPE":
            assert actual.get("witness", {}).get("kind") == expected.get("witness", {}).get("kind")
        elif actual.get("status") == "UNKNOWN":
            assert actual.get("refusal_code") == expected.get("refusal_code")
