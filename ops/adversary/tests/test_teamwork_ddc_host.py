"""Actual native custody and durable host admission, with offline PFP fixtures."""

import hashlib
import json
import sqlite3
import sys
import tempfile

import pytest

from adversary.infrastructure.teamwork_intelligence_host import (
    admitted_recheck,
    bind_acceptance,
    bind_episode_admission,
    execute_host_action,
    validate_ddc_context,
)
from adversary.infrastructure.teamwork_panel import create_teamwork_run
from adversary.tests.teamwork_support import role_observation
from adversary.use_cases.teamwork import next_action, observe
from adversary.use_cases.teamwork_pfp import check_teamwork_reply, prepare_teamwork_turn


@pytest.fixture(autouse=True)
def native_writable_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


def test_original_infrastructure_pfp_imports_are_exact_owner_operations():
    from adversary.infrastructure import teamwork_pfp as public_adapter
    from adversary.use_cases.teamwork import TeamworkAction

    assert public_adapter.prepare_teamwork_turn is prepare_teamwork_turn
    assert public_adapter.check_teamwork_reply is check_teamwork_reply
    assert public_adapter.TeamworkAction is TeamworkAction
    from adversary.use_cases.teamwork import TeamworkObservation
    assert public_adapter.TeamworkObservation is TeamworkObservation
    action = TeamworkAction(action_id="old-import-path", kind="build", objective="Fixture task", instructions="Return fixture text")
    turn = public_adapter.prepare_teamwork_turn(action)
    raw = json.dumps({**{key: turn.binding[key] for key in (
        "task_id", "attempt_id", "input_sha256")}, "answer": "Offline fixture proposal"}).encode()
    result = public_adapter.check_teamwork_reply(action, turn, raw, worker="offline characterization")
    assert result.content == "Offline fixture proposal" and not result.blocked


def prepared(tmp_path, *, candidate="accepted", max_repairs=1):
    artifact, checker, counted = tmp_path / "candidate.txt", tmp_path / "checker.py", tmp_path / "count.txt"
    artifact.write_text(candidate, encoding="utf-8")
    checker.write_text("from pathlib import Path\nimport sys\n"
        "p = Path(sys.argv[2])\np.write_text(p.read_text() + 'x' if p.exists() else 'x')\n"
        "raise SystemExit(Path(sys.argv[1]).read_text() != 'accepted')\n", encoding="utf-8")
    requirement = bind_acceptance("file-content.v1", (sys.executable, str(checker), str(artifact), str(counted)),
                                  source_paths=(checker,))
    run = create_teamwork_run("Create the accepted text", historical_v3=True, run_id="real-native-ddc",
                              acceptance_check=requirement, max_actions=64, max_repairs=max_repairs)
    run = run.model_copy(update={"episode_binding": bind_episode_admission(run, tmp_path / "episodes.sqlite3")})
    while (action := next_action(run)).kind != "recheck":
        hashes = {str(artifact): hashlib.sha256(artifact.read_bytes()).hexdigest()} if action.kind == "build" else None
        run = observe(run, role_observation(action, content=candidate, artifacts=hashes))
    return run, artifact, checker, counted


def stored(tmp_path):
    run, artifact, checker, counted = prepared(tmp_path)
    run = observe(run, admitted_recheck(run, next_action(run)))
    action = next_action(run)
    assert action.kind == "ddc_store"
    run = observe(run, execute_host_action(run, action, output_dir=tmp_path / "native"))
    assert next_action(run).role_id == "scar_chronicler"
    return run, artifact, checker, counted


