"""Extra checks for the visible SN09 offline ledger derivative, not frozen code."""

import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

LEDGER = Path(
    os.environ.get(
        "PFP_SN09_BUDGET_UNDER_TEST", Path(__file__).resolve().parents[1] / "budget_ledger.py"
    )
)
spec = importlib.util.spec_from_file_location("sn09_extra_budget_under_test", LEDGER)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def book(tmp_path, **kwargs):
    return b.BudgetLedger(tmp_path / "ledger.json", **kwargs)


def test_local_defaults_are_offline_cap_not_legacy_authorization(tmp_path):
    ledger = book(tmp_path)
    data = ledger.snapshot()
    assert data["schema"] == b.SCHEMA
    for key in ("pilot_cap_usd", "campaign_cap_usd", "balance_ceiling_usd"):
        assert data[key] == "0.010"
    with pytest.raises(ValueError, match="NOT_AUTHORIZED"):
        b.BudgetLedger(tmp_path / "other.json", pilot_cap_usd="0.011")


def test_direct_arithmetic_is_independent_of_decimal_context(tmp_path):
    ledger = book(tmp_path)
    with localcontext() as context:
        context.prec = 2
        ledger.reserve("a", ".009")
        ledger.mark_dispatched("a")
        ledger.settle("a", ".009")
        before = ledger.path.read_bytes()
        with pytest.raises(ValueError, match="BUDGET_RESERVATION_REFUSED"):
            ledger.reserve("b", ".001000001")
        assert ledger.path.read_bytes() == before
        ledger.reserve("b", ".001")
        ledger.mark_dispatched("b")
        ledger.settle("b", ".000000001")
        summary = ledger.summary()
    assert summary["settled_usd"] == "0.009000001"
    assert summary["exposure_usd"] == "0.009000001"


@pytest.mark.parametrize("token", ["0.000000001", "0.000000000"])
def test_tiny_plain_money_survives_reserve_restart_and_settlement(tmp_path, token):
    ledger = book(tmp_path)
    ledger.reserve("a", token)
    restarted = book(tmp_path)
    assert restarted.snapshot()["requests"]["a"]["reserved_usd"] == token
    assert restarted.reserve("a", token)["error_code"] == "REQUEST_ALREADY_RESERVED"
    restarted.mark_dispatched("a")
    result = book(tmp_path).settle("a", token)
    assert result["cost_usd"] == token
    final = book(tmp_path)
    assert final.settle("a", token) == result
    assert final.snapshot()["requests"]["a"]["cost_usd"] == token
    assert final.summary()["settled_usd"] == token
    assert final.summary()["exposure_usd"] == token
    assert "E-" not in final.path.read_text(encoding="utf-8")


@pytest.mark.parametrize("token", [True, 0.005, "1e-3", "0.0000000001", "1000000", "NaN", "-.01"])
def test_direct_money_boundary_remains_bounded(tmp_path, token):
    ledger = book(tmp_path)
    assert b._money(token) is None
    before = ledger.path.read_bytes()
    with pytest.raises(ValueError, match="INVALID_RESERVATION"):
        ledger.reserve("a", token)
    assert ledger.path.read_bytes() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount_usd", ".003"),
        ("model", "other"),
        ("pricing_sha256", "other-price"),
        ("request_sha256", "other-request"),
    ],
)
def test_repeated_reservation_binds_complete_identity(tmp_path, field, value):
    ledger = book(tmp_path)
    identity = dict(
        amount_usd=".004", request_sha256="request", model="model", pricing_sha256="price"
    )
    assert ledger.reserve("a", **identity) is None
    assert ledger.reserve("a", **identity)["error_code"] == "REQUEST_ALREADY_RESERVED"
    before = ledger.path.read_bytes()
    with pytest.raises(ValueError, match="DIFFERENT_INPUT"):
        ledger.reserve("a", **{**identity, field: value})
    assert ledger.path.read_bytes() == before
    assert book(tmp_path).reserve("a", **identity)["error_code"] == "REQUEST_ALREADY_RESERVED"


