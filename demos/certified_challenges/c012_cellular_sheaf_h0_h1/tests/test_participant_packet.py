"""Tests for C012 Participant Packet.

Verifies:
1. TASK.md existence, formal specifications, closed refusal enum, closed out-of-scope enum.
2. 20 public examples existence, JSON validity, required keys.
3. Sandboxed runner execution and accounting.json conformity.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from c012_cellular_sheaf_h0_h1.participant_packet.runner import (
    load_cases,
    load_solver_func,
    run_cases,
)

PACKET_DIR = Path(__file__).resolve().parent.parent / "participant_packet"
EXAMPLES_DIR = PACKET_DIR / "examples"


def test_task_md_specification_invariants():
    """Asserts that TASK.md contains all formal problem definitions and bounds."""
    task_file = PACKET_DIR / "TASK.md"
    assert task_file.exists(), "TASK.md missing"
    content = task_file.read_text(encoding="utf-8")

    # Formal problem elements
    assert "Cellular Sheaf" in content
    assert "H^0" in content
    assert "H^1" in content
    assert "Coboundary" in content
    assert "240" in content
    assert "d_v" in content

    # Closed enums
    for r in [
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "STALK_DIM_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "MALFORMED_RESTRICTION_MATRIX",
        "MALFORMED_TARGET_COCHAIN",
        "MALFORMED_CASE_STRUCTURE",
    ]:
        assert r in content, f"TASK.md missing refusal enum {r}"

    for oos in ["RESTRICTION_SHAPE_MISMATCH", "SELF_LOOP", "UNKNOWN_ENDPOINT"]:
        assert oos in content, f"TASK.md missing out-of-scope enum {oos}"


def test_examples_inventory_and_validity():
    """Asserts 20 public examples exist and conform to schema."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) == 20, f"Expected 20 examples, found {len(example_files)}"

    for f in example_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        assert "id" in data
        inp = data.get("input", data)
        assert "vertices" in inp
        assert "edges" in inp
        assert "targets" in inp
        assert isinstance(inp["vertices"], list)
        assert isinstance(inp["edges"], list)
        assert isinstance(inp["targets"], list)


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


def test_runner_on_public_example(tmp_path: Path):
    """Asserts sandboxed runner executes reference solver on a public example."""
    ex_file = EXAMPLES_DIR / "ex01_solved_constant_tree.json"
    assert ex_file.exists()
    cases = load_cases(ex_file)
    assert len(cases) == 1
    solver_fn = load_solver_func()
    out_file = tmp_path / "answers.jsonl"
    count = run_cases(solver_fn, cases, out_file)
    assert count == 1
    record = json.loads(out_file.read_text(encoding="utf-8").strip())
    assert record.get("status") == "SOLVED"
    assert record.get("h0_dim") == "1"
    assert record.get("h1_dim") == "0"
    assert len(record.get("targets", [])) == 1
