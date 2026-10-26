"""Tests for the C041 budget gate, reference self-consistency gate and commit-reveal runner.

AuthorityEffect: None.

No test writes into the real package: every run uses a temporary copy of the
package (``pkg_dir=``) and a temporary intelligence root (``intelligence_root=``)
under ``tmp_path``. When the real judge manifest does not verify over
LF-normalised bytes, the copy's manifest is rebuilt over LF bytes. Lean is never
invoked: the Phase 3 tests replace ``solve`` and ``evaluate_dual`` in the runner.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.governance.commit_reveal_runner as runner_mod
import pytest
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    C041BudgetGate,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.governance.commit_reveal_runner import (
    CommitRevealRunner,
    ManifestCustodyError,
    reference_case_outcome,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.governance.woland_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    case_passed,
    case_warranted_refusal,
)

_pkg_root = Path(__file__).resolve().parent.parent
_POISON_OUT_OF_SCOPE = "c041_poison_01.json"


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _package_copy(tmp_path: Path) -> Path:
    """Copy the package under tmp_path; rebuild the copy's manifest over LF bytes if the real one does not verify."""
    copy = tmp_path / _pkg_root.name
    shutil.copytree(_pkg_root, copy, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    manifest_path = copy / "judge_packet" / "manifest.json"
    try:
        runner_mod.verify_manifest_entries(manifest_path, copy)
    except ManifestCustodyError:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, entry in manifest["entries"].items():
            data = (copy / rel).read_bytes().replace(b"\r\n", b"\n")
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            entry["size_bytes"] = len(data)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return copy


def _runner(copy: Path, tmp_path: Path) -> CommitRevealRunner:
    return CommitRevealRunner(pkg_dir=copy, intelligence_root=tmp_path / "intel")


def _expected_reference_answer(case: dict) -> dict:
    """A stand-in reference answer that matches each case's declared expectation."""
    status = case.get("expected_status", "SOLVED")
    answer = {"_reference": True, "aux": [], "case_id": case["case_id"], "status": status}
    if status == "SOLVED":
        answer["kind"] = case["expected_kind"]
        answer["proof"] = "by decide"
    return answer


def _fake_dual(case: dict, answer: dict) -> tuple[bool, str, dict]:
    """Checker stand-in: verifies reference SOLVED answers, calls reference OUT_OF_SCOPE a warranted
    refusal (ok False, as the real dual evaluator does), and rejects everything else (the mutations)."""
    if answer.get("_reference") is True and answer.get("status") == "SOLVED":
        return True, "CONSENSUS_PASS (stand-in)", {"outcome": f"VERIFIED_{answer['kind']}"}
    if answer.get("_reference") is True and answer.get("status") == "OUT_OF_SCOPE":
        return False, "NOT VERIFIED (refusal scored separately)", {"outcome": "WARRANTED_REFUSAL"}
    return False, "REJECTED (stand-in)", {"outcome": "REJECTED"}


def test_budget_gate_initialization():
    gate = C041BudgetGate()
    assert gate.ceiling_microusd == HARD_CEILING_MICROUSD
    assert gate.target_microusd == TARGET_BUDGET_MICROUSD
    assert gate.is_within_target is True


def test_budget_gate_disallows_fallbacks():
    gate = C041BudgetGate()
    with pytest.raises(Exception) as exc_info:
        gate.validate_model("openrouter", "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=True)
    assert "allow_fallbacks" in str(exc_info.value)


def test_commit_reveal_phase_1_and_2(tmp_path):
    copied_package = _package_copy(tmp_path)
    runner = _runner(copied_package, tmp_path)
    rec1 = runner.phase_1_judge_commitment()
    assert rec1["phase"] == "PHASE_1_JUDGE_COMMITMENT"
    assert rec1["manifest_sha256"] == _lf_sha256(copied_package / "judge_packet" / "manifest.json")
    assert rec1["digest_normalization"] == "CRLF_TO_LF"
    assert rec1["case_count"] == 64
    assert rec1["mutation_count"] == 48

    rec2 = runner.phase_2_freeze_record()
    assert rec2["phase"] == "PHASE_2_FREEZE_RECORD"
    assert rec2["phase1_binding_sha256"] == rec1["manifest_sha256"]
    assert "combined_solver_sha256" in rec2
    assert "solver.py" in rec2["solver_files"]
    assert runner.phase1_file.parent == copied_package / "commitments"


def test_reference_out_of_scope_with_warranted_refusal_outcome_is_consistent_but_not_verified(
    monkeypatch,
):
    # Counterexample: before, ok=False made this reference refusal a failed case; the opposite error
    # would count it as a verified pass. It must be consistent (0 defects) and not verified.
    case = json.loads(
        (_pkg_root / "judge_packet" / "cases" / _POISON_OUT_OF_SCOPE).read_text(encoding="utf-8")
    )
    assert case["expected_status"] == "OUT_OF_SCOPE"
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)

    outcome = reference_case_outcome(case, _expected_reference_answer(case))

    assert outcome["checker_accepted"] is False
    assert outcome["checker_outcome"] == "WARRANTED_REFUSAL"
    assert outcome["verified"] is False
    assert outcome["warranted_refusal"] is True
    assert outcome["defects"] == 0
    assert case_passed(outcome) is True
    assert case_warranted_refusal(outcome) is True


def test_warranted_refusal_outcome_on_a_case_that_declares_a_proof_is_a_defect(monkeypatch):
    case = json.loads(
        (_pkg_root / "judge_packet" / "cases" / "c041_base_01.json").read_text(encoding="utf-8")
    )
    monkeypatch.setattr(
        runner_mod,
        "evaluate_dual",
        lambda c, a: (
            False,
            "NOT VERIFIED (refusal scored separately)",
            {"outcome": "WARRANTED_REFUSAL"},
        ),
    )
    answer = {"case_id": case["case_id"], "status": "OUT_OF_SCOPE"}
    outcome = reference_case_outcome(case, answer)
    assert (outcome["verified"], outcome["warranted_refusal"], outcome["defects"]) == (
        False,
        False,
        1,
    )
    assert case_passed(outcome) is False


def test_abstention_is_a_defect_even_where_a_refusal_is_expected(monkeypatch):
    case = json.loads(
        (_pkg_root / "judge_packet" / "cases" / _POISON_OUT_OF_SCOPE).read_text(encoding="utf-8")
    )
    monkeypatch.setattr(
        runner_mod, "evaluate_dual", lambda c, a: (False, "ABSTAINED", {"outcome": "ABSTAINED"})
    )
    outcome = reference_case_outcome(
        case, {"case_id": case["case_id"], "status": "UNKNOWN", "code": "X"}
    )
    assert outcome["abstained"] is True
    assert (outcome["verified"], outcome["warranted_refusal"], outcome["defects"]) == (
        False,
        False,
        1,
    )


def test_phase3_counts_warranted_refusals_separately_from_verified_answers(tmp_path, monkeypatch):
    copied_package = _package_copy(tmp_path)
    monkeypatch.setattr(runner_mod, "solve", _expected_reference_answer)
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)
    runner = _runner(copied_package, tmp_path)
    runner.phase_1_judge_commitment()
    runner.phase_2_freeze_record()

    receipt = runner.phase_3_scoring(task_key="t_warranted")

    assert receipt["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert receipt["total_cases"] == 64
    assert receipt["warranted_refusal_cases"] == 4
    assert receipt["passed_cases"] == 60
    assert receipt["failed_cases"] == 0
    assert (receipt["mutations_killed"], receipt["mutations_total"]) == (48, 48)
    assert receipt["receipt"]["verified_answer_cases"] == 60
    assert receipt["receipt"]["warranted_refusal_cases"] == 4
    assert (
        tmp_path / "intel" / "_intelligence" / "_woland" / "runs" / "t_warranted" / "receipt.json"
    ).is_file()
    assert runner.phase3_file.parent == copied_package / "commitments"


def test_phase3_refuse_all_reference_is_inconsistent(tmp_path, monkeypatch):
    copied_package = _package_copy(tmp_path)
    monkeypatch.setattr(
        runner_mod,
        "solve",
        lambda case: {
            "case_id": case["case_id"],
            "status": "UNKNOWN",
            "code": "SEARCH_LIMIT_REACHED",
        },
    )
    monkeypatch.setattr(
        runner_mod, "evaluate_dual", lambda c, a: (False, "ABSTAINED", {"outcome": "ABSTAINED"})
    )
    runner = _runner(copied_package, tmp_path)
    runner.phase_1_judge_commitment()
    runner.phase_2_freeze_record()

    receipt = runner.phase_3_scoring(task_key="t_refuse_all")

    assert receipt["verdict"] == TERMINAL_REFUSE
    assert receipt["passed_cases"] == 0
    assert receipt["warranted_refusal_cases"] == 0
    assert receipt["abstained_cases"] == 64


def test_phase3_detects_a_tampered_manifest(tmp_path, monkeypatch):
    copied_package = _package_copy(tmp_path)
    monkeypatch.setattr(runner_mod, "solve", _expected_reference_answer)
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)
    runner = _runner(copied_package, tmp_path)
    runner.phase_1_judge_commitment()
    runner.phase_2_freeze_record()
    manifest_path = copied_package / "judge_packet" / "manifest.json"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Judge manifest tampered"):
        runner.phase_3_scoring(task_key="t_tamper")
    assert runner.failure_file.is_file()


