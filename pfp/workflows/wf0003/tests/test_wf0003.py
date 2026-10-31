"""WF3 pre-mining, answer isolation, shared budgeting and lineage controls."""

import base64
import json
from copy import deepcopy

import pytest

from operations.domain.rop.result import Ok
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest
from pfp.infrastructure.workflow_accounting import EstimatedBudgetGateway
from pfp.workflows.wf0002.tests.test_wf0002 import candidate as wf2_answer
from pfp.workflows.wf0003 import runner, workflow
from adversary.domain.providers.attempt import AdmittedRequest, CompletionOutcome
from adversary.domain.providers.types import CandidateResponse, Provider


@pytest.fixture
def spec():
    return json.loads(workflow.resource_text("examples/integer_sum.task.json"))


def mining_answer():
    return dict(
        operad_candidates=[
            dict(
                id="sum",
                operation="Sum the integer list without computing a result here.",
                source_colours=["IntegerList"],
                target_colour="Integer",
                arity=1,
                source=dict(kind="seed_prompt", quote="input.values"),
                witness_refs=["task_result"],
            )
        ],
        focus_slots=["concrete_spans", "parameter_bindings", "invariant_witnesses"],
        failure_triggers=["Reject floating point substitutes and preserve every input operand."],
        l2_guidance=[
            dict(
                slot=slot,
                source=dict(kind="seed_prompt", quote="input.values"),
                guidance="Bind the entire public signed integer list exactly once without rounding.",
            )
            for slot in sorted(workflow.SUM_L2)
        ],
    )


def solver_answer():
    answer = wf2_answer()
    answer["operad_candidates"] = deepcopy(mining_answer()["operad_candidates"])
    values = [17, 25, -4]
    bindings = dict(
        concrete_spans=dict(source="input.values", literal=values),
        parameter_bindings=dict(values=values, arithmetic="integer_exact"),
        instantiated_arguments=dict(operad_id="sum", arguments=values),
        preservation_obligations=dict(
            all_operands_once=True, signed_integers=True, rounding="forbidden"
        ),
    )
    for row in answer["slot_report"]:
        if row["slot"] in bindings:
            row["value"] = bindings[row["slot"]]
        row["reason"] = ""
    answer["slot_report"] = {row.pop("slot"): row for row in answer["slot_report"]}
    return answer


def reply(turn, answer):
    return json.dumps(
        {
            **{k: turn.binding[k] for k in ("task_id", "attempt_id", "input_sha256")},
            "answer": answer,
        },
        ensure_ascii=False,
    ).encode()


def attachment(spec):
    turn = workflow.MiningContract.prepare_task(spec)
    raw = reply(turn, mining_answer())
    checked = workflow.MiningContract.check_reply(spec, raw)
    screen = workflow.screen_mining(spec, raw, checked)
    assert screen["accepted"]
    return workflow.freeze_attachment(raw, checked, screen)


