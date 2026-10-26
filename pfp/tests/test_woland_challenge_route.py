"""Full retinue fixture turns retain independent original finite judges; no model sends."""

import copy
import hashlib
import json
import tempfile

import pytest

from omega_engine_pfp.infrastructure.challenge_live import choose_case
from omega_engine_woland.tests.pilots.challenge_suite.catalog import load_case


@pytest.fixture(autouse=True)
def native_writable_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


def fixture():
    row = choose_case("C005", "development", 0)
    case = load_case(row)
    return row, dict(verdict=case["expected_verdict"], certificate=case["expected_certificate"])


def raw_reply(prompt, answer):
    props = prompt["response_schema"]["properties"]
    return json.dumps({key: props[key]["const"] for key in (
        "task_id", "attempt_id", "input_sha256")} | {"answer": answer}).encode()


def contribute_until(state, kind):
    from omega_engine_woland.infrastructure import challenge_play as woland

    while (pending := woland.report(state)["next_action"]) and pending["kind"] != kind:
        if pending["kind"] != "review":
            break
        state = woland.submit(state, raw_reply(woland.report(state)["pfp_turn"],
            {"summary": "Inspected the original task and candidate", "findings": []}))
    return state


def candidate(state, answer):
    from omega_engine_woland.infrastructure import challenge_play as woland

    state = contribute_until(state, "build") if woland.report(state)["next_action"]["phase"] == "intake" else state
    state = woland.submit(state, raw_reply(woland.report(state)["pfp_turn"], json.dumps(answer)))
    return contribute_until(state, "learn")


def finish_learning(state):
    from omega_engine_woland.infrastructure import challenge_play as woland

    pending = woland.report(state)["next_action"]
    assert pending is not None, [(item["metadata"].get("failure_code"), item["summary"])
        for item in state["run"]["observations"] if item["blocked"]]
    assert pending["kind"] == "learn"
    return woland.submit(state, raw_reply(woland.report(state)["pfp_turn"], {
        "summary": "Recorded the actual finite judge outcome", "findings": [], "lessons": [],
        "no_change_reason": "Existing guidance already covers this scoped fixture.",
        **consumption(pending["ddc_program"])}))