def _infra_error_answer(case: dict) -> dict:
    return {
        "case_id": case["case_id"],
        "status": "UNKNOWN",
        "code": "INFRA_ERROR",
        "infra_errors": ["TIMEOUT"],
    }


def _committed_runner(tmp_path: Path) -> tuple[Path, CommitRevealRunner]:
    copied_package = _package_copy(tmp_path)
    runner = _runner(copied_package, tmp_path)
    runner.phase_1_judge_commitment()
    runner.phase_2_freeze_record()
    return copied_package, runner


def _run_dirs(tmp_path: Path, task_key: str) -> list[Path]:
    intel = tmp_path / "intel" / "_intelligence"
    return [intel / "_woland" / "runs" / task_key, intel / "symbol_game" / "runs" / task_key]


def test_phase3_reruns_a_transient_reference_infra_error_and_labels_from_the_real_answer(
    tmp_path, monkeypatch
):
    # Counterexample: a cold Lean start made the reference answer UNKNOWN/INFRA_ERROR, which was scored
    # as an abstention and labelled the run REFERENCE_SELF_INCONSISTENT. It is now rerun instead.
    _copy, runner = _committed_runner(tmp_path)
    calls: dict[str, int] = {}

    def cold_then_warm(case: dict) -> dict:
        calls[case["case_id"]] = calls.get(case["case_id"], 0) + 1
        return (
            _infra_error_answer(case)
            if calls[case["case_id"]] == 1
            else _expected_reference_answer(case)
        )

    monkeypatch.setattr(runner_mod, "solve", cold_then_warm)
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)

    receipt = runner.phase_3_scoring(task_key="t_infra_transient")

    assert receipt["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert (
        receipt["passed_cases"],
        receipt["warranted_refusal_cases"],
        receipt["abstained_cases"],
    ) == (60, 4, 0)
    assert receipt["infra_error_reruns"] == {"cases": 64, "mutations": 0}
    assert set(calls.values()) == {2}
    summary = json.loads(
        (_run_dirs(tmp_path, "t_infra_transient")[0] / "summary.json").read_text(encoding="utf-8")
    )
    assert all(
        c["status"] != "UNKNOWN" and c["infra_error_reruns"] == 1 for c in summary["case_outcomes"]
    )


