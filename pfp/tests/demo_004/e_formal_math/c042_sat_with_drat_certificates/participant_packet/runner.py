# AuthorityEffect: None.
"""
Participant Test Runner for C042.
Executes solve(case) on public examples and checks against answers.jsonl.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.solver import solve


def run_participant_benchmark() -> bool:
    ex_dir = PKG_ROOT / "participant_packet" / "examples"
    ans_file = PKG_ROOT / "participant_packet" / "answers.jsonl"

    expected_answers = {}
    if ans_file.exists():
        with open(ans_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    expected_answers[item["case_id"]] = item

    cases = sorted(ex_dir.glob("*.json"))
    print(f"Running C042 Participant Runner on {len(cases)} public examples...")

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