@pytest.mark.parametrize("field", ["pilot_cap_usd", "campaign_cap_usd", "balance_ceiling_usd"])
def test_all_persisted_caps_bind_reopening(tmp_path, field):
    ledger = book(tmp_path)
    before = ledger.path.read_bytes()
    with pytest.raises(ValueError, match="LEDGER_CAP_MISMATCH"):
        book(tmp_path, **{field: ".009"})
    assert ledger.path.read_bytes() == before


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate",
        "not-object",
        "requests-not-object",
        "negative",
        "nonfinite",
        "unbounded",
        "unknown-state",
        "non-string-state",
        "non-boolean-dispatch",
        "invalid-result",
        "reserved-result",
        "premature-timestamp",
        "missing-terminal-timestamp",
    ],
)
def test_persisted_corruption_refuses_without_rewriting(tmp_path, kind):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    data = ledger.snapshot()
    if kind == "not-object":
        data = []
    elif kind == "requests-not-object":
        data["requests"] = []
    elif kind in {"negative", "nonfinite", "unbounded"}:
        data["requests"]["a"]["reserved_usd"] = {
            "negative": "-.005",
            "nonfinite": float("nan"),
            "unbounded": "0.0000000001",
        }[kind]
    elif kind == "unknown-state":
        data["requests"]["a"]["state"] = "invented"
    elif kind == "non-string-state":
        data["requests"]["a"]["state"] = []
    elif kind == "non-boolean-dispatch":
        data["requests"]["a"]["dispatched"] = "false"
    elif kind == "invalid-result":
        ledger.mark_dispatched("a")
        ledger.settle("a", ".001")
        data = ledger.snapshot()
        data["requests"]["a"]["result"]["cost_usd"] = "0"
    elif kind == "reserved-result":
        data["requests"]["a"]["result"] = {"request_id": "a", "cost_usd": "0", "status": "COMPLETE"}
    elif kind == "premature-timestamp":
        data["requests"]["a"]["cancelled_at"] = "not-cancelled"
    elif kind == "missing-terminal-timestamp":
        ledger.mark_dispatched("a")
        ledger.settle("a", ".001")
        data = ledger.snapshot()
        del data["requests"]["a"]["updated_at"]
    raw = json.dumps(data).encode()
    if kind == "duplicate":
        # Last-wins parsing would erase all existing reservations.
        raw = raw[:-1] + b',"requests":{}}'
    ledger.path.write_bytes(raw)
    with pytest.raises(ValueError, match="LEDGER_"):
        ledger.snapshot()
    with pytest.raises(ValueError, match="LEDGER_"):
        ledger.reserve("b", "0")
    with pytest.raises(ValueError, match="LEDGER_"):
        ledger.reserve("a", ".005")
    assert ledger.path.read_bytes() == raw


def test_disappearing_established_state_is_not_a_fresh_budget(tmp_path):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    ledger.path.unlink()
    with pytest.raises(ValueError, match="ESTABLISHED_STATE_MISSING"):
        ledger.snapshot()
    with pytest.raises(ValueError, match="ESTABLISHED_STATE_MISSING"):
        book(tmp_path)
    assert not ledger.path.exists()
    # Deletion of both ledger AND marker is not detectable by this local scheme.


def test_prior_unknown_authorization_cannot_name_a_future_request(tmp_path):
    ledger = book(tmp_path)
    with pytest.raises(ValueError, match="PRIOR_UNKNOWN_AUTHORIZATION_REFUSED"):
        book(tmp_path, authorized_prior_unknown_ids=("future",))
    ledger.reserve("a", ".005")
    ledger.mark_dispatched("a")
    ledger.unresolved("a")
    approved = book(tmp_path, authorized_prior_unknown_ids=("a",))
    approved.reserve("b", ".005")
    approved.mark_dispatched("b")
    approved.unresolved("b")
    with pytest.raises(ValueError, match="CHARGE_HOLDS"):
        approved.reserve("c", "0")


def test_unknown_hold_blocks_dispatch_of_an_older_reservation(tmp_path):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    ledger.reserve("b", ".005")
    ledger.mark_dispatched("a")
    ledger.unresolved("a")
    with pytest.raises(ValueError, match="CHARGE_HOLDS"):
        ledger.mark_dispatched("b")
    assert ledger.snapshot()["requests"]["b"]["dispatched"] is False
    book(tmp_path, authorized_prior_unknown_ids=("a",)).mark_dispatched("b")


def test_undispatched_reservation_cannot_be_settled_or_unknown(tmp_path):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    before = ledger.path.read_bytes()
    for operation in (lambda: ledger.settle("a", "0"), lambda: ledger.unresolved("a")):
        with pytest.raises(ValueError, match="NOT_DISPATCHED"):
            operation()
    assert ledger.path.read_bytes() == before
    assert ledger.cancel("a")["state"] == "CANCELLED"


def test_result_cannot_override_financial_identity(tmp_path):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    ledger.mark_dispatched("a")
    result = ledger.settle(
        "a", ".004", result={"request_id": "other", "cost_usd": "0", "status": "BAD"}
    )
    assert result == {"request_id": "a", "cost_usd": "0.004", "status": "COMPLETE"}
    assert book(tmp_path).settle("a", ".004") == result


