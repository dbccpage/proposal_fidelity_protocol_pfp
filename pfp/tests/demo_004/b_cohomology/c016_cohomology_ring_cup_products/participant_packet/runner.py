"""Participant sandbox runner for C016."""

from __future__ import annotations

import json
import sys

from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.solver import (
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
