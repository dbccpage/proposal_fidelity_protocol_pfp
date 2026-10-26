"""Tests for C023 Governance, BudgetGate, reference self-consistency gate, and CommitRevealRunner.

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
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.governance.woland_gate import (
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


def test_budget_gate_invariants():
    gate = BudgetGate(ceiling_microusd=500_000, target_microusd=50_000)
    assert gate.limit_microusd == 500_000
    assert gate.target_microusd == 50_000
    assert gate.is_within_target is True
    assert gate.is_within_hard_ceiling is True

    # Check fallback rejection
    with pytest.raises(FallbackNotAllowedError):
        gate.validate_model("openrouter", "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=True)

    # Check ceiling exceeded error
    with pytest.raises(BudgetCeilingExceededError):
        BudgetGate(ceiling_microusd=HARD_CEILING_MICROUSD + 1)


def test_woland_gate_verdict(tmp_path: Path):
    gate = WolandGate(intelligence_root=tmp_path / "_intelligence")
    good_results = [
        {
            "id": "c1",
            "status": "SOLVED",
            "checker_pass": True,
            "phi1": Fraction(0),
            "gamma2": Fraction(0),
        },
        {"id": "c2", "status": "OUT_OF_SCOPE", "checker_pass": True},
    ]
    assert gate.judge(good_results) == TERMINAL_REFERENCE_SELF_CONSISTENT

    bad_results = [
        {
            "id": "c1",
            "status": "SOLVED",
            "checker_pass": False,
            "phi1": Fraction(1),
            "gamma2": Fraction(1),
        },
    ]
    assert gate.judge(bad_results) == TERMINAL_REFUSE


def test_woland_gate_per_case_defect_values_are_exact(tmp_path: Path):
    """Counterexample: per-case phi1=1/10^9 passed because float(phi1) <= 1e-6, and a float phi1 was accepted."""
    gate = WolandGate(intelligence_root=tmp_path / "_intelligence")
    assert (
        gate.judge([{"status": "SOLVED", "checker_pass": True, "phi1": Fraction(1, 10**9)}])
        == TERMINAL_REFUSE
    )
    with pytest.raises(TypeError):
        gate.judge([{"status": "SOLVED", "checker_pass": True, "phi1": 0.0}])
    assert gate.judge([{"status": "SOLVED", "checker_pass": "PASS"}]) == TERMINAL_REFUSE
    assert gate.judge([]) == "REFERENCE_SELF_INCONSISTENT"


def test_woland_gate_default_root_is_the_intelligence_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Counterexample: WolandGate() wrote to <repo>/_woland/runs instead of <repo>/_intelligence/_woland/runs."""
    monkeypatch.setenv("OMEGA_INTELLIGENCE_ROOT", str(tmp_path))
    gate = WolandGate()
    assert gate.woland_runs_dir == tmp_path.resolve() / "_intelligence" / "_woland" / "runs"


def test_woland_gate_force_clean_never_deletes_an_existing_run(tmp_path: Path):
    """Counterexample: force_clean=True rmtree'd an existing run folder under _intelligence."""
    gate = WolandGate(intelligence_root=tmp_path / "_intelligence")
    existing = gate.woland_runs_dir / "kept_run"
    existing.mkdir(parents=True)
    (existing / "sentinel.txt").write_text("earlier run", encoding="utf-8")
    hygiene = {
        "supports": "s",
        "does_not_support": "d",
        "narrowest_defensible_claim": "n",
        "next_test_needed": "t",
    }
    with pytest.raises(RunFolderExistsError):
        gate.persist_run(
            "kept_run",
            [{"status": "SOLVED", "checker_pass": True}],
            [],
            {},
            hygiene,
            force_clean=True,
        )
    assert (existing / "sentinel.txt").read_text(encoding="utf-8") == "earlier run"


def test_commit_reveal_phases(tmp_path: Path):
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(
        challenge_root=challenge_root,
        intelligence_repo_root=tmp_path / "intelligence",
    )
    p1 = runner.phase_1_commit_judge_packet()
    assert p1["phase"] == "PHASE_1_JUDGE_COMMITMENT"
    assert "manifest_sha256" in p1
    assert p1["digest_normalization"] == "CRLF_TO_LF"

    p2 = runner.phase_2_freeze_deliverables()
    assert p2["phase"] == "PHASE_2_SOLVER_FREEZE"
    assert "composite_freeze_sha256" in p2

    p3 = runner.phase_3_evaluate_and_score(task_key="c023_test_run", force_clean=True)
    assert p3["phase"] == "PHASE_3_SCORING_RECEIPT"
    assert p3["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert p3["gate_scope"] == GATE_SCOPE
    assert p3["all_passed"] is True
    assert p3["case_count"] == len(_case_files(challenge_root))
    runs = tmp_path / "intelligence" / "_intelligence" / "_woland" / "runs" / "c023_test_run"
    assert (runs / "receipt.json").is_file()


def test_commit_reveal_refuses_case_file_not_in_manifest(tmp_path: Path):
    """Counterexample: Phase 3 scored case files without checking them against the committed manifest."""
    challenge_root = _isolated_copy(tmp_path)
    runner = CommitRevealRunner(
        challenge_root=challenge_root, intelligence_repo_root=tmp_path / "intelligence"
    )
    runner.phase_1_commit_judge_packet()
    runner.phase_2_freeze_deliverables()
    cases_dir = challenge_root / "judge_packet" / "cases"
    shutil.copyfile(_case_files(challenge_root)[0], cases_dir / "zz_added_after_commitment.json")
    with pytest.raises(ValueError) as exc_info:
        runner.phase_3_evaluate_and_score(task_key="unlisted_case", force_clean=True)
    assert exc_info.value.code == "CASE_FILE_NOT_IN_MANIFEST"
    failure = json.loads(runner.failure_receipt_file.read_text(encoding="utf-8"))
    assert failure["error_code"] == "CASE_FILE_NOT_IN_MANIFEST"