def test_summary_uses_one_snapshot(tmp_path, monkeypatch):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    ledger.mark_dispatched("a")
    ledger.unresolved("a")
    snapshot = ledger.snapshot()
    calls = []

    def once():
        calls.append(True)
        assert len(calls) == 1
        return snapshot

    monkeypatch.setattr(ledger, "snapshot", once)
    assert ledger.summary() == {
        "settled_usd": "0",
        "held_usd": "0.005",
        "exposure_usd": "0.005",
        "unknown_request_ids": ["a"],
        "request_count": 1,
    }


def test_concurrent_separate_instances_share_one_exact_cap(tmp_path):
    def reserve(index):
        ledger = book(tmp_path)
        try:
            ledger.reserve(str(index), ".003")
            return True
        except ValueError as error:
            assert str(error) == "BUDGET_RESERVATION_REFUSED"
            return False

    with ThreadPoolExecutor(max_workers=6) as pool:
        accepted = list(pool.map(reserve, range(6)))
    assert sum(accepted) == 3
    assert Decimal(book(tmp_path).summary()["exposure_usd"]) == Decimal(".009")


def test_failed_atomic_replace_preserves_data_and_removes_own_temp(tmp_path, monkeypatch):
    ledger = book(tmp_path)
    before = ledger.path.read_bytes()

    def refused(*args):
        raise OSError("planted replace refusal")

    monkeypatch.setattr(b.os, "replace", refused)
    with pytest.raises(OSError, match="planted replace refusal"):
        ledger.reserve("a", ".005")
    assert ledger.path.read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_temp_collision_does_not_delete_foreign_bytes(tmp_path, monkeypatch):
    ledger = book(tmp_path)
    before = ledger.path.read_bytes()
    collision = tmp_path / "ledger.json.fixed-collision.tmp"
    collision.write_bytes(b"foreign bytes that this operation did not create")
    monkeypatch.setattr(b.uuid, "uuid4", lambda: SimpleNamespace(hex="fixed-collision"))
    with pytest.raises(FileExistsError):
        ledger.reserve("a", ".005")
    assert ledger.path.read_bytes() == before
    assert collision.read_bytes() == b"foreign bytes that this operation did not create"


def test_successful_replace_does_not_delete_recreated_temp_path(tmp_path, monkeypatch):
    ledger = book(tmp_path)
    real_replace = b.os.replace
    recreated = []

    def replace_then_recreate(source, destination):
        real_replace(source, destination)
        Path(source).write_bytes(b"another writer owns this new file")
        recreated.append(Path(source))

    monkeypatch.setattr(b.os, "replace", replace_then_recreate)
    ledger.reserve("a", ".005")
    assert len(recreated) == 1
    assert recreated[0].read_bytes() == b"another writer owns this new file"
    assert ledger.summary()["held_usd"] == "0.005"


def test_persisted_and_new_state_are_bounded(tmp_path, monkeypatch):
    ledger = book(tmp_path)
    monkeypatch.setattr(b, "MAX_REQUESTS", 1)
    ledger.reserve("a", "0")
    with pytest.raises(ValueError, match="LEDGER_REQUEST_LIMIT"):
        ledger.reserve("b", "0")
    monkeypatch.setattr(b, "MAX_LEDGER_BYTES", 16)
    with pytest.raises(ValueError, match="LEDGER_SIZE_LIMIT"):
        ledger.snapshot()


