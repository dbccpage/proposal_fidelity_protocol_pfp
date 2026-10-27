"""Synthetic Anthropic bytes through actual parsing, PFP and the existing ledger."""

import base64
import copy
import json
from hashlib import sha256

import pytest

from operations.domain.rop.result import Ok
from pfp.infrastructure import estimated_gateway as owner
from pfp.infrastructure.pilot_matrix import complete_pilot_turn, validate_pilot_gateways
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1, Provider
from adversary.infrastructure.providers.gateway import unbudgeted_gateway
from adversary.infrastructure.providers.credential_source import ResolvedCredential


MODELS = ("claude-haiku-5-5", "claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-sonnet-4-5-20250929")


def test_messages_builder_uses_supported_structured_output_without_generation_seed():
    from adversary.infrastructure.providers.anthropic_messages import build_anthropic_body
    schema=dict(type='object',properties=dict(answer=dict(type='string')),required=['answer'],additionalProperties=False)
    request=CandidateRequest('system','user',decoding=DecodingParamsV1(
        response_format=dict(type='json_schema',json_schema=dict(name='answer',schema=schema))))
    body=build_anthropic_body(request,model='claude-sonnet-5-5')
    assert body['output_config']==dict(format=dict(type='json_schema',schema=schema))
    assert not {'seed','temperature','top_p','thinking'} & set(body)


