"""Current research entrypoints retain original observers in fresh captures."""

import json

import pytest

from omega_engine_pfp.infrastructure.adapters import pfp_derivation, pfp_experiment
from omega_engine_pfp.use_cases.pfp_derivation_loops import DerivationLimits
from omega_engine_woland.tests.pilots.relational_spacetime import baseline, compact_trials
from omega_engine_woland.tests.pilots.relational_spacetime import parameter_trials, typed_signals


@pytest.mark.parametrize("kind", ["baseline", "typed", "temperature", "compact"])
def test_current_entrypoint_checks_pfp_then_original_observer_and_replays(tmp_path, monkeypatch, kind):
    module = {"baseline": baseline, "typed": typed_signals,
              "temperature": parameter_trials, "compact": compact_trials}[kind]
    pilot, model = next(iter(baseline.BY_ID)), "fixture/free-model"
    catalog = json.dumps({"data": [{"id": model,
        "supported_parameters": ["max_tokens", "temperature", "reasoning", "seed"],
        "pricing": {"prompt": "0", "completion": "0"}}]}).encode()
    monkeypatch.setattr(module, "fetch_openrouter_catalog", lambda **kwargs: catalog)
    monkeypatch.setattr(module, "sources", lambda: {"files": {}})
    sent = []

    def send(selected, request, maximum, timeout):
        assert selected == model and timeout > 0
        task = json.loads(request.user)
        assert isinstance(task["input"]["prompt"], str)
        sent.append(task)
        # A correct binding admits this empty proposal to the original judge,
        # which must refuse it. PFP validity cannot manufacture a science result.
        reply = {key: task[key] for key in ("task_id", "attempt_id", "input_sha256")}
        reply["answer"] = {}
        return json.dumps({"id": f"synthetic-{len(sent)}", "model": model,
            "usage": {"prompt_tokens": 20, "completion_tokens": 20,
                      "total_tokens": 40, "cost": 0},
            "choices": [{"message": {"content": json.dumps(reply)},
                         "finish_reason": "stop"}]}).encode()

    monkeypatch.setattr(pfp_derivation, "dispatch_deadline", send)
    monkeypatch.setattr(pfp_experiment, "dispatch_deadline", send)
    output = tmp_path / "current"
    if kind == "baseline":
        terminal = module.run(pilot, output=output, model=model, limits=DerivationLimits(loops=1))
        replay = lambda: module.replay_current(output, pilot)
        folder = output
    elif kind == "typed":
        prior = tmp_path / "prior"
        prior.mkdir()
        (prior / "terminal.json").write_text(json.dumps({"pilot_id": pilot,
            "provider_calls": 4, "settled_calls": 4, "cost_microusd": 0,
            "tokens": 100, "elapsed_seconds": 1}), encoding="utf-8")
        terminal = module.run(pilot, output=output, model=model, prior_run=prior)
        replay = lambda: module.replay_current(output, pilot)
        folder = output
    elif kind == "temperature":
        terminal = module.run("temperature", [pilot], output=output, model=model)[0]
        replay = lambda: module.replay("temperature", [pilot], output=output)
        folder = output / "temperature" / pilot
    else:
        preparation = tmp_path / "preparation"
        module.prepare(output=preparation, model=model)
        terminal = module.run([pilot], output=output, model=model,
                              preflight=preparation / "preflight.json")[0]
        replay = lambda: module.replay([pilot], output=output)
        folder = output / pilot
    assert terminal["terminal"] == "LOOP_LIMIT"
    assert len(sent) == {"baseline": 1, "typed": 1, "temperature": 2, "compact": 3}[kind]
    verdict = json.loads((folder / "loop_01/host_verdict.json").read_bytes())
    assert verdict["schema_status"] == "REFUSED"
    if kind in ("baseline", "typed"):
        assert list((output / "capsules" / pilot / "tests").glob("**/response.yaml"))
    captured = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    monkeypatch.setattr(pfp_derivation, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    monkeypatch.setattr(pfp_experiment, "dispatch_deadline", lambda *a: pytest.fail("replay sent"))
    replay()
    assert captured == {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}


def test_fresh_output_refuses_history_and_reuse_before_network(tmp_path):
    pilot = next(iter(baseline.BY_ID))
    with pytest.raises(ValueError, match="FRESH_OUTPUT_REQUIRED"):
        baseline.fresh_run_output(None, model="fixture", pilots=[pilot])
    with pytest.raises(ValueError, match="HISTORICAL_OUTPUT_FORBIDDEN"):
        baseline.fresh_run_output(baseline.PILOTS / "new-current-capture", model="fixture", pilots=[pilot])
    with pytest.raises(ValueError, match="RUN_ALREADY_EXISTS"):
        baseline.fresh_run_output(tmp_path, model="fixture", pilots=[pilot])


def test_typed_continuation_does_not_reset_unknown_prior_bill(tmp_path, monkeypatch):
    pilot = next(iter(baseline.BY_ID))
    (tmp_path / "terminal.json").write_text(json.dumps({"pilot_id": pilot,
        "provider_calls": 1, "settled_calls": 0, "cost_microusd": None}), encoding="utf-8")
    monkeypatch.setattr(typed_signals, "fetch_openrouter_catalog", lambda **k: pytest.fail("network"))
    with pytest.raises(ValueError, match="PRIOR_RUN_REQUIRES_RECONCILIATION"):
        typed_signals.run(pilot, output=tmp_path / "new", model="fixture", prior_run=tmp_path)
