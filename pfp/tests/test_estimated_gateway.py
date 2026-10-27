"""Estimated limits use the existing durable provider ledger, with zero network."""

import json
from dataclasses import replace

import pytest

from operations.domain.rop.result import Err, Ok
from pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
from adversary.domain.providers.types import CandidateRequest, Provider
from adversary.tests.test_teamwork_openrouter import Gateway


def gateway(tmp_path, *, cost=0.000010, limit=100, max_calls=2, generation=True):
    class ProviderGateway(Gateway):
        def complete_result(self, request, **options):
            outcome = super().complete_result(request, **options).value
            self.returned_wire = outcome.reply_bytes
            return Ok(replace(outcome, candidate=replace(outcome.candidate,
                cost_usd=cost, generation_id=f"generation-{len(self.calls)}" if generation else "")))
    provider = ProviderGateway("raw", raw=True)
    price = dict(catalog_sha256="snapshot", row=dict(id="vendor/model",
        pricing={"prompt": "0.000000001", "completion": "0.000000001"}))
    return EstimatedBudgetGateway(provider, model="vendor/model", price=price,
        limit_microusd=limit, max_calls=max_calls, accounting_path=tmp_path / "budget.sqlite3"), provider


def send(bound):
    return bound.complete_result(CandidateRequest("System", "Task"),
        provider=Provider.OPENROUTER, model="vendor/model")


def test_estimated_reservation_call_limit_and_restart_do_not_reset(tmp_path):
    bound, provider = gateway(tmp_path, cost=0.000001, max_calls=1)
    first = send(bound)
    assert isinstance(first, Ok) and first.value.state == "CompletedSettled"
    assert first.value.admitted.estimated_microusd > 0
    stopped = send(bound)
    assert isinstance(stopped, Err) and stopped.error.code == "CALL_ALLOWANCE_EXHAUSTED"
    assert len(provider.calls) == 1
    resumed, new_provider = gateway(tmp_path, cost=0.000001, max_calls=1)
    assert isinstance(send(resumed), Err) and not new_provider.calls


def test_original_c006_wheel_fuel_40_fits_one_existing_estimated_gateway(tmp_path):
    bound, provider = gateway(tmp_path, cost=0.000001, limit=10000, max_calls=40)
    for _ in range(40):
        assert send(bound).value.state == "CompletedSettled"
    assert send(bound).error.code == "CALL_ALLOWANCE_EXHAUSTED"
    assert len(provider.calls) == 40
    resumed, replacement = gateway(tmp_path, cost=0.000001, limit=10000, max_calls=40)
    assert send(resumed).error.code == "CALL_ALLOWANCE_EXHAUSTED" and not replacement.calls


def test_estimated_factory_allows_original_fuel_but_hard_scope_keeps_its_limit(monkeypatch, tmp_path):
    from pfp.infrastructure import estimated_gateway
    from adversary.domain.providers.attempt import ProviderFailure, RetryClass
    from adversary.domain.providers.types import ProviderConfigError

    monkeypatch.setattr(estimated_gateway, "resolve_openrouter_key", lambda _: Err(
        ProviderFailure("TEST_CREDENTIAL_BOUNDARY", "test", RetryClass.TERMINAL)))
    with pytest.raises(ProviderConfigError, match="TEST_CREDENTIAL_BOUNDARY"):
        estimated_gateway.create_accounted_openrouter_gateway("vendor/model", 128,
            max_estimated_cost_microusd=1000, max_calls=40, accounting_path=tmp_path / "factory.sqlite3")
    with pytest.raises(ValueError, match="max_calls"):
        estimated_gateway.create_accounted_openrouter_gateway("vendor/model", 128,
            max_cost_microusd=1000, max_calls=40)


def test_factory_preserves_explicit_http_timeout_and_refuses_invalid_before_credentials(monkeypatch):
    from pfp.infrastructure import estimated_gateway

    transports = []
    sentinel = object()
    monkeypatch.setattr(estimated_gateway, "resolve_openrouter_key", lambda _: Ok("synthetic-key"))
    def transport(*args, **options):
        transports.append(options)
        return sentinel
    monkeypatch.setattr(estimated_gateway, "OpenAiCompatTransport", transport)
    monkeypatch.setattr(estimated_gateway, "unbudgeted_gateway", lambda **options: options)
    result = estimated_gateway.create_accounted_openrouter_gateway("vendor/model", 128,
        allow_unbounded_cost=True, timeout=180)
    assert result["transport"] is sentinel and transports[0]["timeout"] == 180
    monkeypatch.setattr(estimated_gateway, "resolve_openrouter_key",
                        lambda _: pytest.fail("invalid timeout reached credentials"))
    for timeout in (0, 301, True, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="INVALID_PROVIDER_TIMEOUT"):
            estimated_gateway.create_accounted_openrouter_gateway("vendor/model", 128,
                allow_unbounded_cost=True, timeout=timeout)


