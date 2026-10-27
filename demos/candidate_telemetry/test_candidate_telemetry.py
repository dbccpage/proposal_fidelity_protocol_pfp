"""Verification suite for long-horizon candidate telemetry: AST fault tracing,
dense diff metrics, and checkpoint-tree backtracking.

AuthorityEffect: None.
"""

from __future__ import annotations

from ast_fault_tracer import trace_ast_faults
from diff_telemetry import compute_dense_diff_telemetry
from state_graph_recovery import MctsStateGraph


def test_ast_fault_tracer_clean_code() -> None:
    """Verify clean Python code parses and extracts declared functions without faults."""
    code = (
        "def compute_harmonic_sum(n: int) -> int:\n"
        "    total = 0\n"
        "    for i in range(1, n + 1):\n"
        "        total += i\n"
        "    return total\n"
    )
    report = trace_ast_faults(code)
    assert not report.has_syntax_error
    assert report.syntax_error_detail == ""
    assert "compute_harmonic_sum" in report.declared_functions
    assert len(report.illegal_nodes_detected) == 0


def test_ast_fault_tracer_syntax_error() -> None:
    """Verify malformed Python code triggers syntax fault reporting."""
    code = "def invalid_syntax(\n    return 42\n"
    report = trace_ast_faults(code)
    assert report.has_syntax_error
    assert "SyntaxError" in report.syntax_error_detail


def test_ast_fault_tracer_detects_illegal_float_constants() -> None:
    """Verify floating point literals are flagged as illegal nodes under exact rational arithmetic."""
    code = (
        "def area(radius: int) -> float:\n"
        "    pi = 3.14159\n"
        "    return pi * radius * radius\n"
    )
    report = trace_ast_faults(code)
    assert not report.has_syntax_error
    assert len(report.illegal_nodes_detected) > 0
    assert any("FloatConstant" in node for node in report.illegal_nodes_detected)


def test_dense_diff_telemetry_computation() -> None:
    """Verify unified diff calculation, line counts, and token amortization score."""
    base = (
        "def process():\n"
        "    old_step()\n"
        "    finish()\n"
    )
    new = (
        "def process():\n"
        "    new_step_a()\n"
        "    new_step_b()\n"
        "    finish()\n"
    )
    record = compute_dense_diff_telemetry(
        round_index=1,
        candidate_id="cand_1",
        parent_candidate_id="base",
        base_code=base,
        new_code=new,
        tokens_billed=500,
    )
    assert record.round_index == 1
    assert record.candidate_id == "cand_1"
    assert record.added_lines == 2
    assert record.removed_lines == 1
    assert record.diff_sha256.startswith("sha256:")
    assert record.token_amortization_score > 0.0
    assert "new_step_a" in record.unified_diff


def test_mcts_state_graph_backtracking() -> None:
    """Verify checkpoint tree navigation and MCTS-style backtracking upon failure accumulation."""
    graph = MctsStateGraph(root_code="root_code()", root_sha256="sha256:root000")
    assert graph.current_tip_id == "root"

    # Round 1: candidate degrades or fails oracle
    graph.record_candidate(
        checkpoint_id="c1",
        round_index=1,
        code="c1_code()",
        code_sha256="sha256:c111",
        oracle_score=0.6,
        verdict="REJECTED",
    )
    assert graph.current_tip_id == "c1"
    needs_bt, ancestor = graph.check_need_backtrack(threshold_failures=2)
    assert not needs_bt

    # Round 2: candidate fails again
    graph.record_candidate(
        checkpoint_id="c2",
        round_index=2,
        code="c2_code()",
        code_sha256="sha256:c222",
        oracle_score=0.3,
        verdict="REJECTED",
    )
    assert graph.current_tip_id == "c2"

    # Threshold reached: 2 consecutive failures -> trigger backtrack recommendation
    needs_bt, recommended_ancestor = graph.check_need_backtrack(threshold_failures=2)
    assert needs_bt
    assert recommended_ancestor in ("root", "c1")

    # Backtrack tip to recommended ancestor
    restored_node = graph.backtrack_to(recommended_ancestor or "root")
    assert restored_node is not None
    assert graph.current_tip_id == recommended_ancestor
