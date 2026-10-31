"""Finite WF4 contracts, negative gluing witnesses, and genuine thread overlap."""

import json
from copy import deepcopy
from threading import Barrier, Lock

import pytest

from operations.domain.rop.result import Err, Ok
from pfp.infrastructure.adapters.pfp_campaign import canonical
from pfp.infrastructure.workflow_accounting import EstimatedBudgetGateway
from pfp.workflows.tests.fixtures import SPEC
from pfp.workflows.wf0003.tests.test_wf0003 import mining_answer, reply
from pfp.workflows.wf0004 import runner, workflow
from adversary.domain.providers.attempt import AdmittedRequest, CompletionOutcome
from adversary.domain.providers.types import CandidateRequest, CandidateResponse, Provider


def mined(spec=SPEC):
    turn = workflow.MiningContract.prepare_task(spec)
    answer = mining_answer()
    for op in answer["operad_candidates"]:
        op["source"]["quote"] = "exact sum"
    for item in answer["l2_guidance"]:
        item["source"]["quote"] = "exact sum"
    raw = reply(turn, answer)
    checked = workflow.MiningContract.check_reply(spec, raw)
    screen = workflow.wf3.screen_mining(spec, raw, checked)
    assert screen["accepted"], screen
    return workflow.wf3.freeze_attachment(raw, checked, screen)


def solver(spec=SPEC, i=1):
    attachment = mined(spec)
    return workflow.SolverContract(attachment, workflow.freeze_profile(spec, attachment), i)


def answer(contract, total=38):
    return dict(
        task_result=dict(total=total),
        profile_ref=contract.profile["sha256"],
        values=[17, 25, -4],
        operad_ids=["sum"],
        ddc_moves=[],
    )


def local(total=38):
    contract = solver()
    return contract.check_reply(SPEC, reply(contract.prepare_task(SPEC), answer(contract, total)))


def test_exact_five_and_no_answer_in_contract():
    contract = solver()
    turn = contract.prepare_task(SPEC)
    assert "38" not in turn.prompt.system
    assert '"total":38' not in turn.prompt.user
    assert "const" not in turn.task.answer_schema["properties"]["task_result"].get(
        "properties", {}
    ).get("total", {})
    assert len(contract.profile["payload"]["slot_report"]) == 31
    assert all(row["id"] in turn.prompt.system for row in workflow.codec.catalogue()["slots"])
    value = workflow.evaluate_global(SPEC, [local() for _ in range(5)])
    assert value["status"] == "HOST_ACCEPTED"
    assert value["lggr"]["gluing_defect_delta"] == 0
    assert not value["lggr"]["detector_adequacy_certified"]
    with pytest.raises(ValueError, match="FIVE"):
        workflow.evaluate_global(SPEC, [local()])


@pytest.mark.parametrize("totals", [[39] * 5, [38, 38, 38, 38, 39]])
def test_local_green_global_red_is_detected_even_with_unanimity(totals):
    checks = [local(n) for n in totals]
    assert all(row["local_green"] for row in checks)
    value = workflow.evaluate_global(SPEC, checks)
    assert not value["global_green"]
    assert value["lggr"]["gluing_defect_delta"] == -1


@pytest.mark.parametrize(
    "field,value",
    [
        ("values", []),
        ("values", [17.0, 25, -4]),
        ("profile_ref", "x" * 64),
        ("operad_ids", ["unknown"]),
        ("task_result", {"total": 38.0}),
        ("task_result", {"total": True}),
        ("ddc_moves", [{"op": "invented"}]),
    ],
)
def test_bad_bindings_and_native_types_fail_local(field, value):
    contract = solver()
    a = answer(contract)
    a[field] = value
    assert not contract.check_reply(SPEC, reply(contract.prepare_task(SPEC), a))["local_green"]


def test_reference_digest_and_unsupported_scope_fail_before_dispatch():
    c = solver()
    bad = deepcopy(c.profile)
    bad["payload"]["slot_report"]["carrier"]["value"] = "Float"
    with pytest.raises(ValueError, match="DIGEST"):
        workflow.SolverContract(c.attachment, bad, 1)
    spec = deepcopy(SPEC)
    spec["checker"] = "schema_only"
    with pytest.raises(ValueError, match="INTEGER_SUM"):
        workflow.validate_task(spec)


