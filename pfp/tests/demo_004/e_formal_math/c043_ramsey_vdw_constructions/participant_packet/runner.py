# AuthorityEffect: None.
"""
Participant Test Runner for C043 Ramsey & Van der Waerden Constructions.
Executes solve(case) on public examples and verifies using dual checkers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PKG_ROOT.parent.parent.parent.parent.parent
for p in (PKG_ROOT, REPO_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from judge_packet.checkers.dual_evaluator import evaluate_dual
from reference_solver.solver import solve


def run_participant_benchmark() -> bool:
    ex_dir = PKG_ROOT / "participant_packet" / "examples"
    cases = sorted(ex_dir.glob("*.json"))
    print(f"Running C043 Participant Runner on {len(cases)} public examples...")

    passed = 0
    for cpath in cases:
        with open(cpath, "r", encoding="utf-8") as f:
            case = json.load(f)

        ans = solve(case)
        ok, msg, meta = evaluate_dual(case, ans)
        status_lbl = "PASS" if ok else "FAIL"
        print(f"[{status_lbl}] {case['case_id']}: {msg}")
        if ok:
            passed += 1

    print(f"\nParticipant Summary: {passed}/{len(cases)} passed.")
    return passed == len(cases)


if __name__ == "__main__":
    success = run_participant_benchmark()
    sys.exit(0 if success else 1)
