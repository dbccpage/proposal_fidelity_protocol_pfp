"""test_l8_n4_cross_validation.py — Unit Tests for L=8, N=4 Cross-Validation under Correlated Noise.

AuthorityEffect: None.
Reference: PFP XX, Paper 020, gemini_000.md.
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
import pytest

# Ensure code dir is in sys.path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from l8_n4_cross_validation import (
    L8N4CrossValidationReceipt,
    L8N4CrossValidationRunner,
    L8N4LeaderboardEntry,
    L8N4RoundResult,
    run_l8_n4_cross_validation_demo,
)


class TestL8N4CrossValidation:
    """Test suite for L=8, N=4 cross-validation runner and noise models."""

    def test_runner_initialization_defaults(self) -> None:
        runner = L8N4CrossValidationRunner()
        assert runner.validation_id == "L8-N4-CROSSVAL-V1"
        assert runner.lattice_l == 8
        assert runner.num_qubits == 4
        assert runner.num_modes == 16
        assert runner.num_folds == 3

    def test_cross_validation_run_deterministic(self) -> None:
        runner = L8N4CrossValidationRunner(validation_id="TEST-L8N4-RUN", num_folds=1)
        receipt = runner.run_validation(
            noise_budgets=[Fraction(1, 100)],
            target_operations=["cnot_14", "ghz_4"],
        )

        assert receipt.validation_id == "TEST-L8N4-RUN"
        assert receipt.lattice_l == 8
        assert receipt.num_qubits == 4
        assert receipt.num_modes == 16
        assert receipt.num_folds == 1
        assert len(receipt.leaderboard) == 4
        assert receipt.authority_effect == "None"
        assert receipt.sha256_hash == receipt.canonical_digest()

    def test_all_target_operations_and_strategies(self) -> None:
        runner = L8N4CrossValidationRunner(validation_id="TEST-ALL-OPS", num_folds=1)
        receipt = runner.run_validation(
            noise_budgets=[Fraction(1, 100)],
            target_operations=["cnot_14", "ghz_4", "cluster_4", "star_14", "fallback_op"],
        )
        assert len(receipt.evaluated_operations) == 5
        # Total rounds: 1 fold * 1 budget * 2 noise models * 5 operations * 4 models = 40 evaluations
        assert len(receipt.round_results) == 40
        for r in receipt.round_results:
            assert r.gate_count >= 1

    def test_negative_control_target_refusal(self) -> None:
        """Verify referee rejects negative controls that omit requested target gates."""
        runner = L8N4CrossValidationRunner(validation_id="TEST-TARGET-REFUSAL", num_folds=1)
        receipt = runner.run_validation(
            noise_budgets=[Fraction(1, 100)],
            target_operations=["cnot_14"],
        )
        random_rounds = [r for r in receipt.round_results if r.proposer_id == "agent-random-baseline"]
        for r in random_rounds:
            assert not r.is_accepted
            assert r.status_reason == "REFUSAL_TARGET_UNFULFILLED"

        # Check random baseline ranks last
        random_entry = [e for e in receipt.leaderboard if e.proposer_id == "agent-random-baseline"][0]
        assert random_entry.acceptance_rate == Fraction(0, 1)
        assert random_entry.rank == 4

    def test_tight_tolerance_refusal(self) -> None:
        """Verify referee rejects when tolerance is too tight."""
        runner = L8N4CrossValidationRunner(validation_id="TEST-REFUSAL", num_folds=1)
        receipt = runner.run_validation(
            noise_budgets=[Fraction(1, 10)],
            target_operations=["cnot_14"],
            tolerance_multiplier=Fraction(1, 1000),  # very tight tolerance
        )
        for r in receipt.round_results:
            assert not r.is_accepted
            assert r.status_reason in ("REFUSAL_NOISE_LEAKAGE", "REFUSAL_TARGET_UNFULFILLED")

    def test_claim_hygiene_summary_formatting(self) -> None:
        runner = L8N4CrossValidationRunner(validation_id="TEST-HYGIENE", num_folds=1)
        receipt = runner.run_validation(
            noise_budgets=[Fraction(1, 100)],
            target_operations=["cnot_14"],
        )
        summary = receipt.claim_hygiene_summary()

        assert "AuthorityEffect: None" in summary
        assert "## 1. What it supports" in summary
        assert "## 2. What it does not support" in summary
        assert "## 3. Narrowest defensible claim" in summary
        assert "## 4. Next test needed" in summary

        # Check that no forbidden hype words are present
        forbidden = [
            "proves",
            "guarantees",
            "mathematically verifies",
            "fundamentally",
            "true intelligence",
            "impossible",
            "universal",
            "flawless",
            "clearly",
            "obviously",
        ]
        summary_lower = summary.lower()
        for word in forbidden:
            assert word not in summary_lower

    def test_canonical_demo_execution(self) -> None:
        receipt = run_l8_n4_cross_validation_demo()
        assert isinstance(receipt, L8N4CrossValidationReceipt)
        assert receipt.validation_id == "L8-N4-CROSSVAL-V1"
        assert len(receipt.leaderboard) == 4
