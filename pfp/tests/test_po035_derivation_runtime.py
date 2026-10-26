"""Historical v1 fixture writers exercise current replay without changing old wire."""

import json
import sqlite3

import pytest

from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import prompt_container
from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import evaluate
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import VARIANTS
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import check_variant
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import fixture_payload
from omega_engine_pfp.infrastructure.adapters import pfp_derivation as adapter
from omega_engine_pfp.tests._po035_historical import historical_derivation
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import write_once
from omega_engine_pfp.use_cases.pfp_derivation_loops import (
    DerivationLimits,
    DerivationStop,
    run_derivation_loops,
)


@pytest.mark.parametrize("pilot", list(BY_ID))
@pytest.mark.parametrize("variant", VARIANTS)
def test_finite_predicates(pilot, variant):
    check_variant(pilot, variant)


@pytest.mark.parametrize(
    "field,value",
    [("loops", 6), ("tokens", 120001), ("microusd", 50001), ("seconds", 181), ("loops", True)],
)
def test_authorization_ceiling(field, value):
    with pytest.raises(ValueError):
        DerivationLimits(**{field: value})


def test_acceptance_does_not_stop_exploration():
    class Port:
        def begin(self, limits):
            self.calls = []

        def propose(self, loop, context):
            self.calls.append(loop)
            return "accepted"

        def observe(self, loop, proposal, context):
            return {"accepted": True}

        def finish(self, completed, terminal, context):
            return completed, terminal, self.calls

    assert run_derivation_loops(Port()) == (5, "LOOP_LIMIT", [1, 2, 3, 4, 5])


def test_explicit_stop_preserves_completed_count():
    class Port:
        def begin(self, limits):
            pass

        def propose(self, loop, context):
            if loop == 3:
                raise DerivationStop("TIME_CAP")

        def observe(self, loop, proposal, context):
            return {"loop": loop}

        def finish(self, completed, terminal, context):
            return completed, terminal, context

    assert run_derivation_loops(Port()) == (2, "TIME_CAP", {"loop": 2})


def test_immutable_evidence(tmp_path):
    path = tmp_path / "receipt.json"
    write_once(path, {"x": 1})
    write_once(path, {"x": 1})
    with pytest.raises(ValueError, match="IMMUTABLE"):
        write_once(path, {"x": 2})


@pytest.mark.parametrize(
    "mutation",
    [
        "raw",
        "request",
        "completed",
        "context",
        "reason",
        "limits",
        "tokens",
        "cost",
        "calls",
        "ledger",
    ],
)
def test_live_adapter_and_offline_tamper(tmp_path, monkeypatch, mutation):
    pilot = next(iter(BY_ID))
    calls = []

    def send(model, request, maximum):
        user = json.loads(request.user)
        payload = fixture_payload(pilot, user["prompt_id"])
        calls.append(payload)
        return json.dumps(
            dict(
                id=f"fixture-{len(calls)}",
                model=model,
                usage=dict(prompt_tokens=20, completion_tokens=20, total_tokens=40, cost=0),
                choices=[dict(message=dict(content=json.dumps(payload)), finish_reason="stop")],
            )
        ).encode()

    monkeypatch.setattr(
        historical_derivation,
        "dispatch_deadline",
        lambda model, request, maximum, timeout: send(model, request, maximum),
    )

    def observer(pilot, loop, path, prompt, result, receipt, context):
        verdict, _ = evaluate(pilot, prompt["prompt_id"], result["content"])
        write_once(path / "verdict.json", verdict)
        return {"feedback": verdict, "parent_prompt_id": prompt["prompt_id"]}

    port = historical_derivation.PfpDerivationAdapter(
        pilot=pilot,
        folder=tmp_path,
        campaign="fixture",
        model="fixture",
        pricing_sha256="test",
        sources={},
        prompt_builder=prompt_container,
        observer=observer,
    )
    assert run_derivation_loops(port)["terminal"] == "LOOP_LIMIT"
    monkeypatch.setattr(
        adapter,
        "dispatch_deadline",
        lambda *args: pytest.fail("offline replay used transport"),
    )
    captured = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert (
        adapter.replay_run(tmp_path, pilot, "fixture", prompt_container, observer, {})[
            "replayed_calls"
        ]
        == 5
    )
    assert {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    } == captured
    if mutation in ("raw", "request"):
        path = tmp_path / (
            "loop_01/raw_reply.json" if mutation == "raw" else "loop_01/request.json"
        )
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path = tmp_path / ("budget_snapshot.json" if mutation == "ledger" else "terminal.json")
        doc = json.loads(path.read_bytes())
        if mutation == "completed":
            doc["completed_loops"] = 1
        elif mutation == "context":
            doc["context"] = {}
        elif mutation == "reason":
            doc["terminal"] = "TIME_CAP"
        elif mutation == "limits":
            doc["limits"]["tokens"] = 210000
        elif mutation == "tokens":
            doc["tokens"] += 1
        elif mutation == "cost":
            doc["cost_microusd"] = 1
        elif mutation == "calls":
            doc["provider_calls"] = 1
        elif mutation == "ledger":
            doc["spent"] = 1
        path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError):
        adapter.replay_run(tmp_path, pilot, "fixture", prompt_container, observer, {})