def scripted_factory(calls, *, wrong=False, unknown=False):
    barrier, lock = Barrier(5), Lock()

    def factory(root, model, tokens):
        class Scripted:
            unbudgeted_max_output_tokens = tokens

            def complete_result(self, request, **options):
                public = json.loads(request.user)
                miner = public["attempt_id"] == workflow.MiningContract.ATTEMPT_ID
                if not miner:
                    with bound.ledger.transaction(bound.limit) as state:
                        # Every reservation exists before any solver provider is invoked.
                        assert len(state["attempts"]) == 6
                    barrier.wait(timeout=10)
                with lock:
                    calls.append(public["attempt_id"])
                    generation = f"fixture-{len(calls)}"
                if miner:
                    a = mining_answer()
                    a["operad_candidates"][0]["source"]["quote"] = "exact sum"
                    for row in a["l2_guidance"]:
                        row["source"]["quote"] = "exact sum"
                else:
                    context = public["input"]
                    a = dict(
                        task_result=dict(total=39 if wrong else 38),
                        profile_ref=context["profile_ref"],
                        values=context["values"],
                        operad_ids=[context["mined"]["operads"][0]["id"]],
                        ddc_moves=[],
                    )
                content = workflow.compact(
                    {
                        **{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
                        "answer": a,
                    }
                )
                cost = None if unknown else 0.000001
                wire = canonical(
                    dict(
                        id=generation,
                        choices=[dict(message=dict(content=content), finish_reason="stop")],
                        usage=dict(prompt_tokens=15, completion_tokens=25, cost=cost),
                    )
                )
                candidate = CandidateResponse(
                    content,
                    model,
                    "openrouter",
                    input_tokens=15,
                    output_tokens=25,
                    cost_usd=cost,
                    generation_id=generation,
                    transport="fixture",
                )
                admitted = AdmittedRequest(
                    generation, "", "", Provider.OPENROUTER, model, request, tokens, None, None
                )
                return Ok(CompletionOutcome(candidate, admitted, reply_bytes=wire))

        bound = EstimatedBudgetGateway(
            Scripted(),
            model=model,
            price=dict(
                catalog_sha256="fixture",
                row=dict(id=model, pricing={"prompt": "0.0000001", "completion": "0.00000032"}),
            ),
            limit_microusd=runner.read(root / "plan.json")["estimated_run_cap_microusd"],
            max_calls=6,
            accounting_path=root / "accounting.sqlite3",
            run_id="wf0004:" + root.resolve().name,
            objective_sha256=workflow.digest(canonical(SPEC)),
            max_output_tokens=tokens,
        )
        return bound

    return factory


def test_shared_six_action_run_concurrent_and_readonly_replay(tmp_path):
    calls = []
    root = tmp_path / "run"
    result = runner.run(SPEC, root, gateway_factory=scripted_factory(calls))
    assert result["status"] == "HOST_ACCEPTED", result
    assert len(calls) == len(set(calls)) == 6
    assert result["concurrency"]["peak_in_flight"] == 5
    assert result["emitted_operad_references"] == 5 and result["newly_emitted_operads"] == 0
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert runner.replay_run(root)["replay_verified"]
    assert before == {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    (root / "agent-4/response.raw").write_bytes(b"{}")
    with pytest.raises(ValueError, match="DIGEST"):
        runner.replay_run(root)


def test_unknown_mining_billing_stops_all_five(tmp_path):
    calls = []
    result = runner.run(
        SPEC, tmp_path / "unknown", gateway_factory=scripted_factory(calls, unknown=True)
    )
    assert result["status"] == "INFRASTRUCTURE_ERROR" and len(calls) == 1


def test_batch_budget_refusal_is_atomic_and_keeps_original_allowance(tmp_path):
    from pfp.workflows.tests.gateways import gateway

    bound, provider = gateway(tmp_path, limit=10, max_calls=5)
    requests = {f"a{i}": CandidateRequest("x" * 1000, "y") for i in range(5)}
    stopped = bound.complete_batch_result(
        requests, provider=Provider.OPENROUTER, model="vendor/model"
    )
    assert isinstance(stopped, Err) and not provider.calls
    with bound.ledger.transaction(bound.limit) as state:
        assert not state["attempts"] and state["spent"] == 0


def test_batch_unknown_liability_blocks_later_actions_and_duplicate_ids(tmp_path):
    from pfp.workflows.tests.gateways import gateway

    bound, provider = gateway(tmp_path, cost=None, limit=100, max_calls=5)
    requests = {"first": CandidateRequest("s", "u")}
    assert isinstance(
        bound.complete_batch_result(requests, provider=Provider.OPENROUTER, model="vendor/model"),
        Ok,
    )
    assert (
        bound.for_action("second")
        .complete_result(
            CandidateRequest("s", "u"), provider=Provider.OPENROUTER, model="vendor/model"
        )
        .error.code
        == "UNRECONCILED_ATTEMPT"
    )
    assert (
        bound.complete_batch_result(
            requests, provider=Provider.OPENROUTER, model="vendor/model"
        ).error.code
        == "PFP_ACTION_ALREADY_CLAIMED"
    )
    assert len(provider.calls) == 1


@pytest.mark.parametrize(
    "limit,code", [(10, "ESTIMATED_BUDGET_EXCEEDED"), (22, "FUZZY_BUDGET_MILESTONE_REACHED")]
)
def test_batch_checks_aggregate_liability_and_stop_threshold(tmp_path, limit, code):
    from pfp.workflows.tests.gateways import gateway

    bound, provider = gateway(tmp_path, limit=limit, max_calls=5)
    requests = {f"a{i}": CandidateRequest("x" * 1000, "y") for i in range(5)}
    assert (
        bound.complete_batch_result(
            requests, provider=Provider.OPENROUTER, model="vendor/model"
        ).error.code
        == code
    )
    assert not provider.calls


def test_batch_checks_call_allowance_without_partial_dispatch(tmp_path):
    from pfp.workflows.tests.gateways import gateway

    bound, provider = gateway(tmp_path, limit=100, max_calls=4)
    result = bound.complete_batch_result(
        {f"a{i}": CandidateRequest("s", "u") for i in range(5)},
        provider=Provider.OPENROUTER,
        model="vendor/model",
    )
    assert result.error.code == "CALL_ALLOWANCE_EXHAUSTED" and not provider.calls
    with bound.ledger.transaction(bound.limit) as state:
        assert not state["attempts"]


def test_batch_dispatch_exceptions_retain_unknown_reservation(tmp_path):
    from pfp.workflows.tests.gateways import gateway

    bound, provider = gateway(tmp_path, limit=100, max_calls=3)

    def broken(request, **options):
        raise TimeoutError("synthetic transport timeout")

    provider.complete_result = broken
    result = bound.complete_batch_result(
        {"broken": CandidateRequest("s", "u")}, provider=Provider.OPENROUTER, model="vendor/model"
    )
    assert isinstance(result, Ok)
    assert isinstance(result.value["broken"]["outcome"], Err)
    with bound.ledger.transaction(bound.limit) as state:
        assert state["attempts"]["broken"]["state"] == "reserved"
        assert state["action_claims"]["broken"]["state"] == "outcome_unknown"
        assert state["spent"] > 0
    blocked = bound.complete_batch_result(
        {"new": CandidateRequest("s", "u")}, provider=Provider.OPENROUTER, model="vendor/model"
    )
    assert blocked.error.code == "UNRECONCILED_ATTEMPT"


def test_full_wrong_unanimous_run_rejected_and_replayable(tmp_path):
    calls = []
    root = tmp_path / "wrong"
    result = runner.run(SPEC, root, gateway_factory=scripted_factory(calls, wrong=True))
    assert len(calls) == 6 and result["status"] == "TYPED_REFUSAL"
    assert result["lggr"]["gluing_defect_delta"] == -1
    assert result["selected_agent"] is None
    assert result["task_claim_audit"]["false"] == 5
    assert runner.replay_run(root)["status"] == "TYPED_REFUSAL"
