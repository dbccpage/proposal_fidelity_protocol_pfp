"""Finite independent oracle controls for the bounded live repair task."""

import json
import sqlite3
import subprocess
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pytest

from adversary.tests.pilots.challenge_suite import typed_certificate_repair
from adversary.tests.pilots.challenge_suite.typed_certificate_repair import (
    EDGES,
    check_certificate,
)


def test_positive_wrong_witness_and_rebound_wrong_calculations():
    case = dict(vertices=6, edges=EDGES)
    witness = dict(potentials=[0, 4, -3, 6, 3, 8], edge_residuals=[0] * 8)
    assert check_certificate(case, witness)["accepted"]
    wrong = dict(witness, potentials=[0, -4, -3, 0, 1, 0])
    assert not check_certificate(case, wrong)["accepted"]
    rebound = dict(wrong, edge_residuals=[w - (wrong["potentials"][v] - wrong["potentials"][u]) for u, v, w in EDGES])
    assert not check_certificate(case, rebound)["accepted"]
    assert not check_certificate(case, dict(witness, potentials=[False, 4, -3, 6, 3, 8]))["accepted"]


PACKET_REVISION = "0622e7e666877c61ae9330fe55b6a223965e23eb"
PACKET = "_ic/adversary/oev1rc_integration_closure/live_teamwork"


def packet_bytes(name: str) -> bytes:
    root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(
        ["git", "cat-file", "blob", f"{PACKET_REVISION}:{PACKET}/{name}"],
        cwd=root,
    )


def replay_fixture(tmp_path):
    for name in ("cycle_certificate.json", "typed_repair.json"):
        (tmp_path / name).write_bytes(packet_bytes(name))
    state_data = json.loads(packet_bytes("run.json"))
    ledger = tmp_path / "run.sqlite3"
    state_data["provider_binding"]["run_budget"]["accounting_path"] = str(ledger)
    action = "critique:" + sha256((typed_certificate_repair.RECIPE + "\0typed-repair-1").encode()).hexdigest()
    raw = packet_bytes("typed_repair.provider_wire.json")
    name = sha256(action.encode()).hexdigest() + ".wire"
    replies = ledger.with_name(ledger.name + ".replies")
    replies.mkdir()
    (replies / name).write_bytes(raw)
    # Reconstruct only the read-only custody surface from retained real wire.
    budget = {k: v for k, v in state_data["provider_binding"]["run_budget"].items() if k != "accounting_path"}
    with closing(sqlite3.connect(ledger)) as connection, connection:
        connection.execute("CREATE TABLE provider_budget (state TEXT)")
        connection.execute("INSERT INTO provider_budget VALUES (?)", (json.dumps(dict(run_scope=budget,
            action_claims={action: dict(wire_file=name, wire_sha256=sha256(raw).hexdigest(), wire_bytes=len(raw))})),))
    state = tmp_path / "run.json"
    state.write_text(json.dumps(state_data), encoding="utf-8")
    return state, ledger


def test_actual_failed_completion_replays_without_credentials_and_rejects_cached_verdict_tamper(tmp_path, monkeypatch):
    state, ledger = replay_fixture(tmp_path)
    before = ledger.read_bytes()

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay constructed a provider or requested credentials")

    monkeypatch.setattr(typed_certificate_repair, "create_accounted_openrouter_gateway", forbidden)
    result = typed_certificate_repair.run(state, replay=True)
    assert result["provider_calls"] == 0
    assert not result["pfp_schema_valid"]
    assert result["independent_judge"] == {"accepted": False, "reason": "PFP_SCHEMA"}
    assert ledger.read_bytes() == before

    record_path = tmp_path / "typed_repair.json"
    record = json.loads(record_path.read_bytes())
    record["pfp"]["schema_valid"] = True
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="REPLAY_JUDGEMENT_MISMATCH"):
        typed_certificate_repair.run(state, replay=True)


def test_rehashed_fabricated_completion_cannot_replace_retained_provider_wire(tmp_path):
    state, _ = replay_fixture(tmp_path)
    record_path = tmp_path / "typed_repair.json"
    record = json.loads(record_path.read_bytes())
    raw = bytes.fromhex(record["raw_completion_hex"])
    fabricated = raw.rstrip()[:-1]  # Removing the actual extra brace would repair the model output.
    record["raw_completion_hex"] = fabricated.hex()
    record["raw_completion_sha256"] = sha256(fabricated).hexdigest()
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="REPLAY_PROVIDER_WIRE_MISMATCH"):
        typed_certificate_repair.run(state, replay=True)


def test_previously_claimed_action_cannot_report_or_send_a_new_call(tmp_path, monkeypatch):
    state, _ = replay_fixture(tmp_path)
    (tmp_path / "typed_repair.json").unlink()

    def forbidden(*args, **kwargs):
        raise AssertionError("Previously claimed action reached provider factory")

    monkeypatch.setattr(typed_certificate_repair, "create_accounted_openrouter_gateway", forbidden)
    with pytest.raises(ValueError, match="REPAIR_ACTION_ALREADY_CLAIMED"):
        typed_certificate_repair.run(state, replay=False)


def test_duplicate_content_in_original_vendor_wire_cannot_be_silently_repaired(tmp_path):
    from adversary.domain.providers.types import ProviderError

    state, ledger = replay_fixture(tmp_path)
    with closing(sqlite3.connect(ledger)) as connection, connection:
        custody = json.loads(connection.execute("SELECT state FROM provider_budget").fetchone()[0])
        claim = next(iter(custody["action_claims"].values()))
        wire_path = ledger.with_name(ledger.name + ".replies") / claim["wire_file"]
        wire = wire_path.read_bytes().replace(b'"content":', b'"content":"discarded","content":', 1)
        wire_path.write_bytes(wire)
        claim.update(wire_bytes=len(wire), wire_sha256=sha256(wire).hexdigest())
        connection.execute("UPDATE provider_budget SET state=?", (json.dumps(custody),))
    with pytest.raises(ProviderError, match="duplicate object keys"):
        typed_certificate_repair.run(state, replay=True)


@pytest.mark.parametrize("changed_scope", [False, True])
def test_missing_original_ledger_or_changed_objective_refuses_before_factory(tmp_path, monkeypatch, changed_scope):
    (tmp_path / "cycle_certificate.json").write_bytes(packet_bytes("cycle_certificate.json"))
    state = json.loads(packet_bytes("run.json"))
    missing = tmp_path / "missing.sqlite3"
    state["provider_binding"]["run_budget"]["accounting_path"] = str(missing)
    if changed_scope:
        state["objective"] += " altered"
    state_path = tmp_path / "run.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    def forbidden(*args, **kwargs):
        raise AssertionError("Missing run custody reached credential/provider factory")

    monkeypatch.setattr(typed_certificate_repair, "create_accounted_openrouter_gateway", forbidden)
    with pytest.raises((ValueError, FileNotFoundError)):
        typed_certificate_repair.run(state_path, replay=False)
    assert not missing.exists()