def consumption(program):
    return {"consumed_ddc_root": program["binding"]["semantic_ddc_root"],
        "consumed_procedure_sha256": hashlib.sha256(json.dumps(program["binding"],
            sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()}


def test_current_ide_candidate_reaches_original_judge_and_replay_never_dispatches(monkeypatch):
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    state = woland.start(row)
    assert "expected_certificate" not in woland.report(state)["pfp_turn"]["user"]
    state = finish_learning(candidate(state, answer))
    observed = woland.report(state)
    assert observed["work_status"] == "completed"
    assert observed["retinue_coverage"]["complete"]
    assert observed["task_check"]["status"] == "HOST_ACCEPTED"
    assert observed["provider_replies"] == 0 and observed["ide_submissions"] == 21
    assert observed["known_cost_usd"] is None
    assert state["run"]["schema_version"] == "omega.woland.teamwork.v4"
    native = [item["metadata"]["native_gate_receipt"]
        for item in state["run"]["observations"] if "native_gate_receipt" in item["metadata"]]
    assert len(native) == 4
    assert all(receipt["summary"]["coverage_complete"] for receipt in native)
    assert all(len(receipt["summary"]["observed"]) == 35 for receipt in native)
    monkeypatch.setattr(woland, "create_accounted_openrouter_gateway", lambda *a, **kw:
        pytest.fail("Replay dispatched a provider"))
    assert woland.replay(state)["provider_calls"] == 0
    corrupted = copy.deepcopy(state)
    first_pfp = next(item["metadata"]["pfp"] for item in corrupted["run"]["observations"]
        if "pfp" in item["metadata"])
    first_pfp["raw_reply_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="PFP_REPLAY_MISMATCH|REPLAY_RAW_MISMATCH"):
        woland.replay(corrupted)


def test_schema_valid_false_witness_needs_repair_after_every_specialist_review():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    bad = copy.deepcopy(answer)
    name = next(iter(bad["certificate"]))
    bad["certificate"][name] = str(int(bad["certificate"][name]) + 1)
    state = candidate(woland.start(row, max_repairs=1), bad)
    pending = woland.report(state)
    assert pending["task_check"]["status"] == "PROVIDER_COMPLETED"
    assert pending["next_action"]["kind"] == "repair"
    assert "expected_certificate" not in pending["pfp_turn"]["user"]
    state = finish_learning(candidate(state, answer))
    assert woland.report(state)["task_check"]["status"] == "HOST_ACCEPTED"
    assert woland.report(state)["work_status"] == "completed"


def test_wrong_task_raw_reply_blocks_and_retains_exact_bytes_without_judging():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    state = contribute_until(woland.start(row, max_repairs=0), "build")
    raw = json.loads(raw_reply(woland.report(state)["pfp_turn"], json.dumps(answer)))
    raw["task_id"] = "wrong-task"
    state = woland.submit(state, json.dumps(raw).encode())
    assert woland.report(state)["work_status"] == "blocked"
    assert woland.report(state)["task_check"] is None
    assert next(item for item in state["run"]["observations"] if item["blocked"])["metadata"]["pfp"]["raw_reply_base64"]


def test_changed_wrong_candidate_can_use_explicit_remaining_repair_allowance():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    state = woland.start(row, max_repairs=2, max_actions=80)
    name = next(iter(answer["certificate"]))
    for offset in (1, 2):
        wrong = copy.deepcopy(answer)
        wrong["certificate"][name] = str(int(wrong["certificate"][name]) + offset)
        state = candidate(state, wrong)
        assert woland.report(state)["next_action"]["kind"] == "repair"
    assert woland.report(finish_learning(candidate(state, answer)))["work_status"] == "completed"


def test_learning_finding_returns_to_original_candidate_under_same_bounded_plan():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    state = candidate(woland.start(row), answer)
    diagnostic = "The original witness needs a local invariant recheck."
    state = woland.submit(state, raw_reply(woland.report(state)["pfp_turn"], {
        "summary": "Recheck requested", "findings": [diagnostic], "lessons": [diagnostic],
        **consumption(woland.report(state)["next_action"]["ddc_program"])}))
    pending = woland.report(state)
    assert pending["next_action"]["kind"] == "repair"
    assert json.loads(pending["next_action"]["candidate"]) == answer
    assert diagnostic in state["run"]["observations"][-1]["findings"]


@pytest.mark.parametrize("field,value", [
    ("findings", []), ("blocked", True),
    ("candidate_sha256", "0" * 64), ("checker_id", "invented-checker"),
])
def test_replay_rejects_changed_independent_judge_decision_and_binding(field, value):
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    answer.update(verdict="INCONSISTENT", certificate={})
    state = candidate(woland.start(row, max_repairs=0), answer)
    assert woland.report(state)["work_status"] == "partial"
    assert woland.replay(state)["provider_calls"] == 0
    review = next(item for item in reversed(state["run"]["observations"]) if "task_check" in item["metadata"])
    if field in ("findings", "blocked"):
        review[field] = value
    else:
        review["metadata"][field] = value
    with pytest.raises(ValueError, match="REPLAY_JUDGE_MISMATCH|FAILED_CHECK"):
        woland.replay(state)


def _gateway(answer, state, tmp_path):
    from dataclasses import replace

    from omega_engine_operations.domain.rop.result import Ok
    from omega_engine_pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
    from omega_engine_woland.tests.test_teamwork_openrouter import Gateway

    class RetinueGateway(Gateway):
        def complete_result(self, request, **options):
            public = json.loads(request.user)
            schema = public["answer_schema"]
            output = json.dumps(answer) if schema["type"] == "string" else {
                "summary": "Concrete fixture role contribution", "findings": []}
            if "lessons" in schema.get("properties", {}):
                output.update(lessons=[], no_change_reason="Existing guidance is sufficient.",
                    **consumption(public["input"]["context"]["ddc_program"]))
            self.content = json.dumps({key: public[key] for key in (
                "task_id", "attempt_id", "input_sha256")} | {"answer": output})
            outcome = super().complete_result(request, **options).value
            return Ok(replace(outcome, candidate=replace(outcome.candidate,
                cost_usd=0.000001, generation_id=f"synthetic-{len(self.calls)}")))

    provider = RetinueGateway("", raw=True)
    bound = EstimatedBudgetGateway(provider, model="vendor/model",
        price={"catalog_sha256": "explicit-synthetic-price", "row": {"id": "vendor/model",
            "pricing": {"prompt": "0.000000001", "completion": "0.000000001"}}},
        limit_microusd=50000, max_calls=42, accounting_path=tmp_path / "budget.sqlite3",
        run_id=state["run"]["run_id"],
        objective_sha256=hashlib.sha256(state["run"]["objective"].encode()).hexdigest(),
        max_output_tokens=512)
    bound.provider_fixture = provider
    return bound


def test_openrouter_uses_full_retinue_and_one_gateway_before_original_judge(tmp_path):
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    initial = woland.start(row, executor="openrouter")
    gateway = _gateway(answer, initial, tmp_path)
    state = woland.run_bound(initial, gateway, "vendor/model")
    assert len(gateway.provider_fixture.calls) == 21
    assert woland.report(state)["task_check"]["status"] == "HOST_ACCEPTED"
    assert woland.report(state)["work_status"] == "completed"
    assert woland.report(state)["retinue_coverage"]["complete"]


@pytest.mark.parametrize("attempt_state", [
    "CompletedCostUnknown", "CompletedOverEstimatedBudget", "CompletedAccountingUnavailable",
])
def test_unsettled_charged_reply_stops_before_judging_or_retry(attempt_state, tmp_path):
    from dataclasses import replace

    from omega_engine_operations.domain.rop.result import Ok
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, answer = fixture()
    initial = woland.start(row, executor="openrouter")
    gateway = _gateway(answer, initial, tmp_path)
    actual_complete = gateway.provider_fixture.complete_result

    def unsettled(*args, **kwargs):
        result = actual_complete(*args, **kwargs)
        values = {"CompletedCostUnknown": {"cost_usd": None},
            "CompletedOverEstimatedBudget": {"cost_usd": 0.05},
            "CompletedAccountingUnavailable": {"generation_id": ""}}
        return Ok(replace(result.value, candidate=replace(result.value.candidate, **values[attempt_state])))

    gateway.provider_fixture.complete_result = unsettled
    state = woland.run_bound(initial, gateway, "vendor/model")
    assert len(gateway.provider_fixture.calls) == 1
    assert woland.report(state)["work_status"] == "blocked"
    assert woland.report(state)["task_check"] is None
    observed = next(item for item in state["run"]["observations"] if item["blocked"])
    assert observed["metadata"]["failure_code"] == attempt_state
    assert observed["metadata"]["pfp"]["raw_reply_base64"]


def test_source_drift_refuses_before_any_model_turn():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, _answer = fixture()
    state = woland.start(row)
    assert "omega_engine_woland/infrastructure/teamwork_openrouter.py" in state["sources"]
    state["sources"][next(iter(state["sources"]))] = "0" * 64
    with pytest.raises(ValueError, match="CHALLENGE_SOURCE_DRIFT"):
        woland.report(state)


def test_original_public_case_reaches_canonical_role_prompt_without_expected_answers():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, _answer = fixture()
    prompt = woland.report(woland.start(row))["pfp_turn"]
    assert row["case_id"] in prompt["user"]
    assert "expected_certificate" not in prompt["user"]
    assert "Original public input:" in prompt["user"]


def test_c001_original_distractor_case_reaches_typed_judge_and_replay():
    from omega_engine_pfp.tests.demo_004.a_mechanism.c001_attention_distractor_mask.solve import (
        solve,
    )
    from omega_engine_woland.infrastructure import challenge_play as woland

    row = choose_case("C001", "development", 0)
    state = finish_learning(candidate(woland.start(row), solve(load_case(row))))
    assert woland.report(state)["task_check"]["status"] == "HOST_ACCEPTED"
    assert woland.replay(state)["provider_calls"] == 0


@pytest.mark.parametrize("cap", [0, -1, 50001])
def test_challenge_cli_refuses_invalid_run_cap_before_gateway_or_state(tmp_path, monkeypatch, capsys, cap):
    from omega_engine_woland.infrastructure import challenge_play as woland

    monkeypatch.setattr(woland, "create_accounted_openrouter_gateway", lambda *args, **kwargs:
        pytest.fail("Invalid run cap constructed a provider gateway"))
    state = tmp_path / "not-created.json"
    assert woland.main(["run", "--challenge", "C005", "--state", str(state), "--model", "unused",
                        "--max-estimated-cost-microusd", str(cap)]) == 2
    assert "RUN_COST_CAP_INVALID" in capsys.readouterr().out
    assert not state.exists()


def test_challenge_cannot_disable_the_required_learning_role():
    from omega_engine_woland.infrastructure import challenge_play as woland

    row, _answer = fixture()
    with pytest.raises(ValueError, match="RETINUE_LEARNING_REQUIRED"):
        woland.start(row, learn_after_run=False)