def test_phase3_refuses_a_persistent_reference_infra_error_and_writes_no_label(
    tmp_path, monkeypatch
):
    _copy, runner = _committed_runner(tmp_path)
    receipt_bytes_before = runner.phase3_file.read_bytes() if runner.phase3_file.is_file() else None
    stuck_case = json.loads(
        sorted((_copy / "judge_packet" / "cases").glob("*.json"))[0].read_text(encoding="utf-8")
    )
    stuck_calls: list[str] = []

    def stuck_on_one_case(case: dict) -> dict:
        if case["case_id"] == stuck_case["case_id"]:
            stuck_calls.append(case["case_id"])
            return _infra_error_answer(case)
        return _expected_reference_answer(case)

    monkeypatch.setattr(runner_mod, "solve", stuck_on_one_case)
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)

    with pytest.raises(runner_mod.InfraErrorRefusal) as refusal:
        runner.phase_3_scoring(task_key="t_infra_stuck")

    assert refusal.value.code == "INFRA_ERROR"
    assert len(stuck_calls) == runner_mod.INFRA_ERROR_ATTEMPTS == 3
    failure = json.loads(runner.failure_file.read_text(encoding="utf-8"))
    assert failure["error_code"] == "INFRA_ERROR"
    assert failure["error_detail"] == {
        "attempts": 3,
        "errors": ["TIMEOUT"],
        "item": stuck_case["case_id"],
        "source": "case",
    }
    # No label input: the scoring receipt keeps its bytes and no run bundle was written.
    assert (
        runner.phase3_file.read_bytes() if runner.phase3_file.is_file() else None
    ) == receipt_bytes_before
    assert not any(d.exists() for d in _run_dirs(tmp_path, "t_infra_stuck"))