def test_token_hold_stops_before_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        adapter, "dispatch_deadline", lambda *args: pytest.fail("over-budget dispatch")
    )
    pilot = next(iter(BY_ID))
    port = historical_derivation.PfpDerivationAdapter(
        pilot=pilot,
        folder=tmp_path,
        campaign="fixture",
        model="fixture",
        pricing_sha256="test",
        sources={},
        prompt_builder=prompt_container,
        observer=None,
    )
    terminal = run_derivation_loops(port, DerivationLimits(tokens=1))
    assert terminal["terminal"] == "TOKEN_CAP" and terminal["provider_calls"] == 0


def test_worker_timeout_retains_attempt_hold(tmp_path, monkeypatch):
    import subprocess

    def timeout(*args):
        raise subprocess.TimeoutExpired("fixture", 0.001)

    monkeypatch.setattr(historical_derivation, "dispatch_deadline", timeout)
    pilot = next(iter(BY_ID))
    port = historical_derivation.PfpDerivationAdapter(
        pilot=pilot,
        folder=tmp_path,
        campaign="fixture",
        model="fixture",
        pricing_sha256="test",
        sources={},
        prompt_builder=prompt_container,
        observer=None,
    )
    terminal = run_derivation_loops(port)
    assert terminal["terminal"] == "INFRASTRUCTURE_ERROR"
    state = port.state()
    assert state["attempts"]["1"]["state"] == "reserved"
    assert terminal["settled_calls"] == 0


def test_negative_controls_are_schema_valid():
    from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import negative_control

    for pilot in BY_ID:
        payload = fixture_payload(pilot, "fixture")
        from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body

        body = proposal_body(payload)
        body["certificate"] = dict(reversed(list(body["certificate"].items())))
        result = negative_control(pilot, "fixture", payload)
        assert result["rejected"] and result["code"] != "SCHEMA_VIOLATION"


@pytest.mark.parametrize("value", [None, True, -1, "NaN", "Infinity"])
def test_unknown_cost_is_not_zero(value):
    with pytest.raises(ValueError):
        adapter.microusd(value)


@pytest.mark.parametrize("failure", [None, "query", "database", "snapshot", "missing"])
def test_replay_closes_read_only_database_on_success_and_refusal(tmp_path, monkeypatch, failure):
    pilot = next(iter(BY_ID))
    monkeypatch.setattr(
        adapter, "dispatch_deadline", lambda *args: pytest.fail("replay fixture used transport")
    )
    port = historical_derivation.PfpDerivationAdapter(
        pilot=pilot,
        folder=tmp_path,
        campaign="lifetime-fixture",
        model="fixture",
        pricing_sha256="test",
        sources={},
        prompt_builder=prompt_container,
        observer=None,
    )
    terminal = run_derivation_loops(port, DerivationLimits(tokens=1))
    assert terminal["terminal"] == "TOKEN_CAP" and terminal["provider_calls"] == 0
    database = tmp_path / "budget.sqlite3"
    if failure == "query":
        connection = sqlite3.connect(database)
        try:
            connection.execute("DROP TABLE provider_budget")
            connection.commit()
        finally:
            connection.close()
    elif failure == "database":
        database.write_bytes(b"not a SQLite database")
    elif failure == "snapshot":
        snapshot = json.loads((tmp_path / "budget_snapshot.json").read_bytes())
        snapshot["spent"] += 1
        (tmp_path / "budget_snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
    elif failure == "missing":
        database.unlink()
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    connect, opened, calls = sqlite3.connect, [], []

    class TrackedConnection(sqlite3.Connection):
        def close(self):
            self.explicitly_closed = True
            return super().close()

    def tracking_connect(*args, **options):
        calls.append((args, options))
        connection = connect(*args, factory=TrackedConnection, **options)
        connection.explicitly_closed = False
        opened.append(connection)  # Retain it so garbage collection cannot hide the leak.
        return connection

    monkeypatch.setattr(adapter.sqlite3, "connect", tracking_connect)
    try:
        if failure is None:
            assert adapter.replay_run(tmp_path, pilot, "fixture", prompt_container, None, {}) == {
                "pilot_id": pilot,
                "replayed_calls": 0,
                "context": {},
                "analytical_status": "UNVERIFIED",
            }
        else:
            error, message = {
                "query": (sqlite3.OperationalError, "no such table"),
                "database": (sqlite3.DatabaseError, "file is not a database"),
                "snapshot": (ValueError, "BUDGET_SNAPSHOT_MISMATCH"),
                "missing": (sqlite3.OperationalError, "unable to open database file"),
            }[failure]
            with pytest.raises(error, match=message):
                adapter.replay_run(tmp_path, pilot, "fixture", prompt_container, None, {})
        assert calls == [((database.resolve().as_uri() + "?mode=ro",), {"uri": True})]
        assert {
            path.relative_to(tmp_path): path.read_bytes()
            for path in tmp_path.rglob("*")
            if path.is_file()
        } == before
        assert len(opened) == (0 if failure == "missing" else 1)
        for connection in opened:
            assert connection.explicitly_closed is True
            with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                connection.execute("SELECT 1")
    finally:
        for connection in opened:
            connection.close()


def test_derivation_keeps_canonical_provider_type_identities():
    from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1
    from omega_engine_woland.infrastructure.providers.budget_ledger import SqliteBudgetLedger

    prompt = prompt_container(next(iter(BY_ID)), 1, {})
    request = adapter.request_for(prompt)
    assert type(request) is CandidateRequest
    assert type(request.decoding) is DecodingParamsV1
    assert adapter.SqliteBudgetLedger is SqliteBudgetLedger
