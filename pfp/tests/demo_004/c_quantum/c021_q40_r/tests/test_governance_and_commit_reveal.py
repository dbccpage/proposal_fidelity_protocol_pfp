"""Unit and Integration Tests for C021 Governance and Commit-Reveal.

AuthorityEffect: None.

Verifies:
1. BudgetGate pre-call fail-closed checks (< $0.05 target, <= $0.25 hard ceiling).
2. Model parameter ceiling <= 70B and allow_fallbacks: false mandate.
3. Reference self-consistency labels (REFERENCE_SELF_CONSISTENT, REFERENCE_SELF_INCONSISTENT,
   OPEN_RESIDUAL) decided on exact values.
4. Reverse write order, 4-file bundle of measured values, and dual-sink persistence.
5. RUN_FOLDER_EXISTS collision protection.
6. 3-Phase Commit-Reveal workflow (SG-CP v1), sequence enforcement, and tamper detection.

Every commit-reveal phase runs on a temporary copy of the package; no test
writes into the package's own commitments/ directory (an autouse fixture
checks this). If the package's judge manifest does not verify (for example
before a manifest regeneration), the copy's manifest is rebuilt over LF bytes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.budget_gate import (
    FALLBACK_NOT_ALLOWED,
    HARD_CEILING_MICROUSD,
    HARD_CEILING_USD,
    TARGET_BUDGET_MICROUSD,
    TARGET_BUDGET_USD,
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.woland_gate import (
    GATE_SCOPE,
    RUN_FOLDER_EXISTS,
    TERMINAL_OPEN_RESIDUAL,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    WolandGate,
)

from omega_engine_woland.domain.providers.model_registry import (
    ModelNotRegistered,
    ModelParameterCeilingRefused,
)
from omega_engine_woland.domain.providers.types import BudgetExceeded, Provider

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
CASE_SUBDIRS = ("base", "controls", "poisoned")


# ============================================================================
# 0. Isolation helpers
# ============================================================================


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
    """Counterexample: tests that called CommitRevealRunner() on the package overwrote its commitments/*.json."""
    before = _commitments_snapshot()
    yield
    assert _commitments_snapshot() == before, (
        "a test wrote into the package's own commitments/ directory"
    )


def _judged_files(judge_dir: Path) -> list[Path]:
    cases = [p for sub in CASE_SUBDIRS for p in sorted((judge_dir / "cases" / sub).glob("*.json"))]
    return cases + sorted((judge_dir / "mutation_suite" / "mutations").glob("*.json"))


def _disk_counts(judge_dir: Path) -> dict[str, Any]:
    per_dir = {sub: len(list((judge_dir / "cases" / sub).glob("*.json"))) for sub in CASE_SUBDIRS}
    return {
        "case_counts": {**per_dir, "total_cases": sum(per_dir.values())},
        "mutation_count": len(list((judge_dir / "mutation_suite" / "mutations").glob("*.json"))),
    }


def _manifest_verifies(root: Path) -> bool:
    judge_dir = root / "judge_packet"
    data = json.loads((judge_dir / "manifest.json").read_text(encoding="utf-8"))
    listed: set[Path] = set()
    for entry in data["files"]:
        path = judge_dir / entry["path"]
        if not path.is_file() or hashlib.sha256(_lf_bytes(path)).hexdigest() != entry["sha256"]:
            return False
        listed.add(path.resolve())
    if any(p.resolve() not in listed for p in _judged_files(judge_dir)):
        return False
    counts = _disk_counts(judge_dir)
    return (
        data.get("case_counts") == counts["case_counts"]
        and data.get("mutation_count") == counts["mutation_count"]
    )


def _rebuild_manifest(root: Path) -> None:
    """Rebuild the copy's manifest: drop missing entries, add unlisted judged files, rehash, recount."""
    judge_dir = root / "judge_packet"
    manifest_file = judge_dir / "manifest.json"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = {e["path"]: dict(e) for e in data["files"] if (judge_dir / e["path"]).is_file()}
    for path in _judged_files(judge_dir):
        rel = path.relative_to(judge_dir).as_posix()
        entries.setdefault(rel, {"path": rel})
    for rel, entry in entries.items():
        content = _lf_bytes(judge_dir / rel)
        entry["sha256"] = hashlib.sha256(content).hexdigest()
        entry["size_bytes"] = len(content)
    data["files"] = [entries[k] for k in sorted(entries, key=lambda s: s.encode("utf-8"))]
    data.update(_disk_counts(judge_dir))
    manifest_file.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))


def _isolated_copy(tmp_path: Path) -> Path:
    dest = tmp_path / "c021_q40_r"
    shutil.copytree(
        PACKAGE_ROOT, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "commitments")
    )
    if not _manifest_verifies(dest):
        _rebuild_manifest(dest)
    return dest


# ============================================================================
# 1. Budget Gate & Cost Governance Tests
# ============================================================================


def test_budget_gate_defaults_and_accounting_dict() -> None:
    gate = BudgetGate()
    assert gate.limit_microusd == HARD_CEILING_MICROUSD  # 250,000 uUSD = $0.25
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD  # 50,000 uUSD = $0.05
    assert gate.spent_microusd == 0
    assert gate.remaining_microusd == HARD_CEILING_MICROUSD
    assert gate.is_within_target is True
    assert gate.is_within_hard_ceiling is True

    acct = gate.to_accounting_dict()
    assert acct["budget_ceiling_usd"] == HARD_CEILING_USD
    assert acct["budget_target_usd"] == TARGET_BUDGET_USD
    assert acct["total_billed_cost_usd"] == 0.0
    assert acct["spent_microusd"] == 0
    assert acct["remaining_microusd"] == 250_000
    assert acct["within_budget"] is True
    assert acct["within_target"] is True
    assert acct["model_parameter_ceiling"] == "70B"
    assert acct["allow_fallbacks"] is False
    assert acct["authority_effect"] == "None"


def test_budget_gate_ceiling_limit_exceeded_raises() -> None:
    # Attempting to declare ceiling > $0.25 (250,000 uUSD) must fail immediately
    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_microusd=250_001)

    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_microusd=1_000_000)  # $1.00


def test_budget_gate_pre_call_fail_closed_check() -> None:
    gate = BudgetGate(ceiling_microusd=50_000)
    # Check within budget
    gate.pre_call_check(20_000)

    # Check exceeding ceiling fail-closed
    with pytest.raises(BudgetExceeded) as exc_info:
        gate.pre_call_check(50_001)
    assert exc_info.value.requested == 50_001
    assert exc_info.value.limit == 50_000


def test_budget_gate_quote_and_charge_pre_call_success() -> None:
    gate = BudgetGate()
    # Charge meta-llama/llama-3.3-70b-instruct for modest token count
    receipt = gate.quote_and_charge_pre_call(
        provider=Provider.OPENROUTER,
        model_id="meta-llama/llama-3.3-70b-instruct",
        input_tokens=1000,
        max_output_tokens=500,
        allow_fallbacks=False,
    )
    assert receipt.cost_microusd > 0
    assert gate.spent_microusd == receipt.cost_microusd
    assert gate.is_within_hard_ceiling is True


def test_budget_gate_quote_and_charge_pre_call_exceeded_halts_fail_closed() -> None:
    gate = BudgetGate(ceiling_microusd=100)  # very tiny budget
    with pytest.raises(BudgetExceeded):
        gate.quote_and_charge_pre_call(
            provider=Provider.OPENROUTER,
            model_id="meta-llama/llama-3.3-70b-instruct",
            input_tokens=10_000,
            max_output_tokens=10_000,
            allow_fallbacks=False,
        )
    # Verify spend remains 0 because call was blocked BEFORE execution
    assert gate.spent_microusd == 0


def test_budget_gate_model_parameter_ceiling_admissions() -> None:
    gate = BudgetGate()
    # 70B dense model is admitted
    spec1 = gate.validate_model(
        Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=False
    )
    assert spec1.total_parameters == 70_000_000_000
    assert spec1.open_weights is True

    # 32B dense model is admitted
    spec2 = gate.validate_model(
        Provider.OPENROUTER, "qwen/qwen-2.5-coder-32b-instruct", allow_fallbacks=False
    )
    assert spec2.total_parameters == 32_000_000_000


def test_budget_gate_model_parameter_ceiling_rejections() -> None:
    gate = BudgetGate()

    # 72B is over ceiling (> 70B)
    with pytest.raises(ModelParameterCeilingRefused) as exc1:
        gate.validate_model(
            Provider.OPENROUTER, "qwen/qwen-2.5-72b-instruct", allow_fallbacks=False
        )
    assert exc1.value.code == "MODEL_OVER_PARAMETER_CEILING"

    # 671B MoE is over ceiling
    with pytest.raises(ModelParameterCeilingRefused) as exc2:
        gate.validate_model(Provider.NVIDIA, "deepseek-ai/deepseek-r1", allow_fallbacks=False)
    assert exc2.value.code == "MODEL_OVER_PARAMETER_CEILING"

    # MoE counts total parameters (141B > 70B)
    with pytest.raises(ModelParameterCeilingRefused) as exc3:
        gate.validate_model(
            Provider.OPENROUTER, "mistralai/mixtral-8x22b-instruct", allow_fallbacks=False
        )
    assert exc3.value.code == "MODEL_OVER_PARAMETER_CEILING"

    # Undisclosed parameter model is refused
    with pytest.raises(ModelParameterCeilingRefused) as exc4:
        gate.validate_model(Provider.OPENROUTER, "google/gemini-2.5-flash", allow_fallbacks=False)
    assert exc4.value.code == "MODEL_SIZE_UNDISCLOSED"

    # Unknown model is refused
    with pytest.raises(ModelNotRegistered):
        gate.validate_model(
            Provider.OPENROUTER, "unknown-vendor/hypothetical-model", allow_fallbacks=False
        )


def test_budget_gate_allow_fallbacks_strict_refusal() -> None:
    gate = BudgetGate()
    with pytest.raises(FallbackNotAllowedError) as exc_info:
        gate.validate_model(
            Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=True
        )
    assert exc_info.value.code == FALLBACK_NOT_ALLOWED


# ============================================================================
# 2. Reference Self-Consistency Gate & Reverse Write Order Tests
# ============================================================================


def test_woland_gate_terminal_verdicts(tmp_path: Path) -> None:
    gate = WolandGate(base_repo_root=tmp_path)

    # Case A: All passed with agreement, 0 defects -> REFERENCE_SELF_CONSISTENT
    cases_all_pass = [
        {"case_id": "c1", "verdict": "PASS", "agreement": True},
        {"case_id": "c2", "verdict": "PASS", "agreement": True},
    ]
    assert (
        gate.determine_terminal_verdict(cases_all_pass, defect_count=0)
        == TERMINAL_REFERENCE_SELF_CONSISTENT
    )

    # Case B: Checker failure -> REFERENCE_SELF_INCONSISTENT
    cases_with_fail = [
        {"case_id": "c1", "verdict": "PASS", "agreement": True},
        {"case_id": "c2", "verdict": "FAIL", "agreement": True},
    ]
    assert gate.determine_terminal_verdict(cases_with_fail, defect_count=1) == TERMINAL_REFUSE

    # Case C: Disagreement -> REFERENCE_SELF_INCONSISTENT
    cases_with_disagreement = [
        {"case_id": "c1", "verdict": "PASS", "agreement": False},
    ]
    assert (
        gate.determine_terminal_verdict(cases_with_disagreement, defect_count=1) == TERMINAL_REFUSE
    )

    # Case D: Non-zero defects -> REFERENCE_SELF_INCONSISTENT
    assert gate.determine_terminal_verdict(cases_all_pass, defect_count=2) == TERMINAL_REFUSE

    # Case E: Non-vanishing exact Phi1 or Gamma2 -> REFERENCE_SELF_INCONSISTENT
    assert (
        gate.determine_terminal_verdict(cases_all_pass, defect_count=0, phi1=Fraction(1, 100))
        == TERMINAL_REFUSE
    )
    assert (
        gate.determine_terminal_verdict(cases_all_pass, defect_count=0, gamma2=Fraction(1, 100))
        == TERMINAL_REFUSE
    )

    # Case F: Declared closed residual -> OPEN_RESIDUAL
    assert (
        gate.determine_terminal_verdict(cases_all_pass, defect_count=0, has_closed_residual=True)
        == TERMINAL_OPEN_RESIDUAL
    )


def test_woland_gate_label_is_reference_self_check_not_pass_to_master(tmp_path: Path) -> None:
    """Counterexample: an all-pass self-score of the reference solver was labelled PASS_TO_MASTER."""
    gate = WolandGate(base_repo_root=tmp_path)
    assert (
        gate.determine_terminal_verdict([{"verdict": "PASS", "agreement": True}])
        == "REFERENCE_SELF_CONSISTENT"
    )
    assert gate.determine_terminal_verdict([]) == "REFERENCE_SELF_INCONSISTENT"


def test_woland_gate_defect_values_are_exact_without_tolerance(tmp_path: Path) -> None:
    """Counterexample: phi1=1e-6 passed under a 1e-6 float tolerance; a measured 1/10^7 must be inconsistent."""
    gate = WolandGate(base_repo_root=tmp_path)
    cases = [{"verdict": "PASS", "agreement": True}]
    assert gate.determine_terminal_verdict(cases, phi1=Fraction(1, 10**7)) == TERMINAL_REFUSE
    assert (
        gate.determine_terminal_verdict(cases, phi1=0, gamma2=Fraction(0))
        == TERMINAL_REFERENCE_SELF_CONSISTENT
    )
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(cases, phi1=1e-6)
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(cases, gamma2=False)


def test_woland_gate_reverse_write_order_and_sha256_bindings(tmp_path: Path) -> None:
    """Counterexample: the report was a templated 7-act novella and the DDA tape 8 constant rows."""
    gate = WolandGate(base_repo_root=tmp_path)

    cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
    claim_hygiene = {
        "supports": "Supports test case c1",
        "does_not_support": "Does not support heuristic solvers",
        "narrowest_defensible_claim": "Case c1 passed exact verification",
        "next_test_needed": "Case c2",
    }

    verdict, path_woland, path_sg, digests = gate.evaluate_and_persist(
        task_key="test_run_reverse_order",
        run_id="test_run_id_001",
        case_results=cases,
        claim_hygiene=claim_hygiene,
    )

    assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert path_woland.exists()
    assert path_sg.exists()

    # Verify all 4 files exist in both locations
    for run_dir in (path_woland, path_sg):
        novella_file = run_dir / "novella.md"
        dda_file = run_dir / "dda_actions.jsonl"
        summary_file = run_dir / "summary.json"
        receipt_file = run_dir / "receipt.json"

        assert novella_file.exists()
        assert dda_file.exists()
        assert summary_file.exists()
        assert receipt_file.exists()

        # Compute actual digests from disk
        novella_sha = hashlib.sha256(novella_file.read_bytes()).hexdigest()
        dda_sha = hashlib.sha256(dda_file.read_bytes()).hexdigest()
        summary_sha = hashlib.sha256(summary_file.read_bytes()).hexdigest()
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))

        # Verify receipt binds the exact digests of the other 3 files
        assert receipt_data["novella_sha256"] == novella_sha
        assert receipt_data["dda_actions_sha256"] == dda_sha
        assert receipt_data["summary_sha256"] == summary_sha
        assert receipt_data["authority_effect"] == "None"
        assert receipt_data["status"] == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert receipt_data["gate_scope"] == GATE_SCOPE
        assert "letter_tape" not in receipt_data

        # Verify summary content and claim hygiene
        summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
        assert summary_data["authority_effect"] == "None"
        assert summary_data["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert summary_data["claim_hygiene"]["supports"] == claim_hygiene["supports"]
        assert (
            summary_data["claim_hygiene"]["does_not_support"] == claim_hygiene["does_not_support"]
        )
        assert (
            summary_data["claim_hygiene"]["narrowest_defensible_claim"]
            == claim_hygiene["narrowest_defensible_claim"]
        )
        assert (
            summary_data["claim_hygiene"]["next_test_needed"] == claim_hygiene["next_test_needed"]
        )

        # Verify the report carries measured values only
        novella_text = novella_file.read_text(encoding="utf-8")
        assert "| Judge cases scored | 1 |" in novella_text
        assert "| Cases with checker agreement | 1 |" in novella_text
        assert "Four-Part Claim Hygiene Summary" in novella_text
        assert "**AuthorityEffect**: None" in novella_text
        assert "Act I" not in novella_text and "100%" not in novella_text

        # The DDA tape holds three rows whose metadata are the measured counts and the label
        rows = [json.loads(line) for line in dda_file.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 3
        assert rows[0]["payload"]["metadata"] == {"case_count": 1}
        assert rows[1]["payload"]["metadata"] == {
            "agreement_count": 1,
            "defect_count": 0,
            "passed_count": 1,
        }
        assert rows[2]["payload"]["metadata"] == {
            "label": TERMINAL_REFERENCE_SELF_CONSISTENT,
            "scope": GATE_SCOPE,
        }


def test_woland_gate_run_folder_exists_collision_protection(tmp_path: Path) -> None:
    gate = WolandGate(base_repo_root=tmp_path)
    cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
    claim_hygiene = {
        "supports": "A",
        "does_not_support": "B",
        "narrowest_defensible_claim": "C",
        "next_test_needed": "D",
    }

    # First persist succeeds
    gate.evaluate_and_persist(
        task_key="collision_key",
        run_id="collision_run_id",
        case_results=cases,
        claim_hygiene=claim_hygiene,
    )

    # Second persist to same task_key / run_id must raise RunFolderExistsError
    with pytest.raises(RunFolderExistsError) as exc_info:
        gate.evaluate_and_persist(
            task_key="collision_key",
            run_id="collision_run_id",
            case_results=cases,
            claim_hygiene=claim_hygiene,
        )
    assert exc_info.value.code == RUN_FOLDER_EXISTS


# ============================================================================
# 3. Commit-Reveal Protocol & Pipeline Tests (temporary package copies only)
# ============================================================================


def test_commit_reveal_phase1_judge_commitment_integrity(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(challenge_root=root, intelligence_repo_root=tmp_path / "intel")
    payload = runner.run_phase1_judge_commitment()

    manifest = json.loads((root / "judge_packet" / "manifest.json").read_text(encoding="utf-8"))
    counts = _disk_counts(root / "judge_packet")
    assert payload["schema"] == "omega.symbol-game.judge-commitment.v1"
    assert payload["challenge_id"] == "c021_q40_r"
    assert payload["protocol"] == "SG-CP-v1"
    assert payload["phase"] == "PHASE_1_OPERATOR_JUDGE_COMMITMENT"
    assert payload["total_judge_files"] == len(manifest["files"])
    assert payload["case_counts"] == counts["case_counts"]
    assert payload["mutation_count"] == counts["mutation_count"]
    assert payload["digest_normalization"] == "CRLF_TO_LF"
    assert payload["authority_effect"] == "None"

    # Verify file was written to disk in the copy
    commit_file = root / "commitments" / "c021_q40_r_judge_commitment.json"
    assert commit_file.exists()
    disk_data = json.loads(commit_file.read_text(encoding="utf-8"))
    assert disk_data["manifest_sha256"] == payload["manifest_sha256"]


def test_commit_reveal_phase2_freeze_record_integrity(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(challenge_root=root, intelligence_repo_root=tmp_path / "intel")
    runner.run_phase1_judge_commitment()
    payload = runner.run_phase2_freeze_record()

    assert payload["schema"] == "omega.symbol-game.freeze-record.v1"
    assert payload["challenge_id"] == "c021_q40_r"
    assert payload["phase"] == "PHASE_2_SOLVER_FREEZE_RECORD"
    assert payload["entrypoint"] == "reference_solver.solver:solve"
    assert payload["authority_effect"] == "None"
    assert len(payload["solver_files"]) == 3

    # Check solver files list is sorted ordinally
    paths = [f["path"] for f in payload["solver_files"]]
    assert paths == sorted(paths, key=lambda s: s.encode("utf-8"))

    # Verify file was written to disk in the copy
    freeze_file = root / "commitments" / "c021_q40_r_freeze_record.json"
    assert freeze_file.exists()
    disk_data = json.loads(freeze_file.read_text(encoding="utf-8"))
    assert disk_data["freeze_digest"] == payload["freeze_digest"]


def test_commit_reveal_sequence_enforcement(tmp_path: Path) -> None:
    # Create isolated challenge directory structure
    challenge_dir = tmp_path / "c021_q40_r"
    commitments_dir = challenge_dir / "commitments"
    commitments_dir.mkdir(parents=True)

    isolated_runner = CommitRevealRunner(
        challenge_root=challenge_dir, intelligence_repo_root=tmp_path / "intel"
    )

    # Calling Phase 2 without Phase 1 commitment must raise RuntimeError
    with pytest.raises(RuntimeError, match="Phase 1 judge commitment must precede Phase 2"):
        isolated_runner.run_phase2_freeze_record()

    # Calling Phase 3 without Phase 1 and 2 must raise RuntimeError
    with pytest.raises(
        RuntimeError, match="Both judge commitment and solver freeze record must exist"
    ):
        isolated_runner.run_phase3_reveal_and_score()


def test_commit_reveal_manifest_tamper_detection(tmp_path: Path) -> None:
    """Counterexample: a failed Phase 3 left no record (now a failure receipt is written)."""
    dest_challenge = _isolated_copy(tmp_path)

    runner = CommitRevealRunner(
        challenge_root=dest_challenge, intelligence_repo_root=tmp_path / "intel"
    )
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()

    # Tamper with judge manifest
    manifest_file = dest_challenge / "judge_packet" / "manifest.json"
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest_data["created_utc"] = "2099-01-01T00:00:00Z"  # tamper
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    # Phase 3 must detect manifest tamper and reject scoring
    with pytest.raises(ValueError, match="Judge manifest SHA-256 mismatch") as exc_info:
        runner.run_phase3_reveal_and_score()
    assert exc_info.value.code == "MANIFEST_DIGEST_MISMATCH"
    failure = json.loads(runner.failure_receipt_file.read_text(encoding="utf-8"))
    assert failure["error_code"] == "MANIFEST_DIGEST_MISMATCH"


def test_commit_reveal_solver_tamper_detection(tmp_path: Path) -> None:
    dest_challenge = _isolated_copy(tmp_path)

    runner = CommitRevealRunner(
        challenge_root=dest_challenge, intelligence_repo_root=tmp_path / "intel"
    )
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()

    # Tamper with solver file after freeze
    solver_file = dest_challenge / "reference_solver" / "solver.py"
    content = solver_file.read_text(encoding="utf-8")
    solver_file.write_text(content + "\n# malicious alteration\n", encoding="utf-8")

    # Phase 3 must detect solver tamper and reject scoring
    with pytest.raises(ValueError, match="was modified after freeze"):
        runner.run_phase3_reveal_and_score()


def test_commit_reveal_refuses_case_file_not_in_manifest(tmp_path: Path) -> None:
    """Counterexample: a judge case file added after the commitment was scored as if committed."""
    dest_challenge = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(
        challenge_root=dest_challenge, intelligence_repo_root=tmp_path / "intel"
    )
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()

    base_dir = dest_challenge / "judge_packet" / "cases" / "base"
    shutil.copyfile(sorted(base_dir.glob("*.json"))[0], base_dir / "zz_added_after_commitment.json")
    with pytest.raises(ValueError) as exc_info:
        runner.run_phase3_reveal_and_score(task_key="unlisted_case")
    assert exc_info.value.code == "CASE_FILE_NOT_IN_MANIFEST"


def test_commit_reveal_phase3_evaluates_all_manifest_cases_end_to_end(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(challenge_root=root, intelligence_repo_root=tmp_path / "intel")
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()
    receipt = runner.run_phase3_reveal_and_score(task_key="c021_q40_r_scoring_run_test")

    assert receipt["schema"] == "omega.symbol-game.scoring-receipt.v1"
    assert receipt["challenge_id"] == "c021_q40_r"
    assert receipt["protocol"] == "SG-CP-v1"
    assert receipt["authority_effect"] == "None"
    assert receipt["gate_scope"] == GATE_SCOPE
    assert receipt["digest_normalization"] == "CRLF_TO_LF"

    # Evaluation summary assertions: the case count is the manifest's, not a constant
    total = _disk_counts(root / "judge_packet")["case_counts"]["total_cases"]
    summary = receipt["evaluation_summary"]
    assert summary["total_cases"] == total
    assert summary["passed_cases"] == total
    assert summary["failed_cases"] == 0
    assert summary["defect_count"] == 0
    assert summary["agreement_count"] == total
    assert summary["verdict"] == "PASS"

    # Budget accounting assertions
    budget = receipt["budget_accounting"]
    assert budget["budget_ceiling_usd"] == 0.25
    assert budget["budget_target_usd"] == 0.05
    assert budget["within_budget"] is True
    assert budget["within_target"] is True
    assert budget["model_parameter_ceiling"] == "70B"
    assert budget["allow_fallbacks"] is False

    # Reference self-consistency label and run-folder digests (run folders under tmp_path)
    woland = receipt["woland_reality_gate"]
    assert woland["terminal_verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert Path(woland["woland_run_folder"]).is_relative_to(tmp_path)
    assert len(woland["novella_sha256"]) == 64
    assert len(woland["dda_actions_sha256"]) == 64
    assert len(woland["summary_sha256"]) == 64
    assert len(woland["receipt_sha256"]) == 64
    assert len(woland["dda_head_sha256"]) == 64

    # Claim hygiene assertions
    claim = receipt["claim_hygiene"]
    assert "supports" in claim
    assert "does_not_support" in claim
    assert "narrowest_defensible_claim" in claim
    assert "next_test_needed" in claim
