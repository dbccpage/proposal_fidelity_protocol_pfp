# AuthorityEffect: None.
"""
Comprehensive Test Suite for C046: Knuth-Bendix Completion.
Verifies:
1. 100% pass rate on 64 hidden evaluation cases.
2. 100% kill rate (48/48) on hostile mutations.
3. Consensus agreement across exact_checker and independent_checker.
"""

import json
import sys
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.solver import (
    solve,
)


def test_hidden_cases_pass_rate():
    hidden_path = (
        Path(__file__).resolve().parents[1]
        / "judge_packet"
        / "hidden_cases"
        / "c046_hidden_cases_64.json"
    )
    assert hidden_path.exists(), f"Missing hidden cases file at {hidden_path}"
    with open(hidden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"
    passed = 0
    for case in cases:
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        assert ok, f"Case {case['case_id']} failed evaluation: {msg} (receipt: {receipt})"
        passed += 1

    assert passed == 64, f"Expected 64 passes, got {passed}"
    print("[PASS] test_hidden_cases_pass_rate: 64/64 passed dual checker audit.")


def test_hostile_mutations_kill_rate():
    mutations_path = (
        Path(__file__).resolve().parents[1]
        / "judge_packet"
        / "mutation_suite"
        / "c046_hostile_mutations_48.json"
    )
    assert mutations_path.exists(), f"Missing mutations file at {mutations_path}"
    with open(mutations_path, "r", encoding="utf-8") as f:
        mutations = json.load(f)

    assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"
    killed = 0
    for m in mutations:
        case = m["case"]
        corrupted = m["corrupted_ans"]
        ok, msg, receipt = evaluate_dual(case, corrupted)
        if not ok:
            killed += 1
        else:
            print(f"[MUTATION SURVIVED] {m['mutation_id']} ({m['type']}): {msg}")

    assert killed == 48, f"Expected 48/48 mutations killed, but {48 - killed} survived!"
    print("[PASS] test_hostile_mutations_kill_rate: 48/48 (100.0%) hostile mutations killed.")


if __name__ == "__main__":
    test_hidden_cases_pass_rate()
    test_hostile_mutations_kill_rate()
