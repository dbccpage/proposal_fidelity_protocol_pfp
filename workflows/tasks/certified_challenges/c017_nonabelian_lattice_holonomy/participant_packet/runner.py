"""Participant sandbox runner for C017."""

from __future__ import annotations

import json
import sys

from pathlib import Path

_CHALLENGES = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_CHALLENGES) not in sys.path:
    sys.path.insert(0, str(_CHALLENGES))

from c017_nonabelian_lattice_holonomy.reference_solver.solver import (
    solve,
)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python runner.py <case.json>")
        sys.exit(1)
    case_path = sys.argv[1]
    with open(case_path, "r", encoding="utf-8") as f:
        case = json.load(f)
    result, tracer = solve(case)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