def snapshot():
    data = dict(source_url="https://platform.claude.com/docs/en/about-claude/pricing",
        observed_at_utc="2026-10-14T12:00:00Z", rows=[
            dict(id=model, pricing=dict(prompt=prompt, completion=output))
            for model, prompt, output in zip(MODELS,
                ("0.0000001", "0.000001", "0.000002", "0.000003"),
                ("0.0000005", "0.000005", "0.00001", "0.000015"))])
    return {**data, "catalog_sha256": sha256(json.dumps(data, sort_keys=True,
        separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()}


def make_gateway(tmp_path, *, model=MODELS[1], fault=None, max_calls=4, limit=250000,
                 pricing=None):
    calls, raw = [], []
    def send(provider, selected, request):
        calls.append(request)
        if fault == "timeout":
            raise TimeoutError("synthetic attempted send")
        task = json.loads(request.user)
        envelope = {key: task[key] for key in ("task_id", "attempt_id", "input_sha256")}
        envelope["answer"] = "4"
        if fault == "binding":
            envelope["task_id"] = "wrong-task"
        usage = dict(input_tokens=12, output_tokens=8)
        if fault == "missing":
            usage.pop("input_tokens")
        if fault == "cache":
            usage["cache_read_input_tokens"] = 1
        if fault == "thinking-details":
            usage["output_tokens_details"] = {"thinking_tokens": 0}
        body = dict(type="message", id=f"msg-{selected}-{len(calls)}", model=selected,
            content=[dict(type="text", text="not JSON" if fault == "malformed" else json.dumps(envelope))],
            stop_reason="end_turn", usage=usage)
        wire = json.dumps(body).encode()
        raw.append(wire)
        return wire
    gateway = unbudgeted_gateway(provider=Provider.ANTHROPIC, model=model,
        transport=send, max_output_tokens=256)
    bound = owner.EstimatedBudgetGateway(gateway, provider=Provider.ANTHROPIC, model=model,
        price=owner.anthropic_price(pricing or snapshot(), model), limit_microusd=limit,
        max_calls=max_calls, accounting_path=tmp_path / "anthropic.sqlite3", run_id="anthropic-fixture",
        objective_sha256=sha256(b"actual same public task").hexdigest(), max_output_tokens=256)
    return bound, calls, raw


def complete(gateway, attempt="first"):
    return complete_pilot_turn(gateway, CandidateRequest("Return the sum.", "2+2",
        decoding=DecodingParamsV1(thinking="disabled", temperature=None)),
        provider=Provider.ANTHROPIC, model=gateway.model, task_id="sum", attempt_id=attempt,
        max_tokens=256)


def test_actual_anthropic_reply_is_rated_separately_from_absent_vendor_cost(tmp_path):
    gateway, calls, raw = make_gateway(tmp_path)
    result = complete(gateway)
    assert result["ok"] and not result["stop"] and result["content"] == "4"
    assert result["attempt_state"] == "CompletedRatedEstimate"
    assert result["usage"]["cost"] is None
    assert result["rated_cost_usd"] == "0.000052"
    assert result["cost_basis"] == "anthropic-standard-rated-v1"
    assert result["pricing_sha256"] == snapshot()["catalog_sha256"]
    assert result["request"]["thinking"] == {"type": "disabled"}
    assert "temperature" not in result["request"] and "response_format" not in result["request"]
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == raw[0]
    assert gateway.action("first")["actual"] is None
    assert gateway.action("first")["rated_microusd"] == 52
    assert len(calls) == 1


def test_all_models_share_one_allowance_and_recover_actual_wire_without_send(tmp_path):
    first, calls, raw = make_gateway(tmp_path, max_calls=1)
    second, later, _ = make_gateway(tmp_path, model=MODELS[0], max_calls=1)
    validate_pilot_gateways({first.model:first, second.model:second},
        (first.model,second.model), max_tokens=256, provider=Provider.ANTHROPIC)
    assert complete(first)["ok"]
    assert complete(second, "second")["error"] == "CALL_ALLOWANCE_EXHAUSTED" and not later
    reopened, new_calls, _ = make_gateway(tmp_path, max_calls=1)
    recovered = reopened.for_action("first").recover_result(calls[0],
        provider=Provider.ANTHROPIC, model=reopened.model)
    assert recovered.is_ok and recovered.value.state == "CompletedRatedEstimate"
    assert recovered.value.candidate.cost_usd is None and recovered.value.reply_bytes == raw[0]
    assert not new_calls
    with reopened.ledger.transaction(reopened.limit) as state:
        assert state["spent"] == 52


@pytest.mark.parametrize("fault", ["missing", "cache", "timeout"])
def test_unknown_rating_or_send_preserves_hold_and_blocks_later_attempts(tmp_path, fault):
    gateway, calls, raw = make_gateway(tmp_path, fault=fault)
    result = complete(gateway)
    assert result["stop"] and not result["ok"]
    if raw:
        assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == raw[0]
    assert complete(gateway, "second")["error"] == "UNRECONCILED_ATTEMPT"
    assert len(calls) == 1
    assert gateway.action("first")["state"] != "settled"


@pytest.mark.parametrize("fault", ["binding", "malformed"])
def test_rated_but_invalid_pfp_answer_is_retained_without_judge_content(tmp_path, fault):
    gateway, calls, raw = make_gateway(tmp_path, fault=fault)
    result = complete(gateway)
    assert not result["ok"] and not result["stop"] and result["content"] is None
    assert result["attempt_state"] == "CompletedRatedEstimate"
    assert result["rated_cost_usd"] == "0.000052"
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == raw[0]
    assert len(calls) == 1


def test_pricing_catalog_and_provider_cannot_drift_or_expand_the_bound_scope(tmp_path):
    gateway, calls, _ = make_gateway(tmp_path)
    changed = copy.deepcopy(snapshot())
    changed["rows"][0]["pricing"]["prompt"] = "0"
    with pytest.raises(ValueError, match="ANTHROPIC_PRICING"):
        owner.anthropic_price(changed, MODELS[0])
    with pytest.raises(ValueError, match="SCOPE_MISMATCH|limit differs"):
        make_gateway(tmp_path, limit=500000)
    wrong = complete_pilot_turn(gateway, CandidateRequest("System", "Task"),
        model=gateway.model, task_id="sum", attempt_id="wrong-provider", max_tokens=256)
    assert not wrong["ok"] and wrong["stop"] and not calls


def test_rate_helper_requires_actual_usage_and_refuses_unpriced_extras():
    price = owner.anthropic_price(snapshot(), MODELS[1])
    assert owner.rate_anthropic_usage(dict(usage=dict(input_tokens=12, output_tokens=8)), price) == "0.000052"
    for usage in (dict(input_tokens=True, output_tokens=8), dict(input_tokens=12),
                  dict(input_tokens=12, output_tokens=8, server_tool_use={"web_search_requests":1}),
                  dict(input_tokens=12, output_tokens=8, future_billable_units=1)):
        with pytest.raises(ValueError, match="ANTHROPIC_USAGE"):
            owner.rate_anthropic_usage(dict(usage=usage), price)


def test_single_model_catalog_and_aware_utc_timestamp_are_valid():
    data = snapshot()
    data.pop("catalog_sha256")
    data["rows"] = data["rows"][:1]
    data["observed_at_utc"] = "2026-10-14T12:00:00+00:00"
    data["catalog_sha256"] = sha256(json.dumps(data, sort_keys=True,
        separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    assert owner.anthropic_price(data, MODELS[0])["row"]["id"] == MODELS[0]


def test_factory_validates_profile_before_credential_resolution(monkeypatch, tmp_path):
    monkeypatch.setattr(owner, "resolve_credential", lambda *a, **k: pytest.fail("Invalid profile reached credentials"))
    changed = copy.deepcopy(snapshot())
    changed["catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="ANTHROPIC_PRICING"):
        owner.create_accounted_anthropic_gateway(MODELS[0], 256, pricing_snapshot=changed,
            max_estimated_cost_microusd=250000, accounting_path=tmp_path / "factory.sqlite3",
            run_id="factory", objective_sha256=sha256(b"factory").hexdigest())
    assert not list(tmp_path.iterdir())


def test_factory_composes_existing_transport_and_explicit_credential_file(monkeypatch, tmp_path):
    observed = []
    def credential(names, *, explicit_file):
        observed.append((names, explicit_file))
        return Ok(ResolvedCredential("ANTHROPIC_API_KEY", "synthetic-test-only", "injected"))
    monkeypatch.setattr(owner, "resolve_credential", credential)
    monkeypatch.setattr(owner, "AnthropicTransport", lambda **kwargs: observed.append(kwargs) or object())
    factory = owner.create_accounted_anthropic_gateway(MODELS[0], 256, pricing_snapshot=snapshot(),
        max_estimated_cost_microusd=250000, accounting_path=tmp_path / "factory.sqlite3",
        run_id="factory", objective_sha256=sha256(b"factory").hexdigest(), env_file=tmp_path / "chosen.env")
    assert factory.provider is Provider.ANTHROPIC and factory.limit == 250000
    assert observed[0] == (("ANTHROPIC_API_KEY",), tmp_path / "chosen.env")
    assert observed[1]["timeout"] == 60.0


def test_observed_standard_usage_thinking_breakdown_is_already_in_total():
    usage = dict(input_tokens=689, cache_creation_input_tokens=0, cache_read_input_tokens=0,
        cache_creation=dict(ephemeral_5m_input_tokens=0, ephemeral_1h_input_tokens=0),
        output_tokens=142, output_tokens_details={"thinking_tokens":0},
        service_tier="standard", inference_geo="global")
    price = owner.anthropic_price(snapshot(), MODELS[0])
    assert owner.rate_anthropic_usage({"usage":usage}, price) == "0.0001399"
    for details in ({"thinking_tokens":143}, {"thinking_tokens":True}, {"thinking_tokens":-1},
                    {"thinking_tokens":0, "unknown_charge":1}):
        with pytest.raises(ValueError, match="ANTHROPIC_USAGE"):
            owner.rate_anthropic_usage({"usage":{**usage, "output_tokens_details":details}}, price)


@pytest.mark.parametrize("tokens,accepted", [(8000, True), (16000, True), (16001, False)])
def test_anthropic_output_bound_allows_thinking_room_up_to_its_ceiling(tmp_path, tokens, accepted):
    """Live 2026-10-21: an Opus builder used all 2000 tokens on thinking plus a partial answer."""
    gateway = unbudgeted_gateway(provider=Provider.ANTHROPIC, model=MODELS[0],
        transport=lambda *a: b"", max_output_tokens=tokens)
    build = lambda: owner.EstimatedBudgetGateway(gateway, provider=Provider.ANTHROPIC, model=MODELS[0],
        price=owner.anthropic_price(snapshot(), MODELS[0]), limit_microusd=250000, max_calls=4,
        accounting_path=tmp_path / "bound.sqlite3", run_id="bound",
        objective_sha256=sha256(b"bound").hexdigest(), max_output_tokens=tokens)
    if accepted:
        assert build().max_output_tokens == tokens
    else:
        with pytest.raises(ValueError, match="INVALID_OUTPUT_TOKEN_LIMIT"):
            build()


def test_observed_standard_speed_rates_and_fast_speed_is_refused():
    """The live Messages usage on 2026-10-21 carried speed='standard' (Opus 5.5)."""
    usage = dict(input_tokens=1038, cache_creation_input_tokens=0, cache_read_input_tokens=0,
        cache_creation=dict(ephemeral_5m_input_tokens=0, ephemeral_1h_input_tokens=0),
        output_tokens=422, output_tokens_details={"thinking_tokens": 222},
        service_tier="standard", inference_geo="global", speed="standard")
    price = owner.anthropic_price(snapshot(), MODELS[0])
    assert owner.rate_anthropic_usage({"usage": usage}, price) == "0.0003148"
    with pytest.raises(ValueError, match="ANTHROPIC_USAGE"):
        owner.rate_anthropic_usage({"usage": {**usage, "speed": "fast"}}, price)


def test_recover_original_previously_unrated_wire_settles_hold_without_dispatch(tmp_path, monkeypatch):
    gateway, calls, raw = make_gateway(tmp_path, fault="thinking-details")
    current_rating = owner.rate_anthropic_usage
    def previous_classifier(body, price):
        if "output_tokens_details" in body["usage"]:
            raise ValueError("ANTHROPIC_USAGE_UNRATABLE")
        return current_rating(body, price)
    monkeypatch.setattr(owner, "rate_anthropic_usage", previous_classifier)
    first = complete(gateway)
    assert first["stop"] and gateway.action("first")["state"] == "identity_unavailable"
    held = gateway.action("first")["reserved"]
    monkeypatch.setattr(owner, "rate_anthropic_usage", current_rating)
    recovered = gateway.for_action("first").recover_result(calls[0],
        provider=Provider.ANTHROPIC, model=gateway.model)
    assert recovered.is_ok and recovered.value.state == "CompletedRatedEstimate"
    assert recovered.value.reply_bytes == raw[0] and len(calls) == 1
    assert gateway.action("first")["rated_microusd"] == 52 < held
    with gateway.ledger.transaction(gateway.limit) as state:
        assert state["spent"] == 52
