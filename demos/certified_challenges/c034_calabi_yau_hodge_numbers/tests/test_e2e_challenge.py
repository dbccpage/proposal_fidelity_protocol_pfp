"""End-to-End Multi-Tier Integration Test for Challenge C034.

AuthorityEffect: None.

Verifies:
  Tier 1: Participant packet integrity and schema conformity.
  Tier 2: Reference solver accuracy across examples and base cases.
  Tier 3: 100% dual checker concordance across all 46 judge cases.
  Tier 4: 100% hostile mutation detection across all 52 corrupted certificates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from c034_calabi_yau_hodge_numbers.judge_packet.checkers.affine_hnf_checker import (
    verify_affine_hnf_certificate,
)
from c034_calabi_yau_hodge_numbers.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c034_calabi_yau_hodge_numbers.judge_packet.checkers.facet_point_checker import (
    verify_facet_point_certificate,
)
from c034_calabi_yau_hodge_numbers.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
MUT_DIR = JUDGE_DIR / "mutation_suite" / "mutations"


def test_tier1_participant_packet_conformance(tmp_path: Path):
    """Tier 1: Validates participant artifacts and CLI runner."""
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file()

    acc_file = PARTICIPANT_DIR / "accounting.json"
    assert acc_file.is_file()
    acc_data = json.loads(acc_file.read_text(encoding="utf-8"))
    assert acc_data["tier"] == "T2"
    assert acc_data["cost_ceiling_usd"] == 0.50

    # Runner CLI test
    out_file = tmp_path / "runner_out.json"
    cmd = [
        sys.executable,
        str(PARTICIPANT_DIR / "runner.py"),
        "--cases",
        str(PARTICIPANT_DIR / "examples" / "ex01_quintic_dual.json"),
        "--solver",
        str(CHALLENGE_DIR / "reference_solver" / "solver.py"),
        "--output",
        str(out_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert out_file.is_file()


def test_tier2_reference_solver_benchmarks():
    """Tier 2: Validates solver outputs across all 8 canonical examples."""
    examples = sorted((PARTICIPANT_DIR / "examples").glob("*.json"))
    assert len(examples) == 8

    for ex in examples:
        data = json.loads(ex.read_text(encoding="utf-8"))
        case = data.get("input", data)
        expected = data.get("expected_output")
        actual = solve(case)

        assert actual["status"] == expected["status"], f"Status mismatch on {ex.name}"
        if actual["status"] == "SOLVED":
            assert actual["h11"] == expected["h11"]
            assert actual["h21"] == expected["h21"]
            assert actual["euler"] == expected["euler"]


def test_tier3_dual_checker_concordance_46_cases():
    """Tier 3: Asserts 100% agreement and pass rate on all 46 judge cases."""
    case_files = sorted(CASES_DIR.rglob("*.json"))
    assert len(case_files) == 46

    agreed = 0
    passed = 0
    for cf in case_files:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        eval_res = evaluate_dual(case, ans)
        if eval_res["agreed"]:
            agreed += 1
        if eval_res["verdict"] == "PASS":
            passed += 1

    assert agreed == 46, f"Disagreements detected: {agreed}/46"
    assert passed == 46, f"Failures detected: {passed}/46"


def test_tier4_hostile_mutation_kill_rate_100_percent():
    """Tier 4: Asserts 100% kill rate across all 52 hostile mutations."""
    mut_files = sorted(MUT_DIR.glob("*.json"))
    assert len(mut_files) == 52

    killed_c1 = 0
    killed_c2 = 0
    for mf in mut_files:
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted = data.get("corrupted_result") or data.get("result")

        ok1, _ = verify_facet_point_certificate(case, corrupted)
        ok2, _ = verify_affine_hnf_certificate(case, corrupted)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == 52, f"Checker 1 missed mutations: killed {killed_c1}/52"
    assert killed_c2 == 52, f"Checker 2 missed mutations: killed {killed_c2}/52"
