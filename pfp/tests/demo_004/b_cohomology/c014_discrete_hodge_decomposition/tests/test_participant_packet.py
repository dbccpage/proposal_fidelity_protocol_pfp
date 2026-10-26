"""Tests for C014 Participant Packet.

Verifies:
1. TASK.md existence, formal specifications, closed refusal enum, closed out-of-scope enum.
2. 20 public examples existence, JSON validity, required keys.
3. Sandboxed runner execution and accounting.json conformity.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.participant_packet.runner import (
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
    assert "Discrete Hodge Decomposition" in content
    assert "Orthogonality" in content
    assert "harmonic_basis" in content
    assert "|V| <= 80" in content
    assert "|E| <= 200" in content
    assert "|F| <= 150" in content

    # Closed refusal enums
    for r in [
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "FACE_COUNT_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "WEIGHT_DENOMINATOR_EXCEEDED",
        "WEIGHT_NON_POSITIVE",
        "MALFORMED_INPUT",
        "MALFORMED_CASE_STRUCTURE",
    ]:
        assert r in content, f"TASK.md missing refusal enum {r}"

    assert "OUT_OF_SCOPE" in content
    assert "D1_D0_NONZERO" in content


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
        assert "vertices" in inp
        assert "edges" in inp
        assert isinstance(inp["vertices"], list)
        assert isinstance(inp["edges"], list)


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
    ex_file = EXAMPLES_DIR / "ex01.json"
    assert ex_file.exists()
    out = run_participant_solver(ex_file)
    assert out.get("status") == "SOLVED"
    assert out.get("harmonic_dim") == "1"
    assert len(out.get("harmonic_basis", [])) == 1
