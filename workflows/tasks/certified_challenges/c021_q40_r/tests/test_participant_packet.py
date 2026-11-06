"""Tests validating C021 participant packet schema, examples, and runner.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = ROOT_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"


def test_task_markdown_exists_and_contains_formal_invariants():
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file(), "TASK.md must exist in participant_packet"

    content = task_file.read_text(encoding="utf-8")

    # Hamiltonian equation check
    assert "H =" in content or "H =" in content or "H =" in content
    assert "w_i" in content or "wᵢ" in content
    assert "1 \\le n \\le 8" in content or "1 <= n <= 8" in content
    assert "M \\le 24" in content or "M <= 24" in content

    # Closed refusal list check
    required_codes = [
        "NUM_QUBITS_OUT_OF_BOUNDS",
        "TERM_COUNT_OUT_OF_BOUNDS",
        "INVALID_WEIGHT",
        "DUPLICATE_TERM_ID",
        "MALFORMED_PAULI_WORD",
        "INVALID_TARGET_SIGN",
    ]
    for code in required_codes:
        assert code in content, f"Refusal code {code} missing from TASK.md"

    # Schema definition presence
    assert "SOLVED" in content
    assert "OUT_OF_SCOPE" in content
    assert "UNKNOWN" in content
    assert "minimizers" in content
    assert "degeneracy" in content


def test_accounting_template_fields():
    accounting_file = PARTICIPANT_DIR / "accounting.json"
    assert accounting_file.is_file(), "accounting.json must exist in participant_packet"

    data = json.loads(accounting_file.read_text(encoding="utf-8"))
    assert data.get("challenge_id") == "c021_q40_r"
    assert data.get("protocol") == "SG-CP v1"
    assert data.get("cost_ceiling_usd") == 0.25
    assert data.get("target_cost_usd") == 0.05
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
        assert isinstance(inp["n"], int) and 1 <= inp["n"] <= 9  # ex10 is n=9 out-of-bounds test
        assert isinstance(inp["terms"], list)

        # Check non-positional term IDs
        for term in inp["terms"]:
            assert isinstance(term["id"], str)
            # Ensure not pure integer strings
            assert not term["id"].isdigit(), (
                f"Term ID {term['id']!r} in {ex_file.name} should be non-positional"
            )

        status = out["status"]
        if status == "SOLVED":
            solved_count += 1
            assert isinstance(out["energy"], list) and len(out["energy"]) == 2
            assert out["energy"][1] > 0
            assert isinstance(out["degeneracy"], int) and out["degeneracy"] >= 1
            assert isinstance(out["basis"], list)
            assert isinstance(out["decomposition"], list)
            assert isinstance(out["minimizers"], list)
        elif status == "OUT_OF_SCOPE":
            oos_count += 1
            assert isinstance(out["witness"], list) and len(out["witness"]) == 2
            assert out["witness"][0] < out["witness"][1], (
                f"Witness {out['witness']} not sorted in {ex_file.name}"
            )
        elif status == "UNKNOWN":
            unknown_count += 1
            assert "refusal_code" in out
        else:
            pytest.fail(f"Invalid status {status!r} in {ex_file.name}")

    # Verify distribution: 5 solved, 3 OOS, 2 unknown, 2 relabel pairs (which are SOLVED)
    # Total SOLVED = 5 + 2 = 7
    assert solved_count == 7, f"Expected 7 solved examples (5 base + 2 relabel), got {solved_count}"
    assert oos_count == 3, f"Expected 3 OUT_OF_SCOPE examples, got {oos_count}"
    assert unknown_count == 2, f"Expected 2 UNKNOWN examples, got {unknown_count}"


def test_runner_execution_and_canonical_jsonl():
    runner_path = PARTICIPANT_DIR / "runner.py"
    assert runner_path.is_file(), "runner.py must exist"

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "test_answers.jsonl"
        cmd = [
            sys.executable,
            str(runner_path),
            "--cases",
            str(EXAMPLES_DIR),
            "--output",
            str(out_file),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"runner.py failed: {res.stderr}\n{res.stdout}"
        assert out_file.is_file(), "answers.jsonl was not written"

        lines = out_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 12, f"Expected 12 lines in answers.jsonl, got {len(lines)}"

        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "status" in data
            assert data["status"] in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN")