def test_insufficient_estimated_budget_prevents_any_send(tmp_path):
    bound, provider = gateway(tmp_path, limit=1)
    stopped = send(bound)
    assert isinstance(stopped, Err) and stopped.error.code == "ESTIMATED_BUDGET_EXCEEDED"
    assert not provider.calls


def test_unknown_actual_cost_retains_provider_bytes_and_stops_future_calls(tmp_path):
    bound, provider = gateway(tmp_path, cost=None)
    result = send(bound)
    assert result.value.state == "CompletedCostUnknown"
    assert result.value.candidate.cost_usd is None
    assert result.value.reply_bytes == provider.returned_wire
    assert json.loads(result.value.reply_bytes)["choices"][0]["message"]["content"] == "raw"
    assert send(bound).error.code == "UNRECONCILED_ATTEMPT" and len(provider.calls) == 1


def test_over_estimate_reports_actual_cost_and_stops_future_calls(tmp_path):
    bound, provider = gateway(tmp_path, cost=0.000500)
    result = send(bound)
    assert result.value.state == "CompletedOverEstimatedBudget"
    assert result.value.candidate.cost_usd == 0.000500
    assert send(bound).error.code == "UNRECONCILED_ATTEMPT" and len(provider.calls) == 1


def test_missing_generation_identity_does_not_settle_or_retry(tmp_path):
    bound, provider = gateway(tmp_path, generation=False)
    assert send(bound).value.state == "CompletedAccountingUnavailable"
    assert send(bound).error.code == "UNRECONCILED_ATTEMPT" and len(provider.calls) == 1


def test_generic_pricing_only_requires_actual_parameters_without_weakening_math_campaign(monkeypatch):
    from pfp.infrastructure.adapters import pfp_campaign

    row = dict(id="openai/gpt-4o-mini", pricing={"prompt": "0.00000015", "completion": "0.0000006"},
        supported_parameters=["max_tokens", "temperature"])
    class Catalog:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, *args): return json.dumps({"data": [row]}).encode()
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kw: Catalog())
    assert pfp_campaign.snapshot_pricing(row["id"], required_parameters=("max_tokens",))["row"] == row
    with pytest.raises(ValueError, match="DECODING_UNSUPPORTED"):
        pfp_campaign.snapshot_pricing(row["id"])


def actual_gateway(tmp_path, *, model="vendor/model", output=64, rates=None, cost="0.000001", fault=None,
                   limit=50000, max_calls=6, run_id="objective-a"):
    from hashlib import sha256

    from adversary.infrastructure.providers.gateway import unbudgeted_gateway

    calls = []
    def wire(provider, selected, request):
        calls.append(request)
        if fault == "crash":
            raise RuntimeError("unknown send")
        usage = dict(prompt_tokens=10, completion_tokens=8)
        if cost is not None:
            usage["cost"] = cost
        if fault == "missing-usage":
            usage.pop("prompt_tokens")
        if fault == "output-overrun":
            usage["completion_tokens"] = output + 1
        raw = dict(id="" if fault == "unknown-identity" else "generation-" + selected + str(len(calls)), model=selected,
            choices=[dict(message=dict(content="  actual completion \n"))], usage=usage)
        return json.dumps(raw).encode()
    provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model=model, transport=wire,
        max_output_tokens=output)
    price = dict(catalog_sha256="observed-synthetic-text-price", row=dict(id=model,
        pricing=rates or {"prompt": "0.0000001", "completion": "0.0000002"}))
    return EstimatedBudgetGateway(provider, model=model, price=price, limit_microusd=limit,
        max_calls=max_calls, accounting_path=tmp_path / "actual.sqlite3", run_id=run_id,
        objective_sha256=sha256(b"one original objective").hexdigest(), max_output_tokens=output), calls


def bound_send(gateway, action="worker"):
    return gateway.for_action(action).complete_result(CandidateRequest("System", "Task"),
        provider=Provider.OPENROUTER, model=gateway.model)


