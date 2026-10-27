"""End-to-End Multi-Tier Integration Test for Challenge C037.

AuthorityEffect: None.

Verifies:
  Tier 1: Participant packet integrity and schema conformity.
  Tier 2: Reference solver accuracy across all 8 canonical examples.
  Tier 3: 100% dual checker concordance across all 34 judge cases.
  Tier 4: 100% hostile mutation detection across all 48 corrupted certificates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c037_virasoro_minimal_model_fusion.judge_packet.checkers.combinatorial_fusion_checker import (
    verify_combinatorial_fusion_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c037_virasoro_minimal_model_fusion.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c037_virasoro_minimal_model_fusion.judge_packet.checkers.verlinde_cyclotomic_checker import (
    verify_verlinde_cyclotomic_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c037_virasoro_minimal_model_fusion.reference_solver.solver import (
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
    assert acc_data["tier"] in ("T2", "T3")
    assert acc_data["cost_ceiling_usd"] == 0.50

    out_file = tmp_path / "runner_out.json"
    cmd = [
        sys.executable,
        str(PARTICIPANT_DIR / "runner.py"),
        "--cases",
        str(PARTICIPANT_DIR / "examples" / "ex01_ising_m43.json"),
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

    expected_statuses = {
        "ex01_ising_m43.json": "SOLVED",
        "ex02_lee_yang_m52.json": "SOLVED",
        "ex03_tricritical_ising_m54.json": "SOLVED",
        "ex04_su2_k1.json": "SOLVED",
        "ex05_su2_k2.json": "SOLVED",
        "ex06_su2_k3.json": "SOLVED",
        "ex07_non_coprime_m64_out_of_scope.json": "OUT_OF_SCOPE",
        "ex08_oversized_level_su2_k25_unknown.json": "UNKNOWN",
    }

    for ex in examples:
        case = json.loads(ex.read_text(encoding="utf-8"))
        actual = solve(case)
        exp_status = expected_statuses[ex.name]
        assert actual["status"] == exp_status, f"Status mismatch on {ex.name}"


def test_tier3_dual_checker_concordance_34_cases():
    """Tier 3: Asserts 100% agreement and pass rate on all 34 judge cases."""
    case_files = sorted(CASES_DIR.rglob("*.json"))
    assert len(case_files) == 34

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

    assert agreed == 34, f"Disagreements detected: {agreed}/34"
    assert passed == 34, f"Failures detected: {passed}/34"


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

        ok1, _ = verify_verlinde_cyclotomic_certificate(case, corrupted)
        ok2, _ = verify_combinatorial_fusion_certificate(case, corrupted)

        if not ok1:
            killed_c1 += 1
        if not ok2:
            killed_c2 += 1

    assert killed_c1 == 48, f"Checker 1 missed mutations: killed {killed_c1}/48"
    assert killed_c2 == 48, f"Checker 2 missed mutations: killed {killed_c2}/48"