@pytest.mark.parametrize(
    "state,damage",
    [
        ("RESERVED", "empty-id"),
        ("RESERVED", "not-row"),
        ("RESERVED", "missing-field"),
        ("RESERVED", "extra-field"),
        ("RESERVED", "invalid-identity"),
        ("RESERVED", "dispatch-without-time"),
        ("RESERVED", "unbilled-cost"),
        ("SETTLED", "missing-cost"),
        ("SETTLED", "no-dispatch"),
        ("UNKNOWN", "no-dispatch"),
        ("CANCELLED", "dispatched-cancel"),
        ("SETTLED", "overbill-not-breach"),
        ("BREACH", "underbill-is-breach"),
        ("CANCELLED", "invalid-time"),
        ("BREACH", "wrong-breach-code"),
        ("RESERVED", "over-cap-row"),
        ("RESERVED", "over-cap-total"),
    ],
)
def test_persisted_transition_inconsistencies_are_not_admitted(tmp_path, state, damage):
    ledger = book(tmp_path)
    ledger.reserve("a", ".005")
    if state == "CANCELLED":
        ledger.cancel("a")
    elif state != "RESERVED":
        ledger.mark_dispatched("a")
        if state == "UNKNOWN":
            ledger.unresolved("a")
        else:
            ledger.settle("a", ".006" if state == "BREACH" else ".004")
    data = ledger.snapshot()
    row = data["requests"]["a"]
    if damage == "empty-id":
        data["requests"][""] = data["requests"].pop("a")
    elif damage == "not-row":
        data["requests"]["a"] = []
    elif damage == "missing-field":
        del row["reserved_at"]
    elif damage == "extra-field":
        row["magic"] = True
    elif damage == "invalid-identity":
        row["model"] = 3
    elif damage == "dispatch-without-time":
        row["dispatched"] = True
    elif damage == "unbilled-cost":
        row["cost_usd"] = "0"
    elif damage == "missing-cost":
        row["cost_usd"] = None
    elif damage == "no-dispatch":
        row["dispatched"] = False
        del row["dispatched_at"]
    elif damage == "dispatched-cancel":
        row.update(dispatched=True, dispatched_at="retained time")
    elif damage in {"overbill-not-breach", "underbill-is-breach"}:
        row["cost_usd"] = ".006" if damage == "overbill-not-breach" else ".004"
        row["result"]["cost_usd"] = row["cost_usd"]
    elif damage == "invalid-time":
        row["cancelled_at"] = None
    elif damage == "wrong-breach-code":
        row["result"]["error_code"] = "COMPLETE"
    elif damage == "over-cap-row":
        row["reserved_usd"] = ".011"
    else:
        assert damage == "over-cap-total"
        data["requests"]["b"] = {**row, "reserved_usd": ".006"}
    raw = json.dumps(data).encode()
    ledger.path.write_bytes(raw)
    with pytest.raises(ValueError, match="LEDGER_"):
        ledger.snapshot()
    with pytest.raises(ValueError, match="LEDGER_"):
        ledger.reserve("c", "0")
    assert ledger.path.read_bytes() == raw


@pytest.mark.parametrize("raw", [b"{", b"\xff"])
def test_invalid_json_or_encoding_does_not_reset_state(tmp_path, raw):
    ledger = book(tmp_path)
    ledger.path.write_bytes(raw)
    with pytest.raises(ValueError, match="LEDGER_JSON_CORRUPT"):
        ledger.snapshot()
    assert ledger.path.read_bytes() == raw


def test_persisted_request_count_and_write_size_limits_preserve_bytes(tmp_path, monkeypatch):
    ledger = book(tmp_path)
    ledger.reserve("a", "0")
    data = ledger.snapshot()
    data["requests"]["b"] = dict(data["requests"]["a"])
    raw = json.dumps(data).encode()
    ledger.path.write_bytes(raw)
    with monkeypatch.context() as patch:
        patch.setattr(b, "MAX_REQUESTS", 1)
        with pytest.raises(ValueError, match="LEDGER_REQUEST_LIMIT"):
            ledger.snapshot()
    monkeypatch.setattr(b, "MAX_LEDGER_BYTES", len(raw) + 10)
    with pytest.raises(ValueError, match="LEDGER_SIZE_LIMIT"):
        ledger.reserve("c", "0", model="x" * 100)
    assert ledger.path.read_bytes() == raw and list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("authorization", ["future", ("",), (3,), ("future",)])
def test_fresh_ledger_cannot_preauthorize_future_unknowns(tmp_path, authorization):
    with pytest.raises(ValueError, match="PRIOR_UNKNOWN_AUTHORIZATION_REFUSED"):
        book(tmp_path, authorized_prior_unknown_ids=authorization)
    assert not (tmp_path / "ledger.json").exists()


def test_corrupt_lock_marker_is_refused_without_ledger_reset(tmp_path):
    ledger = book(tmp_path)
    raw = ledger.path.read_bytes()
    ledger.path.with_suffix(".lock").write_bytes(b"?")
    with pytest.raises(ValueError, match="LEDGER_LOCK_MARKER_CORRUPT"):
        book(tmp_path)
    assert ledger.path.read_bytes() == raw


def test_invalid_public_identity_and_result_values_never_mutate_state(tmp_path):
    ledger = book(tmp_path)
    raw = ledger.path.read_bytes()
    with pytest.raises(ValueError, match="INVALID_REQUEST_IDENTITY"):
        ledger.reserve("", "0")
    assert ledger.path.read_bytes() == raw
    ledger.reserve("a", ".005")
    ledger.mark_dispatched("a")
    raw = ledger.path.read_bytes()
    with pytest.raises(ValueError, match="INVALID_RESULT"):
        ledger.settle("a", "0", result=[])
    with pytest.raises(ValueError, match="INVALID_RESULT"):
        ledger.unresolved("a", reason="")
    assert ledger.path.read_bytes() == raw
