"""Tests validating C031 governance (BudgetGate, reference self-consistency gate, and Commit-Reveal protocol).

Every phase runs on a temporary copy of this package and every run folder goes
under the test's temporary directory, so running this file never writes into
the package's commitments/ or into a real _intelligence/ tree.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.governance.commit_reveal_runner import (
    CommitRevealRunner,
    ManifestCustodyError,
    lf_normalized_bytes,
    verify_manifest_entries,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c031_anomaly_free_u1_charges.governance.woland_gate import (
    FAILURE_RECEIPT_NAME,
    RUN_FOLDER_EXISTS,
    TERMINAL_OPEN_RESIDUAL,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    WolandGate,
    persist_single_bundle,
)

from omega_engine_woland.domain.providers.types import BudgetExceeded, Provider

ROOT_DIR = Path(__file__).resolve().parent.parent


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


def test_budget_gate_configuration_and_limits():
    """Validates Tier T3 budget limits, pre-call checks, and hard ceiling enforcement."""
    gate = BudgetGate()
    assert gate.limit_microusd == HARD_CEILING_MICROUSD  # 1,000,000 uUSD = $1.00
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD  # 50,000 uUSD = $0.05
    assert gate.spent_microusd == 0
    assert gate.is_within_hard_ceiling is True
    assert gate.is_within_target is True

    # Declared ceiling exceeding 1,000,000 uUSD must be rejected
    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_microusd=1_200_000)

    # Pre-call fail-closed check
    gate.pre_call_check(500_000)  # ok
    with pytest.raises(BudgetExceeded):
        gate.pre_call_check(1_000_001)  # exceeds ceiling


def test_budget_gate_fallback_and_model_admittance():
    """Validates that fallbacks are strictly prohibited and model parameter ceiling <= 70B is enforced."""
    gate = BudgetGate()

    # Fallback rejection
    with pytest.raises(FallbackNotAllowedError):
        gate.validate_model(
            Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=True
        )

    # Valid model admission (<= 70B open weights)
    spec = gate.validate_model(
        Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=False
    )
    assert spec is not None
    assert spec.total_parameters <= 70_000_000_000


def test_woland_gate_verdict_and_bundle_persistence(tmp_path: Path):
    """Validates the reference self-consistency label and the 4-file bundle persistence under tmp_path."""
    gate = WolandGate(base_repo_root=tmp_path)

    # 1. Label determination
    verdict_pass = gate.determine_terminal_verdict([{"verdict": "PASS", "agreement": True}])
    assert verdict_pass == TERMINAL_REFERENCE_SELF_CONSISTENT

    verdict_refuse = gate.determine_terminal_verdict(
        [{"verdict": "FAIL", "agreement": True}], defect_count=1
    )
    assert verdict_refuse == TERMINAL_REFUSE == "REFERENCE_SELF_INCONSISTENT"

    verdict_residual = gate.determine_terminal_verdict(
        [{"verdict": "PASS", "agreement": True}], has_closed_residual=True
    )
    assert verdict_residual == TERMINAL_OPEN_RESIDUAL

    # 2. Evaluate and persist 4-file bundle
    task_key = "test_run_c031_01"
    run_id = "sg_run_c031_01"
    claim_hygiene = {
        "supports": "Tested C031.",
        "does_not_support": "Higher degree or continuum string vacua.",
        "narrowest_defensible_claim": "Passed test run.",
        "next_test_needed": "C032.",
    }

    verdict, p_woland, p_sg, digests = gate.evaluate_and_persist(
        task_key=task_key,
        run_id=run_id,
        case_results=[{"verdict": "PASS", "agreement": True}],
        claim_hygiene=claim_hygiene,
    )

    assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert p_woland.is_dir()
    assert p_sg.is_dir()

    # Check 4-file bundle contents in both sinks
    for run_dir in (p_woland, p_sg):
        assert tmp_path in run_dir.parents
        assert (run_dir / "novella.md").is_file()
        assert (run_dir / "dda_actions.jsonl").is_file()
        assert (run_dir / "summary.json").is_file()
        assert (run_dir / "receipt.json").is_file()
        report = (run_dir / "novella.md").read_text(encoding="utf-8")
        assert "| Judge cases scored | 1 |" in report
        assert "| Phi_1 (exact) | not measured |" in report
        receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
        assert receipt["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
        assert "retinue_verdict" not in receipt

    # Check RUN_FOLDER_EXISTS collision protection
    with pytest.raises(RunFolderExistsError) as info:
        gate.evaluate_and_persist(
            task_key=task_key,
            run_id=run_id,
            case_results=[{"verdict": "PASS", "agreement": True}],
            claim_hygiene=claim_hygiene,
        )
    assert info.value.code == RUN_FOLDER_EXISTS


def test_woland_gate_counts_and_exact_defects():
    """Counterexamples: 1 of 2 cases passing with no defects was labelled OPEN_RESIDUAL by the
    count-based verdict, an empty suite must not be consistent, and a float Phi_1 of 0.0 was accepted."""
    gate = WolandGate(base_repo_root=Path("unused"))
    assert gate.decide_terminal_verdict(2, 1, 0) == TERMINAL_REFUSE
    assert gate.decide_terminal_verdict(0, 0, 0) == TERMINAL_REFUSE
    assert gate.decide_terminal_verdict(2, 2, 0) == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert gate.determine_terminal_verdict([]) == TERMINAL_REFUSE
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict([{"verdict": "PASS", "agreement": True}], phi1=0.0)


def test_failed_bundle_write_keeps_a_failure_receipt(tmp_path: Path):
    """Counterexample: a failed bundle write rmtree'd its staging directory inside _intelligence,
    leaving no trace. The staged files and a failure receipt must be kept in the run folder."""
    target = tmp_path / "_intelligence" / "_woland" / "runs" / "c031_failed"
    with pytest.raises(TypeError):
        persist_single_bundle(target, "report", [{"not_json": object()}], {}, {})
    assert (target / FAILURE_RECEIPT_NAME).is_file()
    assert (target / "novella.md").read_text(encoding="utf-8") == "report"


def test_commit_reveal_runner_three_phases_and_tamper(tmp_path: Path):
    """Validates the 3-phase Commit-Reveal protocol (SG-CP v1) and tamper detection on a temporary copy."""
    fake_challenge_root = _temp_package(tmp_path)

    runner = CommitRevealRunner(challenge_root=fake_challenge_root, base_repo_root=tmp_path)

    # Phase 1
    p1 = runner.run_phase1_commit_judge()
    assert runner.phase1_file.is_file()
    assert p1["manifest_sha256"] != ""
    assert p1["digest_normalization"] == "CRLF_TO_LF"

    # Phase 2
    p2 = runner.run_phase2_freeze_solver()
    assert runner.phase2_file.is_file()
    assert p2["phase1_binding_sha256"] == p1["manifest_sha256"]

    # Phase 3
    p3 = runner.run_phase3_reveal_and_score(task_key="tmp_test_task", run_id="tmp_test_run")
    assert runner.phase3_file.is_file()
    assert p3["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert p3["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
    assert p3["all_passed"] is True
    assert p3["agreements_count"] == 46

    # Tamper protection test: mutate manifest and verify Phase 3 fails
    manifest_path = fake_challenge_root / "judge_packet" / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["tampered"] = True
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(ValueError, match="Judge manifest tampered"):
        runner.run_phase3_reveal_and_score(task_key="tmp_tamper_task", run_id="tmp_tamper_run")
    assert runner.failure_file.is_file()


def test_phase3_refuses_a_case_file_missing_from_the_manifest(tmp_path: Path):
    """Counterexample: Phase 3 scored every *.json under cases/, so a case file added after the
    judge commitment was scored and receipted. It must be refused with CASE_FILE_NOT_IN_MANIFEST."""
    root = _temp_package(tmp_path)
    runner = CommitRevealRunner(challenge_root=root, base_repo_root=tmp_path)
    runner.run_phase1_commit_judge()
    runner.run_phase2_freeze_solver()
    base_cases = root / "judge_packet" / "cases" / "base"
    shutil.copyfile(sorted(base_cases.glob("*.json"))[0], base_cases / "zz_unlisted.json")
    with pytest.raises(ManifestCustodyError) as info:
        runner.run_phase3_reveal_and_score(task_key="tmp_unlisted", run_id="tmp_unlisted_run")
    assert info.value.code == "CASE_FILE_NOT_IN_MANIFEST"
    assert not (tmp_path / "_intelligence").exists()