def test_fuzzy_actual_output_limit_headroom_and_wire_replay(tmp_path):
    first, calls = actual_gateway(tmp_path, output=64)
    sent = bound_send(first)
    assert sent.value.state == "CompletedSettled"
    # Literal quote: (10 UTF8 prompt bytes +256 framing)*0.1 +64*0.2 =39.4 microUSD; ceil *2.
    assert sent.value.admitted.estimated_microusd == 80
    assert sent.value.candidate.content == "  actual completion \n"
    raw = first.raw_reply("worker")
    reopened, replacement = actual_gateway(tmp_path, output=64)
    assert bound_send(reopened).error.code == "PFP_ACTION_ALREADY_CLAIMED"
    recovered = reopened.for_action("worker").recover_result(CandidateRequest("System", "Task"),
        provider=Provider.OPENROUTER, model=reopened.model)
    assert recovered.value.reply_bytes == raw and recovered.value.candidate.content == "  actual completion \n"
    with reopened.ledger.transaction(50000) as state:
        assert state["spent"] == 1
    assert len(calls) == 1 and replacement == []


def test_model_switch_uses_same_original_allowance_and_new_prices(tmp_path):
    first, _ = actual_gateway(tmp_path, cost="0.000050")
    assert bound_send(first).value.state == "CompletedSettled"
    second, calls = actual_gateway(tmp_path, model="vendor/other", output=128,
        rates={"prompt": "0.00001", "completion": "0.00002"}, cost="0.000001")
    assert bound_send(second, "review").value.state == "CompletedSettled"
    with second.ledger.transaction(50000) as state:
        assert state["spent"] == 51 and len(state["attempts"]) == 2
        assert state["attempts"]["review"]["reserved"] == 10440
    assert len(calls) == 1 and first.binding == second.binding


@pytest.mark.parametrize("fault", ["crash", "missing-usage", "unknown-cost", "over-estimate"])
def test_unknown_or_excessive_liability_holds_across_restart(tmp_path, fault):
    cost = None if fault == "unknown-cost" else "0.001" if fault == "over-estimate" else "0.000001"
    gateway, calls = actual_gateway(tmp_path, cost=cost, fault=fault)
    if fault == "crash":
        with pytest.raises(RuntimeError, match="unknown send"):
            bound_send(gateway)
    else:
        assert bound_send(gateway).value.state != "CompletedSettled"
    restarted, replacement = actual_gateway(tmp_path)
    assert bound_send(restarted, "next").error.code == "UNRECONCILED_ATTEMPT"
    recovered = restarted.for_action("worker").recover_result(CandidateRequest("System", "Task"),
        provider=Provider.OPENROUTER, model=restarted.model)
    assert isinstance(recovered, Err) and "RUN_RECONCILIATION_REQUIRED" in recovered.error.code
    assert len(calls) == 1 and replacement == []


@pytest.mark.parametrize("change", ["run", "limit", "calls"])
def test_fuzzy_scope_cannot_gain_a_new_allowance(tmp_path, change):
    actual_gateway(tmp_path)
    options = {"run_id": "different"} if change == "run" else {"limit": 40000} if change == "limit" else {"max_calls": 7}
    with pytest.raises(ValueError, match="SCOPE_MISMATCH|budget limit differs"):
        actual_gateway(tmp_path, **options)


def test_fuzzy_stops_at_milestone_and_refuses_unknown_surcharge(tmp_path):
    bound, calls = actual_gateway(tmp_path, limit=99)
    assert bound_send(bound).error.code == "FUZZY_BUDGET_MILESTONE_REACHED" and calls == []
    unknown, calls = actual_gateway(tmp_path, limit=99,
        rates={"prompt": "0.0000001", "completion": "0.0000002", "reasoning": "0.001"})
    assert bound_send(unknown).error.code == "UNSUPPORTED_SURCHARGE" and calls == []


def test_tampered_raw_cannot_replay_or_send_again(tmp_path):
    gateway, calls = actual_gateway(tmp_path)
    bound_send(gateway)
    path = gateway.reply_root / gateway.action("worker")["wire_file"]
    path.write_bytes(b"tampered")
    result = gateway.for_action("worker").recover_result(CandidateRequest("System", "Task"),
        provider=Provider.OPENROUTER, model=gateway.model)
    assert "RUN_RECONCILIATION_REQUIRED" in result.error.code and len(calls) == 1



def test_raw_wire_recovers_crash_before_cost_settlement_without_sending_again(tmp_path, monkeypatch):
    gateway, calls = actual_gateway(tmp_path)
    def crash(*args): raise KeyboardInterrupt("after retained wire, before settlement")
    monkeypatch.setattr(gateway, "_finish", crash)
    with pytest.raises(KeyboardInterrupt):
        bound_send(gateway)
    reopened, replacement = actual_gateway(tmp_path)
    recovered = reopened.for_action("worker").recover_result(CandidateRequest("System", "Task"),
        provider=Provider.OPENROUTER, model=reopened.model)
    assert recovered.value.state == "CompletedSettled" and recovered.value.candidate.cost_usd == 0.000001
    assert len(calls) == 1 and replacement == []
    with reopened.ledger.transaction(50000) as state:
        assert state["spent"] == 1


