#!/usr/bin/env python3
"""run_tournament.py — CLI Runner for Symbol Game Adaptive Braid Tournament.

AuthorityEffect: None.
Reference: PFP XX, 020_pfp_frontier_research.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

# Add code dir to sys.path
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from adaptive_braid_tournament_demo import (
    AdaptiveBraidTournament,
    CANONICAL_TOURNAMENT_MODELS,
    ProposerStrategyConfig,
    MODEL_8B,
    MODEL_70B,
    MODEL_GLM53,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run multi-agent evaluation tournaments in the Symbol Game."
    )
    parser.add_argument(
        "--qubits",
        type=int,
        default=2,
        help="Number of logical qubits (4 modes per qubit, default: 2).",
    )
    parser.add_argument(
        "--operation",
        type=str,
        default="hadamard_q1",
        choices=["hadamard_q1", "phase_q1", "cnot_12", "bell_pair"],
        help="Target logical operation (default: hadamard_q1).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional path to write the JSON tournament receipt.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Attempt live OpenRouter queries if OPENROUTER_API_KEY is present.",
    )
    args = parser.parse_args()

    proposers = [
        ProposerStrategyConfig(
            proposer_id="agent-llama-8b",
            model_name=MODEL_8B,
            strategy_type="direct_unmitigated",
            use_live_openrouter=args.live,
        ),
        ProposerStrategyConfig(
            proposer_id="agent-llama-70b",
            model_name=MODEL_70B,
            strategy_type="echo_mitigated",
            use_live_openrouter=args.live,
        ),
        ProposerStrategyConfig(
            proposer_id="agent-glm-5.3",
            model_name=MODEL_GLM53,
            strategy_type="targeted_compensation",
            use_live_openrouter=args.live,
        ),
        ProposerStrategyConfig(
            proposer_id="agent-random-baseline",
            model_name="random-negative-control",
            strategy_type="random_baseline",
            use_live_openrouter=False,
        ),
    ]

    tournament = AdaptiveBraidTournament(
        tournament_id="PFP-TOURNAMENT-CLI-020",
        num_qubits=args.qubits,
        proposers=proposers,
    )

    noise_budgets = [Fraction(1, 100), Fraction(1, 50), Fraction(1, 20), Fraction(1, 10)]

    receipt = tournament.run_sweep(noise_budgets=noise_budgets, target_operation=args.operation)

    print("=== TOURNAMENT LEADERBOARD ===")
    for entry in receipt.leaderboard:
        print(
            f"Rank {entry.rank}: {entry.proposer_id} ({entry.model_name}) | "
            f"Strategy: {entry.strategy_type} | "
            f"Accepted: {entry.accepted_rounds}/{entry.total_rounds} ({entry.acceptance_rate}) | "
            f"Mean Defect: {entry.mean_noise_defect}"
        )

    print("\n" + receipt.claim_hygiene_summary())

    if args.output:
        out_path = Path(args.output)
        payload = {
            "tournament_id": receipt.tournament_id,
            "sha256_hash": receipt.sha256_hash,
            "num_qubits": receipt.num_qubits,
            "num_rounds": receipt.num_rounds,
            "noise_budgets": [str(b) for b in receipt.noise_budgets],
            "models_evaluated": list(receipt.models_evaluated),
            "leaderboard": [
                {
                    "rank": e.rank,
                    "proposer_id": e.proposer_id,
                    "model_name": e.model_name,
                    "strategy_type": e.strategy_type,
                    "acceptance_rate": str(e.acceptance_rate),
                    "mean_noise_defect": str(e.mean_noise_defect),
                }
                for e in receipt.leaderboard
            ],
            "authority_effect": receipt.authority_effect,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote tournament receipt to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
