"""Tests for C013 Participant Packet.

Verifies:
1. TASK.md existence, formal specifications, closed refusal enum, closed out-of-scope enum.
2. 20 public examples existence, JSON validity, required keys.
3. Sandboxed runner execution and accounting.json conformity.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.b_cohomology.c013_integral_homology_torsion.participant_packet.runner import (
    run_participant_solver,
)

PACKET_DIR = Path(__file__).resolve().parent.parent / "participant_packet"
EXAMPLES_DIR = PACKET_DIR / "examples"


def test_task_md_specification_invariants():
    """Asserts that TASK.md contains all formal problem definitions and bounds."""
    task_file = PACKET_DIR / "TASK.md"
    assert task_file.exists(), "TASK.md missing"
    content = task_file.read_text(encoding="utf-8")

    # Formal problem elements
    assert "Integral Homology" in content
    assert "Smith Normal Form" in content
    assert "Unimodularity" in content
    assert "dim K <= 3" in content
    assert "|K| <= 1000" in content

    # Closed refusal enums
    for r in [
        "SIMPLEX_COUNT_OUT_OF_BOUNDS",
        "DIMENSION_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "MALFORMED_INPUT",
        "MALFORMED_CASE_STRUCTURE",
    ]:
        assert r in content, f"TASK.md missing refusal enum {r}"

    assert "OUT_OF_SCOPE" in content
    assert "missing_face" in content


def test_examples_inventory_and_validity():
    """Asserts 20 public examples exist and conform to schema."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 20, f"Expected 20 examples, found {len(example_files)}"

    for f in example_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        assert "input" in data
        assert "expected_output" in data
        inp = data["input"]
        assert "id" in inp
        assert "simplices" in inp
        assert isinstance(inp["simplices"], list)


def test_accounting_json_structure():
    """Asserts accounting.json conforms to model budget constraints."""
    acct_file = PACKET_DIR / "accounting.json"
    assert acct_file.exists(), "accounting.json missing"
    data = json.loads(acct_file.read_text(encoding="utf-8"))

    assert data.get("tier") == "T2"
    assert data.get("cost_ceiling_usd") == 0.50
    assert data.get("target_cost_usd") == 0.05
    assert data.get("allow_fallbacks") is False
    assert data.get("model_ceiling_parameters") == 70_000_000_000


def test_runner_on_public_example():
    """Asserts sandboxed runner executes reference solver on a public example."""
    ex_file = EXAMPLES_DIR / "ex08.json"
    assert ex_file.exists()
    out = run_participant_solver(ex_file)
    assert out.get("status") == "SOLVED"
    assert out.get("homology")[0]["betti"] == "1"
    assert out.get("homology")[1]["torsion"] == ["2"]
    assert len(out.get("snf", [])) == 2
