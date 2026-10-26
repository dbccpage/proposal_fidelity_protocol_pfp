# AuthorityEffect: None.
"""Tests for C026 governance: budget gate, reference self-consistency gate, and CommitRevealRunner.

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
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    BudgetCeilingExceededError,
    C026BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.governance.woland_gate import (
    GATE_SCOPE,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    WolandRealityGate,
)

from omega_engine_woland.domain.providers.types import BudgetExceeded, Provider

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = PACKAGE_ROOT.name
MUTATION_GLOB = "judge_packet/mutation_suite/*.json"


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


CEILING_USD = Fraction(HARD_CEILING_MICROUSD, 1_000_000)
COST_USD = Fraction(4, 100)


def test_budget_gate_invariants():
    gate = C026BudgetGate()
    assert gate.ceiling_microusd == gate.limit_microusd == HARD_CEILING_MICROUSD
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD
    assert gate.is_within_target
    assert gate.is_within_hard_ceiling

    # Ceiling exceeding hard limit raises BudgetCeilingExceededError
    with pytest.raises(BudgetCeilingExceededError):
        C026BudgetGate(ceiling_microusd=HARD_CEILING_MICROUSD + 1)

    # Fallbacks not allowed
    with pytest.raises(FallbackNotAllowedError):
        gate.validate_model("openrouter", "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=True)

    # Pre-call check fails closed
    with pytest.raises(BudgetExceeded):
        gate.pre_call_check(HARD_CEILING_MICROUSD + 1)


def test_budget_gate_charges_through_the_provider_budget_api():
    """Counterexample: quote_and_charge_pre_call called quote.projected_cost_microusd, which does not exist."""
    gate = C026BudgetGate()
    receipt = gate.quote_and_charge_pre_call(
        Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", 1000, 500
    )
    assert type(receipt.cost_microusd) is int and receipt.cost_microusd > 0
    assert gate.spent_microusd == receipt.cost_microusd


def test_woland_reality_gate_verdicts(tmp_path: Path):
    wgate = WolandRealityGate(base_repo_root=tmp_path)

    # Pass condition
    v_pass = wgate.evaluate_verdict(
        cases_evaluated=10,
        cases_passed=10,
        mutations_killed=12,
        mutations_total=12,
        cost_usd=COST_USD,
        ceiling_usd=CEILING_USD,
    )
    assert v_pass == TERMINAL_REFERENCE_SELF_CONSISTENT

    # Refusal on a failed case
    v_case_fail = wgate.evaluate_verdict(
        cases_evaluated=10,
        cases_passed=9,
        mutations_killed=12,
        mutations_total=12,
        cost_usd=COST_USD,
        ceiling_usd=CEILING_USD,
    )
    assert v_case_fail == TERMINAL_REFUSE

    # Refusal on a surviving mutation
    v_mut_fail = wgate.evaluate_verdict(
        cases_evaluated=10,
        cases_passed=10,
        mutations_killed=11,
        mutations_total=12,
        cost_usd=COST_USD,
        ceiling_usd=CEILING_USD,
    )
    assert v_mut_fail == TERMINAL_REFUSE

    # Refusal on cost exceeded
    v_cost_fail = wgate.evaluate_verdict(
        cases_evaluated=10,
        cases_passed=10,
        mutations_killed=12,
        mutations_total=12,
        cost_usd=CEILING_USD + Fraction(1, 20),
        ceiling_usd=CEILING_USD,
    )
    assert v_cost_fail == TERMINAL_REFUSE


def test_woland_reality_gate_refuses_empty_suites_and_inexact_inputs(tmp_path: Path):
    """Counterexample: 0 of 0 mutations passed the gate, and float costs or bool counts were accepted."""
    wgate = WolandRealityGate(base_repo_root=tmp_path)
    assert (
        wgate.evaluate_verdict(10, 10, 0, 0, COST_USD, CEILING_USD) == "REFERENCE_SELF_INCONSISTENT"
    )
    assert (
        wgate.evaluate_verdict(0, 0, 12, 12, COST_USD, CEILING_USD) == "REFERENCE_SELF_INCONSISTENT"
    )
    with pytest.raises(TypeError):
        wgate.evaluate_verdict(10, 10, 12, 12, 0.04, CEILING_USD)
    with pytest.raises(TypeError):
        wgate.evaluate_verdict(True, True, 12, 12, COST_USD, CEILING_USD)


def test_woland_reality_gate_never_deletes_an_existing_run(tmp_path: Path):
    """Counterexample: allow_overwrite=True rmtree'd an existing run folder under _intelligence."""
    wgate = WolandRealityGate(base_repo_root=tmp_path)
    existing = tmp_path / "_intelligence" / "_woland" / "runs" / "kept_run"
    existing.mkdir(parents=True)
    (existing / "sentinel.txt").write_text("earlier run", encoding="utf-8")
    with pytest.raises(RunFolderExistsError):
        wgate.persist_run("kept_run", TERMINAL_REFUSE, 1, 0, 1, 1, 0, [], {}, allow_overwrite=True)
    assert (existing / "sentinel.txt").read_text(encoding="utf-8") == "earlier run"


