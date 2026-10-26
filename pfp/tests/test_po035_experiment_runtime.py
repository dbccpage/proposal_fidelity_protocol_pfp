"""Historical v1 experiment custody, shared caps and current replay checks."""

from __future__ import annotations

import json
import sqlite3
from decimal import Decimal
from functools import partial
from types import SimpleNamespace

import pytest

from omega_engine_pfp.infrastructure.adapters.pfp_derivation import microusd
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import canonical, digest
from omega_engine_pfp.tests._po035_historical import (
    historical_derivation as pfp_derivation,
)
from omega_engine_pfp.tests._po035_historical import (
    historical_experiment as pfp_experiment,
)
from omega_engine_pfp.use_cases.pfp_derivation_loops import (
    DerivationLimits,
    run_derivation_loops,
)
from omega_engine_woland.tests.pilots.relational_spacetime import parameter_trials as experiments
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import fixture_payload
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID, proposal_body

PAID_PROFILE = {"model": "fixture/model", "ceiling_usd_per_token": "0.0000004"}
CONTROL_MARKER = "INDEPENDENT_CONTROL_RESPONSE_MUST_NOT_ENTER_TREATMENT"


def _payload(pilot, user):
    if user["stage"] in ("workpad_draft", "workpad_audit"):
        stage = "draft" if user["stage"] == "workpad_draft" else "audit"
        return {
            "derived_under_policy": "SPK-001",
            "workpad_schema": "pfp.po035-public-workpad.v1",
            "prompt_id": user["prompt_id"],
            "stage": stage,
            "public_records": [
                {
                    "record_id": f"{stage}_record",
                    "carrier": "host-only fixture",
                    "kind": "calculation",
                    "expression": f"{stage.upper()}_PUBLIC_MARKER",
                    "justification": "Offline custody fixture; no analytical certification.",
                    "status": "PROPOSED",
                }
            ],
            "candidate_certificate": proposal_body(fixture_payload(pilot, user["prompt_id"]))[
                "certificate"
            ],
            "open_obligations": ["Analytical derivation remains unverified."],
        }
    payload = fixture_payload(pilot, user["prompt_id"])
    if user["stage"] == "control":
        proposal_body(payload)["derivation"]["claim"] = CONTROL_MARKER
    return payload


