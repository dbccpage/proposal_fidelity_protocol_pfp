"""Sandboxed challenge runner for C020."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_CHALLENGES = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_CHALLENGES) not in sys.path:
    sys.path.insert(0, str(_CHALLENGES))

from c020_spectral_sequence_double_complex.reference_solver.solver import (
    solve,
)


def run_public_examples() -> dict[str, Any]:
    examples_dir = Path(__file__).resolve().parent / "examples"
    example_files = sorted(examples_dir.glob("*.json"))

    results: list[dict[str, Any]] = []
    for ef in example_files:
        with ef.open(encoding="utf-8") as f:
            case = json.load(f)
        output = solve(case)
        results.append(
            {
                "example_id": case.get("id"),
                "status": output.get("status"),
            }
        )

    return {
        "total_examples": len(example_files),
        "results": results,
    }


if __name__ == "__main__":
    res = run_public_examples()
    print(f"Executed {res['total_examples']} public examples.")
