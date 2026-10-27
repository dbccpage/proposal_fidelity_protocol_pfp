"""Current accounted stage proposals and preserved synthetic v1 replay controls."""
from __future__ import annotations

import base64
import importlib
import json
import shutil
from types import SimpleNamespace

import pytest

from pfp.tests.test_pilot_matrix_pfp import make_gateway
from adversary.domain.providers.types import Provider
from adversary.infrastructure.providers.gateway import unbudgeted_gateway

MODEL = "offline-numbered-stage-fixture"

@pytest.fixture
def campaign(monkeypatch):
    module = importlib.import_module("pfp.infrastructure.adapters.pfp_campaign")
    monkeypatch.setattr(module, "snapshot_pricing", lambda _: pytest.fail("unexpected pricing/network"))
    return module


def packet(stage=1, **changes):
    from pfp.domain.prompts.prompts import PromptPacket
    values = dict(demo_id="provider-fixture", stage=stage,
        system="Return the requested object.", user="A bounded fixture",
        response_schema={"type": "object"}, seed_sha256="a" * 64)
    values.update(changes)
    return PromptPacket(**values)


def frozen_legacy_capture(campaign, output):
    """Create OLD-format synthetic bytes, never run the retired live adapter.

    These are new local fixtures for the exact retained v1 replay contract, not
    claims of reproduction or replacement of any historical provider run.
    """
    from pfp.domain.contracts.pfp_runtime import PfpPrompt
    output.mkdir()
    price = dict(row=dict(id=MODEL, pricing=dict(prompt="0", completion="0.000001")))
    campaign.write_new(output / "pricing.json", price)
    original = packet()
    prompt = PfpPrompt(original.system,
        original.user + "\nReturn only JSON satisfying this response schema:\n"
        + json.dumps(original.response_schema, sort_keys=True), original.response_schema)
    prepared = campaign.prepare_stage(prompt, MODEL, price)
    stage = output / "stage_1"
    stage.mkdir()
    raw = campaign.canonical(dict(id="old-fixture-1", model=MODEL,
        usage=dict(prompt_tokens=3, completion_tokens=4, total_tokens=7, cost="0.000002"),
        choices=[dict(message=dict(content='{"candidate":1}'), finish_reason="stop")]))
    campaign.write_new(stage / "request.json", prepared.wire_body)
    campaign.write_new(stage / "provider_response.json", raw)
    campaign.write_new(stage / "reservation.json", dict(
        reserved_microusd=prepared.reserved_microusd,
        request_sha256=campaign.digest(campaign.canonical(prepared.wire_body))))
    checked = campaign.grade_reply(raw, MODEL,
        lambda _: dict(status="PROVIDER_COMPLETED", failure_class="NONE"))
    checked.data.update(latency_seconds=0.25, raw_sha256=campaign.digest(raw),
        request_sha256=campaign.digest((stage / "request.json").read_bytes()),
        packet_sha256=campaign.digest(campaign.canonical(original.model_dump(mode="json"))),
        pricing_sha256=campaign.digest((output / "pricing.json").read_bytes()))
    campaign.write_new(stage / "receipt.json", checked.data)


def live_adapter(campaign, tmp_path, *, content=None, cost=0.000001, max_calls=4,
                 transport_error=None, wrong_model=False, output_name="live"):
    gateway, _ = make_gateway(tmp_path, model=MODEL, cost=cost, max_calls=max_calls,
        max_output_tokens=256)
    provider = SimpleNamespace(calls=[], raw=None)

    def transport(provider_id, model, request):
        provider.calls.append(request)
        if transport_error is not None:
            raise transport_error
        task = json.loads(request.user)
        answer = {key: task[key] for key in ("task_id", "attempt_id", "input_sha256")}
        answer["answer"] = {"candidate": 1}
        completion = content if content is not None else json.dumps(answer)
        provider.raw = json.dumps(dict(id=f"fixture-{len(provider.calls)}",
            model="wrong/model" if wrong_model else model,
            usage=dict(prompt_tokens=3, completion_tokens=4, total_tokens=7, cost=cost),
            choices=[dict(message=dict(content=completion), finish_reason="stop")]),
            ensure_ascii=True).encode("ascii")
        return provider.raw

    gateway.gateway = unbudgeted_gateway(provider=Provider.OPENROUTER, model=MODEL,
        transport=transport, max_output_tokens=256)
    adapter = campaign.PfpPipelineProviderAdapter(tmp_path / output_name, MODEL, gateway=gateway)
    return adapter, gateway, provider