def _run(
    tmp_path,
    monkeypatch,
    *,
    experiment="scratchpad",
    pilot=None,
    profile=None,
    limits=None,
    missing_cost=False,
    invalid_draft=False,
    observer=None,
    reported_usage=None,
):
    pilot = pilot or next(iter(BY_ID))
    folder = tmp_path / experiment / pilot
    calls = []
    port = None

    def send(model, request, maximum, timeout):
        user = json.loads(request.user)
        loop = len(calls) + 1
        wire = pfp_experiment.build_openai_compat_body(request, model=model, max_tokens=maximum)
        wire["usage"] = {"include": True}
        state = port.state()
        attempt = state["attempts"][str(loop)]
        assert attempt["state"] == "reserved"
        assert attempt["request_sha256"] == digest(canonical(wire))
        assert attempt["token_hold"] == len(canonical(wire)) + 512 + maximum
        assert attempt["reserved"] == microusd(port.rate * attempt["token_hold"])
        assert state["spent"] >= attempt["reserved"]
        assert 0 < timeout <= port.limits.seconds
        calls.append(
            {
                "wire": wire,
                "user": user,
                "hold": attempt["token_hold"],
                "reserved": attempt["reserved"],
                "timeout": timeout,
            }
        )
        payload = _payload(pilot, user)
        content = (
            "{}" if invalid_draft and user["stage"] == "workpad_draft" else json.dumps(payload)
        )
        usage = dict(prompt_tokens=20, completion_tokens=20, total_tokens=40)
        if not missing_cost:
            usage["cost"] = "0.000001" if port.rate else "0"
        if reported_usage:
            usage.update(reported_usage)
        return json.dumps(
            {
                "id": f"fixture-{loop}",
                "model": model,
                "usage": usage,
                "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            }
        ).encode()

    monkeypatch.setattr(pfp_experiment, "dispatch_deadline", send)
    monkeypatch.setattr(experiments, "EVIDENCE", tmp_path)
    monkeypatch.setattr(experiments, "sources", lambda: {})
    port = pfp_experiment.PfpExperimentAdapter(
        pilot=pilot,
        folder=folder,
        campaign=f"{experiments.CAMPAIGN}:{experiment}",
        model="fixture/model",
        pricing_sha256="fixture-catalog",
        sources={},
        profile=profile,
        prompt_builder=partial(experiments.render, experiment=experiment),
        observer=observer or partial(experiments.observe, experiment=experiment),
    )
    if limits is None:
        limits = DerivationLimits(loops=4 if experiment == "scratchpad" else 2)
    terminal = run_derivation_loops(port, limits)
    return port, terminal, calls, folder


@pytest.mark.parametrize("pilot", list(BY_ID))
def test_four_scratchpad_calls_share_one_budget_and_exclude_control(tmp_path, monkeypatch, pilot):
    port, terminal, calls, folder = _run(tmp_path, monkeypatch, pilot=pilot)
    assert terminal["terminal"] == "LOOP_LIMIT"
    assert (
        terminal["provider_calls"] == terminal["settled_calls"] == terminal["completed_loops"] == 4
    )
    assert terminal["tokens"] == 160 and terminal["cost_microusd"] == 0
    assert terminal["limits"] == vars(DerivationLimits(loops=4))
    assert [call["wire"]["max_tokens"] for call in calls] == [2500, 1000, 1000, 2500]
    assert [call["user"]["stage"] for call in calls] == [
        "control",
        "workpad_draft",
        "workpad_audit",
        "typed_final",
    ]
    assert all(CONTROL_MARKER not in json.dumps(call["wire"]) for call in calls[1:])
    assert "DRAFT_PUBLIC_MARKER" in json.dumps(calls[2]["wire"])
    assert "AUDIT_PUBLIC_MARKER" in json.dumps(calls[3]["wire"])
    assert set(port.state()["attempts"]) == {"1", "2", "3", "4"}
    for loop, call in enumerate(calls, 1):
        receipt = json.loads((folder / f"loop_{loop:02d}/provider_receipt.json").read_bytes())
        assert receipt["request_sha256"] == digest(canonical(call["wire"]))
        assert (folder / f"loop_{loop:02d}/request.json").read_bytes() == canonical(call["wire"])
    assert experiments.replay("scratchpad", [pilot])[0]["replayed_calls"] == 4


@pytest.mark.parametrize("pilot", list(BY_ID))
def test_temperature_pair_has_two_fresh_requests_and_real_wire_values(tmp_path, monkeypatch, pilot):
    _, terminal, calls, folder = _run(tmp_path, monkeypatch, experiment="temperature", pilot=pilot)
    assert terminal["provider_calls"] == terminal["completed_loops"] == 2
    assert [call["wire"]["temperature"] for call in calls] == [0, 0.7]
    assert calls[0]["wire"]["seed"] == calls[1]["wire"]["seed"]
    first, second = (dict(call["user"]) for call in calls)
    assert first.pop("prompt_id") != second.pop("prompt_id")
    assert first == second
    assert terminal["limits"] == vars(DerivationLimits(loops=2))
    for loop, call in enumerate(calls, 1):
        receipt = json.loads((folder / f"loop_{loop:02d}/provider_receipt.json").read_bytes())
        assert receipt["request_sha256"] == digest(canonical(call["wire"]))
    assert experiments.replay("temperature", [pilot])[0]["replayed_calls"] == 2


def test_logit_bias_reaches_actual_wire_and_bound_receipts(tmp_path, monkeypatch):
    import sys

    module = "omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls"
    tokenizer = tmp_path / "tokenizer-fixture"
    tokenizer.write_bytes(b"host-only tokenizer fixture")
    _missing_module = object()
    _previous_module = sys.modules.get(module, _missing_module)
    try:
        sys.modules[module] = SimpleNamespace(
            cached_tokenizer_path=lambda: tokenizer,
            format_only_logit_bias=lambda raw: {"12": -7, "34": 5},
        )
        _, terminal, calls, folder = _run(
            tmp_path, monkeypatch, experiment="logit", profile=PAID_PROFILE
        )
        assert terminal["provider_calls"] == 2
        assert [call["wire"]["temperature"] for call in calls] == [0.7, 0.7]
        assert calls[0]["wire"]["logit_bias"] == {}
        assert calls[1]["wire"]["logit_bias"] == {"12": -7, "34": 5}
        assert "reasoning" not in calls[1]["wire"]
        prompt = json.loads((folder / "loop_01/prompt.json").read_bytes())
        assert "/logit/" in prompt["prompt_uri"]
        assert prompt["stage_config"]["temperature"] == 0.7
        for loop, call in enumerate(calls, 1):
            receipt = json.loads((folder / f"loop_{loop:02d}/provider_receipt.json").read_bytes())
            assert receipt["request_sha256"] == digest(canonical(call["wire"]))
    finally:
        if _previous_module is _missing_module:
            sys.modules.pop(module, None)
        else:
            sys.modules[module] = _previous_module


def test_invalid_draft_is_not_forwarded_and_does_not_abort_later_stages(tmp_path, monkeypatch):
    _, terminal, calls, folder = _run(tmp_path, monkeypatch, invalid_draft=True)
    assert terminal["provider_calls"] == 4
    assert calls[2]["user"]["public_workpads_untrusted"] == {}
    assert calls[2]["user"]["workpad_feedback_codes"] == ["WORKPAD_SCHEMA_VIOLATION"]
    assert "draft" not in calls[3]["user"]["public_workpads_untrusted"]
    verdict = json.loads((folder / "loop_02/host_verdict.json").read_bytes())
    assert verdict["schema_status"] == "REFUSED"


@pytest.mark.parametrize("profile", [None, PAID_PROFILE])
def test_missing_cost_stops_and_retains_zero_or_paid_reservation(tmp_path, monkeypatch, profile):
    port, terminal, calls, folder = _run(tmp_path, monkeypatch, profile=profile, missing_cost=True)
    assert terminal["terminal"] == "INFRASTRUCTURE_ERROR"
    assert len(calls) == terminal["provider_calls"] == 1
    assert terminal["settled_calls"] == terminal["completed_loops"] == 0
    attempt = port.state()["attempts"]["1"]
    assert attempt["state"] == "reserved"
    assert attempt["token_hold"] > 0
    assert attempt["reserved"] == calls[0]["reserved"]
    assert terminal["cost_microusd"] == attempt["reserved"]
    assert bool(attempt["reserved"]) is bool(profile)
    error = json.loads((folder / "loop_01/infrastructure_error.json").read_bytes())
    assert error["hold_retained"] is True
    assert error["raw_sha256"] == digest((folder / "loop_01/raw_reply.json").read_bytes())
    assert experiments.replay("scratchpad", [next(iter(BY_ID))])[0]["replayed_calls"] == 0


def test_paid_holds_exist_before_dispatch_and_settle_to_reported_cost(tmp_path, monkeypatch):
    port, terminal, calls, _ = _run(tmp_path, monkeypatch, profile=PAID_PROFILE)
    assert len(calls) == 4 and all(call["reserved"] > 1 for call in calls)
    assert terminal["cost_microusd"] == port.state()["spent"] == 4
    assert all(attempt["actual"] == 1 for attempt in port.state()["attempts"].values())
    assert port.rate == Decimal(PAID_PROFILE["ceiling_usd_per_token"])


@pytest.mark.parametrize("limit", ["tokens", "cost"])
def test_pre_dispatch_reservation_refuses_inadequate_shared_cap(tmp_path, monkeypatch, limit):
    limits = DerivationLimits(loops=4, **({"tokens": 1} if limit == "tokens" else {"microusd": 1}))
    port, terminal, calls, _ = _run(tmp_path, monkeypatch, profile=PAID_PROFILE, limits=limits)
    assert calls == [] and port.state()["attempts"] == {}
    assert terminal["terminal"] == ("TOKEN_CAP" if limit == "tokens" else "COST_CAP")


def test_host_stage_time_is_in_same_interval_as_all_provider_stages(tmp_path, monkeypatch):
    clock = SimpleNamespace(value=0.0)
    source = SimpleNamespace(monotonic=lambda: clock.value)
    monkeypatch.setattr(pfp_derivation, "time", source)
    monkeypatch.setattr(pfp_experiment, "time", source)

    def observe(*args):
        context = experiments.observe(*args, experiment="scratchpad")
        clock.value += 180
        return context

    _, terminal, calls, _ = _run(tmp_path, monkeypatch, observer=observe)
    assert len(calls) == 1
    assert calls[0]["timeout"] <= (180 - 8) / 4
    assert terminal["terminal"] == "TIME_CAP"
    assert terminal["elapsed_seconds"] == 180


@pytest.mark.parametrize(
    "profile,usage,reason,cost,tokens",
    [
        (None, {"cost": "0.000001"}, "INFRASTRUCTURE_ERROR", 1, 40),
        (PAID_PROFILE, {"cost": "0.06"}, "COST_CAP", 60000, 40),
        (
            PAID_PROFILE,
            {"prompt_tokens": 119981, "completion_tokens": 20, "total_tokens": 120001},
            "TOKEN_CAP",
            None,
            120001,
        ),
    ],
)
def test_reported_overruns_stop_and_retain_observed_usage(
    tmp_path, monkeypatch, profile, usage, reason, cost, tokens
):
    port, terminal, calls, folder = _run(
        tmp_path, monkeypatch, profile=profile, reported_usage=usage
    )
    assert len(calls) == 1 and terminal["settled_calls"] == 0
    assert terminal["terminal"] == reason
    assert terminal["tokens"] == tokens
    attempt = port.state()["attempts"]["1"]
    assert attempt["state"] == "reserved"
    assert terminal["cost_microusd"] == (cost if cost is not None else calls[0]["reserved"])
    error = json.loads((folder / "loop_01/infrastructure_error.json").read_bytes())
    assert error["observed_unsettled_usage"]["tokens"] == tokens
    assert experiments.replay("scratchpad", [next(iter(BY_ID))])[0]["replayed_calls"] == 0


@pytest.mark.parametrize("mutation", ["request", "error", "ledger_hold"])
def test_replay_refuses_pending_attempt_mutations(tmp_path, monkeypatch, mutation):
    _, _, _, folder = _run(tmp_path, monkeypatch, profile=PAID_PROFILE, missing_cost=True)
    pilot = next(iter(BY_ID))
    assert experiments.replay("scratchpad", [pilot])[0]["replayed_calls"] == 0
    if mutation == "request":
        path = folder / "loop_01/request.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "error":
        path = folder / "loop_01/infrastructure_error.json"
        error = json.loads(path.read_bytes())
        error["raw_sha256"] = "0" * 64
        path.write_text(json.dumps(error), encoding="utf-8")
    else:
        snapshot_path = folder / "budget_snapshot.json"
        snapshot = json.loads(snapshot_path.read_bytes())
        snapshot["attempts"]["1"]["token_hold"] += 1
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        with sqlite3.connect(folder / "budget.sqlite3") as connection:
            connection.execute(
                "UPDATE provider_budget SET state=? WHERE id=?", (json.dumps(snapshot), pilot)
            )
    with pytest.raises(ValueError):
        experiments.replay("scratchpad", [pilot])


@pytest.mark.parametrize(
    "mutation",
    [
        "raw",
        "request",
        "prompt",
        "receipt",
        "completed",
        "limits",
        "run_limits",
        "reason",
        "sqlite",
        "pricing",
    ],
)
def test_replay_refuses_digest_accounting_and_limit_mutations(tmp_path, monkeypatch, mutation):
    _, _, _, folder = _run(tmp_path, monkeypatch, experiment="temperature")
    pilot = next(iter(BY_ID))
    assert experiments.replay("temperature", [pilot])[0]["replayed_calls"] == 2
    if mutation in ("raw", "request"):
        path = folder / "loop_01" / ("raw_reply.json" if mutation == "raw" else "request.json")
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "sqlite":
        with sqlite3.connect(folder / "budget.sqlite3") as connection:
            encoded = connection.execute(
                "SELECT state FROM provider_budget WHERE id=?", (pilot,)
            ).fetchone()[0]
            state = json.loads(encoded)
            state["spent"] += 1
            connection.execute(
                "UPDATE provider_budget SET state=? WHERE id=?", (json.dumps(state), pilot)
            )
    else:
        name = {
            "prompt": "loop_01/prompt.json",
            "receipt": "loop_01/provider_receipt.json",
            "pricing": "pricing_profile.json",
            "run_limits": "run.json",
        }.get(mutation, "terminal.json")
        path = folder / name
        document = json.loads(path.read_bytes())
        if mutation == "prompt":
            document["user_prompt"] += " "
        elif mutation == "receipt":
            document["elapsed_seconds"] = -1
        elif mutation == "completed":
            document["completed_loops"] = 0
        elif mutation in ("limits", "run_limits"):
            document["limits"]["tokens"] = 120001
        elif mutation == "reason":
            document["terminal"] = "TIME_CAP"
        elif mutation == "pricing":
            document["ceiling_usd_per_token"] = "0.001"
        path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        experiments.replay("temperature", [pilot])