def test_actual_native_store_checked_pfp_consumption_and_final_readback(tmp_path):
    run, artifact, _, counted = stored(tmp_path)
    action = next_action(run)
    program = validate_ddc_context(action)
    assert [step["letter"] for step in program["steps"]] == ["C", "R", "I", "T"]
    assert program["mathematical_acceptance"] == "UNVERIFIED"
    turn = prepare_teamwork_turn(action)
    assert action.ddc_program.binding.semantic_ddc_root in turn.prompt.user
    run = observe(run, role_observation(action))
    action = next_action(run)
    assert action.kind == "ddc_complete"
    final = execute_host_action(run, action, output_dir=tmp_path / "native")
    assert final.metadata["native_sealed_readback"] and final.metadata["final_current_source_checked"]
    run = observe(run, final)
    assert run.work_status == "completed" and run.evidence_verdict == "OPEN_RESIDUAL"
    assert artifact.read_text() == "accepted" and counted.read_text() == "x"
    assert len(list((tmp_path / "native" / "runs").iterdir())) == 2
    assert final.ddc_program.binding.completed_stages == () and final.ddc_program.binding.mode_ids == ()
    assert final.ddc_program.steps[1]["observed_procedure"]["observation_count"] == len(run.observations) - 1
    from pathlib import Path
    sealed = json.loads((Path(final.ddc_program.run_path) / "summary.json").read_bytes())["retained_context"]
    learning = next(item for item in sealed["observations"] if item["metadata"].get("role_id") == "scar_chronicler")
    assert learning["metadata"]["pfp"]["raw_reply_base64"]
    assert learning["metadata"]["consumed_ddc_root"]


@pytest.mark.parametrize("changed", ["candidate", "checker", "trace", "premises"])
def test_current_source_checker_candidate_and_premise_changes_refuse_reuse(tmp_path, changed):
    run, artifact, checker, _ = stored(tmp_path)
    action = next_action(run)
    if changed == "candidate":
        artifact.write_text("regressed")
    elif changed == "checker":
        checker.write_text("raise SystemExit(0)")
    elif changed == "trace":
        from pathlib import Path
        trace = Path(action.ddc_program.run_path) / "ddc.jsonl"
        trace.write_bytes(trace.read_bytes() + b" ")
    else:
        action = action.model_copy(update={"initial_task_id": "transplanted-task"})
    with pytest.raises(ValueError, match="(ARTIFACT_CHANGED|DDC_PROGRAM_CUSTODY_REFUSED|DDC_REUSE_PREMISES_MISMATCH)"):
        validate_ddc_context(action)


