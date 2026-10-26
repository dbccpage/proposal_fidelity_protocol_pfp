"""Offline PFP lifecycle fixtures, budget failures, and replay mutations."""

import json
from copy import deepcopy

import pytest

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from omega_engine_pfp.infrastructure.adapters.pfp_campaign import (
    CAP,
    PfpCampaignAdapter,
    canonical,
    micro,
    replay_stages,
)
from omega_engine_pfp.use_cases.pfp_prompt import AssemblePfpPromptUseCase
from omega_engine_pfp.use_cases.pfp_proposal import REPAIR_RULES
from omega_engine_pfp.use_cases.pfp_stages import RunPfpStagesUseCase

MODEL = "offline-fixture"


def assemble(feedback=None):
    return AssemblePfpPromptUseCase().execute(
        PfpPromptTemplate(
            "SPK-001", "[USER PROMPT]", {"properties": {"sections": {"type": "array"}}}
        ),
        PfpTaskPrompt(
            "fixture",
            'Equation contract\n```json\n{"status":"SOLVED","x":938456}\n```',
            {"n": 3, "expected_answer": 42},
        ),
        feedback=feedback,
    )


def reply(number=1, cost="0.000001"):
    return canonical(
        dict(
            id=f"fixture-{number}",
            model=MODEL,
            usage=dict(prompt_tokens=10, completion_tokens=10, total_tokens=20, cost=cost),
            choices=[dict(message=dict(content='{"fixture":true}'), finish_reason="stop")],
        )
    )


def adapter(tmp_path, outcomes=None, costs=None, rate="0.0000001", send_error=None):
    outcomes = iter(outcomes or [("HOST_ACCEPTED", "NONE")])
    costs = iter(costs or ["0.000001", "0.000001"])
    sends = []
    feedbacks = []
    price = dict(row=dict(id=MODEL, pricing=dict(prompt="0", completion=rate)))
    (tmp_path / "pricing.json").write_bytes(canonical(price))

    def prompt(feedback):
        feedbacks.append(feedback)
        return assemble(feedback)

    def send(model, request, limit):
        number = len(sends) + 1
        # Budget and exact request must be durable before any provider call.
        assert (tmp_path / f"stage_{number}/request.json").exists()
        with port.ledger.transaction(CAP) as state:
            assert state["attempts"][str(number)]["state"] == "reserved"
        sends.append((model, request, limit))
        if send_error:
            raise send_error
        return reply(number, next(costs))

    def judge(text):
        # Raw bytes must survive checker and decoding failures.
        assert (tmp_path / f"stage_{len(sends)}/provider_response.json").exists()
        status, failure = next(outcomes)
        return dict(status=status, failure_class=failure)

    port = PfpCampaignAdapter(tmp_path, MODEL, price, prompt, judge, send, {})
    return port, sends, feedbacks


def ledger_state(port):
    with port.ledger.transaction(CAP) as state:
        return deepcopy(state)


def test_prompt_projection_preserves_protocol_and_does_not_mutate_inputs():
    schema = dict(type="object", properties=dict(kind=dict(const="consistency")))
    original = deepcopy(schema)
    template = PfpPromptTemplate("SPK-001", "[USER PROMPT]", {"properties": {}})
    task = PfpTaskPrompt(
        "fixture",
        '```json\n{"status":"SOLVED","x":938456}\n```',
        {"expected_answer": 42, "input": {"n": 3}},
        schema,
    )
    prompt = AssemblePfpPromptUseCase().execute(template, task)
    assert "938456" not in prompt.user and "expected_answer" not in prompt.user
    assert "SOLVED" not in prompt.user and '"n": 3' in prompt.user
    assert "status" in prompt.user
    assert prompt.response_schema["properties"]["answer"] == original
    prompt.response_schema["properties"]["answer"]["properties"].clear()
    assert schema == original
    assert template.response_schema == {"properties": {}}


def test_two_stage_feedback_and_settlement(tmp_path):
    port, sends, feedbacks = adapter(
        tmp_path, [("PROVIDER_COMPLETED", "CERTIFICATE"), ("HOST_ACCEPTED", "NONE")]
    )
    records = RunPfpStagesUseCase().execute(port)
    assert len(records) == len(sends) == 2
    assert feedbacks == [None, REPAIR_RULES["CERTIFICATE"]]
    state = ledger_state(port)
    assert state["spent"] == 2
    assert all(a["state"] == "settled" for a in state["attempts"].values())


@pytest.mark.parametrize(
    "status,failure",
    [
        ("HOST_ACCEPTED", "NONE"),
        ("TYPED_REFUSAL", "NONE"),
        ("CHECKER_DEFECT", "CERTIFICATE"),
        ("INFRASTRUCTURE_ERROR", "CERTIFICATE"),
        ("PROVIDER_COMPLETED", "UNREGISTERED"),
    ],
)
def test_terminal_outcomes_never_authorize_another_turn(tmp_path, status, failure):
    port, sends, _ = adapter(tmp_path, [(status, failure)])
    assert len(RunPfpStagesUseCase().execute(port)) == len(sends) == 1


