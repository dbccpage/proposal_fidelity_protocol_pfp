"""Pinned v1 fixture/replay controls plus current fresh-output admission checks."""

import json
import sqlite3

import pytest
import yaml

from adversary.tests.pilots.relational_spacetime import compact_trials as round_
from adversary.tests.pilots.relational_spacetime.tasks import BY_ID
from adversary.tests.pilots.relational_spacetime.tasks import proposal_body
from pfp.infrastructure.numbered_prompts import FIELD_CARRIERS
from adversary.tests.pilots.relational_spacetime.finite_fixtures import fixture_payload
from pfp.infrastructure.adapters import pfp_experiment
from pfp.tests._po035_historical import historical_experiment
from pfp.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)
from pfp.use_cases.pfp_derivation_loops import run_derivation_loops


def test_current_sources_bind_canonical_versioned_profile():
    pins = round_.sources()["files"]
    assert str(round_.TEMPLATES.relative_to(round_.ROOT)).replace("\\", "/") == (
        "pfp/infrastructure/yaml/prompts/templates"
    )
    assert (
        "pfp/infrastructure/yaml/prompts/templates/"
        "template_role_registry.yaml"
    ) in pins
    assert (
        "pfp/infrastructure/yaml/prompts/templates/"
        "template_pfp_r0001.yaml"
    ) in pins
    assert "education/pilots/evidence/po035_simplified_20261012/spec.yaml" not in pins
    assert not any(path.startswith("education/pfp/") for path in pins)
    assert "pfp/infrastructure/numbered_prompts.py" in pins
    assert "education/pilots/relational_spacetime/compact_prompts.py" not in pins


def test_current_campaign_does_not_reuse_frozen_namespace():
    assert round_.CAMPAIGN == "po035_simplified_v1_0_4_20261013"
    assert round_.EVIDENCE.name == round_.CAMPAIGN


def final_fixture(pilot, prompt_id, marker):
    envelope = fixture_payload(pilot, prompt_id)
    body = proposal_body(envelope)
    certificate = body["certificate"]
    body.clear()
    body.update(
        prompt_id=prompt_id,
        status="PROPOSAL",
        derivation={"argument": marker, "open": ["Offline fixture is not an analytical proof."]},
        certificate=certificate,
        calculations={
            field: {
                "carrier": FIELD_CARRIERS[pilot][field],
                "expression": "OFFLINE_FIXTURE_ONLY",
                "result": value,
            }
            for field, value in certificate.items()
        },
    )
    return envelope


