"""Tests for C036 Governance and Cryptographic Commit-Reveal State Machine.

Every phase runs on a temporary copy of this package and every run folder goes
under the test's temporary directory, so running this file never writes into
the package's commitments/ or into a real _intelligence/ tree.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from fractions import Fraction
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.governance import (
    adversary_gate as adversary_gate_module,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.governance.budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.governance.commit_reveal_runner import (
    ManifestCustodyError,
    lf_normalized_bytes,
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    verify_commitments,
    verify_manifest_entries,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.governance.adversary_gate import (
    CANONICAL_OUTPUT_FILES,
    RunFolderExistsError,
    AdversaryGate,
)

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
    """Asserts BudgetGate enforces $0.50 ceiling, $0.05 target, and disallows fallbacks."""
    gate = BudgetGate()
    assert gate.ceiling_usd == 0.50
    assert gate.target_usd == 0.05
    assert gate.ceiling_microusd == 500_000
    assert gate.allow_fallbacks is False

    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_usd=1.00)

    with pytest.raises(FallbackNotAllowedError):
        BudgetGate(allow_fallbacks=True)


def test_budget_gate_accumulates_exact_micro_usd():
    """Counterexample: spend was accumulated as float USD, so $0.10 + $0.20 became
    0.30000000000000004, and float or bool amounts were accepted. Spend is int micro-USD now."""
    gate = BudgetGate()
    for amount in (100_000, 200_000):
        gate.check_pre_call(amount)
        gate.record_call_cost(amount)
    assert gate.accumulated_cost_usd == Fraction(3, 10)
    gate.check_pre_call(200_000)  # exactly at the 500,000 micro-USD ceiling
    with pytest.raises(BudgetCeilingExceededError):
        gate.check_pre_call(200_001)
    for bad in (0.1, True):
        with pytest.raises(TypeError):
            gate.record_call_cost(bad)
        with pytest.raises(TypeError):
            gate.check_pre_call(bad)


def test_budget_gate_audit_accounting_config():
    """Audits participant accounting.json against Tier T2 requirements."""
    acc_file = CHALLENGE_DIR / "participant_packet" / "accounting.json"
    assert acc_file.is_file()

    gate = BudgetGate()
    data = json.loads(acc_file.read_text(encoding="utf-8"))
    audit = gate.audit_accounting_config(data)

    assert audit["valid"] is True, f"Accounting audit violations: {audit['violations']}"
    assert audit["tier"] == "T2"
    assert audit["ceiling_usd"] == 0.50
    assert audit["target_usd"] == 0.05


def test_adversary_gate_quad_persistence(tmp_path: Path):
    """Asserts AdversaryGate writes all 4 bundle files and a report of the measured values.

    Counterexample: the report used to be a fixed seven-act narrative ("Act I: Patriarch's
    Ponds" ... "Act VII") whatever the counts were; it must now show the counts it was given."""
    gate = AdversaryGate(task_key="c036_quintic_gromov_witten_mirror", base_dir=tmp_path)
    novella = gate.generate_novella(CONSISTENT, {"total_cases": 28, "agreements_count": 28})

    receipt = {"challenge_id": "c036_quintic_gromov_witten_mirror", "verdict": CONSISTENT}
    summary = {"challenge_id": "c036_quintic_gromov_witten_mirror", "cases": 28}
    dda_actions = [{"step": 1, "verdict": "PASS"}]

    targets = gate.persist_run_bundle(
        receipt=receipt,
        summary=summary,
        dda_actions=dda_actions,
        novella=novella,
    )

    for run_dir in (targets["adversary_run_dir"], targets["symgam_run_dir"]):
        assert run_dir.is_dir()
        assert tmp_path in run_dir.parents
        for fname in CANONICAL_OUTPUT_FILES:
            f = run_dir / fname
            assert f.is_file(), f"Missing quad file: {fname} in {run_dir}"

        novella_content = (run_dir / "novella.md").read_text(encoding="utf-8")
        assert "| Judge cases scored | 28 |" in novella_content
        assert "| Cases with checker agreement | 28 |" in novella_content
        assert "| Cases with verdict PASS | not reported |" in novella_content
        assert "Act " not in novella_content


def test_adversary_gate_labels_come_from_exact_counts():
    """Counterexamples: an empty suite, one checker disagreement and a float Phi_1 must not be consistent,
    and a PASS_TO_MASTER label must be refused."""
    gate = AdversaryGate(base_dir=Path("unused"))
    assert gate.determine_terminal_verdict(0, 0, 0) == INCONSISTENT
    assert gate.determine_terminal_verdict(28, 28, 27) == INCONSISTENT
    assert gate.determine_terminal_verdict(28, 28, 28) == CONSISTENT
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(28, 28, 28, phi1=0.0)
    with pytest.raises(ValueError):
        gate.generate_novella("PASS_TO_MASTER", {})


def test_adversary_gate_never_replaces_a_run_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Counterexample: every run wrote into the same runs/<task_key> folder and overwrote the previous bundle."""

    class _Frozen(adversary_gate_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 29, 12, 0, 0, tzinfo=adversary_gate_module.timezone.utc)

    monkeypatch.setattr(adversary_gate_module, "datetime", _Frozen)
    gate = AdversaryGate(task_key="c036_collision", base_dir=tmp_path)
    first = gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="first")
    with pytest.raises(RunFolderExistsError):
        gate.persist_run_bundle(receipt={}, summary={}, dda_actions=[], novella="second")
    assert (first["adversary_run_dir"] / "novella.md").read_text(encoding="utf-8") == "first"


def test_commit_reveal_workflow(tmp_path: Path):
    """Validates the Phase 1 -> Phase 2 -> Phase 3 pipeline on a temporary copy of the package."""
    root = _temp_package(tmp_path)
    commitments = root / "commitments"

    p1 = phase1_commit_judge(challenge_dir=root)
    assert p1["phase"] == "PHASE_1_JUDGE_COMMITMENT"
    assert p1["digest_normalization"] == "CRLF_TO_LF"
    assert (commitments / "c036_judge_commitment.json").is_file()

    p2 = phase2_freeze_solver(challenge_dir=root)
    assert p2["phase"] == "PHASE_2_SOLVER_FREEZE"
    assert p2["phase1_binding_sha256"] == p1["manifest_sha256"]
    assert (commitments / "c036_freeze_record.json").is_file()

    p3 = phase3_reveal_and_score(challenge_dir=root, base_dir=tmp_path)
    assert p3["phase"] == "PHASE_3_SCORING_RECEIPT"
    assert p3["verdict"] == CONSISTENT
    assert p3["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
    assert p3["all_agreed"] is True
    assert p3["all_passed"] is True
    assert p3["dual_agreements"] == 28
    assert (commitments / "c036_scoring_receipt.json").is_file()
    assert verify_commitments(challenge_dir=root) is True


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
