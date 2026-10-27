"""Actual PFP preparation/checking around the existing durable estimated ledger."""

import base64
import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from operations.domain.rop.result import Ok
from pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
from pfp.infrastructure.pilot_matrix import (
    complete_pilot_turn,
    validate_pilot_gateways,
)
from adversary.domain.providers.attempt import AdmittedRequest, CompletionOutcome
from adversary.domain.providers.types import CandidateRequest, CandidateResponse, Provider


def make_gateway(tmp_path, *, model="vendor/model", cost=0.000001, answer=None,
    raw_content=None, max_calls=4, accounting_name="budget.sqlite3", max_output_tokens=256):
    class ScriptedProvider:
        unbudgeted_max_output_tokens = max_output_tokens

        def __init__(self):
            self.calls = []
            self.raw = b""

        def complete_result(self, request, **options):
            # The host reservation exists before the provider receives the turn.
            with bound.ledger.transaction(bound.limit) as state:
                assert any(row["state"] == "reserved" for row in state["attempts"].values())
            self.calls.append(request)
            prepared = json.loads(request.user)
            reply = {key: prepared[key] for key in ("task_id", "attempt_id", "input_sha256")}
            reply["answer"] = answer if answer is not None else {"case_id": "case_01", "value": 1}
            content = raw_content if raw_content is not None else json.dumps(reply)
            self.raw = json.dumps({"choices": [{"message": {"content": content},
                "finish_reason": "stop"}], "usage": {"cost": cost}, "extra": "retained α"},
                ensure_ascii=False).encode("utf-8")
            candidate = CandidateResponse(content, model, "openrouter", input_tokens=12,
                output_tokens=8, transport="fixture", generation_id=f"{model}-{len(self.calls)}",
                cost_usd=cost)
            admitted = AdmittedRequest(f"attempt-{model}-{len(self.calls)}", "", "request",
                Provider.OPENROUTER, model, request, max_output_tokens, None, None)
            return Ok(CompletionOutcome(candidate, admitted, reply_bytes=self.raw))

    provider = ScriptedProvider()
    price = dict(catalog_sha256="fixture-price", row=dict(id=model,
        pricing={"prompt": "0.000000001", "completion": "0.000000001"}))
    bound = EstimatedBudgetGateway(provider, model=model, price=price, limit_microusd=50000,
        max_calls=max_calls, accounting_path=tmp_path / accounting_name)
    return bound, provider


def send(gateway, *, model="vendor/model", attempt="case-0", max_tokens=256):
    return complete_pilot_turn(gateway, CandidateRequest("Solve the public task.", '{"n": 2}'),
        model=model, task_id="public-task", attempt_id=attempt, max_tokens=max_tokens)


def test_unaccounted_gateway_refuses_before_any_send():
    called = []
    fake = SimpleNamespace(complete_result=lambda *a, **k: called.append(a))
    result = send(fake)
    assert not result["ok"] and result["stop"]
    assert result["error"] == "PFP_ACCOUNTED_GATEWAY_REQUIRED" and not called