def run_fixture(tmp_path, monkeypatch, *, invalid_pad=False, missing_cost=False):
    pilot = next(iter(BY_ID))
    folder = tmp_path / pilot
    monkeypatch.setattr(round_, "EVIDENCE", tmp_path)
    catalog = (
        round_.PILOTS / "evidence/po035_experiments_20261012/catalog_scratchpad.json"
    ).read_bytes()
    write_once(tmp_path / "catalog.json", catalog)
    profile = {
        "model": round_.MODEL,
        "ceiling_usd_per_token": "0",
        "selected_model": round_.model_pricing(catalog, round_.MODEL),
    }
    calls = []
    port = historical_experiment.PfpExperimentAdapter(
        pilot=pilot,
        folder=folder,
        campaign=round_.CAMPAIGN,
        model=round_.MODEL,
        pricing_sha256=digest(catalog),
        sources=round_.sources(),
        profile=profile,
        prompt_builder=round_.render,
        observer=round_.observe,
    )

    def send(model, request, maximum, timeout):
        loop = len(calls) + 1
        wire = yaml.safe_load(request.user)
        state = port.state()
        require = state["attempts"][str(loop)]
        assert require["state"] == "reserved"
        assert require["reserved"] == 0
        assert 0 < timeout <= 180
        assert request.decoding.temperature == 0
        assert request.decoding.allow_fallbacks is False
        assert maximum == (600 if loop == 2 else 2500)
        calls.append(wire)
        if loop == 2:
            packet = {
                "derived_under_policy": "SPK-001",
                "prompt_id": wire["prompt_id"],
                "records": [
                    {
                        "field": "l1_radius",
                        "expression": "PUBLIC_DRAFT_MARKER",
                        "result": "unverified",
                    }
                ],
                "open": ["Check this record."],
            }
            content = "{}" if invalid_pad else json.dumps(packet)
        else:
            content = json.dumps(
                final_fixture(
                    pilot,
                    wire["prompt_id"],
                    "CONTROL_ONLY_MARKER" if loop == 1 else "FINAL_FIXTURE_MARKER",
                )
            )
        usage = {"prompt_tokens": 20, "completion_tokens": 20, "total_tokens": 40}
        if not missing_cost:
            usage["cost"] = 0
        return canonical(
            {
                "id": f"offline-generation-{loop}",
                "model": model,
                "usage": usage,
                "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            }
        )

    monkeypatch.setattr(historical_experiment, "dispatch_deadline", send)
    terminal = run_derivation_loops(port, round_.LIMITS)
    return pilot, folder, calls, terminal


@pytest.mark.parametrize("invalid_pad", [False, True])
def test_complete_round_replays_and_control_cannot_carry(tmp_path, monkeypatch, invalid_pad):
    pilot, folder, calls, terminal = run_fixture(tmp_path, monkeypatch, invalid_pad=invalid_pad)
    assert terminal["provider_calls"] == terminal["settled_calls"] == 3
    assert terminal["tokens"] == 120
    assert terminal["cost_microusd"] == 0
    assert terminal["terminal"] == "LOOP_LIMIT"
    assert "CONTROL_ONLY_MARKER" not in json.dumps(calls[1:])
    assert ("PUBLIC_DRAFT_MARKER" in json.dumps(calls[2])) is not invalid_pad
    assert round_.replay_complete_run(folder, pilot)["replayed_calls"] == 3


def test_missing_cost_retains_hold_and_stops(tmp_path, monkeypatch):
    _, folder, calls, terminal = run_fixture(tmp_path, monkeypatch, missing_cost=True)
    assert len(calls) == 1
    assert terminal["terminal"] == "INFRASTRUCTURE_ERROR"
    assert terminal["settled_calls"] == 0
    snapshot = json.loads((folder / "budget_snapshot.json").read_text())
    assert snapshot["attempts"]["1"]["state"] == "reserved"
    with pytest.raises(ValueError, match="PARTIAL_RUN_REQUIRES_RECONCILIATION"):
        round_.replay_complete_run(folder, next(iter(BY_ID)))


@pytest.mark.parametrize(
    "mutation",
    [
        "raw",
        "verdict",
        "context",
        "missing_loop",
        "snapshot",
        "typed_reservation",
        "limits",
        "role",
    ],
)
def test_replay_rejects_decisive_mutations(tmp_path, monkeypatch, mutation):
    pilot, folder, _, _ = run_fixture(tmp_path, monkeypatch)
    if mutation == "raw":
        path = folder / "loop_01/raw_reply.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation in ("verdict", "context"):
        name = "host_verdict.json" if mutation == "verdict" else "next_context.json"
        (folder / "loop_01" / name).write_text('{"injected_control":"forbidden"}')
    elif mutation == "missing_loop":
        (folder / "loop_02").rename(folder / "missing_workpad")
    elif mutation in ("snapshot", "typed_reservation"):
        path = folder / "budget_snapshot.json"
        snapshot = json.loads(path.read_text())
        snapshot["attempts"]["1"]["reserved"] = False if mutation == "typed_reservation" else 1
        path.write_text(json.dumps(snapshot))
        if mutation == "typed_reservation":
            with sqlite3.connect(folder / "budget.sqlite3") as db:
                db.execute(
                    "UPDATE provider_budget SET state=? WHERE id=?", (json.dumps(snapshot), pilot)
                )
    else:
        path = folder / ("run.json" if mutation == "limits" else "loop_01/prompt.json")
        value = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "limits":
            value["limits"]["loops"] = 4
        else:
            value["experiment_stage"] = "WRONG_ROLE"
        path.write_text(json.dumps(value))
    with pytest.raises((ValueError, FileNotFoundError)):
        round_.replay_complete_run(folder, pilot)


def test_existing_run_refuses_before_catalog_fetch(tmp_path, monkeypatch):
    pilot = next(iter(BY_ID))
    preparation = tmp_path / "preparation"
    round_.prepare(output=preparation, model=round_.MODEL)
    write_once(tmp_path / pilot / "run.json", {})
    calls = []
    monkeypatch.setattr(round_, "fetch_openrouter_catalog", lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ValueError, match="RUN_ALREADY_EXISTS"):
        round_.run([pilot], output=tmp_path, model=round_.MODEL,
            preflight=preparation / "preflight.json")
    assert calls == []


def test_preflight_source_drift_refuses_before_catalog_fetch(tmp_path, monkeypatch):
    preparation = tmp_path / "preparation"
    previews = round_.prepare(output=preparation, model=round_.MODEL)
    assert len(previews) == 15
    assert all((preparation / p["path"]).exists() for p in previews)
    monkeypatch.setattr(round_, "sources", lambda: {"files": {"changed": "source"}})
    calls = []
    monkeypatch.setattr(round_, "fetch_openrouter_catalog", lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ValueError, match="PREFLIGHT_SOURCE_DRIFT"):
        round_.run([next(iter(BY_ID))], output=tmp_path / "run", model=round_.MODEL,
            preflight=preparation / "preflight.json")
    assert calls == []


@pytest.mark.parametrize("pilots", [[], [next(iter(BY_ID))] * 2, ["unknown"]])
def test_invalid_pilot_sets_refuse(tmp_path, pilots):
    preparation = tmp_path / "preparation"
    round_.prepare(output=preparation, model=round_.MODEL)
    with pytest.raises(ValueError, match="INVALID_PILOT_SET"):
        round_.run(pilots, output=tmp_path / "run", model=round_.MODEL,
            preflight=preparation / "preflight.json")


def test_group_stops_after_uncertain_first_attempt(tmp_path, monkeypatch):
    preparation, output = tmp_path / "preparation", tmp_path / "run"
    round_.prepare(output=preparation, model=round_.MODEL)
    catalog = (
        round_.PILOTS / "evidence/po035_experiments_20261012/catalog_scratchpad.json"
    ).read_bytes()
    monkeypatch.setattr(round_, "fetch_openrouter_catalog", lambda **kwargs: catalog)
    calls = []

    def missing_cost(model, request, maximum, timeout):
        calls.append(request)
        return canonical(
            {
                "id": "offline-missing-cost",
                "model": model,
                "usage": {"prompt_tokens": 20, "completion_tokens": 20, "total_tokens": 40},
                "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
            }
        )

    monkeypatch.setattr(pfp_experiment, "dispatch_deadline", missing_cost)
    pilots = list(BY_ID)[:2]
    terminals = round_.run(pilots, output=output, model=round_.MODEL,
        preflight=preparation / "preflight.json")
    assert len(calls) == len(terminals) == 1
    assert terminals[0]["terminal"] == "INFRASTRUCTURE_ERROR"
    assert not (output / pilots[1] / "run.json").exists()


def test_token_reservation_refuses_before_dispatch(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(pfp_experiment, "dispatch_deadline", lambda *args: calls.append(args))
    pilot = next(iter(BY_ID))
    port = pfp_experiment.PfpExperimentAdapter(
        pilot=pilot,
        folder=tmp_path,
        campaign=round_.CAMPAIGN,
        model=round_.MODEL,
        pricing_sha256="offline",
        sources={},
        profile={"ceiling_usd_per_token": "0"},
        prompt_builder=round_.render,
        observer=round_.observe,
    )
    terminal = run_derivation_loops(port, round_.DerivationLimits(loops=3, tokens=1))
    assert terminal["terminal"] == "TOKEN_CAP"
    assert terminal["provider_calls"] == 0
    assert calls == []
