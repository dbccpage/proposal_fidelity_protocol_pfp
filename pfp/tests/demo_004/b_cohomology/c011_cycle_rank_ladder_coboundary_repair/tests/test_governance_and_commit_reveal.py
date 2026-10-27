"""Tests validating C011 governance (BudgetGate, AdversaryGate, and Commit-Reveal protocol).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance import (
    commit_reveal_runner as runner_mod,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance.adversary_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    AdversaryGate,
)

from adversary.domain.providers.types import BudgetExceeded, Provider

ROOT_DIR = Path(__file__).resolve().parent.parent


def _rebuild_manifest_if_stale(challenge_root: Path) -> None:
    """Rebuild a temporary copy's judge manifest over LF bytes when the committed one does not verify.

    The runner refuses a manifest whose entries do not match the files (counterexample: the
    CRLF-era manifests of C012-C014). Tests run on copies, so they must not depend on the
    committed manifest having been regenerated.
    """
    manifest_file = challenge_root / "judge_packet" / "manifest.json"
    try:
        runner_mod.verify_manifest_entries(manifest_file, challenge_root)
        return
    except runner_mod.ManifestCustodyError:
        pass
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    key = "files" if "files" in data else "manifest"
    rebuilt = []
    for entry in data[key]:
        candidate = manifest_file.parent / entry["path"]
        path = candidate if candidate.is_file() else challenge_root / entry["path"]
        if path.is_file():
            rebuilt.append({**entry, "sha256": runner_mod.sha256_of_file(path)})
    listed = {(manifest_file.parent / e["path"]).resolve() for e in rebuilt} | {
        (challenge_root / e["path"]).resolve() for e in rebuilt
    }
    prefix = (
        ""
        if data[key] and not data[key][0]["path"].startswith("judge_packet/")
        else "judge_packet/"
    )
    for case_file in sorted((challenge_root / "judge_packet" / "cases").rglob("*.json")):
        if case_file.resolve() not in listed:
            rel = case_file.relative_to(challenge_root / "judge_packet").as_posix()
            rebuilt.append({"path": prefix + rel, "sha256": runner_mod.sha256_of_file(case_file)})
    data[key] = rebuilt
    manifest_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def _count_case_files(challenge_root: Path) -> int:
    return sum(
        len(list((challenge_root / "judge_packet" / "cases" / sub).glob("*.json")))
        for sub in ("base", "controls", "poisoned")
    )


def test_budget_gate_configuration_and_limits():
    gate = BudgetGate()
    assert gate.limit_microusd == HARD_CEILING_MICROUSD  # 500,000 uUSD = $0.50
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD  # 50,000 uUSD = $0.05
    assert gate.spent_microusd == 0
    assert gate.is_within_hard_ceiling is True
    assert gate.is_within_target is True

    # Declared ceiling exceeding 500,000 uUSD must be rejected
    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_microusd=600_000)

    # Pre-call fail-closed check
    gate.pre_call_check(100_000)  # ok
    with pytest.raises(BudgetExceeded):
        gate.pre_call_check(500_001)  # exceeds ceiling


def test_budget_gate_fallback_and_model_admittance():
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


def test_adversary_gate_verdict_and_bundle_persistence():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        gate = AdversaryGate(base_repo_root=repo_root)

        # 1. Verdict determination
        verdict_pass = gate.determine_terminal_verdict([{"verdict": "PASS", "agreement": True}])
        assert verdict_pass == TERMINAL_REFERENCE_SELF_CONSISTENT

        verdict_refuse = gate.determine_terminal_verdict(
            [{"verdict": "FAIL", "agreement": True}], defect_count=1
        )
        assert verdict_refuse == TERMINAL_REFUSE

        # 2. Evaluate and persist 4-file bundle
        task_key = "test_run_c011_01"
        run_id = "sg_run_c011_01"
        claim_hygiene = {
            "supports": "Tested C011.",
            "does_not_support": "Higher degree.",
            "narrowest_defensible_claim": "Passed test run.",
            "next_test_needed": "C012.",
        }

        verdict, p_adversary, p_sg, digests = gate.evaluate_and_persist(
            task_key=task_key,
            run_id=run_id,
            case_results=[{"verdict": "PASS", "agreement": True}],
            claim_hygiene=claim_hygiene,
        )

        assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert p_adversary.is_dir()
        assert p_sg.is_dir()

        # Check 4-file bundle contents in both sinks
        for run_dir in (p_adversary, p_sg):
            assert (run_dir / "novella.md").is_file()
            assert (run_dir / "dda_actions.jsonl").is_file()
            assert (run_dir / "summary.json").is_file()
            assert (run_dir / "receipt.json").is_file()

        # Check RUN_FOLDER_EXISTS collision protection
        with pytest.raises(RunFolderExistsError):
            gate.evaluate_and_persist(
                task_key=task_key,
                run_id=run_id,
                case_results=[{"verdict": "PASS", "agreement": True}],
                claim_hygiene=claim_hygiene,
            )


def test_commit_reveal_runner_three_phases_and_tamper():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_challenge_root = Path(tmp_dir) / "challenge"
        # Copy challenge structure to isolated tempdir
        import shutil

        shutil.copytree(ROOT_DIR / "judge_packet", fake_challenge_root / "judge_packet")
        shutil.copytree(ROOT_DIR / "reference_solver", fake_challenge_root / "reference_solver")
        _rebuild_manifest_if_stale(fake_challenge_root)

        runner = CommitRevealRunner(
            challenge_root=fake_challenge_root, base_repo_root=Path(tmp_dir)
        )

        # Phase 1
        p1 = runner.run_phase1_commit_judge()
        assert runner.phase1_file.is_file()
        assert p1["manifest_sha256"] != ""

        # Phase 2
        p2 = runner.run_phase2_freeze_solver()
        assert runner.phase2_file.is_file()
        assert p2["phase1_binding_sha256"] == p1["manifest_sha256"]

        # Phase 3
        p3 = runner.run_phase3_reveal_and_score(task_key="tmp_test_task", run_id="tmp_test_run")
        assert runner.phase3_file.is_file()
        assert p3["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert p3["all_passed"] is True
        assert p3["agreements_count"] == p3["case_count"] == _count_case_files(fake_challenge_root)

        # Tamper protection test: mutate manifest and verify Phase 3 fails
        manifest_path = fake_challenge_root / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_data["tampered"] = True
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        with pytest.raises(ValueError, match="Judge manifest tampered"):
            runner.run_phase3_reveal_and_score(task_key="tmp_tamper_task", run_id="tmp_tamper_run")
