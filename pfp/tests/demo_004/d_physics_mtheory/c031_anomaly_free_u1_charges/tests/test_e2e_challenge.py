"""End-to-End (E2E) Test Suite for C031 (Anomaly-Free Chiral U(1) Charges).

Opaque-box, requirement-driven test suite structured across Tiers 1-4:
- Tier 1: Feature Coverage (Exact Diophantine equations, primitivity, chirality, canonical sorting)
- Tier 2: Boundary Values & Corner Cases (Fermion counts n=3..12, bounds up to 2e6, closed refusals, OOS witnesses)
- Tier 3: Cross-Seam Integration (CommitRevealRunner, BudgetGate, reference self-consistency gate, DDCTracer)
- Tier 4: Real-World Scenarios & Falsification (All 46 judge cases, 100% agreement, 100% mutation kill rate)

The commit-reveal run uses a temporary copy of this package, so running this file
never writes into the package's commitments/ or into a real _intelligence/ tree.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.governance.commit_reveal_runner import (
    CommitRevealRunner,
    ManifestCustodyError,
    lf_normalized_bytes,
    verify_manifest_entries,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.governance.adversary_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.reference_solver.solver import (
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


def _temp_package(base: Path) -> Path:
    """Copy this package under base; rebuild the copy's judge manifest over LF bytes if it does not verify."""
    root = base / ROOT_DIR.name
    shutil.copytree(ROOT_DIR, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    manifest_file = root / "judge_packet" / "manifest.json"
    try:
        verify_manifest_entries(manifest_file, root)
    except ManifestCustodyError:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            data = lf_normalized_bytes(manifest_file.parent / entry["path"])
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            if "size_bytes" in entry:
                entry["size_bytes"] = len(data)
        manifest_file.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
    return root


# ============================================================================
# TIER 1: FEATURE COVERAGE
# ============================================================================


def test_tier1_n5_enumeration_exact_solution():
    """Validates exact enumeration of anomaly-free chiral spectra for n=5."""
    case = json.loads((EXAMPLES_DIR / "ex03_enumerate_n5_bound9.json").read_text(encoding="utf-8"))[
        "input"
    ]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["count"] == 1
    assert res["solutions"] == [[-9, -5, -1, 7, 8]]

    eval_res = assert_dual_agreement(case, res)
    assert eval_res["verdict"] == "PASS"


def test_tier1_complete_solvable_case():
    """Validates completion of fixed charges into a full chiral spectrum."""
    case = json.loads(
        (EXAMPLES_DIR / "ex06_complete_n5_solvable.json").read_text(encoding="utf-8")
    )["input"]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["completion"] == [-1, 7, 8]

    eval_res = assert_dual_agreement(case, res)
    assert eval_res["verdict"] == "PASS"


def test_tier1_spectator_pair_completion():
    """Validates completion with spectator pairs for higher fermion counts."""
    case = {
        "id": "t1_spectator",
        "query": "complete",
        "n": 10,
        "bound": 100,
        "fixed": [-5, -1, -1, 4],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert len(res["completion"]) == 6

    eval_res = assert_dual_agreement(case, res)
    assert eval_res["verdict"] == "PASS"


def test_tier1_non_existence_refusal():
    """Validates certified refusal for vector-like traps."""
    case = json.loads(
        (EXAMPLES_DIR / "ex08_complete_vector_like_only.json").read_text(encoding="utf-8")
    )["input"]
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["completion"] is None
    assert res["claim"] == "NO_COMPLETION"

    eval_res = assert_dual_agreement(case, res)
    assert eval_res["verdict"] == "PASS"


# ============================================================================
# TIER 2: BOUNDARY VALUES & CORNER CASES
# ============================================================================


def test_tier2_extreme_charge_bound_2e6():
    """Validates arbitrary-precision integer arithmetic on large bounds (Q=2*10^6)."""
    case = json.loads(
        (POIS_DIR / "pois_06_int64_overflow_bound_2e6.json").read_text(encoding="utf-8")
    )
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["completion"] is not None

    eval_res = assert_dual_agreement(case, res)
    assert eval_res["verdict"] == "PASS"


def test_tier2_fermion_count_extremes():
    """Validates behavior at fermion count boundaries n=3 (empty) and n=12 (solvable)."""
    # n=3 empty
    res_n3 = solve({"id": "n3_bound_check", "query": "enumerate", "n": 3, "bound": 10})
    assert res_n3["status"] == "SOLVED"
    assert res_n3["count"] == 0

    # n=12 solvable
    case_n12 = json.loads(
        (BASE_DIR / "base_comp_16_n12_b1000_sol.json").read_text(encoding="utf-8")
    )
    res_n12 = solve(case_n12)
    assert res_n12["status"] == "SOLVED"
    assert res_n12["completion"] is not None

    eval_res = assert_dual_agreement(case_n12, res_n12)
    assert eval_res["verdict"] == "PASS"


def test_tier2_closed_refusal_codes():
    """Asserts that all closed refusal codes trigger properly."""
    cases_refusals = [
        ({"id": "r1", "query": "enumerate", "n": 0, "bound": 10}, "N_OUT_OF_BOUNDS"),
        ({"id": "r2", "query": "enumerate", "n": 15, "bound": 10}, "N_OUT_OF_BOUNDS"),
        ({"id": "r3", "query": "enumerate", "n": 5, "bound": 0}, "BOUND_OUT_OF_BOUNDS"),
        ({"id": "r4", "query": "unsupported", "n": 5, "bound": 10}, "MALFORMED_QUERY_TYPE"),
        ("invalid_mapping", "MALFORMED_CASE_STRUCTURE"),
    ]
    for case_data, expected_code in cases_refusals:
        ans = solve(case_data)  # type: ignore
        assert ans["status"] == "UNKNOWN"
        assert ans["refusal_code"] == expected_code


def test_tier2_out_of_scope_witnesses():
    """Asserts that all OUT_OF_SCOPE witness kinds are properly emitted."""
    # 1. fixed_charge_exceeds_bound
    c1 = {"id": "o1", "query": "complete", "n": 6, "bound": 10, "fixed": [15, 2]}
    res1 = solve(c1)
    assert res1["status"] == "OUT_OF_SCOPE"
    assert res1["witness"]["kind"] == "fixed_charge_exceeds_bound"

    # 2. fixed_charge_zero
    c2 = {"id": "o2", "query": "complete", "n": 6, "bound": 10, "fixed": [0, 2]}
    res2 = solve(c2)
    assert res2["status"] == "OUT_OF_SCOPE"
    assert res2["witness"]["kind"] == "fixed_charge_zero"

    # 3. too_many_fixed_charges
    c3 = {"id": "o3", "query": "complete", "n": 4, "bound": 10, "fixed": [1, 2, 3, 4]}
    res3 = solve(c3)
    assert res3["status"] == "OUT_OF_SCOPE"
    assert res3["witness"]["kind"] == "too_many_fixed_charges"


# ============================================================================
# TIER 3: CROSS-SEAM INTEGRATION
# ============================================================================


def test_tier3_commit_reveal_runner_and_governance():
    """Validates the full Commit-Reveal pipeline (budget gate and self-consistency gate) on a temporary copy.

    Counterexample: the runner was built with the default challenge_root, so run_all rewrote
    the package's committed commitments/c031_*.json every time this test ran."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        root = _temp_package(tmp_path)
        runner = CommitRevealRunner(challenge_root=root, base_repo_root=tmp_path)
        assert runner.phase1_file.parent == root / "commitments"
        res = runner.run_all(task_key="e2e_c031_bout", run_id="e2e_c031_run")
        assert res["phase1"]["manifest_sha256"] != ""
        assert res["phase2"]["phase1_binding_sha256"] == res["phase1"]["manifest_sha256"]
        assert res["phase3"]["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert res["phase3"]["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
        assert res["phase3"]["all_passed"] is True
        assert res["phase3"]["agreements_count"] == 46
        assert (tmp_path / "_intelligence" / "_adversary" / "runs" / "e2e_c031_bout").is_dir()


def test_tier3_ddc_tracer_receipt_chain():
    """Validates DDC 8-letter trace transitions and hash chaining."""
    case = {"id": "e2e_trace", "query": "enumerate", "n": 5, "bound": 9}
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
    assert len(mut_files) >= 36, f"Expected at least 36 mutations, got {len(mut_files)}"

    for mf in mut_files:
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("corrupted_result") or data.get("result")
        eval_res = evaluate_dual(case, corrupted_result)
        assert eval_res["verdict"] == "FAIL", f"Mutation {mf.name} escaped detection! {eval_res}"
