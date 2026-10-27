"""
Local test runner for Challenge C054 participant packet.
"""

from pathlib import Path
import glob
import json
import os
import sys

for _parent in Path(__file__).resolve().parents:
    if (_parent / "sqlite_pilot_store.py").is_file():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from c054_exact_linear_systems.judge_packet.exact_checker import (
    check_exact,
)
from c054_exact_linear_systems.judge_packet.independent_checker import (
    independent_check,
)
from c054_exact_linear_systems.reference_solver.linear_solver import (
    solve_linear_system,
)


def main():
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")
    example_files = sorted(glob.glob(os.path.join(examples_dir, "*.json")))
    if not example_files:
        print(f"Error: No example files found in {examples_dir}")
        sys.exit(1)

    print(f"Running C054 Participant Packet on {len(example_files)} examples...")
    passed = 0
    for path in example_files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data["input"]
        res = solve_linear_system(inp)

        ok_exact, msg_exact = check_exact(inp, res)
        ok_indep, msg_indep = independent_check(inp, res)

        cid = inp.get("case_id")
        if ok_exact and ok_indep:
            print(f"  [PASS] {cid} -> {res.get('status')} ({res.get('kind', 'N/A')})")
            passed += 1
        else:
            print(f"  [FAIL] {cid} -> exact: {msg_exact}, indep: {msg_indep}")

    print(f"\nResult: {passed}/{len(example_files)} passed.")
    if passed == len(example_files):
        print("ALL EXAMPLES PASSED SUCCESSFULLY.")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
