"""Tests for C022 Governance, Budget Gate, Reference Self-Consistency Gate, and Commit-Reveal Protocol.

Every commit-reveal phase runs on a temporary copy of the package; no test
writes into the package's own commitments/ directory (an autouse fixture
checks this). If the package's judge manifest does not verify, the copy's
manifest is rebuilt over LF bytes before the run.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.governance.woland_gate import (
    GATE_SCOPE,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    WolandGate,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = PACKAGE_ROOT.name
MUTATION_GLOB = "judge_packet/mutation_suite/mutations/*.json"


# ---------------------------------------------------------------------------
# Isolation helpers: phases run on temporary package copies only
# ---------------------------------------------------------------------------


def _lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _commitments_snapshot() -> dict[str, str]:
    commitments = PACKAGE_ROOT / "commitments"
    if not commitments.is_dir():
        return {}
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(commitments.iterdir())
        if p.is_file()
    }


@pytest.fixture(autouse=True)
def _real_commitments_untouched() -> Iterator[None]:
    """Counterexample: tests ran the runner on the package itself and rewrote its commitments/*.json."""
    before = _commitments_snapshot()
    yield
    assert _commitments_snapshot() == before, (
        "a test wrote into the package's own commitments/ directory"
    )


def _case_files(root: Path) -> list[Path]:
    return sorted((root / "judge_packet" / "cases").glob("*.json"))


def _mutation_files(root: Path) -> list[Path]:
    return sorted(root.glob(MUTATION_GLOB))


def _manifest_verifies(root: Path) -> bool:
    data = json.loads((root / "judge_packet" / "manifest.json").read_text(encoding="utf-8"))
    listed: set[Path] = set()
    for rel, meta in data["files"].items():
        path = root / rel
        if not path.is_file() or hashlib.sha256(_lf_bytes(path)).hexdigest() != meta["sha256"]:
            return False
        listed.add(path.resolve())
    if any(p.resolve() not in listed for p in _case_files(root) + _mutation_files(root)):
        return False
    counts = data.get("counts", {})
    return counts.get("judge_cases") == len(_case_files(root)) and counts.get(
        "hostile_mutations"
    ) == len(_mutation_files(root))


def _rebuild_manifest(root: Path) -> None:
    """Rebuild the copy's manifest: drop missing entries, add unlisted judged files, rehash, recount."""
    manifest_file = root / "judge_packet" / "manifest.json"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = {rel: dict(meta) for rel, meta in data["files"].items() if (root / rel).is_file()}
    for path in _case_files(root) + _mutation_files(root):
        entries.setdefault(path.relative_to(root).as_posix(), {})
    for rel, meta in entries.items():
        content = _lf_bytes(root / rel)
        meta["sha256"] = hashlib.sha256(content).hexdigest()
        meta["size_bytes"] = len(content)
    data["files"] = {k: entries[k] for k in sorted(entries, key=lambda s: s.encode("utf-8"))}
    counts = dict(data.get("counts", {}))
    counts.update(
        custodied_files=len(entries),
        hostile_mutations=len(_mutation_files(root)),
        judge_cases=len(_case_files(root)),
    )
    data["counts"] = counts
    manifest_file.write_bytes((json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _isolated_copy(tmp_path: Path) -> Path:
    dest = tmp_path / PACKAGE_NAME
    shutil.copytree(
        PACKAGE_ROOT, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "commitments")
    )
    if not _manifest_verifies(dest):
        _rebuild_manifest(dest)
    return dest


def test_budget_gate_constants_and_defaults():
    gate = BudgetGate()
    assert gate.limit_microusd == HARD_CEILING_MICROUSD == 1_000_000
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD == 50_000
    assert gate.is_within_target
    assert gate.is_within_hard_ceiling


def test_budget_gate_rejects_fallback():
    gate = BudgetGate()
    with pytest.raises(FallbackNotAllowedError):
        gate.validate_model("openrouter", "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=True)


def test_budget_gate_accounting_dict():
    gate = BudgetGate()
    d = gate.to_accounting_dict()
    assert d["budget_ceiling_usd"] == 1.00
    assert d["budget_target_usd"] == 0.05
    assert d["allow_fallbacks"] is False
    assert d["model_parameter_ceiling"] == "70B"


def test_woland_gate_terminal_verdicts(tmp_path):
    gate = WolandGate(base_repo_root=tmp_path)
    # All pass, 0 defects, exact zero defect values
    verdict = gate.determine_terminal_verdict(
        [{"verdict": "PASS", "agreement": True}],
        defect_count=0,
        phi1=Fraction(0),
        gamma2=Fraction(0),
    )
    assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT

    # Defect present
    verdict_fail = gate.determine_terminal_verdict(
        [{"verdict": "PASS", "agreement": True}],
        defect_count=1,
    )
    assert verdict_fail == TERMINAL_REFUSE


def test_woland_gate_defect_values_are_exact_without_tolerance(tmp_path):
    """Counterexample: phi1=0.0 (float) was accepted and a Phi_1 below 1e-6 passed under a float tolerance."""
    gate = WolandGate(base_repo_root=tmp_path)
    passing = [{"verdict": "PASS", "agreement": True}]
    assert gate.determine_terminal_verdict(passing, phi1=Fraction(1, 10**7)) == TERMINAL_REFUSE
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(passing, phi1=0.0)
    assert gate.determine_terminal_verdict([]) == "REFERENCE_SELF_INCONSISTENT"


def test_woland_gate_persistence(tmp_path):
    gate = WolandGate(base_repo_root=tmp_path)
    claim_hygiene = {
        "supports": "Stabilizer code distance",
        "does_not_support": "Unbounded models",
        "narrowest_defensible_claim": "Reference solver passes 100% of cases",
        "next_test_needed": "Hostile fuzzing",
    }
    verdict, p_woland, p_sg, digests = gate.evaluate_and_persist(
        task_key="c022_unit_test",
        run_id="run_c022_unit_test",
        case_results=[{"verdict": "PASS", "agreement": True}],
        claim_hygiene=claim_hygiene,
    )
    assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert p_woland.exists()
    assert (p_woland / "receipt.json").exists()
    assert (p_woland / "novella.md").exists()
    assert (p_woland / "dda_actions.jsonl").exists()
    assert (p_woland / "summary.json").exists()
    receipt = json.loads((p_woland / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_scope"] == GATE_SCOPE
    assert "letter_tape" not in receipt

    # Re-running with same keys should raise RunFolderExistsError
    with pytest.raises(RunFolderExistsError):
        gate.evaluate_and_persist(
            task_key="c022_unit_test",
            run_id="run_c022_unit_test",
            case_results=[{"verdict": "PASS", "agreement": True}],
            claim_hygiene=claim_hygiene,
        )


def test_commit_reveal_pipeline(tmp_path):
    # Run the full commit-reveal pipeline on a temporary copy; run folders under tmp_path
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(
        challenge_root=challenge_root, intelligence_repo_root=tmp_path / "intelligence"
    )
    p1 = runner.run_phase1_judge_commitment()
    p2 = runner.run_phase2_freeze_record()
    p3 = runner.run_phase3_reveal_and_score(
        task_key="c022_cr_pipeline_test",
        run_id="run_c022_cr_pipeline_test",
    )
    total = len(_case_files(challenge_root))
    assert p1["phase"] == "PHASE_1_OPERATOR_JUDGE_COMMITMENT"
    assert p1["digest_normalization"] == "CRLF_TO_LF"
    assert p2["phase"] == "PHASE_2_SOLVER_FREEZE_RECORD"
    assert p3["phase"] == "PHASE_3_REVEAL_AND_SCORING_RECEIPT"
    assert p3["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert p3["gate_scope"] == GATE_SCOPE
    assert p3["evaluation_summary"]["total_cases_evaluated"] == total
    assert p3["evaluation_summary"]["passed_cases"] == total
    assert p3["evaluation_summary"]["agreement_count"] == total
    assert (
        tmp_path / "intelligence" / "_intelligence" / "_woland" / "runs" / "c022_cr_pipeline_test"
    ).is_dir()


def test_commit_reveal_refuses_case_file_not_in_manifest(tmp_path):
    """Counterexample: a judge case file added after the commitment was scored as if committed."""
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(
        challenge_root=challenge_root, intelligence_repo_root=tmp_path / "intelligence"
    )
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()
    cases_dir = challenge_root / "judge_packet" / "cases"
    shutil.copyfile(_case_files(challenge_root)[0], cases_dir / "zz_added_after_commitment.json")
    with pytest.raises(ValueError) as exc_info:
        runner.run_phase3_reveal_and_score(task_key="unlisted_case", run_id="run_unlisted_case")
    assert exc_info.value.code == "CASE_FILE_NOT_IN_MANIFEST"
    failure = json.loads(runner.failure_receipt_file.read_text(encoding="utf-8"))
    assert failure["error_code"] == "CASE_FILE_NOT_IN_MANIFEST"
