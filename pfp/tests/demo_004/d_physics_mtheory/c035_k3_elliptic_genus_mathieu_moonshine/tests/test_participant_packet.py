"""Tests for C035 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
SOLVER_FILE = CHALLENGE_DIR / "reference_solver" / "solver.py"
RUNNER_FILE = PARTICIPANT_DIR / "runner.py"


def test_task_md_exists_and_declares_bounds():
    """TASK.md must exist and declare exact elliptic genus formulas and AuthorityEffect: None."""
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"
    content = task_file.read_text(encoding="utf-8")
    assert "AuthorityEffect" in content and "None" in content
    assert "Tier" in content and "T2" in content
    assert "theta" in content or "\\theta" in content
    assert "Appell-Lerch" in content or "mock" in content
    assert "M_{24}" in content or "M_24" in content or "M₂₄" in content
    assert "coefficients" in content
    assert "decompose" in content


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
    example_case = EXAMPLES_DIR / "ex01_coefficients_up_to_n3.json"
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
    assert res_data[0].get("A") == {"1": 90, "2": 462, "3": 1540}


def test_runner_cli_directory_input(tmp_path: Path):
    """runner.py must execute across all files when given a directory path."""
    out_file = tmp_path / "all_output.json"
    cmd = [
        sys.executable,
        str(RUNNER_FILE),
        "--cases",
        str(EXAMPLES_DIR),
        "--solver",
        str(SOLVER_FILE),
        "--output",
        str(out_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"runner.py on dir failed: {proc.stderr}"
    assert out_file.is_file()
    results = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(results) == 8


def test_canonical_examples_match_reference_solver():
    """All 8 canonical example files must execute and produce declared statuses."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 8, f"Expected 8 examples, found {len(example_files)}"

    expected_statuses = {
        "ex01_coefficients_up_to_n3.json": "SOLVED",
        "ex02_decomposition_A1.json": "SOLVED",
        "ex03_decomposition_A2.json": "SOLVED",
        "ex04_decomposition_A3.json": "SOLVED",
        "ex05_elliptic_genus_specialization_z0.json": "SOLVED",
        "ex06_perturbed_class_function_malformed.json": "UNKNOWN",
        "ex07_non_integral_multiplicity_oos.json": "OUT_OF_SCOPE",
        "ex08_out_of_bounds_max_n35.json": "UNKNOWN",
    }

    for ef in example_files:
        case = json.loads(ef.read_text(encoding="utf-8"))
        actual = solve(case)
        exp_status = expected_statuses[ef.name]
        assert actual.get("status") == exp_status, f"Status mismatch in {ef.name}: {actual}"

        if exp_status == "SOLVED":
            if ef.name == "ex01_coefficients_up_to_n3.json":
                assert actual.get("A") == {"1": 90, "2": 462, "3": 1540}
            elif ef.name == "ex02_decomposition_A1.json":
                assert actual.get("multiplicities") == {"45": 1, "45bar": 1}
            elif ef.name == "ex03_decomposition_A2.json":
                assert actual.get("multiplicities") == {"231": 1, "231bar": 1}
            elif ef.name == "ex04_decomposition_A3.json":
                assert actual.get("multiplicities") == {"770": 1, "770bar": 1}
            elif ef.name == "ex05_elliptic_genus_specialization_z0.json":
                assert actual.get("constant") == 24
        elif exp_status == "OUT_OF_SCOPE":
            assert actual.get("witness", {}).get("kind") == "non_integral_multiplicity"
        elif exp_status == "UNKNOWN":
            assert actual.get("refusal_code") in ("MALFORMED_CASE_STRUCTURE", "MAX_N_OUT_OF_BOUNDS")


def test_runner_fail_closed_on_missing_file():
    """runner.py must exit non-zero when input path does not exist."""
    cmd = [
        sys.executable,
        str(RUNNER_FILE),
        "--cases",
        "nonexistent_cases_path_xyz.json",
        "--solver",
        str(SOLVER_FILE),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode != 0
