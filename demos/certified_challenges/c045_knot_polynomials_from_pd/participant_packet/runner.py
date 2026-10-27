# AuthorityEffect: None.
"""
Participant Runner for C045 (Knot Polynomials from Planar Diagrams).
Runs solver on all 12 public worked examples and audits consensus with dual checkers.
"""

import json
import sys
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c045_knot_polynomials_from_pd.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c045_knot_polynomials_from_pd.reference_solver.solver import (
    solve,
)


def run_public_evaluation():
    base_dir = Path(__file__).resolve().parent
    examples_dir = base_dir / "examples"
    example_files = sorted(examples_dir.glob("ex*.json"))

    print(f"Running C045 Participant Runner on {len(example_files)} public examples...")
    passed = 0
    for f in example_files:
        with open(f, "r", encoding="utf-8") as stream:
            payload = json.load(stream)
        case = payload["input"]
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
        sys.exit(1)
