"""Tests validating C031 participant packet schema, examples, and runner.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.reference_solver.solver import (
    solve,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = ROOT_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"


def test_task_markdown_exists_and_contains_formal_invariants():
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"

    content = task_file.read_text(encoding="utf-8")

    # Diophantine anomaly equations
    assert (
        "\\sum_{i=1}^n q_i = 0" in content or "sum q_i = 0" in content or "\\sum q_i = 0" in content
    )
    assert (
        "\\sum_{i=1}^n q_i^3 = 0" in content
        or "sum q_i^3 = 0" in content
        or "\\sum q_i^3 = 0" in content
    )

    # n <= 4 non-existence identity theorem
    assert "3(a+b)(b+c)(c+a)" in content or "3(a + b)(b + c)(c + a)" in content

    # Primitivity, chirality, canonical form
    assert "gcd" in content.lower()
    assert "chiral" in content.lower()
    assert "canonical" in content.lower()

    # Closed refusal list check
    required_codes = [
        "INVALID_CHARGE_SPECTRUM",
        "VECTOR_LIKE_TRIVIAL",
        "NON_PRIMITIVE_SPECTRUM",
        "BOUND_EXCEEDED",
        "NO_COMPLETION",
        "N_OUT_OF_BOUNDS",
        "BOUND_OUT_OF_BOUNDS",
        "MALFORMED_QUERY_TYPE",
        "MALFORMED_CASE_STRUCTURE",
    ]
    for code in required_codes:
        assert code in content, f"Refusal code {code} missing from TASK.md"

    # OUT_OF_SCOPE witness kinds
    required_witness_kinds = [
        "fixed_charge_exceeds_bound",
        "fixed_charge_zero",
        "too_many_fixed_charges",
    ]
    for kind in required_witness_kinds:
        assert kind in content, f"Witness kind {kind} missing from TASK.md"

    # Schema definition presence
    assert "SOLVED" in content
    assert "OUT_OF_SCOPE" in content
    assert "UNKNOWN" in content


def test_accounting_template_fields():
    accounting_file = PARTICIPANT_DIR / "accounting.json"
    assert accounting_file.is_file(), "accounting.json must exist in participant_packet"

    data = json.loads(accounting_file.read_text(encoding="utf-8"))
    assert data.get("challenge_id") == "c031_anomaly_free_u1_charges"
    assert data.get("protocol") == "SG-CP v1"
    assert data.get("tier") == "T3"
    assert data.get("cost_ceiling_usd") == 1.00
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
        cid = inp.get("id") or inp.get("case_id")
        assert isinstance(cid, str)
        assert isinstance(inp["query"], str)
        assert inp["query"] in ("enumerate", "complete")
        assert isinstance(inp["n"], int)
        assert isinstance(inp["bound"], int)

        # Confirm solver produces exact expected output
        actual_output = solve(inp)
        assert actual_output["status"] == out["status"], f"Status mismatch in {ex_file.name}"
        assert actual_output == out, f"Output mismatch in {ex_file.name}"

        status = out["status"]
        if status == "SOLVED":
            solved_count += 1
            if inp["query"] == "enumerate":
                assert "count" in out
                assert "solutions" in out
                assert isinstance(out["solutions"], list)
            elif inp["query"] == "complete":
                assert "completion" in out
                if out["completion"] is None:
                    assert out.get("claim") == "NO_COMPLETION"
                else:
                    assert isinstance(out["completion"], list)
                    assert len(out["completion"]) == inp["n"] - len(inp.get("fixed", []))
        elif status == "OUT_OF_SCOPE":
            oos_count += 1
            assert isinstance(out["witness"], dict)
            assert "kind" in out["witness"]
        elif status == "UNKNOWN":
            unknown_count += 1
            assert "refusal_code" in out or "refusal" in out

    assert solved_count == 9, f"Expected 9 SOLVED examples, found {solved_count}"
    assert oos_count == 3, f"Expected 3 OUT_OF_SCOPE examples, found {oos_count}"


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
