#!/usr/bin/env python3
"""run_cross_validation.py — CLI Runner for L=8, N=4 Cross-Validation under Correlated Noise.

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

from l8_n4_cross_validation import (
    L8N4CrossValidationRunner,
    run_l8_n4_cross_validation_demo,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run L=8, N=4 cross-validation sweeps under correlated noise in the Symbol Game."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional path to write the JSON cross-validation receipt.",
    )
    args = parser.parse_args()

    receipt = run_l8_n4_cross_validation_demo()

    if args.output:
        out_path = Path(args.output)
        payload = {
            "validation_id": receipt.validation_id,
            "sha256_hash": receipt.sha256_hash,
            "lattice_l": receipt.lattice_l,
            "num_qubits": receipt.num_qubits,
            "num_modes": receipt.num_modes,
            "evaluated_operations": list(receipt.evaluated_operations),
            "noise_models_tested": list(receipt.noise_models_tested),
            "noise_budgets": [str(b) for b in receipt.noise_budgets],
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
        print(f"\nWrote cross-validation receipt to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
