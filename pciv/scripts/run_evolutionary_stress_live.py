"""Retired disconnected live evolutionary harness. AuthorityEffect: None.

The fixture feedback loop is run_evolutionary_stress_50gen.run_stress_test.
Live work uses the existing plan-consuming native/PFP teamwork boundary; its
executor is not a SeatTurnRequest adapter. This compatibility entry point
refuses before credentials, directories, or provider dispatch.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


def run_live_evolutionary_stress_test(
    num_generations: int = 3,
    output_dir: Path | None = None,
    cost_cap_microusd: int = 50_000,
    max_tokens_per_call: int = 80,
    model_name: str = "openai/gpt-4o-mini",
) -> dict[str, Any]:
    raise RuntimeError(
        "LEGACY_LIVE_RUNNER_RETIRED: disconnected synthetic-defect harness; "
        "use fixture run_stress_test locally or the native/PFP teamwork boundary for live work"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--cost-cap-microusd", type=int, default=50_000)
    parser.add_argument("--max-tokens", type=int, default=80)
    parser.add_argument("--model", default="openai/gpt-4o-mini")
    args = parser.parse_args()
    run_live_evolutionary_stress_test(
        args.generations, args.output_dir, args.cost_cap_microusd,
        args.max_tokens, args.model,
    )