def test_wrong_proposals_stop_after_two_attempts(tmp_path):
    port, sends, _ = adapter(tmp_path, [("PROVIDER_COMPLETED", "CERTIFICATE")] * 2)
    assert len(RunPfpStagesUseCase().execute(port)) == len(sends) == 2


def test_initial_feedback_rejected_before_any_io(tmp_path):
    port, sends, feedbacks = adapter(tmp_path)
    with pytest.raises(ValueError, match="UNTRUSTED_REPAIR_FEEDBACK"):
        RunPfpStagesUseCase().execute(port, "The secret answer is 42")
    assert sends == feedbacks == []
    assert ledger_state(port)["spent"] == 0


def test_cap_rejected_before_first_dispatch(tmp_path):
    port, sends, _ = adapter(tmp_path, rate="1")
    with pytest.raises(ValueError, match="RUN_CAP_EXCEEDED"):
        RunPfpStagesUseCase().execute(port)
    assert sends == [] and ledger_state(port)["spent"] == 0


def test_second_stage_reservation_counts_first_stage_actual_cost(tmp_path):
    port, sends, _ = adapter(
        tmp_path, [("PROVIDER_COMPLETED", "CERTIFICATE")], costs=["0.02"], rate="0.000013"
    )
    with pytest.raises(ValueError, match="RUN_CAP_EXCEEDED"):
        RunPfpStagesUseCase().execute(port)
    assert len(sends) == 1
    assert ledger_state(port)["spent"] == 20000


def test_transport_ambiguity_retains_hold_and_never_retries(tmp_path):
    port, sends, _ = adapter(tmp_path, send_error=TimeoutError("fixture timeout"))
    assert RunPfpStagesUseCase().execute(port) == []
    state = ledger_state(port)
    assert len(sends) == 1
    assert state["spent"] == state["attempts"]["1"]["reserved"] > 0
    assert state["attempts"]["1"]["state"] == "reserved"
    assert json.loads((tmp_path / "summary.json").read_bytes())["cost_microusd"] is None
    with pytest.raises(ValueError, match="UNRECONCILED_ATTEMPT"):
        port.reserve(2, 1)


@pytest.mark.parametrize("cost", [None, True, "NaN", "-1"])
def test_bad_cost_keeps_raw_response_and_hold(tmp_path, cost):
    port, sends, _ = adapter(tmp_path, costs=[cost])
    with pytest.raises(ValueError):
        RunPfpStagesUseCase().execute(port)
    assert len(sends) == 1 and (tmp_path / "stage_1/provider_response.json").exists()
    assert ledger_state(port)["attempts"]["1"]["state"] == "reserved"
    assert not (tmp_path / "stage_1/receipt.json").exists()


def test_missing_cost_is_collated_without_releasing_unknown_spend(tmp_path):
    port, sends, _ = adapter(tmp_path, costs=[None])
    with pytest.raises(ValueError, match="MISSING_COST"):
        RunPfpStagesUseCase().execute(port)
    summary = json.loads((tmp_path / "summary.json").read_bytes())
    assert summary["status"] == "INFRASTRUCTURE_ERROR"
    assert summary["failure_class"] == "ACCOUNTING"
    assert summary["cost_microusd"] is None
    assert summary["completed_stages"] == 0
    assert summary["reconciliation"] == "REQUIRED"
    assert len(sends) == 1
    assert (tmp_path / "stage_1/provider_response.json").read_bytes() == reply(cost=None)
    assert ledger_state(port)["attempts"]["1"]["state"] == "reserved"


def test_excess_bill_does_not_release_hold(tmp_path):
    port, sends, _ = adapter(tmp_path, costs=["0.04"])
    with pytest.raises(ValueError, match="BILL_EXCEEDS_RESERVATION"):
        RunPfpStagesUseCase().execute(port)
    assert len(sends) == 1 and ledger_state(port)["attempts"]["1"]["state"] == "reserved"


def test_duplicate_generation_does_not_settle_second_attempt(tmp_path):
    port, _, _ = adapter(tmp_path, [("PROVIDER_COMPLETED", "CERTIFICATE")] * 2)
    port.send = lambda *args: reply(1)
    port.judge = lambda text: dict(status="PROVIDER_COMPLETED", failure_class="CERTIFICATE")
    with pytest.raises(ValueError, match="DUPLICATE_GENERATION"):
        RunPfpStagesUseCase().execute(port)
    state = ledger_state(port)
    assert state["attempts"]["1"]["state"] == "settled"
    assert state["attempts"]["2"]["state"] == "reserved"


