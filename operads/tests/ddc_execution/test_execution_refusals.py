"""Actual regressions: unbound evaluators, damaged custody, and effectful dry-runs."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from operads.domain.ddc_execution.entities import OperadMorphism
from operads.domain.ddc_execution.execution import (
    EvaluationOutcome,
    ExecutionPlan,
)
from operads.domain.ddc_execution.value_objects import (
    ArtifactOutput,
    ExecutionRunRecord,
)
from operads.domain.operad.errors import Ok
from operads.infrastructure.ddc_execution import (
    trace_storage as trace_storage_module,
)
from operads.infrastructure.ddc_execution.runtime import (
    build_meta_operad_engine,
)
from operads.infrastructure.ddc_execution.trace_storage import (
    FileTraceStorage,
)

SKILL = "meta-dda-dag-emitter"


@pytest.fixture
def configured_root(tmp_path: Path) -> Path:
    directory = tmp_path / "operads/skill_operad/json"
    directory.mkdir(parents=True)
    (directory / "operad_signature.json").write_text(
        json.dumps(
            {
                "operations": [
                    {
                        "skill_id": SKILL,
                        "arity": 1,
                        "source_colours": ["Receipt"],
                        "target_colour": "Diagram",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (directory / "agent_capability_slices.json").write_text(
        json.dumps({"agents": {"fixture": {"licensed_skills": [SKILL]}}}), encoding="utf-8"
    )
    return tmp_path


class ForbiddenEvaluator:
    called = False

    def is_bound(self, skill_id):
        return True

    def evaluate(self, *args):
        self.called = True
        raise AssertionError("unexpected evaluator effect")


def test_dry_run_produces_only_plan_and_no_artifacts(configured_root: Path) -> None:
    engine = build_meta_operad_engine(configured_root)
    evaluator = ForbiddenEvaluator()
    engine.evaluator = evaluator
    before = {
        path.relative_to(configured_root): path.read_bytes()
        for path in configured_root.rglob("*")
        if path.is_file()
    }
    result = engine.execute_morphism(SKILL, ["receipt.json"], agent_id="fixture", dry_run=True)
    after = {
        path.relative_to(configured_root): path.read_bytes()
        for path in configured_root.rglob("*")
        if path.is_file()
    }
    assert result.is_ok
    assert isinstance(result.unwrap(), ExecutionPlan)
    assert result.unwrap().status == "DRY_RUN_PLAN"
    assert not evaluator.called
    assert before == after


def test_unbound_and_unknown_operations_cannot_mint_pass(configured_root: Path) -> None:
    engine = build_meta_operad_engine(configured_root)
    unbound = engine.execute_morphism(SKILL, ["receipt.json"], agent_id="fixture")
    unknown = engine.execute_morphism("operation_does_not_exist", [], dry_run=True)
    assert unbound.is_err
    assert unbound.error.code == "NOT_EXECUTABLE"
    assert unknown.is_err
    assert unknown.error.code == "UNKNOWN_MORPHISM"
    assert not (configured_root / "runs").exists()


@pytest.mark.parametrize("damage", ["missing", "malformed"])
def test_capability_custody_refuses_before_evaluation(configured_root: Path, damage: str) -> None:
    path = (
        configured_root
        / "operads/skill_operad/json/agent_capability_slices.json"
    )
    if damage == "missing":
        path.unlink()
    else:
        path.write_text('{"agents": []}', encoding="utf-8")
    engine = build_meta_operad_engine(configured_root)
    evaluator = ForbiddenEvaluator()
    engine.evaluator = evaluator
    result = engine.execute_morphism(SKILL, ["receipt.json"], agent_id="fixture")
    assert result.is_err
    assert result.error.code in ("OPERAD_REGISTRY_UNAVAILABLE", "OPERAD_REGISTRY_INVALID")
    assert not evaluator.called


@pytest.mark.parametrize("damage", ["missing", "malformed", "forged_pass", "wrong_signature"])
def test_trace_custody_refuses_before_evaluation(configured_root: Path, damage: str) -> None:
    if damage != "missing":
        trace = configured_root / ".agents/skills" / SKILL / "evidence_trace.json"
        trace.parent.mkdir(parents=True)
        data = {
            "schema": "core.operad.evidence_trace.v1",
            "skill_name": SKILL,
            "signature": "(Receipt) -> Diagram",
            "authority_effect": "None",
            "runs": [],
            "total_runs": 0,
            "contractive_runs": 0,
            "required_contractive_runs": 3,
            "residual_evidence_bar_satisfied": False,
        }
        if damage == "malformed":
            data = {"runs": []}
        elif damage == "forged_pass":
            data.update(total_runs=3, contractive_runs=3, residual_evidence_bar_satisfied=True)
        else:
            data["signature"] = "(Code) -> Receipt"
        trace.write_text(json.dumps(data), encoding="utf-8")
    engine = build_meta_operad_engine(configured_root)
    evaluator = ForbiddenEvaluator()
    engine.evaluator = evaluator
    result = engine.execute_morphism(SKILL, ["receipt.json"], agent_id="fixture")
    assert result.is_err
    assert result.error.code == "TRACE_LEDGER_ERROR"
    assert not evaluator.called


def _ledger(root: Path, hosts: tuple[str, ...]) -> bytes:
    payload = {
        "schema": "core.operad.evidence_trace.v1",
        "skill_name": SKILL,
        "signature": "(Receipt) -> Diagram",
        "authority_effect": "None",
        "runs": [],
        "total_runs": 0,
        "contractive_runs": 0,
        "required_contractive_runs": 3,
        "residual_evidence_bar_satisfied": False,
    }
    encoded = (json.dumps(payload) + "\n").encode("utf-8")
    for host in hosts:
        path = root / host / "skills" / SKILL / "evidence_trace.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(encoded)
    return encoded


def test_valid_ledger_without_mirror_directories_refuses_before_evaluation(
    configured_root: Path,
) -> None:
    _ledger(configured_root, (".agents",))
    engine = build_meta_operad_engine(configured_root)
    evaluator = ForbiddenEvaluator()
    engine.evaluator = evaluator
    result = engine.execute_morphism(SKILL, ["receipt.json"], agent_id="fixture")
    assert result.is_err
    assert result.error.code == "TRACE_LEDGER_ERROR"
    assert not evaluator.called


def test_partial_host_replace_restores_prior_ledgers(
    configured_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hosts = (".agents", ".claude", ".codex", ".grok")
    original = _ledger(configured_root, hosts)
    calls = {"count": 0}
    real_replace = os.replace

    def fail_on_second(source: str, destination: str) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("injected mirror replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(trace_storage_module.os, "replace", fail_on_second)
    record = ExecutionRunRecord(
        "2026-10-05T00:00:00+00:00",
        SKILL,
        ("Receipt",),
        "Diagram",
        ("receipt.json",),
        ArtifactOutput("out.json", "a" * 64),
        1,
        0,
        -1,
        True,
        0,
    )
    with pytest.raises(trace_storage_module.TraceLedgerStorageError):
        FileTraceStorage(configured_root).append_run(SKILL, record, "(Receipt) -> Diagram")
    for host in hosts:
        directory = configured_root / host / "skills" / SKILL
        assert [path.name for path in directory.iterdir()] == ["evidence_trace.json"]
        assert (directory / "evidence_trace.json").read_bytes() == original


class RecordingEvaluator:
    def __init__(self, digest: str) -> None:
        self.digest = digest
        self.called = False

    def is_bound(self, skill_id: str) -> bool:
        return True

    def evaluate(self, skill_id: str, inputs: list[str], output_hint: str | None = None) -> Ok:
        self.called = True
        return Ok(EvaluationOutcome(2, 1, "out.json", self.digest, 0))


def test_successful_append_writes_the_same_ledger_to_every_host(configured_root: Path) -> None:
    hosts = (".agents", ".claude", ".codex", ".grok")
    _ledger(configured_root, hosts)
    body = b"observed-artifact"
    digest = hashlib.sha256(body).hexdigest()
    (configured_root / "out.json").write_bytes(body)
    engine = build_meta_operad_engine(configured_root)
    evaluator = RecordingEvaluator(digest)
    engine.evaluator = evaluator
    result = engine.execute_morphism(SKILL, ["receipt.json"], agent_id="fixture")
    assert result.is_ok
    assert evaluator.called
    bodies = [
        (configured_root / host / "skills" / SKILL / "evidence_trace.json").read_bytes()
        for host in hosts
    ]
    assert len(set(bodies)) == 1
    reloaded = FileTraceStorage(configured_root).load_trace(SKILL)
    assert reloaded.total_runs == 1
    assert reloaded.runs[0].contractive
    assert reloaded.runs[0].residual_delta == -1


def test_zero_residual_change_does_not_count_as_contraction(configured_root: Path) -> None:
    operation = build_meta_operad_engine(configured_root).resolve_operation(SKILL)
    morphism = OperadMorphism(operation)
    record = morphism.complete_run(
        ["receipt.json"], "out.json", "a" * 64, 0, 0, 0, timestamp="2026-10-05T00:00:00+00:00"
    )
    assert not record.contractive
    assert record.residual_delta == 0



def test_actual_meta_skill_runner_reports_not_executable_from_current_registry():
    import subprocess
    import sys
    from operads.infrastructure.ddc_execution.runtime import find_repo_root
    root=find_repo_root()
    script=root/".agents/skills/meta-goo-proof-to-audit-verifier/scripts/execute.py"
    result=subprocess.run([sys.executable,str(script)],cwd=root,capture_output=True,text=True,timeout=30)
    assert result.returncode != 0
    assert "NOT_EXECUTABLE" in result.stdout+result.stderr
    assert "OPERAD_REGISTRY_INVALID" not in result.stdout+result.stderr


def test_empty_agent_registry_is_not_execution_authority(configured_root):
    path=configured_root/"operads/skill_operad/json/agent_capability_slices.json"
    path.write_text('{"agents": {}}',encoding="utf8")
    engine=build_meta_operad_engine(configured_root)
    unavailable=engine.execute_morphism(SKILL,[])
    assert unavailable.error.code=="NOT_EXECUTABLE"
    evaluator=ForbiddenEvaluator()
    engine.evaluator=evaluator
    for agent in (None,"unknown"):
        result=engine.execute_morphism(SKILL,["receipt.json"],agent_id=agent)
        assert result.error.code=="PERMISSION_DENIED"
    assert not evaluator.called
