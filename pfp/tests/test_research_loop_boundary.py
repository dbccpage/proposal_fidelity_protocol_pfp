"""Synthetic current PO035 turns: shared PFP, original deadlines/ledger/host seam."""

import json
import pytest

from omega_engine_pfp.infrastructure.adapters import pfp_derivation as derivation
from omega_engine_pfp.infrastructure.adapters import pfp_experiment as experiment
from omega_engine_pfp.use_cases.pfp_derivation_loops import DerivationLimits, run_derivation_loops


def prompt_builder(pilot, loop, context):
    return dict(system_prompt="Return a JSON proposal for the finite public task.",
        user_prompt=json.dumps(dict(public_input=loop, prior=context)), generation=loop)


def run_fixture(tmp_path, monkeypatch, *, kind="derivation", malformed=None,
                unknown_cost=False, transport_error=None, limits=None, cost=0,
                duplicate_generation=False):
    module = derivation if kind == "derivation" else experiment
    calls, observed = [], []
    folder = tmp_path / "new-run"

    def render(pilot, loop, context):
        prompt = prompt_builder(pilot, loop, context)
        if kind == "experiment":
            prompt.update(max_output_tokens=128, experiment_stage="typed_candidate",
                experiment_decoding=dict(seed=17, temperature=0.7, thinking="disabled",
                    logit_bias={"10": -1}))
        return prompt

    def dispatch(model, request, maximum, timeout):
        wire = module.build_openai_compat_body(request, model=model, max_tokens=maximum)
        wire["usage"] = {"include": True}
        assert 0 < timeout <= port.limits.seconds
        assert port.state()["attempts"][str(len(calls) + 1)]["state"] == "reserved"
        calls.append(dict(request=request, wire=wire, timeout=timeout))
        if transport_error:
            raise transport_error
        task = json.loads(request.user)
        reply = {key: task[key] for key in ("task_id", "attempt_id", "input_sha256")}
        reply["answer"] = dict(value=len(calls))
        if malformed == "answer-unicode":
            reply["answer"] = "\ud800"
        if malformed == "binding":
            reply["attempt_id"] = "wrong-attempt"
        content = malformed if malformed not in (None, "binding", "answer-unicode") else json.dumps(reply)
        raw = json.dumps(dict(id=f"fixture-{1 if duplicate_generation else len(calls)}", model=model,
            usage=dict(prompt_tokens=10, completion_tokens=10, total_tokens=20,
                cost=None if unknown_cost else cost),
            choices=[dict(message=dict(content=content), finish_reason="stop")]),
            ensure_ascii=True).encode("ascii")
        if malformed == "provider-json":
            raw = b"malformed provider JSON"
        calls[-1]["raw"] = raw
        return raw

    def observer(pilot, loop, path, prompt, result, receipt, context):
        answer = json.loads(result["content"])
        observed.append(answer)
        return dict(host_value=answer["value"])

    monkeypatch.setattr(module, "dispatch_deadline", dispatch)
    klass = module.PfpDerivationAdapter if kind == "derivation" else module.PfpExperimentAdapter
    port = klass(pilot="synthetic-research", folder=folder, campaign="bounded-fixture",
        model="fixture/model", pricing_sha256="fixture-pricing", sources={},
        prompt_builder=render, observer=observer)
    terminal = run_derivation_loops(port, limits or DerivationLimits(loops=2))
    return module, port, terminal, calls, observed, render, observer


@pytest.mark.parametrize("kind", ["derivation", "experiment"])
def test_current_replay_regenerates_actual_binding_and_original_decoding(tmp_path, monkeypatch, kind):
    module, port, terminal, calls, observed, render, observer = run_fixture(tmp_path, monkeypatch, kind=kind)
    assert terminal["completed_loops"] == terminal["settled_calls"] == terminal["provider_calls"] == 2
    assert terminal["cost_microusd"] == 0 and terminal["analytical_status"] == "UNVERIFIED"
    assert len(port.state()["attempts"]) == 2
    wire = calls[0]["wire"]
    assert wire["provider"] == {"allow_fallbacks": False, "require_parameters": True}
    assert "response_format" not in wire
    if kind == "experiment":
        assert wire["seed"] == 17 and wire["temperature"] == 0.7
        assert wire["logit_bias"] == {"10": -1} and wire["max_tokens"] == 128
    else:
        assert wire["seed"] == 1001 and wire["temperature"] == 0 and wire["max_tokens"] == 2500
    before = {p.relative_to(port.folder): p.read_bytes() for p in port.folder.rglob("*") if p.is_file()}
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    replay = derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})
    assert replay["replayed_calls"] == replay["completed_loops"] == 2
    assert replay["context"] == terminal["context"] and len(calls) == 2
    assert before == {p.relative_to(port.folder): p.read_bytes() for p in port.folder.rglob("*") if p.is_file()}


@pytest.mark.parametrize("malformed", ["not JSON", "binding", "\ud800", "answer-unicode", "provider-json"])
def test_bad_reply_never_reaches_observer_and_replay_preserves_refusal(tmp_path, monkeypatch, malformed):
    module, port, terminal, calls, observed, render, observer = run_fixture(tmp_path, monkeypatch, malformed=malformed)
    assert terminal["completed_loops"] == 0 and not observed and len(calls) == 1
    assert (port.folder / "loop_01/raw_reply.json").read_bytes() == calls[0]["raw"]
    assert terminal["terminal"] != "LOOP_LIMIT"
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    replay = derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})
    assert replay["completed_loops"] == 0 and replay["terminal"] == terminal["terminal"]
    assert not observed


