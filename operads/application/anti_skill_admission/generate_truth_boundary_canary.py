"""Generate proposed truth-boundary specs and computed evaluation receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def generate_truth_boundary_canary(output: Path) -> tuple[Path, ...]:
    raise RuntimeError(
        "Legacy Python prompt_civilization runtime is retired in favor of omega_engine/crates_rs/omega_prompt_civilization"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate truth-boundary specs and evaluation receipts."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate_truth_boundary_canary(args.output)
    return 0


__all__ = ["generate_truth_boundary_canary", "main"]