def test_actual_prepared_reply_checked_and_exact_wire_retained(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    result = send(gateway)
    assert result["ok"] and not result["stop"]
    assert json.loads(result["content"]) == {"case_id": "case_01", "value": 1}
    assert result["pfp"]["schema_valid"] and result["pfp"]["evidence_grade"] == "UNVERIFIED"
    assert result["attempt_state"] == "CompletedSettled"
    prepared = json.loads(provider.calls[0].user)
    assert prepared["input"]["prompt"] == '{"n": 2}' and prepared["task_id"] == "public-task"
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert result["provider_wire"]["raw_reply_sha256"] == sha256(provider.raw).hexdigest()
    assert result["usage"]["cost"] == 0.000001
    assert result["request"]["max_tokens"] == 256
    assert result["request"]["provider"] == {"allow_fallbacks": False, "require_parameters": True}


@pytest.mark.parametrize("raw", ['not JSON', '{}',
    '{"task_id":"wrong","attempt_id":"case-0","input_sha256":"wrong","answer":{"value":1}}'])
def test_malformed_or_wrong_binding_is_not_a_judge_answer(tmp_path, raw):
    gateway, provider = make_gateway(tmp_path, raw_content=raw)
    result = send(gateway)
    assert not result["ok"] and not result["stop"]
    assert result["content"] is None and result["pfp"]["failure_class"] != "NONE"
    assert len(provider.calls) == 1
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == provider.raw


def test_unknown_cost_keeps_reply_and_stops_next_attempt(tmp_path):
    gateway, provider = make_gateway(tmp_path, cost=None)
    result = send(gateway)
    assert not result["ok"] and result["stop"] and result["usage"]["cost"] is None
    assert result["attempt_state"] == "CompletedCostUnknown" and result["content"] is None
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert send(gateway, attempt="case-1")["error"] == "UNRECONCILED_ATTEMPT"
    assert len(provider.calls) == 1


def test_models_and_restart_share_original_call_allowance(tmp_path):
    first, p1 = make_gateway(tmp_path, max_calls=1)
    second, p2 = make_gateway(tmp_path, model="vendor/other", max_calls=1)
    validate_pilot_gateways({"vendor/model": first, "vendor/other": second},
        ["vendor/model", "vendor/other"], max_tokens=256)
    assert send(first)["ok"]
    assert send(second, model="vendor/other", attempt="case-1")["error"] == "CALL_ALLOWANCE_EXHAUSTED"
    reopened, p3 = make_gateway(tmp_path, max_calls=1)
    assert send(reopened, attempt="case-2")["error"] == "CALL_ALLOWANCE_EXHAUSTED"
    assert len(p1.calls) == 1 and not p2.calls and not p3.calls


def test_different_accounting_paths_are_not_one_run(tmp_path):
    first, _ = make_gateway(tmp_path)
    second, _ = make_gateway(tmp_path, model="vendor/other", accounting_name="fresh.sqlite3")
    with pytest.raises(ValueError, match="PFP_SHARED_ACCOUNTING_REQUIRED"):
        validate_pilot_gateways({"vendor/model": first, "vendor/other": second},
            ["vendor/model", "vendor/other"])


def test_output_bound_is_not_silently_shrunk(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    result = send(gateway, max_tokens=4096)
    assert result["error"] == "PFP_OUTPUT_BOUND_MISMATCH" and not provider.calls


def test_model_cannot_select_another_models_price(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    assert send(gateway, model="vendor/other")["error"] == "PRICING_MODEL_MISMATCH"
    assert not provider.calls

def test_restart_cannot_increase_original_call_allowance(tmp_path):
    first, provider = make_gateway(tmp_path, max_calls=1)
    assert send(first)["ok"]
    with pytest.raises(ValueError, match="DURABLE_RUN_SCOPE_MISMATCH"):
        make_gateway(tmp_path, max_calls=4)
    assert len(provider.calls) == 1


def test_same_pfp_action_cannot_dispatch_twice_even_with_remaining_allowance(tmp_path):
    gateway, provider = make_gateway(tmp_path, max_calls=4)
    assert send(gateway)["ok"]
    again = send(gateway)
    assert again["stop"] and not again["ok"]
    assert len(provider.calls) == 1
    assert send(gateway, attempt="case-1")["ok"]
    assert len(provider.calls) == 2

@pytest.mark.parametrize("raw", [b"provider invalid JSON", b'{"choices":[],"usage":{}}'])
def test_provider_decode_and_parse_failures_retain_exact_returned_wire(tmp_path, raw):
    from adversary.infrastructure.providers.gateway import unbudgeted_gateway
    calls = []
    def transport(*args):
        calls.append(args)
        return raw
    provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model="vendor/model",
        transport=transport, max_output_tokens=256)
    price = dict(catalog_sha256="fixture", row=dict(id="vendor/model",
        pricing={"prompt": "0.000000001", "completion": "0.000000001"}))
    gateway = EstimatedBudgetGateway(provider, model="vendor/model", price=price,
        limit_microusd=50000, max_calls=4, accounting_path=tmp_path / "real-parse.sqlite3")
    result = send(gateway)
    assert not result["ok"] and result["stop"] and len(calls) == 1
    assert result["raw_body"] == raw.decode("utf-8")
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == raw
    assert send(gateway, attempt="case-1")["error"] == "UNRECONCILED_ATTEMPT"
    assert len(calls) == 1


@pytest.mark.parametrize("kind, answer", [
    ("consistency", {"verdict": "CONSISTENT", "certificate": {"n0": "0"}}),
    ("repair", {"status": "SOLVED", "repaired": ["1", "-1"], "weighted_l1": "0"}),
])
def test_declared_c005_schema_survives_binding_and_rejects_wrong_answer(tmp_path, kind, answer):
    from copy import deepcopy

    from pilots.llm_mechanism.c005_hosted_decode_controls.schemas import (
        CONSISTENCY_JSON_SCHEMA,
        CYCLE_REPAIR_JSON_SCHEMA,
    )
    from adversary.domain.providers.types import DecodingParamsV1

    declared = deepcopy(CONSISTENCY_JSON_SCHEMA if kind == "consistency" else CYCLE_REPAIR_JSON_SCHEMA)
    request = CandidateRequest("Solve the original task.", "public input",
        decoding=DecodingParamsV1(temperature=0.0,
            response_format={"type": "json_schema", "json_schema": declared}))
    gateway, provider = make_gateway(tmp_path, answer=answer, max_output_tokens=96)
    result = complete_pilot_turn(gateway, request, model="vendor/model", task_id="c005",
        attempt_id="case-0", max_tokens=96)
    assert result["ok"] and json.loads(result["content"]) == answer
    sent = result["request"]["response_format"]["json_schema"]
    assert sent["name"] == declared["name"] and sent["strict"] is True
    embedded = dict(sent["schema"]["properties"]["answer"])
    embedded.pop("$id")
    assert embedded == declared["schema"]
    assert json.loads(provider.calls[0].user)["answer_schema"] == declared["schema"]
    assert result["request"]["max_tokens"] == 96
    negative, bad_provider = make_gateway(tmp_path, answer={"arbitrary": "generic object"},
        max_output_tokens=96, accounting_name="negative.sqlite3")
    rejected = complete_pilot_turn(negative, request, model="vendor/model", task_id="c005",
        attempt_id="case-0", max_tokens=96)
    assert not rejected["ok"] and rejected["content"] is None
    assert rejected["pfp"]["failure_class"] != "NONE"
    assert base64.b64decode(rejected["provider_wire"]["raw_reply_base64"]) == bad_provider.raw


def test_missing_declared_schema_refuses_without_generic_fallback(tmp_path):
    from adversary.domain.providers.types import DecodingParamsV1
    gateway, provider = make_gateway(tmp_path)
    request = CandidateRequest("Solve", "public input", decoding=DecodingParamsV1(
        response_format={"type": "json_schema", "json_schema": {"name": "missing"}}))
    result = complete_pilot_turn(gateway, request, model="vendor/model", task_id="c005",
        attempt_id="case-0", max_tokens=256)
    assert result["error"] == "PFP_DECLARED_ANSWER_SCHEMA_REQUIRED"
    assert not provider.calls


def test_logit_bias_remains_only_declared_provider_control(tmp_path):
    from adversary.domain.providers.types import DecodingParamsV1
    gateway, provider = make_gateway(tmp_path, answer={"verdict": "INCONSISTENT", "certificate": {}})
    bias = {"123": -100, "456": 5}
    request = CandidateRequest("Solve", "public input",
        decoding=DecodingParamsV1(temperature=0.0, logit_bias=bias))
    result = complete_pilot_turn(gateway, request, model="vendor/model", task_id="c005",
        attempt_id="bias-0", max_tokens=256)
    assert result["ok"] and len(provider.calls) == 1
    assert result["request"]["logit_bias"] == bias
    assert "response_format" not in result["request"]