def test_commit_reveal_runner_lifecycle(tmp_path: Path):
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(challenge_root, intelligence_repo_root=tmp_path / "intel")

    # Phase 1: Judge commitment
    r1 = runner.phase_1_judge_commitment()
    assert r1["phase"] == "PHASE_1_JUDGE_COMMITMENT"
    assert len(r1["manifest_sha256"]) == 64
    assert r1["digest_normalization"] == "CRLF_TO_LF"

    # Phase 2: Solver freeze
    r2 = runner.phase_2_solver_freeze()
    assert r2["phase"] == "PHASE_2_SOLVER_FREEZE"
    assert len(r2["solver_files"]) == 6

    # Phase 3: Execute and score
    r3 = runner.phase_3_execute_and_score(task_key="test_c026_run")
    assert r3["phase"] == "PHASE_3_SCORING_RECEIPT"
    assert r3["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert r3["gate_scope"] == GATE_SCOPE
    assert r3["evidence"]["cases_evaluated"] == len(_case_files(challenge_root))
    assert r3["evidence"]["cases_passed"] == r3["evidence"]["cases_evaluated"]
    assert r3["evidence"]["mutations_total"] == len(_mutation_files(challenge_root)) > 0
    assert r3["evidence"]["mutations_killed"] == r3["evidence"]["mutations_total"]
    assert Path(r3["run_folder"]).is_relative_to(tmp_path / "intel")

    # Verify committed JSONs exist in the copy
    c_dir = challenge_root / "commitments"
    assert (c_dir / "c026_ff_judge_commitment.json").is_file()
    assert (c_dir / "c026_ff_freeze_record.json").is_file()
    assert (c_dir / "c026_ff_scoring_receipt.json").is_file()


def test_commit_reveal_refuses_case_file_not_in_manifest(tmp_path: Path):
    """Counterexample: Phase 3 scored case files without checking them against the committed manifest."""
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(challenge_root, intelligence_repo_root=tmp_path / "intel")
    runner.phase_1_judge_commitment()
    runner.phase_2_solver_freeze()
    cases_dir = challenge_root / "judge_packet" / "cases"
    shutil.copyfile(_case_files(challenge_root)[0], cases_dir / "zz_added_after_commitment.json")
    with pytest.raises(ValueError) as exc_info:
        runner.phase_3_execute_and_score(task_key="unlisted_case")
    assert exc_info.value.code == "FILE_NOT_IN_MANIFEST"
    failure = json.loads(runner.failure_receipt_file.read_text(encoding="utf-8"))
    assert failure["error_code"] == "FILE_NOT_IN_MANIFEST"