@pytest.mark.parametrize(
    "mutation,error",
    [
        (None, None),
        ("raw", "REPLAY_BINDING_MISMATCH"),
        ("request", "REPLAY_BINDING_MISMATCH"),
        ("receipt", "REPLAY_RESULT_MISMATCH"),
        ("reservation", "REPLAY_RESERVATION_MISMATCH"),
        ("summary", "REPLAY_SUMMARY_MISMATCH"),
        ("gap", "REPLAY_STAGE_SEQUENCE"),
        ("empty", "REPLAY_STAGE_BOUND"),
    ],
)
def test_replay_uses_saved_bytes_and_rejects_mutations(tmp_path, mutation, error):
    port, sends, _ = adapter(tmp_path)
    RunPfpStagesUseCase().execute(port)
    stage = tmp_path / "stage_1"
    if mutation in ("raw", "request"):
        name = "provider_response.json" if mutation == "raw" else "request.json"
        path = stage / name
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation in ("receipt", "reservation", "summary"):
        path = tmp_path / "summary.json" if mutation == "summary" else stage / f"{mutation}.json"
        data = json.loads(path.read_bytes())
        if mutation == "receipt":
            data["result"]["status"] = "TYPED_REFUSAL"
        elif mutation == "reservation":
            data["reserved_microusd"] += 1
        else:
            data["stages"] = 2
        path.write_bytes(canonical(data))
    elif mutation == "gap":
        stage.rename(tmp_path / "stage_2")
    elif mutation == "empty":
        stage.rename(tmp_path / "unused")

    def judge(text):
        return dict(status="HOST_ACCEPTED", failure_class="NONE")

    if error:
        with pytest.raises(ValueError, match=error):
            replay_stages(tmp_path, MODEL, None, 2, assemble, judge)
    else:
        assert replay_stages(tmp_path, MODEL, None, 2, assemble, judge) == 1
    assert len(sends) == 1


@pytest.mark.parametrize("value,expected", [("0", 0), ("0.0000001", 1), ("0.05", 50000)])
def test_cost_rounds_up_without_zeroing_small_bills(value, expected):
    assert micro(value) == expected


def _host_port(stop_stage, host5, calls):
    from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPipelineStep
    from omega_engine_pfp.domain.stages.host_stages import (
        admit_record,
        hand_off_record,
        receipt_record,
        selection_record,
    )
    from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter

    storage = PfpFileSystemStorageAdapter()
    rules, routing = storage.load_stage_file(9).obligation_rules, storage.load_terminal_routing()
    declaration = {"grammar": "g", "equality_test": "e", "coefficient_profile": "c"}

    class Port:
        def execute_model_stage(self, stage, prior):
            assert stage not in (1, 5, 7, 8, 9, 10)
            calls.append(stage)
            return PfpPipelineStep({"stage": stage, "demo_id": "d"}, stage != stop_stage)

        def execute_host_stage(self, stage, prior):
            calls.append(stage)
            if stage == 1:
                data = admit_record("d", None if stop_stage == 1 else declaration)
                return PfpPipelineStep(data, data["status"] == "admit")
            if stage == 5:
                assert tuple(prior) == (1, 2, 3, 4)
                return PfpPipelineStep({"stage": 5, "demo_id": "d", **host5}, True)
            if stage == 7:
                return PfpPipelineStep({"stage": 7, "demo_id": "d", "host_replay": {
                    "demo_id": "d", "stage": 6, "witnesses": []}}, True)
            builders = {8: lambda: selection_record("d", prior), 9: lambda: receipt_record("d", prior, rules),
                        10: lambda: hand_off_record("d", prior[9], routing)}
            return PfpPipelineStep(builders[stage](), True)

    return Port()


PASS = {"host_verdict": "PASS", "exact_checks_passed": True, "surviving_candidates": ["c"]}


@pytest.mark.parametrize(
    "stop_stage,completed,terminal", [(1, (1,), "BLOCKED_BY_EVIDENCE"), (3, (1, 2, 3), "BLOCKED_BY_EVIDENCE"),
                                      (None, tuple(range(1, 12)), "VERIFIED_WITH_RESIDUALS")]
)
def test_numbered_pipeline_keeps_fifth_stage_host_only(stop_stage, completed, terminal):
    from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase

    calls = []
    run = RunPfpPipelineUseCase().execute(tuple(range(1, 12)), _host_port(stop_stage, PASS, calls))
    assert run.completed_stages == tuple(calls) == completed
    assert run.terminal_status == terminal
    # The adversary checked nothing, so a full run is residual but every requested stage ran.
    assert run.all_stages_passed is (stop_stage is None)


@pytest.mark.parametrize("stages", [(), (2, 1), (1, 2, 3, 4, 6, 7, 8), (True, 2, 3, 4, 5, 6, 7, 8),
                                    tuple(range(1, 13))])
def test_numbered_pipeline_refuses_incomplete_or_coerced_stage_plan(stages):
    from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPipelineFailure
    from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase

    with pytest.raises(PfpPipelineFailure, match="Expected a contiguous"):
        RunPfpPipelineUseCase().execute(stages, object())


@pytest.mark.parametrize("host", [{"host_verdict": "PASS"}, {"host_verdict": "FAIL", "exact_checks_passed": False}])
def test_visiting_stage_five_is_not_independent_success(host):
    from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase

    calls = []
    result = RunPfpPipelineUseCase().execute(tuple(range(1, 12)), _host_port(None, host, calls))
    assert result.completed_stages == (1, 2, 3, 4, 5)
    assert result.terminal_status == "BLOCKED_BY_EVIDENCE"
    assert not result.all_stages_passed