def test_optional_web_price_is_inactive_for_text_only_but_reasoning_price_refuses(tmp_path, monkeypatch):
    from pfp.infrastructure.adapters import pfp_campaign
    row = dict(id="vendor/model", pricing={"prompt": "0.0000001", "completion": "0.0000002",
        "web_search": "0.01"}, supported_parameters=["max_tokens"])
    class Catalog:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, *args): return json.dumps({"data": [row]}).encode()
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kw: Catalog())
    snapshot = pfp_campaign.snapshot_pricing("vendor/model", required_parameters=("max_tokens",), text_only=True)
    assert snapshot["row"] == row
    gateway, calls = actual_gateway(tmp_path, rates=row["pricing"])
    assert bound_send(gateway).value.admitted.estimated_microusd == 80 and len(calls) == 1
    with pytest.raises(ValueError, match="UNSUPPORTED_SURCHARGE"):
        pfp_campaign.snapshot_pricing("vendor/model", required_parameters=("max_tokens",))
    row["pricing"]["reasoning"] = "0.01"
    with pytest.raises(ValueError, match="UNSUPPORTED_SURCHARGE"):
        pfp_campaign.snapshot_pricing("vendor/model", required_parameters=("max_tokens",), text_only=True)


def test_mode_switch_cannot_create_a_second_budget_row(tmp_path):
    from pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
    from pfp.tests.test_durable_run_budget import bind
    from adversary.infrastructure.providers.gateway import unbudgeted_gateway
    hard, _ = bind(tmp_path)
    provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model="vendor/model", transport=lambda *args: b"",
        max_output_tokens=64)
    with pytest.raises(ValueError, match="SCOPE_MISMATCH"):
        EstimatedBudgetGateway(provider, model="vendor/model", price={}, limit_microusd=50000,
            max_calls=8, accounting_path=hard.path, run_id=hard.scope["run_id"],
            objective_sha256=hard.scope["objective_sha256"])
    import sqlite3
    with sqlite3.connect(hard.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM provider_budget").fetchone()[0] == 1



def test_actual_openrouter_request_includes_cost_usage_and_no_optional_tools(monkeypatch):
    from adversary.infrastructure.providers import http
    from adversary.infrastructure.providers.openai_compat import OpenAiCompatTransport
    calls = []
    def capture(url, headers, body, timeout):
        calls.append(body)
        return b"actual provider bytes"
    monkeypatch.setattr(http, "post_json", capture)
    transport = OpenAiCompatTransport(Provider.OPENROUTER, api_key="synthetic-not-a-live-key", max_tokens=64)
    assert transport(Provider.OPENROUTER, "vendor/model", CandidateRequest("System", "Task")) == b"actual provider bytes"
    assert calls[0]["usage"] == {"include": True} and calls[0]["max_tokens"] == 64
    assert not any(key in calls[0] for key in ("plugins", "tools", "web_search", "images", "audio"))



@pytest.mark.parametrize("fault", ["output-overrun", "unknown-identity"])
def test_unsettled_known_cost_holds_larger_actual_liability_idempotently(tmp_path, fault):
    gateway, calls = actual_gateway(tmp_path, cost="0.001", fault=fault)
    result = bound_send(gateway)
    assert result.value.state == "CompletedAccountingUnavailable"
    assert result.value.admitted.estimated_microusd == 80
    assert result.value.candidate.cost_usd == 0.001
    with gateway.ledger.transaction(50000) as state:
        assert state["spent"] == 1000 and state["attempts"]["worker"]["charged"] == 1000
    raw = gateway.raw_reply("worker")
    restarted, replacement = actual_gateway(tmp_path)
    for _ in range(2):
        recovered = restarted.for_action("worker").recover_result(CandidateRequest("System", "Task"),
            provider=Provider.OPENROUTER, model=restarted.model)
        assert recovered.error.code == "RUN_RECONCILIATION_REQUIRED"
        with restarted.ledger.transaction(50000) as state:
            assert state["spent"] == 1000
        assert restarted.raw_reply("worker") == raw
    assert bound_send(restarted, "review").error.code == "UNRECONCILED_ATTEMPT"
    assert len(calls) == 1 and replacement == []
