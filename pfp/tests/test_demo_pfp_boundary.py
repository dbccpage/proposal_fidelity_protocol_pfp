"""Current demo proposals use the shared boundary and preserve traced raw custody."""

import base64
import io
import json
import sys

import pytest

from operations.domain.rop.result import Ok
from pfp.domain.demos import DemoRefusal
from pfp.infrastructure.demos import execution
from pfp.tests.test_pilot_matrix_pfp import make_gateway


def test_live_proposal_checks_actual_bound_reply(tmp_path):
    gateway, provider = make_gateway(tmp_path, answer={"candidate": "op<<0>>"}, max_output_tokens=256)
    proposals = execution.Proposals(gateway, live=True, model="vendor/model", max_output_tokens=256,
        max_provider_calls=1, run_id="demo-test")
    assert json.loads(proposals.propose("public task", "host-only oracle")) == {"candidate": "op<<0>>"}
    assert "host-only oracle" not in provider.calls[0].user
    assert proposals.last_turn["pfp"]["failure_class"] == "NONE"
    assert base64.b64decode(proposals.last_turn["provider_wire"]["raw_reply_base64"]) == provider.raw


@pytest.mark.parametrize("raw, cost", [("not-json", 0.000001),
    ('{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":"x"}', 0.000001),
    (None, None)])
def test_failed_live_turn_is_retained_and_stops_later_proposals(tmp_path, raw, cost):
    gateway, provider = make_gateway(tmp_path, answer="candidate", raw_content=raw,
        cost=cost, max_output_tokens=256)
    proposals = execution.Proposals(gateway, live=True, model="vendor/model", max_output_tokens=256,
        max_provider_calls=4, run_id="demo-test")
    with pytest.raises(DemoRefusal):
        proposals.propose("public task", "host-only oracle")
    assert len(provider.calls) == len(proposals.transcript) == 1
    assert base64.b64decode(proposals.last_turn["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert proposals.transcript[0]["error"]
    with pytest.raises(DemoRefusal):
        proposals.propose("later task", "host-only oracle")
    assert len(provider.calls) == 1


def test_live_requires_explicit_bounds_before_output_or_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr("pfp.infrastructure.estimated_gateway.resolve_openrouter_key",
        lambda *a, **k: pytest.fail("credentials before preflight"))
    with pytest.raises(DemoRefusal, match="LIVE_BOUNDS_REQUIRED"):
        execution.run("demo_3", tmp_path / "new", live=True, model="openai/gpt-4o-mini")
    assert not (tmp_path / "new").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="existing live artifact protector requires Windows DPAPI")
def test_trace_pair_and_pricing_configuration_refuse_without_sends(tmp_path, monkeypatch):
    import pfp.infrastructure.estimated_gateway as factory
    monkeypatch.setattr(factory, "resolve_openrouter_key", lambda *a, **k: pytest.fail("credential lookup"))
    with pytest.raises(ValueError, match="TRACE_AND_ARTIFACT_STORE_REQUIRED_TOGETHER"):
        factory.create_accounted_openrouter_gateway("model", 256, trace=object())
    monkeypatch.setattr(factory, "resolve_openrouter_key", lambda *a, **k: Ok("synthetic-only"))
    def unavailable(*args, **kwargs):
        raise ValueError("MODEL_PRICING_UNAVAILABLE")
    monkeypatch.setattr(factory, "snapshot_pricing", unavailable)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("provider send"))
    receipt = execution.run("demo_3", tmp_path / "new", live=True, model="openai/gpt-4o-mini",
        max_output_tokens=256, max_provider_calls=1, max_estimated_cost_microusd=4000)
    assert receipt["result"]["code"] == "LIVE_CONFIGURATION_REFUSED"
    assert receipt["result"]["status"] == "TYPED_REFUSAL"


@pytest.mark.skipif(sys.platform != "win32", reason="existing live artifact protector requires Windows DPAPI")
def test_actual_composition_preserves_encrypted_trace_and_original_host(tmp_path, monkeypatch):
    import pfp.infrastructure.estimated_gateway as factory
    from pfp.infrastructure.adapters.mssn_scenarios.protocol import run_live_arm
    from pfp.infrastructure.trace.execution_trace import verify_trace
    from pfp.infrastructure.trace.provider_dispatch import DISPATCH_COMPLETE, derive_dispatch_outcomes

    calls, wires = [], []
    def send(request, timeout):
        body = json.loads(request.data)
        public = json.loads(body["messages"][-1]["content"])
        calls.append(body)
        content = json.dumps({**{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
            "answer": "unparsed model proposal"})
        wire = json.dumps({"id": "generation-demo-1", "model": "openai/gpt-4o-mini",
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "cost": 0.000001}}).encode()
        wires.append(wire)
        return io.BytesIO(wire)
    monkeypatch.setattr("urllib.request.urlopen", send)
    monkeypatch.setattr(factory, "resolve_openrouter_key", lambda *a, **k: Ok("synthetic-only"))
    monkeypatch.setattr(factory, "snapshot_pricing", lambda *a, **k: {"catalog_sha256": "fixture",
        "row": {"id": "openai/gpt-4o-mini", "pricing": {"prompt": "0.000000001", "completion": "0.000000001"}}})
    def one_original_arm(scenario, fixture, proposals, quarantine, **kwargs):
        result = run_live_arm("gauge_even_triangle", "P", lambda prompt: proposals.propose(prompt, ""), max_turns=1)
        return {"status": "CHECKED", "host": result}
    monkeypatch.setattr(execution, "run_named", one_original_arm)
    output = tmp_path / "new"
    receipt = execution.run("demo_3", output, live=True, model="openai/gpt-4o-mini",
        max_output_tokens=256, max_provider_calls=1, max_estimated_cost_microusd=4000)
    assert len(calls) == 1 and receipt["result"]["host"]["final_exit"] is None
    assert receipt["result"]["host"]["turns"][0]["host_decision"] == "UNPARSED_MODEL_MOVES"
    scan = verify_trace(output / "trace.jsonl", expected_terminal_digest=receipt["trace_terminal_digest"])
    store = execution.artifact_store(output, True)
    outcomes = derive_dispatch_outcomes(scan.records, artifact_store=store)
    assert len(outcomes) == 1 and outcomes[0].status == DISPATCH_COMPLETE
    assert store.get_canonical(outcomes[0].encrypted_artifact_ref) == wires[0]
    assert execution.verify(output / "receipt.json")["status"] == "INTEGRITY_ONLY"
    monkeypatch.setattr("pfp.infrastructure.trace.provider_dispatch.derive_dispatch_outcomes",
        lambda *a, **k: ())
    with pytest.raises(DemoRefusal, match="PROVIDER_EVIDENCE_MISSING"):
        execution.verify(output / "receipt.json")
