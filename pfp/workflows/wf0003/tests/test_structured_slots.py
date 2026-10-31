"""Keyed-slot transport, exact native bindings and bounded mining reuse."""

import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from pfp.infrastructure.adapters.pfp_campaign import digest, write_new
from pfp.workflows.wf0003 import runner, workflow
from pfp.workflows.wf0003.structured import wire_schema
from pfp.workflows.wf0003.tests.test_wf0003 import (
    attachment,
    factory_for,
    reply,
    solver_answer,
)


@pytest.fixture
def spec():
    return json.loads(workflow.resource_text("examples/integer_sum.task.json"))


def test_wire_schema_resolves_references_and_keeps_all_keyed_slots(spec):
    contract = workflow.SolverContract(attachment(spec))
    turn = contract.prepare_task(spec)
    schema = wire_schema(turn.prompt.response_schema)
    Draft202012Validator.check_schema(schema)
    candidate = json.loads(reply(turn, solver_answer()))
    Draft202012Validator(schema).validate(candidate)
    assert len(schema["properties"]["answer"]["properties"]["slot_report"]["required"]) == 31
    assert (
        len(contract.check_reply(spec, reply(turn, solver_answer()))["answer"]["slot_report"]) == 31
    )


def test_a_missing_key_is_not_an_accepted_shorter_slot_list(spec):
    contract = workflow.SolverContract(attachment(spec))
    answer = solver_answer()
    del answer["slot_report"]["carrier"]
    assert not contract.check_reply(spec, reply(contract.prepare_task(spec), answer))[
        "schema_valid"
    ]


@pytest.mark.parametrize("remaining,expected_calls", [(100, 1), (1, 0)])
def test_reusing_actual_mining_sends_only_one_bounded_solver_action(
    tmp_path, spec, remaining, expected_calls
):
    source = tmp_path / "original"
    runner.run(spec, source, "fixture/model", factory_for([]))
    write_new(
        source / "historical_evidence_manifest.json",
        {"files": {"mining/response.raw": digest((source / "mining/response.raw").read_bytes())}},
    )
    calls = []
    root = tmp_path / "continuation"
    result = runner.run(
        spec,
        root,
        "fixture/model",
        factory_for(calls),
        mining_capture=source,
        remaining_repair_microusd=remaining,
    )
    assert len(calls) == expected_calls
    if expected_calls:
        assert result["status"] == "HOST_ACCEPTED" and result["new_provider_calls"] == 1
        assert result["cost_usd"] == 0.000001 and result["mining_reused"]
        assert calls[0]["attempt_id"] == "wf0003-solver-1"
        assert runner.replay_run(root)["replay_verified"]
        assert (root / "solver/repair_budget_preflight.json").exists()
    else:
        assert result["failure_class"] == "WF3_REPAIR_REMAINING_BUDGET"
        assert result["confirmed_provider_calls"] == 0


def test_a_49_character_explanation_does_not_reject_correct_typed_work(spec):
    contract = workflow.SolverContract(attachment(spec))
    answer = solver_answer()
    answer["slot_report"]["intermediate_bindings"] = dict(
        disposition="not_applicable",
        value="",
        reason="No intermediate bindings required for integer sum",
    )
    assert (
        contract.check_reply(spec, reply(contract.prepare_task(spec), answer))["status"]
        == "HOST_ACCEPTED"
    )


def test_task_policy_preserves_policy_identity_and_explicit_host_boundary(spec):
    contract = workflow.SolverContract(attachment(spec))
    policy = json.loads(contract.prepare_task(spec).prompt.system.split("\n", 1)[0])
    original = yaml.safe_load(workflow.basic_task_template("").system)
    assert policy["policy_id"] == original["semantic_policy_manifest"]["policy_id"]
    assert policy["authority_effect"] == "None" and policy["profile"] == "bounded_task_turn"
    assert "Untrusted proposal; host verifies." in policy["rules"]
