"""Tests for C033 Governance, Budget Gate, Reference Self-Consistency Gate, and Commit-Reveal.

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
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.governance import (
    adversary_gate as adversary_gate_module,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.governance.budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    BudgetGateUnavailable,
    FallbackNotAllowedError,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.governance.commit_reveal_runner import (
    ManifestCustodyError,
    lf_normalized_bytes,
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    verify_manifest_entries,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.governance.adversary_gate import (
    RunFolderExistsError,
    AdversaryGate,
)

from adversary.domain.providers.types import Provider

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


def test_budget_gate_enforces_tier_t2():
    """BudgetGate must enforce Tier T2 limit ($0.50 ceiling, $0.05 target, max 70B params)."""
    gate = BudgetGate(ceiling_usd=0.50, target_usd=0.05, allow_fallbacks=False)
    assert gate.ceiling_usd == 0.50
    assert gate.target_usd == 0.05
    assert gate.ceiling_microusd == 500_000

    # Exceeding hard ceiling must fail
    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_usd=0.51)

    # Allowing fallbacks must fail
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


def test_adversary_gate_novella_and_quad_persistence(tmp_path: Path):
    """AdversaryGate must render the measured-values report and persist the 4-file bundle.

    Counterexample: the report used to be a fixed seven-act narrative that did not depend on
    the counts; it must now show the counts it was given and 'not reported' for the rest."""
    gate = AdversaryGate(base_dir=tmp_path)
    novella = gate.generate_novella(
        CONSISTENT, {"total_cases": 1, "concordance": "100%"}, case_id="test_case_01"
    )

    assert "| Judge cases scored | 1 |" in novella
    assert "| Cases with checker agreement | not reported |" in novella
    assert "**Case**: `test_case_01`" in novella
    assert "Act " not in novella

    receipt = {"challenge_id": "c033_lie_algebra_weight_multiplicities", "status": "TEST_PASS"}
    summary = {
        "challenge_id": "c033_lie_algebra_weight_multiplicities",
        "metrics": {"total_cases": 1},
    }
    actions = [{"action": "intake", "step": 0}]

    sink1, sink2 = gate.persist_quad_bundle(
        "test_run_c033", "test_case_01", CONSISTENT, receipt, summary, actions
    )
    assert sink1.is_dir()
    assert sink2.is_dir()
    assert tmp_path in sink1.parents and tmp_path in sink2.parents

    # Verify the four bundle files exist
    assert (sink1 / "novella.md").is_file()
    assert (sink1 / "dda_actions.jsonl").is_file()
    assert (sink1 / "summary.json").is_file()
    assert (sink1 / "receipt.json").is_file()
    assert "| Judge cases scored | 1 |" in (sink1 / "novella.md").read_text(encoding="utf-8")


def test_adversary_gate_labels_come_from_exact_counts():
    """Counterexamples: an empty suite, one checker disagreement and a float Phi_1 must not be consistent,
    and a PASS_TO_MASTER label must be refused."""
    gate = AdversaryGate(base_dir=Path("unused"))
    assert gate.determine_terminal_verdict(0, 0, 0) == INCONSISTENT
    assert gate.determine_terminal_verdict(46, 46, 45) == INCONSISTENT
    assert gate.determine_terminal_verdict(46, 46, 46) == CONSISTENT
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(46, 46, 46, phi1=0.0)
    with pytest.raises(ValueError):
        gate.generate_novella("PASS_TO_MASTER", {})


def test_adversary_gate_never_replaces_a_run_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Counterexample: a second run in the same second rmtree'd the first run folder and copied over it."""

    class _Frozen(adversary_gate_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 29, 12, 0, 0, tzinfo=adversary_gate_module.timezone.utc)

    monkeypatch.setattr(adversary_gate_module, "datetime", _Frozen)
    gate = AdversaryGate(task_key="c033_collision", base_dir=tmp_path)
    first = gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="first")
    with pytest.raises(RunFolderExistsError):
        gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="second")
    assert (first["adversary_run_dir"] / "novella.md").read_text(encoding="utf-8") == "first"


def test_commit_reveal_three_phases(tmp_path: Path):
    """Asserts that all three phases of the commit-reveal protocol run on a temporary copy of the package."""
    root = _temp_package(tmp_path)
    commitments = root / "commitments"

    c1 = phase1_commit_judge(challenge_dir=root)
    assert c1["phase"] == "PHASE_1_JUDGE_COMMITMENT"
    assert c1["digest_normalization"] == "CRLF_TO_LF"
    assert (commitments / "c033_judge_commitment.json").is_file()

    c2 = phase2_freeze_solver(challenge_dir=root)
    assert c2["phase"] == "PHASE_2_SOLVER_FREEZE"
    assert c2["phase1_binding_sha256"] == c1["manifest_sha256"]
    assert (commitments / "c033_freeze_record.json").is_file()

    c3 = phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
    assert c3["phase"] == "PHASE_3_SCORING_RECEIPT"
    assert c3["final_verdict"] == CONSISTENT
    assert c3["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
    assert c3["dual_agreements"] == c3["total_cases"]
    assert (commitments / "c033_scoring_receipt.json").is_file()


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
    assert not (tmp_path / "_intelligence").exists()
