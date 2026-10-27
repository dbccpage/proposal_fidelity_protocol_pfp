"""Participant runner for C060 Checker Synthesis Scored by Mutation Kill Rate."""

import json
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.reference_solver.checker import (
    check,
)


def main():
    examples_dir = Path(__file__).parent / "examples"
    example_files = sorted(list(examples_dir.glob("*.json")))
    if not example_files:
        print("No examples found in examples/ directory.")
        return

    passed = 0
    total = len(example_files)

    print(f"Running {total} public examples against reference checker...")
    for ex_file in example_files:
        with open(ex_file, "r", encoding="utf-8") as f:
            test_item = json.load(f)

        result = check(test_item.get("case"), test_item.get("cert"))
        ok, msg = verify_candidate(test_item, result)
        status_str = "PASS" if ok else "FAIL"
        print(f"[{status_str}] {ex_file.name}: {msg}")
        if ok:
            passed += 1

    print(f"\nResult: {passed}/{total} examples passed ({passed / total * 100:.1f}%)")


if __name__ == "__main__":
    main()
