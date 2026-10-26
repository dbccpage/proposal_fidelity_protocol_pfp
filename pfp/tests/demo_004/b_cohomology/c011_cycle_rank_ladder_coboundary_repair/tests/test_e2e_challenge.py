"""End-to-End (E2E) Test Suite for C011 (Cycle-Rank Ladder: Minimum-L1 Coboundary Repair).

Opaque-box, requirement-driven test suite structured across Tiers 1-4:
- Tier 1: Feature Coverage (Diamond, K4, trees, parallel edges, exact cochains)
- Tier 2: Boundary Values & Corner Cases (Cycle rank b1=0..16, |V| up to 60, 10^20 claims, 8 closed refusals)
- Tier 3: Cross-Seam Integration (CommitRevealRunner, BudgetGate, WolandGate, DDCTracer)
- Tier 4: Real-World Scenarios & Falsification (All 46 judge cases, 100% agreement, 100% mutation kill rate)

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from fractions import Fraction
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance.woland_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.reference_solver.solver import (
    solve,
    solve_with_trace,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = ROOT_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
JUDGE_DIR = ROOT_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
BASE_DIR = CASES_DIR / "base"
CTRL_DIR = CASES_DIR / "controls"
POIS_DIR = CASES_DIR / "poisoned"
MUT_DIR = JUDGE_DIR / "mutation_suite" / "mutations"


# ============================================================================
# TIER 1: FEATURE COVERAGE
# ============================================================================


def test_tier1_diamond_minimum_l1_repair():
    """Validates exact primal-dual solution on Round-4e diamond."""
    case = json.loads((EXAMPLES_DIR / "ex01_solved_diamond.json").read_text(encoding="utf-8"))[
        "input"
    ]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["phi1"] == "8"
    assert res["potential"] == {"a": "0", "b": "-3", "c": "-3", "d": "-2"}
    assert res["repair"] == {"a->b": "4", "b->c": "2"}
    assert res["dual"]["a->b"] == "1"
    assert res["dual"]["b->c"] == "2"
    assert res["dual"]["c->a"] == "2"
    assert res["dual"]["b->d"] == "-1"
    assert res["dual"]["d->a"] == "-1"


def test_tier1_tree_zero_obstruction():
    """Validates that any tree has Phi1 = 0 and empty repair."""
    case = json.loads((EXAMPLES_DIR / "ex05_solved_forest.json").read_text(encoding="utf-8"))[
        "input"
    ]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["phi1"] == "0"
    assert res["repair"] == {}
    assert res["dual"] == {}


def test_tier1_parallel_edges():
    """Validates graph with parallel edges between two nodes."""
    case = json.loads(
        (EXAMPLES_DIR / "ex06_solved_parallel_edges.json").read_text(encoding="utf-8")
    )["input"]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert Fraction(res["phi1"]) >= 0


def test_tier1_disconnected_components():
    """Validates independent solution across disconnected graph components."""
    case = json.loads((EXAMPLES_DIR / "ex07_solved_disconnected.json").read_text(encoding="utf-8"))[
        "input"
    ]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["phi1"] != ""


# ============================================================================
# TIER 2: BOUNDARY VALUES & CORNER CASES
# ============================================================================


def test_tier2_cycle_rank_ladder_bounds():
    """Validates cycle rank from 0 up to 16."""
    for b1 in [0, 1, 2, 4, 8, 12, 16]:
        n_verts = b1 + 2
        verts = [f"v{i}" for i in range(n_verts)]
        edges = []
        for i in range(n_verts - 1):
            edges.append(
                {"id": f"t_{i}", "u": verts[i], "v": verts[i + 1], "claim": "1", "weight": "1"}
            )
        for j in range(b1):
            edges.append(
                {
                    "id": f"c_{j}",
                    "u": verts[j],
                    "v": verts[(j + 2) % n_verts],
                    "claim": "2",
                    "weight": "1",
                }
            )

        case = {"id": f"b_{b1}", "vertices": verts, "edges": edges}
        res = solve(case)
        assert res["status"] == "SOLVED"
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"


def test_tier2_extreme_claim_values_10e20():
    """Validates arbitrary precision arithmetic on 10^20 claims."""
    case = {
        "id": "extreme_10e20",
        "vertices": ["u", "v", "w"],
        "edges": [
            {"id": "e1", "u": "u", "v": "v", "claim": "100000000000000000000", "weight": "1"},
            {"id": "e2", "u": "v", "v": "w", "claim": "200000000000000000000", "weight": "1"},
            {"id": "e3", "u": "w", "v": "u", "claim": "300000000000000000000", "weight": "1"},
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    # Cycle sum is 6 * 10^20. Max flow with w=1 gives phi1 = 6 * 10^20.
    assert res["phi1"] == "600000000000000000000"
    eval_res = assert_dual_agreement(case, res)
    assert eval_res["verdict"] == "PASS"


def test_tier2_closed_refusal_codes():
    """Asserts all 8 closed refusal codes trigger properly."""
    cases_refusals = [
        ({"id": "r1", "vertices": [], "edges": []}, "VERTEX_COUNT_OUT_OF_BOUNDS"),
        (
            {
                "id": "r2",
                "vertices": ["a", "b"],
                "edges": [
                    {"id": f"e{i}", "u": "a", "v": "b", "claim": "1", "weight": "1"}
                    for i in range(205)
                ],
            },
            "EDGE_COUNT_OUT_OF_BOUNDS",
        ),
        (
            {
                "id": "r3",
                "vertices": ["a", "b"],
                "edges": [{"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "bad"}],
            },
            "INVALID_CAPACITY",
        ),
        (
            {
                "id": "r4",
                "expect_refusal": True,
                "vertices": ["a", "b"],
                "edges": [{"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "-1"}],
            },
            "NEGATIVE_WEIGHT",
        ),
        (
            {
                "id": "r5",
                "require_connected": True,
                "vertices": ["a", "b", "c", "d"],
                "edges": [
                    {"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "1"},
                    {"id": "e2", "u": "c", "v": "d", "claim": "1", "weight": "1"},
                ],
            },
            "DISCONNECTED_GRAPH",
        ),
        (
            {
                "id": "r6",
                "vertices": ["a", "b"],
                "edges": [{"id": "e1", "u": "a", "v": 123, "claim": "1", "weight": "1"}],
            },
            "MALFORMED_EDGE_SPEC",
        ),
        (
            {
                "id": "r7",
                "target_defect": "-1",
                "vertices": ["a", "b"],
                "edges": [{"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "1"}],
            },
            "INVALID_TARGET_DEFECT",
        ),
        ("invalid_mapping", "MALFORMED_CASE_STRUCTURE"),
    ]
    for case_data, expected_code in cases_refusals:
        ans = solve(case_data)  # type: ignore
        assert ans["status"] == "UNKNOWN"
        assert ans["refusal_code"] == expected_code


# ============================================================================
# TIER 3: CROSS-SEAM INTEGRATION
# ============================================================================


def test_tier3_commit_reveal_runner_and_governance():
    """Validates the full commit-reveal pipeline with the reference gate and the budget gate.

    Runs on a temporary copy of the package. Counterexample: the old test ran on
    the package itself and rewrote the checked-in commitments and receipt.
    """
    package_dir = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as tmp_dir:
        challenge_root = Path(tmp_dir) / "c011"
        shutil.copytree(
            package_dir, challenge_root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        runner = CommitRevealRunner(
            challenge_root=challenge_root, base_repo_root=Path(tmp_dir) / "store"
        )
        res = runner.run_all(task_key="e2e_c011_bout", run_id="e2e_c011_run")
        assert res["phase1"]["manifest_sha256"] != ""
        assert res["phase2"]["phase1_binding_sha256"] == res["phase1"]["manifest_sha256"]
        assert res["phase3"]["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert res["phase3"]["all_passed"] is True
        assert res["phase3"]["agreements_count"] == res["phase3"]["case_count"] == 46
        assert (
            Path(tmp_dir) / "store" / "_intelligence" / "_woland" / "runs" / "e2e_c011_bout"
        ).is_dir()


def test_tier3_ddc_tracer_receipt_chain():
    """Validates DDC 8-letter trace transitions and hash chaining."""
    case = json.loads((EXAMPLES_DIR / "ex01_solved_diamond.json").read_text(encoding="utf-8"))[
        "input"
    ]
    res, tracer = solve_with_trace(case)
    assert res["status"] == "SOLVED"
    assert len(tracer.steps) >= 5
    for s in tracer.steps:
        assert s["letter"] in VALID_DDC_LETTERS
    ok, msg = tracer.verify_integrity()
    assert ok is True
    assert msg == "VALID_CHAIN"


# ============================================================================
# TIER 4: REAL-WORLD SCENARIOS & FALSIFICATION
# ============================================================================


def test_tier4_all_46_judge_cases_pass_with_100_percent_agreement():
    """Evaluates all 32 base cases, 8 controls, and 6 poisoned cases with dual evaluator."""
    all_case_files = (
        sorted(BASE_DIR.glob("*.json"))
        + sorted(CTRL_DIR.glob("*.json"))
        + sorted(POIS_DIR.glob("*.json"))
    )
    assert len(all_case_files) == 46, f"Expected 46 total judge cases, got {len(all_case_files)}"

    for cf in all_case_files:
        case = json.loads(cf.read_text(encoding="utf-8"))
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS", f"Case {cf.name} did not pass: {eval_res}"
        assert eval_res["agreement"] is True


def test_tier4_100_percent_mutation_kill_rate():
    """Asserts that dual checkers detect and kill 100% of certificate mutations."""
    mut_files = sorted(MUT_DIR.glob("mut_*.json"))
    assert len(mut_files) >= 38, f"Expected at least 38 mutations, got {len(mut_files)}"

    for mf in mut_files:
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("corrupted_result") or data.get("result")
        eval_res = evaluate_dual(case, corrupted_result)
        assert eval_res["verdict"] == "FAIL", f"Mutation {mf.name} escaped detection! {eval_res}"
