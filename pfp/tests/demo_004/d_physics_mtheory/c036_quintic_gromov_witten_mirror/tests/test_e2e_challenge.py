"""End-to-End Multi-Tier Integration Test for Challenge C036.

AuthorityEffect: None.

Verifies:
  Tier 1: Participant packet integrity and schema conformity.
  Tier 2: Reference solver accuracy across examples and base cases.
  Tier 3: 100% dual checker concordance across all 28 judge cases.
  Tier 4: 100% hostile mutation detection across all 48 corrupted certificates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.judge_packet.checkers.hypergeometric_mirror_checker import (
    verify_hypergeometric_mirror_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.judge_packet.checkers.picard_fuchs_recurrence_checker import (
    verify_picard_fuchs_recurrence_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.reference_solver.solver import (
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
        str(PARTICIPANT_DIR / "examples" / "ex01_quintic_d1.json"),
        "--solver",
        str(CHALLENGE_DIR / "reference_solver" / "solver.py"),
        "--output",
        str(out_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert out_file.is_file()


def test_tier2_reference_solver_benchmarks():
    """Tier 2: Validates solver outputs across all 6 canonical examples."""
    examples = sorted((PARTICIPANT_DIR / "examples").glob("*.json"))
    assert len(examples) == 6

    expected_statuses = {
        "ex01_quintic_d1.json": "SOLVED",
        "ex02_quintic_d2.json": "SOLVED",
        "ex03_quintic_d3.json": "SOLVED",
        "ex04_quintic_permuted_weights.json": "SOLVED",
        "ex05_non_calabi_yau_out_of_scope.json": "OUT_OF_SCOPE",
        "ex06_unlisted_family_unknown.json": "UNKNOWN",
    }

    for ex in examples:
        case = json.loads(ex.read_text(encoding="utf-8"))
        actual = solve(case)
        exp_status = expected_statuses[ex.name]
        assert actual["status"] == exp_status, f"Status mismatch on {ex.name}"


def test_tier3_dual_checker_concordance_28_cases():
    """Tier 3: Asserts 100% agreement and pass rate on all 28 judge cases."""
    case_files = sorted(CASES_DIR.rglob("*.json"))
    assert len(case_files) == 28

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

    assert agreed == 28, f"Disagreements detected: {agreed}/28"
    assert passed == 28, f"Failures detected: {passed}/28"


def test_tier4_hostile_mutation_kill_rate_100_percent():
    """Tier 4: Asserts 100% kill rate across all 48 hostile mutations."""
    mut_files = sorted(MUT_DIR.glob("*.json"))
    assert len(mut_files) == 48

    killed_c1 = 0
    killed_c2 = 0
    for mf in mut_files:
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted = data.get("result")

        ok1, _ = verify_hypergeometric_mirror_certificate(case, corrupted)
        ok2, _ = verify_picard_fuchs_recurrence_certificate(case, corrupted)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == 48, f"Checker 1 missed mutations: killed {killed_c1}/48"
    assert killed_c2 == 48, f"Checker 2 missed mutations: killed {killed_c2}/48"
