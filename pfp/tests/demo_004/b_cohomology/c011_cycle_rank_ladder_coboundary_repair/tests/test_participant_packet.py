"""Tests validating C011 participant packet schema, examples, and runner.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.reference_solver.solver import (
    solve,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = ROOT_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"


def test_task_markdown_exists_and_contains_formal_invariants():
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"

    content = task_file.read_text(encoding="utf-8")

    # Cohomological problem definition
    assert "\\Phi_1" in content or "Phi1" in content or "Φ₁" in content
    assert "\\delta \\phi" in content or "delta" in content
    assert "b_1" in content or "cycle rank" in content
    assert "60" in content  # |V| <= 60 bound

    # Closed refusal list check
    required_codes = [
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "INVALID_CAPACITY",
        "NEGATIVE_WEIGHT",
        "DISCONNECTED_GRAPH",
        "MALFORMED_EDGE_SPEC",
        "INVALID_TARGET_DEFECT",
        "MALFORMED_CASE_STRUCTURE",
    ]
    for code in required_codes:
        assert code in content, f"Refusal code {code} missing from TASK.md"

    # Schema definition presence
    assert "SOLVED" in content
    assert "OUT_OF_SCOPE" in content
    assert "UNKNOWN" in content
    assert "potential" in content
    assert "repair" in content
    assert "dual" in content


def test_accounting_template_fields():
    accounting_file = PARTICIPANT_DIR / "accounting.json"
    assert accounting_file.is_file(), "accounting.json must exist in participant_packet"

    data = json.loads(accounting_file.read_text(encoding="utf-8"))
    assert data.get("challenge_id") == "c011_cycle_rank_ladder_coboundary_repair"
    assert data.get("protocol") == "SG-CP v1"
    assert data.get("tier") == "T2"
    assert data.get("cost_ceiling_usd") == 0.50
    assert data.get("target_cost_usd") == 0.05
    assert data.get("model_ceiling_parameters") == 70000000000
    assert data.get("allow_fallbacks") is False
    assert "calls" in data
    assert isinstance(data["calls"], list)


def test_public_examples_inventory_and_schema():
    example_files = sorted(EXAMPLES_DIR.glob("ex*.json"))
    assert len(example_files) == 12, (
        f"Expected exactly 12 public examples, found {len(example_files)}"
    )

    solved_count = 0
    oos_count = 0
    unknown_count = 0

    for ex_file in example_files:
        content = json.loads(ex_file.read_text(encoding="utf-8"))
        assert "input" in content, f"{ex_file.name} missing 'input'"
        assert "expected_output" in content, f"{ex_file.name} missing 'expected_output'"

        inp = content["input"]
        out = content["expected_output"]

        # Validate input schema basics
        assert isinstance(inp["id"], str)
        assert isinstance(inp["vertices"], list)
        assert isinstance(inp["edges"], list)

        # Confirm solver produces exact expected output
        actual_output = solve(inp)
        assert actual_output["status"] == out["status"], f"Status mismatch in {ex_file.name}"
        assert actual_output == out, f"Output mismatch in {ex_file.name}"

        status = out["status"]
        if status == "SOLVED":
            solved_count += 1
            assert isinstance(out["phi1"], str)
            assert isinstance(out["potential"], dict)
            assert isinstance(out["repair"], dict)
            assert isinstance(out["dual"], dict)
        elif status == "OUT_OF_SCOPE":
            oos_count += 1
            assert isinstance(out["witness"], dict)
            assert "edge" in out["witness"]
            assert "reason" in out["witness"]
        elif status == "UNKNOWN":
            unknown_count += 1
            assert "refusal" in out or "refusal_code" in out

    assert solved_count == 8, f"Expected 8 SOLVED examples, found {solved_count}"
    assert oos_count == 2, f"Expected 2 OUT_OF_SCOPE examples, found {oos_count}"
    assert unknown_count == 2, f"Expected 2 UNKNOWN examples, found {unknown_count}"


def test_runner_execution_on_examples():
    runner_py = PARTICIPANT_DIR / "runner.py"
    assert runner_py.is_file(), "runner.py must exist in participant_packet"

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "answers.jsonl"
        proc = subprocess.run(
            [
                sys.executable,
                str(runner_py),
                "--cases",
                str(EXAMPLES_DIR),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0, f"runner.py failed: {proc.stderr}"
        assert output_file.is_file(), "runner.py did not produce answers.jsonl"

        lines = [
            line.strip()
            for line in output_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) == 12, f"Expected 12 lines in answers.jsonl, got {len(lines)}"

        for line in lines:
            record = json.loads(line)
            assert "status" in record
            assert record["status"] in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN")
