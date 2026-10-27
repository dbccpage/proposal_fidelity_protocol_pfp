"""Tests for the C042 budget gate, reference self-consistency gate and runner.

AuthorityEffect: None.

No test writes into the real package: runs use a temporary copy of the judge
data (``judge_dir=``, ``manifest_file=``), a temporary receipt directory
(``receipt_dir=``) and a temporary intelligence root
(``intelligence_repo_root=``), all under ``tmp_path``. When the real manifest
does not verify over LF-normalised bytes, the copy's manifest is rebuilt over
LF bytes. Amounts are integer micro-USD.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from fractions import Fraction
from pathlib import Path

import pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.governance.commit_reveal_runner as runner_mod
import pytest
from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.governance.budget_gate import BudgetReceipt, C042BudgetGate
from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.governance.commit_reveal_runner import ManifestCustodyError
from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.governance.adversary_gate import (
    TERMINAL_OPEN_RESIDUAL,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    AdversaryGateC042,
)

PKG_ROOT = Path(__file__).resolve().parent.parent


def _judge_copy(tmp_path: Path) -> tuple[Path, Path]:
    """Copy judge cases, mutations and the manifest under tmp_path.

    The copy's manifest keeps the real digests; it is rebuilt over LF bytes only if it does not verify.
    """
    root = tmp_path / "c042_judge_copy"
    (root / "judge_packet").mkdir(parents=True)
    for sub in ("cases", "mutation_suite"):
        shutil.copytree(PKG_ROOT / "judge_packet" / sub, root / "judge_packet" / sub)
    manifest = json.loads((PKG_ROOT / "manifest.json").read_text(encoding="utf-8"))
    manifest_path = root / "manifest.json"
    shutil.copy2(PKG_ROOT / "manifest.json", manifest_path)
    try:
        runner_mod.verify_manifest_entries(manifest_path, root)
    except ManifestCustodyError:
        manifest["files"] = {
            rel: hashlib.sha256((root / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for rel in manifest["files"]
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root / "judge_packet", manifest_path


def _run(tmp_path: Path) -> dict:
    judge_dir, manifest_file = _judge_copy(tmp_path)
    return runner_mod.run_commit_reveal_protocol(
        judge_dir=judge_dir,
        manifest_file=manifest_file,
        receipt_dir=tmp_path / "receipts",
        intelligence_repo_root=tmp_path / "intel",
    )


def _expected_reference_answer(case: dict) -> dict:
    if "expected_status" in case:
        return {"_reference": True, "case_id": case["case_id"], "status": case["expected_status"]}
    return {
        "_reference": True,
        "case_id": case["case_id"],
        "status": "SOLVED",
        "kind": case["expected_kind"],
    }


def _fake_dual(case: dict, answer: dict) -> tuple[bool, str, dict]:
    """Checker stand-in: accepts reference SOLVED and OUT_OF_SCOPE answers, calls UNKNOWN an abstention,
    rejects everything else (the mutations)."""
    if answer.get("status") == "UNKNOWN":
        return False, "ABSTAINED (stand-in)", {"abstained": True}
    if answer.get("_reference") is True:
        return True, "accepted (stand-in)", {}
    return False, "rejected (stand-in)", {}


def test_budget_gate_constraints():
    gate = C042BudgetGate()
    assert gate.limit_microusd == 500_000
    assert gate.target_microusd == 50_000
    assert gate.limit_usd == Fraction(1, 2)
    assert gate.target_usd == Fraction(1, 20)
    assert gate.parameter_ceiling == "70B"

    # Pre-call check passes for a 1,000 micro-USD estimate; a float estimate is refused.
    assert gate.check_pre_call("meta-llama/llama-3.3-70b-instruct", 1_000) is True
    with pytest.raises(TypeError):
        gate.check_pre_call("meta-llama/llama-3.3-70b-instruct", 0.001)

    rcpt = BudgetReceipt(
        call_id="c042_call_01",
        model="meta-llama/llama-3.3-70b-instruct",
        prompt_tokens=150,
        completion_tokens=50,
        billed_cost_microusd=50,
        timestamp="2026-09-28T12:00:00Z",
    )
    gate.record_call(rcpt)
    assert gate.total_spent_microusd() == 50
    assert gate.total_spent_usd() == Fraction(50, 1_000_000)


def test_adversary_structurebench_quad(tmp_path):
    adversary = AdversaryGateC042(task_key="test_c042_quad", intelligence_repo_root=tmp_path / "intel")
    assert not (tmp_path / "intel").exists()
    run_folder = adversary.emit_structurebench_quad(
        verdict=TERMINAL_REFERENCE_SELF_CONSISTENT,
        total_cases=64,
        passed_cases=64,
        defects=[],
        receipt_meta={"challenge": "c042"},
    )
    assert run_folder.parent == tmp_path / "intel" / "_intelligence" / "_adversary" / "runs"
    for name in ("receipt.json", "novella.md", "dda_actions.jsonl", "summary.json"):
        assert (run_folder / name).is_file()
    summary = json.loads((run_folder / "summary.json").read_text(encoding="utf-8"))
    assert summary["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert summary["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"


def test_adversary_gate_refuses_the_retired_label(tmp_path):
    adversary = AdversaryGateC042(task_key="test_c042_label", intelligence_repo_root=tmp_path / "intel")
    with pytest.raises(ValueError, match="LABEL_MISMATCH"):
        adversary.emit_structurebench_quad(
            verdict="PASS_TO_MASTER", total_cases=64, passed_cases=64, defects=[], receipt_meta={}
        )


def test_reference_run_records_custody_facts_without_capping_the_label(tmp_path):
    # Policy: a run without a pre-run commitment records the fact and is not capped at OPEN_RESIDUAL.
    receipt = _run(tmp_path)
    assert receipt["verdict"] in (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE)
    assert receipt["pre_run_commitment"] is False
    assert receipt["commitment_timing"] == "COMPUTED_AT_REVEAL"
    assert receipt["residuals"] == []
    assert receipt["informational_residuals"] == ["NO_PRE_RUN_COMMITMENT"]
    assert (receipt["total_cases"], receipt["mutations_total"]) == (64, 48)
    assert (
        receipt["verified_answer_cases"] + receipt["warranted_refusal_cases"]
        == receipt["passed_cases"]
    )
    assert sorted(p.name for p in (tmp_path / "receipts").iterdir()) == [
        "c042_l41_scoring_receipt.json"
    ]
    run_dir = tmp_path / "intel" / "_intelligence" / "_adversary" / "runs" / receipt["run_folder"]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["informational_residuals"] == ["NO_PRE_RUN_COMMITMENT"]
    assert summary["verdict"] == receipt["verdict"]


def test_poison_03_expects_the_warranted_out_of_scope_the_checker_accepts():
    # Counterexample: poison_03 declared expected_status UNKNOWN, an abstention that is never consistent,
    # so no reference answer could ever make the judge self-consistent.
    case = json.loads(
        (PKG_ROOT / "judge_packet" / "cases" / "c042_poison_03.json").read_text(encoding="utf-8")
    )
    assert case["expected_status"] == "OUT_OF_SCOPE"
    result = runner_mod.score_reference_case(case, runner_mod.solve(case))
    assert result["status"] == "OUT_OF_SCOPE"
    assert result["checker_accepted"] is True
    assert (result["verified"], result["warranted_refusal"], result["verified_answer"]) == (
        True,
        True,
        False,
    )


def test_warranted_out_of_scope_is_consistent_but_not_a_verified_answer(tmp_path, monkeypatch):
    monkeypatch.setattr(runner_mod, "solve", _expected_reference_answer)
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)
    receipt = _run(tmp_path)
    # The judge declares 7 OUT_OF_SCOPE cases (warranted refusals) and 57 SAT/UNSAT cases.
    assert receipt["warranted_refusal_cases"] == 7
    assert receipt["verified_answer_cases"] == 57
    assert receipt["passed_cases"] == 64
    assert receipt["abstained_cases"] == 0
    assert (receipt["mutations_killed"], receipt["mutations_total"]) == (48, 48)
    # Counterexample: before the policy change the missing pre-run commitment capped this at OPEN_RESIDUAL.
    assert receipt["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT


def test_refuse_all_reference_is_inconsistent(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner_mod, "solve", lambda case: {"case_id": case["case_id"], "status": "UNKNOWN"}
    )
    monkeypatch.setattr(runner_mod, "evaluate_dual", _fake_dual)
    receipt = _run(tmp_path)
    assert receipt["verdict"] == TERMINAL_REFUSE
    assert receipt["passed_cases"] == 0
    assert receipt["abstained_cases"] == 64


def test_informational_residuals_never_change_the_gate_label(tmp_path):
    adversary = AdversaryGateC042(task_key="test_c042_notes", intelligence_repo_root=tmp_path / "intel")
    run_folder = adversary.emit_structurebench_quad(
        total_cases=3,
        passed_cases=3,
        defects=[],
        receipt_meta={},
        mutations_total=2,
        mutations_killed=2,
        informational_residuals=["NO_PRE_RUN_COMMITMENT"],
    )
    receipt = json.loads((run_folder / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert receipt["informational_residuals"] == ["NO_PRE_RUN_COMMITMENT"]
    closed = AdversaryGateC042(task_key="test_c042_closed", intelligence_repo_root=tmp_path / "intel")
    closed_folder = closed.emit_structurebench_quad(
        total_cases=3,
        passed_cases=3,
        defects=[],
        receipt_meta={},
        residuals=["DECLARED_CLOSED_RESIDUAL"],
    )
    closed_receipt = json.loads((closed_folder / "receipt.json").read_text(encoding="utf-8"))
    assert closed_receipt["verdict"] == TERMINAL_OPEN_RESIDUAL
