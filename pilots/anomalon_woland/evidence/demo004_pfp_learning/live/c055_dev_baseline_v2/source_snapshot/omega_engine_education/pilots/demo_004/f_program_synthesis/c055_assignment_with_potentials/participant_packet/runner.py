"""
Local test runner for Challenge C055 participant packet.
"""

import glob
import json
import os
import sys

from omega_engine_projects.mssn_sn_symgam.challenges.f_program_synthesis.c055_assignment_with_potentials.judge_packet.exact_checker import (
    check_exact,
)
from omega_engine_projects.mssn_sn_symgam.challenges.f_program_synthesis.c055_assignment_with_potentials.judge_packet.independent_checker import (
    independent_check,
)
from omega_engine_projects.mssn_sn_symgam.challenges.f_program_synthesis.c055_assignment_with_potentials.reference_solver.hungarian import (
    solve_assignment,
)


def main():
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")
    example_files = sorted(glob.glob(os.path.join(examples_dir, "*.json")))
    if not example_files:
        print(f"Error: No example files found in {examples_dir}")
        sys.exit(1)

    print(f"Running C055 Participant Packet on {len(example_files)} examples...")
    passed = 0
    for path in example_files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data["input"]
        res = solve_assignment(inp)

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