def test_phase3_refuses_a_checker_infra_error_on_a_reference_answer(tmp_path, monkeypatch):
    _copy, runner = _committed_runner(tmp_path)
    monkeypatch.setattr(runner_mod, "solve", _expected_reference_answer)
    monkeypatch.setattr(
        runner_mod,
        "evaluate_dual",
        lambda c, a: (False, "INFRA_ERROR: Lean", {"outcome": "INFRA_ERROR"}),
    )

    with pytest.raises(runner_mod.InfraErrorRefusal):
        runner.phase_3_scoring(task_key="t_checker_infra")
    assert (
        json.loads(runner.failure_file.read_text(encoding="utf-8"))["error_detail"]["source"]
        == "case"
    )
    assert not any(d.exists() for d in _run_dirs(tmp_path, "t_checker_infra"))


def test_checker_infra_error_on_a_mutation_is_rerun_and_never_counted_as_a_rejection(
    tmp_path, monkeypatch
):
    # Counterexample: a mutation that Lean could not check came back ok=False and was counted as killed.
    _copy, runner = _committed_runner(tmp_path)
    monkeypatch.setattr(runner_mod, "solve", _expected_reference_answer)
    seen: set[str] = set()

    def mutation_infra_once(case: dict, answer: dict) -> tuple[bool, str, dict]:
        key = json.dumps([case, answer], sort_keys=True)
        if answer.get("_reference") is not True and key not in seen:
            seen.add(key)
            return False, "INFRA_ERROR: Lean", {"outcome": "INFRA_ERROR"}
        return _fake_dual(case, answer)

    monkeypatch.setattr(runner_mod, "evaluate_dual", mutation_infra_once)
    receipt = runner.phase_3_scoring(task_key="t_mutation_infra_once")
    assert (receipt["mutations_killed"], receipt["mutations_total"]) == (48, 48)
    assert receipt["infra_error_reruns"]["mutations"] == len(seen)

    _copy2, runner2 = _committed_runner(tmp_path / "second")
    monkeypatch.setattr(
        runner_mod,
        "evaluate_dual",
        lambda c, a: _fake_dual(c, a)
        if a.get("_reference") is True
        else (False, "INFRA", {"outcome": "INFRA_ERROR"}),
    )
    with pytest.raises(runner_mod.InfraErrorRefusal):
        runner2.phase_3_scoring(task_key="t_mutation_infra_stuck")
    assert (
        json.loads(runner2.failure_file.read_text(encoding="utf-8"))["error_detail"]["source"]
        == "mutation"
    )
