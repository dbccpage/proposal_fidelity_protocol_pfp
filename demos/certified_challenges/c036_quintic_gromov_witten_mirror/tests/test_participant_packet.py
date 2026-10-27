"""Tests for C036 Participant Packet.

Validates TASK.md, accounting.json, runner.py, and all canonical example files.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from c036_quintic_gromov_witten_mirror.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
SOLVER_FILE = CHALLENGE_DIR / "reference_solver" / "solver.py"
RUNNER_FILE = PARTICIPANT_DIR / "runner.py"


def test_task_md_exists_and_declares_bounds():
    """TASK.md must exist and declare mirror symmetry formulas and AuthorityEffect: None."""
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"
    content = task_file.read_text(encoding="utf-8")
    assert "AuthorityEffect" in content and "None" in content
    assert "Tier" in content and "T2" in content
    assert "Gromov-Witten" in content or "Gromov–Witten" in content
    assert "Gopakumar-Vafa" in content or "Gopakumar–Vafa" in content
    assert "Frobenius" in content
    assert "kappa" in content or "\\kappa" in content
    assert "OUT_OF_SCOPE" in content
    assert "UNKNOWN" in content


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
    """runner.py must execute correctly from CLI on single case."""
    example_case = EXAMPLES_DIR / "ex01_quintic_d1.json"
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
    assert res_data[0].get("kappa") == "5"
    assert res_data[0].get("gv") == {"1": "2875"}
    assert res_data[0].get("gw") == {"1": "2875"}
    assert res_data[0].get("mirror_map_coeffs") == ["1"]


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
    assert len(results) == 6


def test_canonical_examples_match_reference_solver():
    """All 6 canonical example files must execute and produce declared statuses."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 6, f"Expected 6 examples, found {len(example_files)}"

    expected_statuses = {
        "ex01_quintic_d1.json": "SOLVED",
        "ex02_quintic_d2.json": "SOLVED",
        "ex03_quintic_d3.json": "SOLVED",
        "ex04_quintic_permuted_weights.json": "SOLVED",
        "ex05_non_calabi_yau_out_of_scope.json": "OUT_OF_SCOPE",
        "ex06_unlisted_family_unknown.json": "UNKNOWN",
    }

    for ef in example_files:
        case = json.loads(ef.read_text(encoding="utf-8"))
        actual = solve(case)
        exp_status = expected_statuses[ef.name]
        assert actual.get("status") == exp_status, f"Status mismatch in {ef.name}: {actual}"

        if exp_status == "SOLVED":
            assert "gv" in actual
            assert "gw" in actual
            assert "mirror_map_coeffs" in actual
            if ef.name == "ex01_quintic_d1.json":
                assert actual.get("gv") == {"1": "2875"}
            elif ef.name == "ex02_quintic_d2.json":
                assert actual.get("gv") == {"1": "2875", "2": "609250"}
                assert actual.get("gw") == {"1": "2875", "2": "4876875/8"}
            elif ef.name == "ex03_quintic_d3.json":
                assert actual.get("gv") == {"1": "2875", "2": "609250", "3": "317206375"}
                assert actual.get("gw") == {"1": "2875", "2": "4876875/8", "3": "8564575000/27"}
        elif exp_status == "OUT_OF_SCOPE":
            assert actual.get("witness", {}).get("kind") == "not_calabi_yau"
        elif exp_status == "UNKNOWN":
            assert actual.get("refusal_code") == "FAMILY_NOT_IN_PINNED_LIST"


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
