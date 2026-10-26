"""
Unit tests for Symbol Game L1 Sparsity and Bullshit Excision Benchmark.
"""

from __future__ import annotations

import json
from pathlib import Path

from l1_sparsity_bullshit_benchmark import (
    build_heldout_dataset,
    deterministic_host_replay,
    run_benchmark,
)


def test_heldout_dataset_integrity():
    """Verify that exactly 50 tasks exist with unique IDs across 7 families."""
    tasks = build_heldout_dataset()
    assert len(tasks) == 50
    ids = [t.task_id for t in tasks]
    assert len(set(ids)) == 50
    families = {t.family for t in tasks}
    assert len(families) == 7
    assert "cyclic_c5" in families
    assert "permutation_s3" in families
    assert "simplicial_cochain" in families


def test_token_support_and_compression():
    """Verify token support reduction and compression ratio rho > 1.5x."""
    summary = run_benchmark()
    assert summary["total_tasks_evaluated"] == 50
    assert summary["mean_tokens_dense"] > summary["mean_tokens_sparse"]
    assert summary["aggregate_compression_ratio_rho"] > 2.0
    assert summary["token_reduction_percentage"] > 50.0


def test_fluff_and_smuggled_ontology_excision():
    """Verify 100% excision of conversational fluff and smuggled ontology."""
    summary = run_benchmark()
    assert summary["total_fluff_tokens_dense"] > 200
    assert summary["total_fluff_tokens_sparse"] == 0
    assert summary["fluff_excision_rate"] == 100.0

    assert summary["total_smuggled_ontology_dense"] > 20
    assert summary["total_smuggled_ontology_sparse"] == 0
    assert summary["smuggled_ontology_excision_rate"] == 100.0


def test_unpriced_rewrite_density():
    """Verify unpriced rewrite density delta_unpriced is 0 in Symbol Game mode."""
    summary = run_benchmark()
    assert summary["unpriced_rewrite_density_sparse"] == 0.0
    assert summary["unpriced_rewrite_density_dense"] > 0.80


def test_deterministic_host_replay_rates():
    """Verify 100% host replay for Symbol Game vs 0% for dense natural language."""
    summary = run_benchmark()
    assert summary["host_replay_success_rate_sparse"] == 100.0
    assert summary["host_replay_success_rate_dense"] == 0.0


def test_firewall_rejections_on_corrupted_replies():
    """Verify that corrupted replies (unlisted ops or out-of-carrier symbols) fail host replay."""
    tasks = build_heldout_dataset()
    task = tasks[0]

    # 1. Corrupt with undeclared op
    bad_op_response = (
        "GUESS period(c5) = 5 evidence: cycle:c5\n"
        "REDUCE 17 mod 5 = 2 evidence: integer-mod-replay\n"
        f"LAND successor^2(alpha) = {task.expected_result} evidence: cycle:c5"
    )
    passed, _ = deterministic_host_replay(task, bad_op_response, is_symbol_game=True)
    assert not passed

    # 2. Corrupt with undeclared carrier codepoint
    bad_carrier_response = (
        "PROVE period(c5) = 5 evidence: cycle:c5\n"
        "REDUCE 17 mod 5 = 2 evidence: integer-mod-replay\n"
        "LAND successor^2(omega_extraneous) = gamma evidence: cycle:c5"
    )
    passed, _ = deterministic_host_replay(task, bad_carrier_response, is_symbol_game=True)
    assert not passed


def test_audit_receipt_generation():
    """Verify that l1_sparsity_benchmark_receipt.json exists and matches schema."""
    receipt_path = Path(__file__).parent.parent / "l1_sparsity_benchmark_receipt.json"
    assert receipt_path.exists()
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data["total_tasks_evaluated"] == 50
    assert len(data["results_by_task"]) == 50
    assert data["host_replay_success_rate_sparse"] == 100.0