def factory_for(calls, *, bad_mining=False, unknown_cost=False, quote="input.values"):
    def factory(root, model, tokens):
        class Scripted:
            unbudgeted_max_output_tokens = tokens

            def complete_result(self, request, **options):
                from adversary.domain.providers.types import thaw_json

                expected_format = (
                    "json_object"
                    if json.loads(request.user)["attempt_id"] == workflow.MiningContract.ATTEMPT_ID
                    else "json_schema"
                )
                assert thaw_json(request.decoding.response_format)["type"] == expected_format
                with gateway.ledger.transaction(gateway.limit) as state:
                    assert any(row["state"] == "reserved" for row in state["attempts"].values())
                public = json.loads(request.user)
                calls.append(public)
                is_miner = public["attempt_id"] == workflow.MiningContract.ATTEMPT_ID
                answer = mining_answer() if is_miner else solver_answer()
                if is_miner:
                    answer["operad_candidates"][0]["source"]["quote"] = quote
                    if bad_mining:
                        answer["operad_candidates"][0]["operation"] = "The result is 38."
                content = json.dumps(
                    {
                        **{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
                        "answer": answer,
                    }
                )
                wire = json.dumps(
                    dict(
                        id=f"fixture-{len(calls)}",
                        choices=[dict(message=dict(content=content))],
                        usage=dict(
                            prompt_tokens=15,
                            completion_tokens=25,
                            cost=None if unknown_cost else 0.000001,
                        ),
                    )
                ).encode()
                c = CandidateResponse(
                    content,
                    model,
                    "openrouter",
                    input_tokens=15,
                    output_tokens=25,
                    cost_usd=None if unknown_cost else 0.000001,
                    generation_id=f"fixture-{len(calls)}",
                    transport="fixture",
                )
                admitted = AdmittedRequest(
                    f"fixture-{len(calls)}",
                    "",
                    "",
                    Provider.OPENROUTER,
                    model,
                    request,
                    tokens,
                    None,
                    None,
                )
                return Ok(CompletionOutcome(c, admitted, reply_bytes=wire))

        gateway = EstimatedBudgetGateway(
            Scripted(),
            model=model,
            price=dict(
                catalog_sha256="fixture",
                row=dict(id=model, pricing={"prompt": "0.000000001", "completion": "0.000000001"}),
            ),
            limit_microusd=json.loads((root / "plan.json").read_text())[
                "estimated_run_cap_microusd"
            ],
            max_calls=json.loads((root / "plan.json").read_text())["maximum_new_provider_calls"],
            accounting_path=root / "accounting.sqlite3",
            run_id="test-wf3:" + root.name,
            objective_sha256=digest(canonical(json.loads((root / "task.json").read_text()))),
            max_output_tokens=tokens,
        )
        return gateway

    return factory


def test_miner_cannot_see_or_solve_with_host_answers(spec):
    spec["checker"] = "schema_only"
    spec["input"]["expected_answer"] = "HIDDEN_ORACLE"
    turn = workflow.MiningContract.prepare_task(spec)
    assert "HIDDEN_ORACLE" not in turn.prompt.user + turn.prompt.system
    assert "Do not solve" in turn.prompt.system
    assert "task_result" not in turn.prompt.response_schema["properties"]["answer"]["properties"]


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("answer_digits", "NUMERICAL"),
        ("bad_arity", "SCHEMA"),
        ("bad_source", "SOURCE"),
        ("duplicate", "DUPLICATE"),
        ("bad_witness", "WITNESS"),
    ],
)
def test_mining_screen_rejects_bad_candidates(spec, mutation, reason):
    answer = mining_answer()
    if mutation == "answer_digits":
        answer["operad_candidates"][0]["operation"] = "The total is 38"
    elif mutation == "bad_arity":
        answer["operad_candidates"][0]["arity"] = 2
    elif mutation == "bad_source":
        answer["operad_candidates"][0]["source"]["quote"] = "not in the seed"
    elif mutation == "duplicate":
        answer["operad_candidates"].append(deepcopy(answer["operad_candidates"][0]))
    else:
        answer["operad_candidates"][0]["witness_refs"] = ["invented"]
    raw = reply(workflow.MiningContract.prepare_task(spec), answer)
    checked = workflow.MiningContract.check_reply(spec, raw)
    assert checked["schema_valid"] is (mutation != "bad_arity")
    result = workflow.screen_mining(spec, raw, checked)
    assert not result["accepted"] and any(reason in error for error in result["errors"])


def test_attachment_is_bound_to_solver_request_without_changing_original_task(spec):
    frozen = attachment(spec)
    contract = workflow.SolverContract(frozen)
    turn = contract.prepare_task(spec)
    public = json.loads(turn.prompt.user)
    assert public["objective"] == spec["seed_prompt"]
    assert public["input"]["values"] == spec["input"]["values"]
    assert public["input"]["pfp_mined_attachment"] == workflow.solver_attachment(frozen)
    assert public["input"]["pfp_mined_attachment"]["sha256"] == frozen["sha256"]
    assert len(workflow.operad_codec.catalogue()["slots"]) == 31
    result = contract.check_reply(spec, reply(turn, solver_answer()))
    assert result["status"] == "HOST_ACCEPTED" and result["operad_structure_valid"]
    changed = deepcopy(frozen)
    changed["payload"]["failure_triggers"] = ["Changed guidance."]
    changed["sha256"] = digest(canonical(changed["payload"]))
    assert (
        workflow.SolverContract(changed).prepare_task(spec).binding["input_sha256"]
        != turn.binding["input_sha256"]
    )


