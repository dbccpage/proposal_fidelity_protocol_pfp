"""Synthetic typed role replies for offline coordinator regression controls."""

import hashlib
import json

from adversary.infrastructure.teamwork_panel import run_syntax_prefilter_check
from adversary.use_cases.teamwork import (
    HostAcceptanceRequirement,
    IntelligenceRead,
    TaskCheck,
    TeamworkDdcProgram,
    TeamworkObservation,
    ddc_task_premises,
    next_action,
    observe,
)
from adversary.use_cases.teamwork_pfp import check_teamwork_reply, prepare_teamwork_turn


def role_observation(action, *, content="Fixture candidate", findings=(), blocked=False,
                     artifacts=None, metadata=None, intelligence=None):
    if blocked:
        return TeamworkObservation(action_id=action.action_id, worker="offline fixture host",
            summary="The required fixture operation is unavailable", findings=findings, blocked=True,
            artifacts=artifacts or {}, intelligence=intelligence,
            metadata={"role_id": action.role_id, "failure_code": "FIXTURE_UNAVAILABLE"})
    if action.communication == "deterministic":
        return run_syntax_prefilter_check(action)
    answer = content if action.kind in ("build", "repair") else {
        "summary": f"Observed fixture contribution from {action.role_id}", "findings": list(findings)}
    if action.kind == "learn":
        answer.update(lessons=["Preserve observations and recheck changed artifacts."],
            **(metadata or {"no_change_reason": "Existing guidance already covers this fixture."}))
        if action.workflow_version in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4"):
            answer.update(consumed_ddc_root=action.ddc_program.binding.semantic_ddc_root,
                consumed_procedure_sha256=action.ddc_program.procedure_sha256)
    turn = prepare_teamwork_turn(action)
    raw = json.dumps({**{key: turn.binding[key] for key in (
        "task_id", "attempt_id", "input_sha256")}, "answer": answer}).encode("utf-8")
    observed = check_teamwork_reply(action, turn, raw, worker="offline fixture host")
    return observed.model_copy(update={"artifacts": artifacts or {}, "intelligence": intelligence})


def submit_role(run, **kwargs):
    return observe(run, role_observation(next_action(run), **kwargs))


def advance_until(run, *, kind, artifacts=None, findings=()):
    """Run every intervening fixture role; no missing contribution is skipped."""
    while (action := next_action(run)) is not None and action.kind != kind:
        if action.communication == "host":
            raise AssertionError("The actual host checker must supply this observation")
        run = submit_role(run, artifacts=artifacts if action.kind in ("build", "repair") else None,
                          findings=findings if action.role_id == "defect_hunter" else ())
    assert next_action(run) is not None and next_action(run).kind == kind
    return run


def finish_learning(run):
    assert next_action(run).kind == "learn"
    return submit_role(run)


def fixture_acceptance():
    return HostAcceptanceRequirement(source_id="a" * 64, checker_id="fixture.independent.v1",
        operation=("fixture-original-check",))


def fixture_host_observation(action, *, findings=(), blocked=False):
    """Synthetic pure replay control; never a storage or subprocess execution claim."""
    from adversary.domain.prompt_family import DdcProgramBinding

    if blocked:
        return role_observation(action, findings=findings, blocked=True, artifacts=action.artifacts)
    metadata = {"role_id": action.role_id, "execution_kind": "host"}
    if action.kind == "recheck":
        return TeamworkObservation(action_id=action.action_id, worker="offline fixture host checker",
            summary="Synthetic independent check control", findings=findings, artifacts=action.artifacts,
            metadata=metadata, check=TaskCheck(initial_task_id=action.initial_task_id,
                source_id=action.check_source_id or action.intelligence.source_id,
                checker_id=action.checker_id, command=action.check_command,
                exit_status=1 if findings else 0, output_sha256="c" * 64, artifacts=action.artifacts))
    if action.kind in ("ddc_store", "ddc_complete"):
        premises = ddc_task_premises(action)
        def digest(value):
            return hashlib.sha256(json.dumps(value, sort_keys=True,
                separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        binding = DdcProgramBinding(family_id="adversary-teamwork-" + action.workflow_version.rsplit(".",1)[1], template_version=action.workflow_version,
            storage_task_key="pure-fixture", prompt_sha256=hashlib.sha256(action.objective.encode()).hexdigest(),
            premises_sha256=digest(premises), semantic_ddc_root="d" * 64,
            stage_artifacts_sha256=digest({}), mode_artifacts_sha256=digest({}))
        return TeamworkObservation(action_id=action.action_id, worker="offline fixture readback",
            summary="Synthetic retained DDC fixture control", artifacts=action.artifacts, metadata=metadata,
            intelligence=(IntelligenceRead(initial_task_id=action.initial_task_id,
                source_id="fixture-source", source_locator="pure-fixture-only")
                if action.feedback_policy and action.kind == "ddc_store" and action.intelligence is None else None),
            ddc_program=TeamworkDdcProgram(binding=binding, run_path="pure-fixture-only",
                source_id="fixture-source", premises=premises, steps=({"letter": "C"},)))
    if action.kind == "digest" and action.feedback_policy:
        return TeamworkObservation(action_id=action.action_id, worker="offline fixture digest",
            summary="Synthetic semantic readback fixture; no host operation executed", artifacts=action.artifacts,
            findings=findings, metadata=metadata, intelligence=IntelligenceRead(
                initial_task_id=action.initial_task_id, source_id="fixture-digest-" + action.action_id,
                source_locator="pure-fixture-digest-only", parent_source_id=action.intelligence.source_id,
                findings=findings))
    raise AssertionError("Supply the real digestion observation explicitly")
