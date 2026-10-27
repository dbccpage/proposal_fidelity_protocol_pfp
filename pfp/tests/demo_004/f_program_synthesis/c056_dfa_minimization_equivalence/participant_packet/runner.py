"""Participant packet runner for C056: DFA Minimization and Equivalence."""

import json
import sys
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.judge_packet.exact_checker import (
    check_exact,
)
from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.judge_packet.independent_checker import (
    independent_check,
)
from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.reference_solver import (
    solve,
)


def run_examples():
    ex_dir = Path(__file__).resolve().parent / "examples"
    example_files = sorted(ex_dir.glob("*.json"))
    print(f"Running {len(example_files)} public examples...")
    passed = 0
    for ef in example_files:
        with open(ef, "r", encoding="utf-8") as f:
            data = json.load(f)
        case = data["case"] if "case" in data else data
        sol = solve(case)
        ok_exact, msg_exact = check_exact(case, sol)
        ok_indep, msg_indep = independent_check(case, sol)
        if ok_exact and ok_indep:
            passed += 1
            print(f"  [PASS] {case.get('case_id')}")
        else:
            print(
                f"  [FAIL] {case.get('case_id')}: exact=({ok_exact}, '{msg_exact}'), indep=({ok_indep}, '{msg_indep}')"
            )
    print(f"Result: {passed}/{len(example_files)} passed")
    return passed == len(example_files)


if __name__ == "__main__":
    success = run_examples()
    sys.exit(0 if success else 1)