def test_attachment_digest_refuses_a_changed_byte(spec):
    frozen = attachment(spec)
    frozen["payload"]["focus_slots"].append("carrier")
    with pytest.raises(ValueError, match="ATTACHMENT_DIGEST"):
        workflow.SolverContract(frozen)


def test_correct_sum_cannot_hide_missing_required_solver_slots(spec):
    answer = solver_answer()
    for slot, row in answer["slot_report"].items():
        if slot in {"carrier", "equality_policy", "terminal"}:
            row.update(disposition="not_applicable", value="", reason="Not required")
    contract = workflow.SolverContract(attachment(spec))
    checked = contract.check_reply(spec, reply(contract.prepare_task(spec), answer))
    assert not checked["schema_valid"] and not checked["operad_structure_valid"]
    assert checked["failure_class"] == "TASK_ENVELOPE"


@pytest.mark.parametrize(
    "mutation",
    ["wrong_operand", "float_operand", "generic_text", "unknown_operation", "numeric_boolean"],
)
def test_correct_total_does_not_bypass_task_grounded_l2(spec, mutation):
    answer = solver_answer()
    slot = "preservation_obligations" if mutation == "numeric_boolean" else "instantiated_arguments"
    row = answer["slot_report"][slot]
    data = deepcopy(row["value"])
    if mutation == "wrong_operand":
        data["arguments"][-1] = -3
    elif mutation == "float_operand":
        data["arguments"][0] = 17.0
    elif mutation == "unknown_operation":
        data["operad_id"] = "invented"
    elif mutation == "numeric_boolean":
        data["all_operands_once"] = 1
    row["value"] = "Finite integer task" if mutation == "generic_text" else data
    contract = workflow.SolverContract(attachment(spec))
    checked = contract.check_reply(spec, reply(contract.prepare_task(spec), answer))
    if checked["schema_valid"]:
        assert checked["task_status"] == "HOST_ACCEPTED"
        assert checked["l2_grounding_valid"] is False
        assert checked["failure_class"] == "WF3_L2_GROUNDING"
    else:
        assert checked["failure_class"] == "TASK_ENVELOPE"


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("missing", "SCHEMA"),
        ("source", "L2_SOURCE"),
        ("answer", "NUMERICAL"),
        ("duplicate", "DUPLICATE_L2"),
    ],
)
def test_mined_l2_requires_grounded_answer_free_task_coverage(spec, mutation, reason):
    answer = mining_answer()
    if mutation == "missing":
        answer["l2_guidance"].pop()
    elif mutation == "source":
        answer["l2_guidance"][0]["source"]["quote"] = "not a real input span"
    elif mutation == "answer":
        answer["l2_guidance"][0]["guidance"] = "The answer is 38"
    else:
        answer["l2_guidance"][1] = deepcopy(answer["l2_guidance"][0])
    raw = reply(workflow.MiningContract.prepare_task(spec), answer)
    checked = workflow.MiningContract.check_reply(spec, raw)
    assert checked["schema_valid"] is (mutation != "missing")
    screened = workflow.screen_mining(spec, raw, checked)
    assert not screened["accepted"] and any(reason in err for err in screened["errors"])


def test_fences_remain_rejected_and_json_mode_is_in_the_actual_wire(tmp_path, spec):
    calls = []
    root = tmp_path / "json-mode"
    result = runner.run(spec, root, "fixture/model", factory_for(calls))
    for phase in result["phases"].values():
        wire = phase["provider"]["request"]
        assert wire["response_format"]["type"] in {"json_object", "json_schema"}
        assert wire["provider"] == {"allow_fallbacks": False, "require_parameters": True}
    contract = workflow.SolverContract(json.loads((root / "attachment.json").read_text()))
    raw = b"```json\n" + reply(contract.prepare_task(spec), solver_answer()) + b"\n```"
    assert contract.check_reply(spec, raw)["schema_valid"] is False
    assert result["l2_grounding_valid"] and len(result["l2_checked_slots"]) == 4


