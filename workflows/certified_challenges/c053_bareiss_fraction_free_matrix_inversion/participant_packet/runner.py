"""Participant runner for C053: Bareiss Fraction-Free Matrix Inversion."""

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "sqlite_pilot_store.py").is_file()
)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from c053_bareiss_fraction_free_matrix_inversion.judge_packet.exact_checker import (
    check_solution,
)
from c053_bareiss_fraction_free_matrix_inversion.reference_solver import (
    solve,
)


def main():
    parser = argparse.ArgumentParser(description="Run matrix inversion solver on test cases.")
    parser.add_argument("--case", type=str, help="Path to single input JSON case file.")
    parser.add_argument(
        "--all-examples", action="store_true", help="Run against all public examples."
    )
    args = parser.parse_args()

    examples_dir = Path(__file__).resolve().parent / "examples"

    if args.case:
        with open(args.case, "r", encoding="utf-8") as f:
            data = json.load(f)
        case_input = data.get("input", data)
        t0 = time.perf_counter()
        result = solve(case_input)
        dt = (time.perf_counter() - t0) * 1000
        ok, msg = check_solution(case_input, result)
        print(f"[{'PASS' if ok else 'FAIL'}] {case_input.get('case_id')}: {msg} ({dt:.2f}ms)")
        print(json.dumps(result, indent=2))
        sys.exit(0 if ok else 1)

    if args.all_examples:
        example_files = sorted(examples_dir.glob("*.json"))
        passed = 0
        total = len(example_files)
        print(f"Running runner across {total} public examples...")
        for ef in example_files:
            with open(ef, "r", encoding="utf-8") as f:
                data = json.load(f)
            case_input = data.get("input", data)
            t0 = time.perf_counter()
            result = solve(case_input)
            dt = (time.perf_counter() - t0) * 1000
            ok, msg = check_solution(case_input, result)
            if ok:
                passed += 1
                print(f"  [PASS] {case_input.get('case_id')} ({dt:.2f}ms): {msg}")
            else:
                print(f"  [FAIL] {case_input.get('case_id')} ({dt:.2f}ms): {msg}")
        print(f"Summary: {passed}/{total} passed.")
        sys.exit(0 if passed == total else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
