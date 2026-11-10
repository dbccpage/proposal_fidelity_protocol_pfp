# AuthorityEffect: None.
"""
Public Runner for C030: Tensor-Network Contraction Order Under a Cost Bound.

Runs all example cases in examples/ through the solver and writes answers.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_file_dir = Path(__file__).resolve().parent
_pkg_root = _file_dir.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from reference_solver.solver import solve


def main() -> None:
    parser = argparse.ArgumentParser(description="Run C030 examples through the reference solver.")
    parser.add_argument("--cases", type=Path, default=_file_dir / "examples")
    parser.add_argument("--out", type=Path, default=_file_dir / "answers.jsonl")
    args = parser.parse_args()

    examples_dir = args.cases
    cases = sorted(examples_dir.glob("*.json"))
    out_file = args.out

    print(f"Executing {len(cases)} cases through solver...")
    answers = []
    for cf in cases:
        with open(cf, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        ans = solve(case_data)
        answers.append(ans)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(json.dumps(ans, sort_keys=True) + "\n")

    print(f"Wrote {len(answers)} answers to {out_file}")


if __name__ == "__main__":
    main()