@pytest.mark.parametrize("kind", ["derivation", "experiment"])
def test_unknown_billing_retains_wire_and_hold_with_no_observer(tmp_path, monkeypatch, kind):
    module, port, terminal, calls, observed, render, observer = run_fixture(tmp_path, monkeypatch,
        kind=kind, unknown_cost=True)
    assert terminal["cost_microusd"] is None and terminal["known_cost_microusd"] == 0
    assert terminal["terminal"] == "INFRASTRUCTURE_ERROR" and len(calls) == 1 and not observed
    assert port.state()["attempts"]["1"]["state"] == "reserved"
    assert (port.folder / "loop_01/raw_reply.json").read_bytes() == calls[0]["raw"]
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    assert derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})["terminal"] == terminal["terminal"]


def test_ambiguous_deadline_stop_is_unknown_and_zero_send_replay(tmp_path, monkeypatch):
    import subprocess
    module, port, terminal, calls, observed, render, observer = run_fixture(tmp_path, monkeypatch,
        transport_error=subprocess.TimeoutExpired("fixture", 0.001))
    assert terminal["cost_microusd"] is None and terminal["provider_calls"] == 1 and not observed
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    assert derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})["terminal"] == "INFRASTRUCTURE_ERROR"
    assert len(calls) == 1


def test_known_bill_of_binding_refusal_stays_known(tmp_path, monkeypatch):
    _, port, terminal, calls, observed, _, _ = run_fixture(tmp_path, monkeypatch, malformed="binding", cost=0.000001)
    assert terminal["cost_microusd"] == terminal["known_cost_microusd"] == 1
    assert terminal["settled_calls"] == 1 and terminal["completed_loops"] == 0
    assert not observed and len(calls) == 1


def test_duplicate_generation_retains_observed_liability_before_stopping(tmp_path, monkeypatch):
    module, port, terminal, calls, observed, render, observer = run_fixture(
        tmp_path, monkeypatch, cost=0.000001, duplicate_generation=True)
    assert terminal["terminal"] == "INFRASTRUCTURE_ERROR"
    assert terminal["provider_calls"] == 2 and terminal["settled_calls"] == 1
    assert terminal["tokens"] == 40 and terminal["known_cost_microusd"] == 2
    assert terminal["cost_microusd"] == terminal["reserved_liability_microusd"] == 2
    assert observed == [{"value": 1}]
    duplicate = port.state()["attempts"]["2"]
    assert duplicate["state"] == "reserved"
    assert duplicate["observed"] == {"tokens": 20, "cost_microusd": 1}
    assert (port.folder / "loop_02/raw_reply.json").read_bytes() == calls[1]["raw"]
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    replay = derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})
    assert replay["terminal"] == "INFRASTRUCTURE_ERROR" and replay["completed_loops"] == 1
    assert len(calls) == 2


@pytest.mark.parametrize("kind", ["derivation", "experiment"])
def test_no_send_budget_refusal_is_known_zero_and_replays(tmp_path, monkeypatch, kind):
    module, port, terminal, calls, observed, render, observer = run_fixture(tmp_path, monkeypatch,
        kind=kind, limits=DerivationLimits(tokens=1))
    assert terminal["terminal"] == "TOKEN_CAP" and terminal["provider_calls"] == 0
    assert terminal["cost_microusd"] == 0 and not calls and not observed
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    assert derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})["terminal"] == "TOKEN_CAP"


@pytest.mark.parametrize("mutation", ["raw", "request", "pfp", "terminal"])
def test_current_replay_refuses_tampering(tmp_path, monkeypatch, mutation):
    module, port, _, _, _, render, observer = run_fixture(tmp_path, monkeypatch)
    if mutation in ("raw", "request"):
        path = port.folder / "loop_01" / ("raw_reply.json" if mutation == "raw" else "request.json")
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path = port.folder / ("loop_01/pfp_check.json" if mutation == "pfp" else "terminal.json")
        value = json.loads(path.read_bytes())
        value["evidence_grade" if mutation == "pfp" else "completed_loops"] = "HOST_ACCEPTED" if mutation == "pfp" else 1
        path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    with pytest.raises(ValueError):
        derivation.replay_run(port.folder, port.pilot, port.model, render, observer, {})


def test_existing_run_refuses_before_dispatch_and_preserves_bytes(tmp_path, monkeypatch):
    module, port, _, calls, _, _, _ = run_fixture(tmp_path, monkeypatch)
    before = {p.relative_to(port.folder): p.read_bytes() for p in port.folder.rglob("*") if p.is_file()}
    monkeypatch.setattr(module, "dispatch_deadline", lambda *a: pytest.fail("existing run sent"))
    with pytest.raises(ValueError, match="RUN_ALREADY_EXISTS"):
        run_derivation_loops(port, DerivationLimits(loops=2))
    assert len(calls) == 2
    assert before == {p.relative_to(port.folder): p.read_bytes() for p in port.folder.rglob("*") if p.is_file()}


def test_current_derivation_mediates_actual_prompt_before_host(tmp_path, monkeypatch):
    module, port, terminal, calls, observed, _, _ = run_fixture(tmp_path, monkeypatch)
    assert terminal["terminal"] == "LOOP_LIMIT" and observed == [{"value": 1}, {"value": 2}]
    assert json.loads((port.folder / "run.json").read_bytes())["schema"] == "pfp.derivation-run.v2"
    assert calls[0]["wire"]["seed"] == 1001 and "response_format" not in calls[0]["wire"]
    assert json.loads(calls[0]["request"].user)["input"]["prompt"] == prompt_builder("x", 1, {})["user_prompt"]
