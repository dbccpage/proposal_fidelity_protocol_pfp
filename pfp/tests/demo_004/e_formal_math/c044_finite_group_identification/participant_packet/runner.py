# AuthorityEffect: None.
"""
Participant Runner for C044 Finite Group Identification.
Executes the participant solver on all public examples and validates via dual checkers.
"""

import json
import sys
from pathlib import Path

# Add repository root to sys.path
_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.solver import (
    solve,
)


def run_public_evaluation():
    base_dir = Path(__file__).resolve().parent
    examples_dir = base_dir / "examples"
    example_files = sorted(examples_dir.glob("c044_pub_*.json"))

    print(f"Running C044 Participant Runner on {len(example_files)} public examples...")
    passed = 0
    for f in example_files:
        with open(f, "r", encoding="utf-8") as stream:
            case = json.load(stream)
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        if ok:
            print(f"[PASS] {case['case_id']}: {msg}")
            passed += 1
        else:
            print(f"[FAIL] {case['case_id']}: {msg}")

    print(f"\nParticipant Summary: {passed}/{len(example_files)} passed.")
    return passed == len(example_files)


if __name__ == "__main__":
    success = run_public_evaluation()
    if not success:
        exit(1)
