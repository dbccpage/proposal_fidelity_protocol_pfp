"""test_adaptive_braid_tournament_demo.py — Unit Tests for Symbol Game Braid Tournament.

AuthorityEffect: None.
Reference: PFP XX, 020_pfp_frontier_research, gemini_000.md.
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure code dir is in sys.path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from adaptive_braid_tournament_demo import (
    AdaptiveBraidTournament,
    BraidTournamentProposerAgent,
    CANONICAL_TOURNAMENT_MODELS,
    MODEL_8B,
    MODEL_70B,
    MODEL_GLM53,
    ProposerLeaderboardEntry,
    ProposerStrategyConfig,
    TournamentRoundResult,
    TournamentRunReceipt,
    run_canonical_tournament_demo,
)


class TestProposerStrategyConfig:
    """Test configuration structures."""

    def test_proposer_config_instantiation(self) -> None:
        cfg = ProposerStrategyConfig(
            proposer_id="agent-test",
            model_name=MODEL_8B,
            strategy_type="direct_unmitigated",
            use_live_openrouter=False,
        )
        assert cfg.proposer_id == "agent-test"
        assert cfg.model_name == MODEL_8B
        assert cfg.strategy_type == "direct_unmitigated"
        assert not cfg.use_live_openrouter


class TestBraidTournamentProposerAgent:
    """Test proposer agent schedule synthesis and fallback modes."""

    def test_direct_unmitigated_schedules(self) -> None:
        cfg = ProposerStrategyConfig("p1", MODEL_8B, "direct_unmitigated")
        agent = BraidTournamentProposerAgent(cfg)

        for op in ("hadamard_q1", "hadamard_q0", "phase_q1", "phase_q0", "cnot_12", "bell_pair", "unknown_op"):
            proposal = agent.propose_schedule(
                round_id="R1",
                num_qubits=2,
                target_operation=op,
                noise_couplings=((1, 2, Fraction(1, 100)),),
                tolerance_epsilon=Fraction(1, 10),
            )
            assert proposal.round_id == "R1"
            assert proposal.num_qubits == 2
            assert len(proposal.operations) >= 1

    def test_echo_mitigated_schedules(self) -> None:
        cfg = ProposerStrategyConfig("p2", MODEL_70B, "echo_mitigated")
        agent = BraidTournamentProposerAgent(cfg)

        for op in ("hadamard_q1", "phase_q1", "cnot_12", "bell_pair", "fallback_op"):
            proposal = agent.propose_schedule(
                round_id="R2",
                num_qubits=2,
                target_operation=op,
                noise_couplings=((1, 2, Fraction(1, 100)),),
                tolerance_epsilon=Fraction(1, 10),
            )
            assert len(proposal.operations) >= 1
            if op == "hadamard_q1":
                # Verify echo pulses are present
                assert any(o[0] == "phase" for o in proposal.operations)
                assert any(o[0] == "hadamard" for o in proposal.operations)

    def test_targeted_compensation_schedules(self) -> None:
        cfg = ProposerStrategyConfig("p3", MODEL_GLM53, "targeted_compensation")
        agent = BraidTournamentProposerAgent(cfg)

        # With active couplings
        couplings = ((1, 2, Fraction(1, 20)), (2, 3, Fraction(1, 10)))
        proposal = agent.propose_schedule(
            round_id="R3",
            num_qubits=2,
            target_operation="hadamard_q1",
            noise_couplings=couplings,
            tolerance_epsilon=Fraction(1, 10),
        )
        assert len(proposal.operations) >= 1
        # Top coupling is (2, 3) which triggers elementary compensation
        assert any(o[0] == "elementary" for o in proposal.operations)

        # Without active couplings
        proposal_empty = agent.propose_schedule(
            round_id="R3b",
            num_qubits=2,
            target_operation="phase_q1",
            noise_couplings=(),
            tolerance_epsilon=Fraction(1, 10),
        )
        assert len(proposal_empty.operations) == 1

    def test_random_baseline_schedules(self) -> None:
        cfg = ProposerStrategyConfig("p4", "random-baseline", "random_baseline")
        agent = BraidTournamentProposerAgent(cfg)
        proposal = agent.propose_schedule(
            round_id="R4",
            num_qubits=2,
            target_operation="hadamard_q1",
            noise_couplings=(),
            tolerance_epsilon=Fraction(1, 10),
        )
        assert proposal.operations == (("elementary", (1, 0)),)

    def test_unknown_strategy_fallback(self) -> None:
        cfg = ProposerStrategyConfig("p5", "model-custom", "unknown_strat")
        agent = BraidTournamentProposerAgent(cfg)
        proposal = agent.propose_schedule(
            round_id="R5",
            num_qubits=2,
            target_operation="hadamard_q1",
            noise_couplings=(),
            tolerance_epsilon=Fraction(1, 10),
        )
        assert len(proposal.operations) >= 1

    def test_openrouter_live_query_handling(self) -> None:
        cfg = ProposerStrategyConfig("p-live", MODEL_8B, "direct_unmitigated", use_live_openrouter=True)
        agent = BraidTournamentProposerAgent(cfg)

        # 1. When API key is not present, falls back cleanly to deterministic schedule
        with patch.dict("os.environ", {}, clear=True):
            proposal = agent.propose_schedule(
                round_id="R-live-1",
                num_qubits=2,
                target_operation="hadamard_q1",
                noise_couplings=((1, 2, Fraction(1, 50)),),
                tolerance_epsilon=Fraction(1, 10),
            )
            assert len(proposal.operations) >= 1

        # 2. When mock OpenRouter response succeeds
        mock_backend = MagicMock()
        mock_receipt = MagicMock()
        mock_receipt.content = json.dumps({"operations": [["hadamard", [1, 0]], ["phase", [1, 0]]]})
        mock_backend.complete_with_receipt.return_value = mock_receipt

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            with patch("model_backends.OpenRouterBackend", return_value=mock_backend):
                proposal_mock = agent.propose_schedule(
                    round_id="R-live-2",
                    num_qubits=2,
                    target_operation="hadamard_q1",
                    noise_couplings=((1, 2, Fraction(1, 50)),),
                    tolerance_epsilon=Fraction(1, 10),
                )
                assert proposal_mock.operations == (("hadamard", (1, 0)), ("phase", (1, 0)))


class TestAdaptiveBraidTournament:
    """Test suite for AdaptiveBraidTournament execution and leaderboard calculation."""

    def test_tournament_run_sweep_deterministic(self) -> None:
        tournament = AdaptiveBraidTournament(
            tournament_id="TEST-TOURNAMENT-001",
            num_qubits=2,
        )
        budgets = [Fraction(1, 100), Fraction(1, 50)]
        receipt = tournament.run_sweep(budgets, target_operation="hadamard_q1")

        assert receipt.tournament_id == "TEST-TOURNAMENT-001"
        assert receipt.num_qubits == 2
        assert receipt.num_rounds == 2
        assert len(receipt.leaderboard) == 4
        assert len(receipt.round_results) == 8
        assert receipt.authority_effect == "None"
        assert receipt.sha256_hash == receipt.canonical_digest()

    def test_refusal_on_high_noise(self) -> None:
        """Verify that when noise exceeds tolerance, referee issues refusal."""
        tournament = AdaptiveBraidTournament(
            tournament_id="TEST-TOURNAMENT-REFUSAL",
            num_qubits=2,
        )
        # Tight tolerance multiplier 1/10 relative to budget
        receipt = tournament.run_sweep(
            noise_budgets=[Fraction(1, 10)],
            target_operation="hadamard_q1",
            tolerance_multiplier=Fraction(1, 100),
        )
        assert receipt.num_rounds == 1
        # In very tight tolerance, all proposers should fail noise leakage gate
        for res in receipt.round_results:
            assert not res.is_accepted
            assert res.status_reason == "REFUSAL_NOISE_LEAKAGE"

    def test_claim_hygiene_summary_formatting(self) -> None:
        tournament = AdaptiveBraidTournament(
            tournament_id="TEST-TOURNAMENT-SUMMARY",
            num_qubits=2,
        )
        receipt = tournament.run_sweep([Fraction(1, 100)])
        summary = receipt.claim_hygiene_summary()

        assert "AuthorityEffect" in summary
        assert "None" in summary
        assert "## 1. What it supports" in summary
        assert "## 2. What it does not support" in summary
        assert "## 3. Narrowest defensible claim" in summary
        assert "## 4. Next test needed" in summary
        # Verify no forbidden hype words
        forbidden = ["proves", "guarantees", "universal", "flawless", "clearly", "obviously"]
        for word in forbidden:
            assert word not in summary.lower()

    def test_canonical_tournament_demo_entrypoint(self) -> None:
        receipt = run_canonical_tournament_demo()
        assert isinstance(receipt, TournamentRunReceipt)
        assert receipt.tournament_id == "PFP-TOURNAMENT-DEMO-020"
        assert receipt.num_rounds == 4
        assert len(receipt.leaderboard) == 4