def test_callable_only_cannot_dispatch_current_numbered_stages(campaign, tmp_path):
    calls = []
    output = tmp_path / "current"
    with pytest.raises(ValueError, match="PFP_ACCOUNTED_GATEWAY_REQUIRED"):
        campaign.PfpPipelineProviderAdapter(output, MODEL, send=lambda *a: calls.append(a))
    assert not calls and not output.exists()


def test_current_stage_retains_actual_wire_pfp_and_original_decoding(campaign, tmp_path):
    adapter, gateway, provider = live_adapter(campaign, tmp_path)
    original = packet()
    assert json.loads(adapter.generate_candidate(original)) == {"candidate": 1}
    stage = adapter.output / "stage_1"
    receipt = json.loads((stage / "receipt.json").read_bytes())
    exchange = json.loads((stage / "exchange.json").read_bytes())
    wire = json.loads((stage / "request.json").read_bytes())
    assert (stage / "provider_response.json").read_bytes() == provider.raw
    assert base64.b64decode(exchange["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert exchange["pfp"]["schema_valid"] and exchange["pfp"]["evidence_grade"] == "UNVERIFIED"
    assert receipt["result"]["status"] == "PROVIDER_COMPLETED"
    assert adapter.provider_calls == len(provider.calls) == 1 and adapter.cost_microusd == 1
    assert receipt["packet_sha256"] == campaign.digest(adapter._bytes(original.model_dump(mode="json")))
    assert wire["temperature"] == 0.0
    assert wire["provider"] == {"allow_fallbacks": False, "require_parameters": True}
    assert "response_format" not in wire and wire["max_tokens"] == 256
    prepared = json.loads(provider.calls[0].user)
    assert prepared["input"]["prompt"] == original.user + "\nReturn only JSON satisfying this response schema:\n" + json.dumps(original.response_schema, sort_keys=True)
    assert provider.calls[0].decoding.thinking == "disabled"
    with gateway.ledger.transaction(gateway.limit) as state:
        assert state["spent"] == 1
        assert len(state["attempts"]) == 1
    assert not (adapter.output / "budget.sqlite3").exists()


def test_current_replay_needs_no_ledger_or_calls(campaign, tmp_path):
    adapter, gateway, provider = live_adapter(campaign, tmp_path)
    expected = adapter.generate_candidate(packet())
    copy = tmp_path / "replay"
    shutil.copytree(adapter.output, copy)
    for file in tmp_path.glob("budget.sqlite3*"):
        if file.is_file():
            file.unlink()
    replay = campaign.PfpPipelineProviderAdapter(copy, MODEL, replay=True,
        send=lambda *args: pytest.fail("replay dispatched"))
    assert replay.generate_candidate(packet()) == expected
    assert replay.provider_calls == 0 and replay.cost_microusd == 1
    assert len(provider.calls) == 1 and not (copy / "budget.sqlite3").exists()


@pytest.mark.parametrize("mutation", ["raw", "request", "receipt", "packet", "pfp", "metadata"])
def test_current_replay_rechecks_binding_and_raw(campaign, tmp_path, mutation):
    adapter, _, _ = live_adapter(campaign, tmp_path)
    adapter.generate_candidate(packet())
    stage = adapter.output / "stage_1"
    replay_packet = packet()
    if mutation in ("raw", "request"):
        path = stage / ("provider_response.json" if mutation == "raw" else "request.json")
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "packet":
        replay_packet = packet(seed_sha256="b" * 64)
    else:
        path = (adapter.output / "pipeline.json" if mutation == "metadata"
            else stage / ("exchange.json" if mutation == "pfp" else "receipt.json"))
        saved = json.loads(path.read_bytes())
        if mutation == "pfp":
            saved["pfp"]["evidence_grade"] = "HOST_ACCEPTED"
        elif mutation == "metadata":
            saved["run_id"] = "wrong-run"
        else:
            saved["cost_microusd"] += 1
        path.write_bytes(adapter._bytes(saved))
    replay = campaign.PfpPipelineProviderAdapter(adapter.output, MODEL, replay=True)
    with pytest.raises(ValueError, match="REPLAY_(BINDING|RESULT)_MISMATCH"):
        replay.generate_candidate(replay_packet)
    assert replay.provider_calls == 0


@pytest.mark.parametrize("content,cost,wrong_model", [
    ("not JSON", 0.000001, False),
    ('{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":{}}', 0.000001, False),
    (None, None, False),
    (None, 0.000001, True),
    ("\ud800", 0.000001, False),
])
def test_refused_reply_retains_wire_and_stops_later_stages(campaign, tmp_path, content, cost, wrong_model):
    adapter, _, provider = live_adapter(campaign, tmp_path,
        content=content, cost=cost, wrong_model=wrong_model)
    with pytest.raises(ValueError):
        adapter.generate_candidate(packet())
    stage = adapter.output / "stage_1"
    assert (stage / "provider_response.json").read_bytes() == provider.raw
    exchange = json.loads((stage / "exchange.json").read_bytes())
    assert not exchange["ok"] and adapter.provider_calls == len(provider.calls) == 1
    if cost is None or wrong_model:
        assert adapter.cost_microusd is None
    else:
        assert adapter.cost_microusd == 1
    if content == "\ud800":
        assert exchange["pfp"]["reason"] == "INVALID_COMPLETION_UNICODE"
        assert exchange["pfp"]["raw_reply_encoding"] == "utf-8-surrogatepass"
    with pytest.raises(ValueError, match="PFP_PIPELINE_STOPPED"):
        adapter.generate_candidate(packet(stage=2))
    assert len(provider.calls) == 1


@pytest.mark.parametrize("content", [
    "not JSON",
    '{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":{}}',
    "\ud800",
])
def test_refused_shape_replay_retains_original_failure_and_known_cost(campaign, tmp_path, content):
    adapter, _, provider = live_adapter(campaign, tmp_path, content=content)
    with pytest.raises(ValueError) as original:
        adapter.generate_candidate(packet())
    before = {p.relative_to(adapter.output): p.read_bytes()
              for p in adapter.output.rglob("*") if p.is_file()}
    replay = campaign.PfpPipelineProviderAdapter(adapter.output, MODEL, replay=True)
    with pytest.raises(ValueError) as replayed:
        replay.generate_candidate(packet())
    assert str(replayed.value) == str(original.value)
    assert replay.cost_microusd == adapter.cost_microusd == 1
    assert replay.provider_calls == 0 and len(provider.calls) == 1
    assert before == {p.relative_to(adapter.output): p.read_bytes()
                      for p in adapter.output.rglob("*") if p.is_file()}


def test_ambiguous_send_is_not_free_and_no_retry(campaign, tmp_path):
    adapter, _, provider = live_adapter(campaign, tmp_path, transport_error=TimeoutError("private-token"))
    with pytest.raises(ValueError):
        adapter.generate_candidate(packet())
    assert adapter.cost_microusd is None and adapter.provider_calls == 1
    assert "private-token" not in (adapter.output / "stage_1/exchange.json").read_text()
    with pytest.raises(ValueError, match="PFP_PIPELINE_STOPPED"):
        adapter.generate_candidate(packet(stage=2))
    assert len(provider.calls) == 1
    replay = campaign.PfpPipelineProviderAdapter(adapter.output, MODEL, replay=True)
    with pytest.raises(ValueError, match="PFP_ADAPTER_ERROR_TimeoutError"):
        replay.generate_candidate(packet())
    assert replay.provider_calls == 0 and replay.cost_microusd is None


def test_accounted_allowance_is_shared_and_existing_output_is_untouched(campaign, tmp_path):
    adapter, gateway, provider = live_adapter(campaign, tmp_path, max_calls=1)
    adapter.generate_candidate(packet())
    with pytest.raises(ValueError, match="CALL_ALLOWANCE_EXHAUSTED"):
        adapter.generate_candidate(packet(stage=8))
    assert len(provider.calls) == 1 and adapter.cost_microusd == 1
    replay = campaign.PfpPipelineProviderAdapter(adapter.output, MODEL, replay=True)
    replay.generate_candidate(packet())
    with pytest.raises(ValueError, match="CALL_ALLOWANCE_EXHAUSTED"):
        replay.generate_candidate(packet(stage=8))
    assert replay.provider_calls == 0 and replay.cost_microusd == 1
    before = {p.relative_to(adapter.output): p.read_bytes() for p in adapter.output.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="RUN_ALREADY_EXISTS"):
        campaign.PfpPipelineProviderAdapter(adapter.output, MODEL, gateway=gateway)
    assert before == {p.relative_to(adapter.output): p.read_bytes() for p in adapter.output.rglob("*") if p.is_file()}


def test_original_stage_schema_is_validated_by_pipeline_not_outer_shape(campaign, tmp_path):
    adapter, _, _ = live_adapter(campaign, tmp_path)
    # The stage owns this stricter validator. Outer shape may pass without its
    # field; no schema or mathematical acceptance is invented by the adapter.
    request = packet(stage=8, response_schema={"type": "object", "required": ["stage_owned"]})
    assert json.loads(adapter.generate_candidate(request)) == {"candidate": 1}
    assert adapter.last_turn["pfp"]["evidence_grade"] == "UNVERIFIED"


def test_old_capture_replays_exactly_without_ledger_or_transport(campaign, tmp_path):
    output = tmp_path / "old"
    frozen_legacy_capture(campaign, output)
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    replay = campaign.PfpPipelineProviderAdapter(output, MODEL, replay=True,
        send=lambda *args: pytest.fail("old replay dispatched"))
    assert replay.generate_candidate(packet()) == '{"candidate":1}'
    assert replay.provider_calls == 0 and replay.cost_microusd == 2
    assert before == {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert not (output / "budget.sqlite3").exists()


@pytest.mark.parametrize("mutation", ["raw", "request", "reservation", "receipt", "packet", "pricing"])
def test_old_replay_retains_original_tamper_refusals(campaign, tmp_path, mutation):
    output = tmp_path / "old"
    frozen_legacy_capture(campaign, output)
    stage = output / "stage_1"
    replay_packet = packet()
    if mutation in ("raw", "request"):
        path = stage / ("provider_response.json" if mutation == "raw" else "request.json")
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "packet":
        replay_packet = packet(seed_sha256="b" * 64)
    elif mutation == "pricing":
        path = output / "pricing.json"
        saved = json.loads(path.read_bytes())
        saved["catalog_sha256"] = "different catalog with identical prices"
        path.write_bytes(campaign.canonical(saved))
    else:
        path = stage / f"{mutation}.json"
        saved = json.loads(path.read_bytes())
        saved["reserved_microusd" if mutation == "reservation" else "cost_microusd"] += 1
        path.write_bytes(campaign.canonical(saved))
    replay = campaign.PfpPipelineProviderAdapter(output, MODEL, replay=True)
    with pytest.raises(ValueError, match="REPLAY_(BINDING|RESERVATION|RESULT)_MISMATCH"):
        replay.generate_candidate(replay_packet)
    assert replay.provider_calls == 0
