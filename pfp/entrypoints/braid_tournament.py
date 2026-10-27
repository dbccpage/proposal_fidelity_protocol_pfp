"""Practical bounded current entrypoint for the original finite braid tournament."""

import argparse
import json
from fractions import Fraction
from pathlib import Path

from pfp.infrastructure.braid_tournament import (
    DEFAULT_NOISE_BUDGETS,
    AdaptiveBraidTournament,
    ProposerStrategyConfig,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--models", nargs="+")
    parser.add_argument("--noise-budgets", nargs="+", default=[str(b) for b in DEFAULT_NOISE_BUDGETS])
    parser.add_argument("--max-rounds", type=int, default=4)
    parser.add_argument("--qubits", type=int, default=2)
    parser.add_argument("--operation", default="hadamard_q1")
    parser.add_argument("--max-output-tokens", type=int, default=1024)
    parser.add_argument("--max-provider-calls", type=int, default=16)
    parser.add_argument("--max-estimated-cost-microusd", type=int)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    if args.live and (not args.models or args.max_estimated_cost_microusd is None):
        parser.error("live requires explicit --models and --max-estimated-cost-microusd")
    if not args.live and args.models:
        parser.error("--models requires --live; offline uses the original deterministic strategies")
    try:
        configs = [ProposerStrategyConfig(f"model-{index}", model, "live_proposal", True)
            for index, model in enumerate(args.models or [])] if args.live else None
        tournament = AdaptiveBraidTournament("PFP-BRAID-TOURNAMENT", args.qubits,
            proposers=configs, output_dir=args.output_dir, max_rounds=args.max_rounds,
            max_output_tokens=args.max_output_tokens, max_provider_calls=args.max_provider_calls,
            max_estimated_cost_microusd=args.max_estimated_cost_microusd, env_file=args.env_file)
        tournament.run_sweep([Fraction(value) for value in args.noise_budgets], args.operation)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc), "authority_effect": "None"}))
        return 2
    print(json.dumps(tournament.report, default=str, ensure_ascii=True))
    return 0 if tournament.report["completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