def test_typed_learning_cannot_omit_or_transplant_consumed_procedure(tmp_path):
    run, _, _, _ = stored(tmp_path)
    action = next_action(run)
    turn = prepare_teamwork_turn(action)
    fields = {key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
    answer = dict(summary="Scoped lesson", findings=[], lessons=[], no_change_reason="Existing guidance covers it.")
    assert check_teamwork_reply(action, turn, json.dumps({**fields, "answer": answer}).encode(), worker="IDE").blocked
    answer.update(consumed_ddc_root="a" * 64, consumed_procedure_sha256=action.ddc_program.procedure_sha256)
    assert check_teamwork_reply(action, turn, json.dumps({**fields, "answer": answer}).encode(), worker="IDE").blocked


def test_durable_admission_recovers_observed_check_without_repeating_subprocess(tmp_path):
    run, _, _, counted = prepared(tmp_path)
    action = next_action(run)
    first = admitted_recheck(run, action)
    assert first.check.exit_status == 0
    assert admitted_recheck(run, action) == first
    assert counted.read_text() == "x"
    ledger = tmp_path / "episodes.sqlite3"
    ledger.unlink()
    with pytest.raises(ValueError, match="EPISODE_LEDGER_MISSING"):
        admitted_recheck(run, action)
    assert counted.read_text() == "x"


@pytest.mark.parametrize("interrupted", [False, True])
def test_round_eleven_and_ambiguous_recovery_stop_before_dispatch(tmp_path, interrupted):
    run, _, _, counted = prepared(tmp_path)
    action = next_action(run)
    with sqlite3.connect(run.episode_binding["path"]) as ledger:
        if interrupted:
            ledger.execute("INSERT INTO episodes (action_id, ordinal) VALUES (?, 1)", (action.action_id,))
        else:
            ledger.executemany("INSERT INTO episodes (action_id, ordinal) VALUES (?, ?)",
                               [(f"retained-{i}", i) for i in range(1, 11)])
    with pytest.raises(ValueError, match="EPISODE_RECONCILIATION_REQUIRED" if interrupted else "EVALUATION_LIMIT"):
        admitted_recheck(run, action)
    assert not counted.exists()


def test_native_store_failure_cannot_advance_to_learning(tmp_path, monkeypatch):
    from operations.domain.rop.result import Err, Refusal
    from adversary.use_cases import skill_run_persistence

    run, _, _, _ = prepared(tmp_path)
    run = observe(run, admitted_recheck(run, next_action(run)))
    action = next_action(run)
    monkeypatch.setattr(skill_run_persistence, "persist_skill_run", lambda *a, **k:
                        Err(Refusal("HOST_UNAVAILABLE", "offline injected refusal", __name__)))
    with pytest.raises(ValueError, match="DDC_PROGRAM_PERSIST_FAILED: HOST_UNAVAILABLE"):
        execute_host_action(run, action, output_dir=tmp_path / "native")
    assert next_action(run) == action and action.kind == "ddc_store"


def test_repeated_same_native_storage_action_recovers_original_bound_bytes(tmp_path):
    from pathlib import Path

    run, _, _, _ = prepared(tmp_path)
    run = observe(run, admitted_recheck(run, next_action(run)))
    action = next_action(run)
    first = execute_host_action(run, action, output_dir=tmp_path / "native")
    path = Path(first.ddc_program.run_path)
    original = {entry.name: entry.read_bytes() for entry in path.iterdir()}
    recovered = execute_host_action(run, action, output_dir=tmp_path / "native")
    assert recovered == first
    assert {entry.name: entry.read_bytes() for entry in path.iterdir()} == original


def test_coherently_rehashed_retained_raw_context_is_rejected(tmp_path):
    from pathlib import Path

    run, _, _, _ = stored(tmp_path)
    action = next_action(run)
    path = Path(action.ddc_program.run_path)
    summary, receipt = json.loads((path / "summary.json").read_bytes()), json.loads((path / "receipt.json").read_bytes())
    summary["retained_context"]["observations"][1]["findings"] = ["Injected different dissent"]
    raw = json.dumps(summary, indent=2).encode()
    (path / "summary.json").write_bytes(raw)
    receipt["summary_sha256"] = hashlib.sha256(raw).hexdigest()
    (path / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="DDC_PROGRAM_CONTEXT_MISMATCH"):
        validate_ddc_context(action)


def test_failed_original_check_still_seals_and_consumes_learning_without_success(tmp_path):
    run, artifact, _, _ = prepared(tmp_path, candidate="wrong", max_repairs=0)
    run = observe(run, admitted_recheck(run, next_action(run)))
    action = next_action(run)
    assert action.kind == "ddc_store" and action.stopped_status == "partial"
    before = artifact.read_bytes()
    run = observe(run, execute_host_action(run, action, output_dir=tmp_path / "native"))
    run = observe(run, role_observation(next_action(run)))
    run = observe(run, execute_host_action(run, next_action(run), output_dir=tmp_path / "native"))
    assert run.work_status == "partial" and next_action(run) is None
    assert artifact.read_bytes() == before
    assert run.continuation_status["open_findings"]
    assert any(item.metadata.get("role_id") == "scar_chronicler" and not item.blocked for item in run.observations)


def test_public_v3_recheck_cannot_dispatch_without_durable_run_binding(tmp_path):
    from adversary.infrastructure.teamwork_intelligence_host import recheck

    run, _, _, counted = prepared(tmp_path)
    with pytest.raises(ValueError, match="EPISODE_ADMISSION_REQUIRED"):
        recheck(next_action(run))
    assert not counted.exists()


def test_observed_evaluator_exception_is_retained_and_can_finish(tmp_path):
    run, _, _, _ = prepared(tmp_path)
    def unavailable(action):
        raise RuntimeError("Observed fixture evaluator outage")
    result = admitted_recheck(run, next_action(run), evaluator=unavailable)
    assert result.blocked and result.metadata["failure_code"] == "CHECK_UNAVAILABLE"
    assert admitted_recheck(run, next_action(run)) == result
    run = observe(run, result)
    assert next_action(run).kind == "ddc_store"
