"""Tests for C032 Governance, Budget Controller, and Commit-Reveal State Machine.

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
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.governance import (
    woland_gate as woland_gate_module,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.governance.budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    BudgetGateUnavailable,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.governance.commit_reveal_runner import (
    ManifestCustodyError,
    lf_normalized_bytes,
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    verify_manifest_entries,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.governance.woland_gate import (
    RunFolderExistsError,
    WolandGate,
)

from omega_engine_woland.domain.providers.types import Provider

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
CONSISTENT = "REFERENCE_SELF_CONSISTENT"
INCONSISTENT = "REFERENCE_SELF_INCONSISTENT"


def _temp_package(base: Path) -> Path:
    """Copy this package under base; rebuild the copy's judge manifest over LF bytes if it does not verify."""
    root = base / CHALLENGE_DIR.name
    shutil.copytree(CHALLENGE_DIR, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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


def test_budget_gate_enforces_tier_t3():
    """BudgetGate must enforce Tier T3 limit ($1.00 ceiling, $0.05 target, max 70B params)."""
    gate = BudgetGate(ceiling_usd=1.00, target_usd=0.05, allow_fallbacks=False)
    assert gate.ceiling_usd == 1.00
    assert gate.target_usd == 0.05
    assert gate.ceiling_microusd == 1_000_000
    assert gate.target_microusd == 50_000

    # Reject ceiling above Tier T3
    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_usd=1.50)

    # Reject allow_fallbacks: True
    with pytest.raises(FallbackNotAllowedError):
        BudgetGate(allow_fallbacks=True)


def test_budget_gate_missing_provider_api_fails_closed():
    """Counterexample: check_pre_call called ModelRegistry.get and record_usage called
    BudgetController.record_spend, neither of which exists, so both crashed with AttributeError.
    Both must refuse with the typed BUDGET_API_UNAVAILABLE error and record no spend."""
    gate = BudgetGate()
    with pytest.raises(BudgetGateUnavailable) as info:
        gate.check_pre_call("meta-llama/llama-3.3-70b-instruct", 100)
    assert info.value.code == "BUDGET_API_UNAVAILABLE"
    with pytest.raises(BudgetGateUnavailable):
        gate.record_usage(Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", 100, 100)
    assert gate.budget_controller.spent_microusd == 0


def test_budget_gate_declared_ceiling_is_exact():
    """Counterexample: int(0.29 * 1_000_000) truncated a $0.29 ceiling to 289,999 micro-USD, and a bool was accepted as $1."""
    assert BudgetGate(ceiling_usd=0.29).ceiling_microusd == 290_000
    with pytest.raises(TypeError):
        BudgetGate(ceiling_usd=True)


def test_woland_gate_quad_persistence(tmp_path: Path):
    """WolandGate must persist the 4-file bundle, stamped with the self-check scope, under the given base_dir."""
    gate = WolandGate(task_key="c032_test_run", base_dir=tmp_path)
    novella = gate.generate_novella(
        CONSISTENT, {"total_cases": 42, "passed_count": 42, "agreements_count": 42}
    )
    res = gate.persist_run_bundle(
        receipt={"verdict": CONSISTENT},
        summary={"status": "OK"},
        dda_actions=[{"step": 1, "action": "test"}],
        novella=novella,
    )

    woland_dir = res["woland_run_dir"]
    symgam_dir = res["symgam_run_dir"]

    for d in (woland_dir, symgam_dir):
        assert tmp_path in d.parents
        assert (d / "novella.md").is_file()
        assert (d / "dda_actions.jsonl").is_file()
        assert (d / "summary.json").is_file()
        assert (d / "receipt.json").is_file()
        receipt = json.loads((d / "receipt.json").read_text(encoding="utf-8"))
        assert receipt["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
        assert "| Judge cases scored | 42 |" in (d / "novella.md").read_text(encoding="utf-8")


def test_woland_gate_labels_come_from_exact_counts():
    """Counterexamples: an empty suite, one checker disagreement and a float Phi_1 must not be consistent,
    and a PASS_TO_MASTER label must be refused."""
    gate = WolandGate(base_dir=Path("unused"))
    assert gate.determine_terminal_verdict(0, 0, 0) == INCONSISTENT
    assert gate.determine_terminal_verdict(42, 42, 41) == INCONSISTENT
    assert gate.determine_terminal_verdict(42, 42, 42) == CONSISTENT
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(42, 42, 42, phi1=0.0)
    with pytest.raises(ValueError):
        gate.generate_novella("PASS_TO_MASTER", {})


def test_woland_gate_never_replaces_a_run_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Counterexample: a second run in the same second rmtree'd the first run folder and copied over it."""

    class _Frozen(woland_gate_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 29, 12, 0, 0, tzinfo=woland_gate_module.timezone.utc)

    monkeypatch.setattr(woland_gate_module, "datetime", _Frozen)
    gate = WolandGate(task_key="c032_collision", base_dir=tmp_path)
    first = gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="first")
    with pytest.raises(RunFolderExistsError):
        gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="second")
    assert (first["woland_run_dir"] / "novella.md").read_text(encoding="utf-8") == "first"


def test_commit_reveal_workflow(tmp_path: Path):
    """Validates the 3-phase Commit-Reveal state machine for C032 on a temporary copy of the package."""
    root = _temp_package(tmp_path)
    commitments = root / "commitments"

    p1 = phase1_commit_judge(challenge_dir=root)
    assert p1["phase"] == "PHASE_1_JUDGE_COMMITMENT"
    assert p1["digest_normalization"] == "CRLF_TO_LF"
    assert (commitments / "c032_judge_commitment.json").is_file()

    p2 = phase2_freeze_solver(challenge_dir=root)
    assert p2["phase"] == "PHASE_2_SOLVER_FREEZE"
    assert p2["phase1_binding_sha256"] == p1["manifest_sha256"]
    assert (commitments / "c032_freeze_record.json").is_file()

    p3 = phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
    assert p3["phase"] == "PHASE_3_SCORING_RECEIPT"
    assert p3["verdict"] == CONSISTENT
    assert p3["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
    assert p3["all_passed"] is True
    assert p3["all_agreed"] is True
    assert (commitments / "c032_scoring_receipt.json").is_file()
    assert (
        tmp_path / "_intelligence" / "_woland" / "runs" / "c032_six_d_sugra_anomaly_cancellation"
    ).is_dir()


def test_phase3_refuses_a_case_file_missing_from_the_manifest(tmp_path: Path):
    """Counterexample: Phase 3 scored every *.json under cases/, so a case file added after the
    judge commitment was scored and receipted. It must be refused with CASE_FILE_NOT_IN_MANIFEST."""
    root = _temp_package(tmp_path)
    phase1_commit_judge(challenge_dir=root)
    phase2_freeze_solver(challenge_dir=root)
    base_cases = root / "judge_packet" / "cases" / "base"
    shutil.copyfile(sorted(base_cases.glob("*.json"))[0], base_cases / "zz_unlisted.json")
    with pytest.raises(ManifestCustodyError) as info:
        phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
    assert info.value.code == "CASE_FILE_NOT_IN_MANIFEST"
    assert (root / "commitments" / "c032_scoring_failure_receipt.json").is_file()
    assert not (tmp_path / "_intelligence").exists()