def test_original_input_cannot_override_host_attachment(spec):
    spec["checker"] = "schema_only"
    spec["input"]["pfp_mined_attachment"] = {"untrusted": True}
    with pytest.raises(ValueError, match="RESERVED_ATTACHMENT"):
        workflow.validate_task(spec)


def test_lower_campaign_allowance_is_shared_without_reset(tmp_path, spec):
    calls = []
    result = runner.run(
        spec, tmp_path / "lower", "fixture/model", factory_for(calls), budget_microusd=4828
    )
    assert len(calls) == 2
    assert result["shared_estimated_run_cap_microusd"] == 4828
    assert all(
        p["provider"]["accounting_binding"]["limit_microusd"] == 4828
        for p in result["phases"].values()
    )


@pytest.mark.parametrize("amount", [5000, 0, -1, True, 4.5])
def test_budget_override_cannot_raise_allowance_or_coerce(tmp_path, spec, amount):
    with pytest.raises(ValueError, match="BUDGET_MUST_BE"):
        runner.prepare_run(spec, tmp_path / "invalid", amount)
    assert not (tmp_path / "invalid").exists()


def test_one_mining_call_and_one_solver_call_share_original_allowance_and_replay(tmp_path, spec):
    calls = []
    root = tmp_path / "complete"
    result = runner.run(spec, root, "fixture/model", factory_for(calls))
    assert len(calls) == 2 and result["new_provider_calls"] == 2
    assert result["status"] == "HOST_ACCEPTED" and result["cost_usd"] == 0.000002
    assert result["prompt_tokens"] == 30 and result["completion_tokens"] == 50
    assert result["mined_signature_reuse_ids"] == ["sum"]
    assert (
        result["reasoning_tokens"] is None
        and result["failure_observations"]["audited_hallucinations"] is None
    )
    assert (root / "accounting.sqlite3").exists()
    assert not (root / "solver" / "accounting.sqlite3").exists()
    before = {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".sqlite3" not in p.name
    }
    replay = runner.replay_run(root)
    assert replay["replay_verified"] and replay["provider_calls_in_this_command"] == 0
    assert len(calls) == 2
    assert before == {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".sqlite3" not in p.name
    }
    with pytest.raises(FileExistsError):
        runner.run(spec, root, "fixture/model", factory_for(calls))


@pytest.mark.parametrize("kind", ["screen", "cost"])
def test_bad_mining_or_unknown_billing_stops_before_solver(tmp_path, spec, kind):
    calls = []
    root = tmp_path / kind
    result = runner.run(
        spec,
        root,
        "fixture/model",
        factory_for(calls, bad_mining=kind == "screen", unknown_cost=kind == "cost"),
    )
    assert len(calls) == 1 and not (root / "solver").exists()
    assert result["status"] in {"TYPED_REFUSAL", "INFRASTRUCTURE_ERROR"}
    assert (root / "mining" / "response.raw").exists()


def test_attachment_change_cannot_be_rebound_after_mining(tmp_path, spec):
    calls = []
    root = tmp_path / "tamper"
    runner.run(spec, root, "fixture/model", factory_for(calls))
    changed = json.loads((root / "attachment.json").read_text())
    changed["payload"]["focus_slots"] = ["carrier"]
    changed["sha256"] = digest(canonical(changed["payload"]))
    (root / "attachment.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="DIGEST_MISMATCH"):
        runner.replay_run(root)
    with pytest.raises(ValueError, match="MINING_LINEAGE_MISMATCH"):
        runner._validate_frozen(root)


def test_malformed_miner_reply_is_not_repaired(spec):
    checked = workflow.MiningContract.check_reply(spec, b"not JSON")
    screened = workflow.screen_mining(spec, b"not JSON", checked)
    assert not screened["accepted"]
    assert base64.b64decode(checked["raw_reply_base64"]) == b"not JSON"


@pytest.mark.parametrize("key", ["lggr", "agents", "seed_rewrite", "maximum_retries"])
def test_wf3_rejects_later_workflow_switches(spec, key):
    spec[key] = True
    with pytest.raises(ValueError, match="WF3_INVALID_TASK"):
        workflow.validate_task(spec)
