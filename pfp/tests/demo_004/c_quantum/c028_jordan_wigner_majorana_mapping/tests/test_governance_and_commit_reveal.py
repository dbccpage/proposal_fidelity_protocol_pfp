# AuthorityEffect: None.
"""Tests for governance gates and the commit-reveal runner (C028).

The package root is put on sys.path by tests/conftest.py, so the package's
modules import as top-level ``governance`` and ``judge_packet``. Every
commit-reveal phase runs on a temporary copy of the package; no test writes
into the package's own commitments/ directory (an autouse fixture checks
this). If the package's judge manifest does not verify, the copy's manifest
is rebuilt over LF bytes before the run.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import pytest
from governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    C028BudgetGate,
)
from governance.commit_reveal_runner import CommitRevealRunner
from governance.woland_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    WolandRealityGate,
)

from omega_engine_woland.domain.providers.model_registry import ModelParameterCeilingRefused
from omega_engine_woland.domain.providers.types import Provider

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


def test_budget_gate_invariants():
    gate = C028BudgetGate()
    assert gate.limit_microusd == HARD_CEILING_MICROUSD
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD
    assert gate.spent_microusd == 0
    assert gate.is_within_hard_ceiling
    assert gate.is_within_target


def test_budget_gate_admission_and_settlement_fail_closed():
    """Counterexample: validate_model called registry.lookup and record_post_call called settle_post_call (absent APIs)."""
    gate = C028BudgetGate()
    with pytest.raises(ModelParameterCeilingRefused) as refused:
        gate.validate_model(Provider.OPENROUTER, "qwen/qwen-2.5-72b-instruct")
    assert refused.value.code == "MODEL_OVER_PARAMETER_CEILING"
    quote = gate.authorize_pre_call(
        Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", 1000, 500
    )
    assert gate.spent_microusd == quote.cost_microusd > 0
    with pytest.raises(RuntimeError) as unavailable:
        gate.record_post_call(quote, 1000, 500)
    assert unavailable.value.code == "BUDGET_GATE_UNAVAILABLE"


def test_woland_gate_pass_verdict(tmp_path: Path):
    gate = WolandRealityGate(base_repo_root=tmp_path)
    verdict = gate.evaluate_verdict(
        cases_evaluated=38,
        cases_passed=38,
        mutations_killed=48,
        mutations_total=48,
        cost_usd=Fraction(0),
        ceiling_usd=CEILING_USD,
        critical_errors=0,
    )
    assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert gate.evaluate_verdict(38, 38 - 1, 48, 48, 0, CEILING_USD) == TERMINAL_REFUSE


def test_woland_gate_refuses_empty_suites_and_inexact_inputs(tmp_path: Path):
    """Counterexample: 0 of 0 mutations passed (kill rate defaulted to 1.0), and float costs were accepted."""
    gate = WolandRealityGate(base_repo_root=tmp_path)
    assert gate.evaluate_verdict(38, 38, 0, 0, 0, CEILING_USD) == "REFERENCE_SELF_INCONSISTENT"
    assert gate.evaluate_verdict(0, 0, 48, 48, 0, CEILING_USD) == "REFERENCE_SELF_INCONSISTENT"
    with pytest.raises(TypeError):
        gate.evaluate_verdict(38, 38, 48, 48, 0.01, 1.00)


def test_woland_gate_never_deletes_an_existing_run(tmp_path: Path):
    """Counterexample: persist_run rmtree'd an existing run folder under _intelligence before writing."""
    gate = WolandRealityGate(base_repo_root=tmp_path)
    existing = tmp_path / "_intelligence" / "_woland" / "runs" / "kept_run"
    existing.mkdir(parents=True)
    (existing / "sentinel.txt").write_text("earlier run", encoding="utf-8")
    with pytest.raises(RunFolderExistsError):
        gate.persist_run("kept_run", TERMINAL_REFUSE, 1, 0, 1, 1, 0, [], {}, allow_overwrite=True)
    assert (existing / "sentinel.txt").read_text(encoding="utf-8") == "earlier run"


def test_commit_reveal_phase_1_and_2(tmp_path: Path):
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(challenge_root, intelligence_repo_root=tmp_path / "intel")
    p1 = runner.phase_1_judge_commitment()
    assert "manifest_sha256" in p1
    assert len(p1["manifest_sha256"]) == 64
    assert p1["digest_normalization"] == "CRLF_TO_LF"

    p2 = runner.phase_2_solver_freeze()
    assert "solver_files" in p2
    assert len(p2["solver_files"]) == 6
    assert (challenge_root / "commitments" / "c028_jw_judge_commitment.json").is_file()
    assert (challenge_root / "commitments" / "c028_jw_freeze_record.json").is_file()


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
