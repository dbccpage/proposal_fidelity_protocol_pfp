"""Participant runner for C058 Straight-Line Superoptimization."""

import json
import sys
from pathlib import Path

# Add project root to path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.judge_packet.exact_checker import (
    verify_candidate,
)
from pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.reference_solver import (
    solve,
)


def main():
    examples_dir = Path(__file__).parent / "examples"
    example_files = sorted(list(examples_dir.glob("*.json")))
    if not example_files:
        print("No examples found in examples/ directory.")
        return

    passed = 0
    total = len(example_files)

    print(f"Running {total} public examples...")
    for ex_file in example_files:
        with open(ex_file, "r", encoding="utf-8") as f:
            case = json.load(f)

        result = solve(case)
        ok, msg = verify_candidate(case, result)
        status_str = "PASS" if ok else "FAIL"
        print(f"[{status_str}] {ex_file.name}: {msg}")
        if ok:
            passed += 1

    print(f"\nResult: {passed}/{total} examples passed ({passed / total * 100:.1f}%)")


if __name__ == "__main__":
    main()
