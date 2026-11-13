import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest

LEDGER = Path(__file__).resolve().parents[1] / "budget_ledger.py"
spec = importlib.util.spec_from_file_location(
    "sn09_budget_dependency_test",
    Path(os.environ.get("PFP_SN09_BUDGET_UNDER_TEST", LEDGER)),
)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def ledger(tmp_path, **kwargs):
    return b.BudgetLedger(
        tmp_path / "ledger.json", ".010", ".010", balance_ceiling_usd=".010", **kwargs
    )


@pytest.mark.parametrize("value", [None, True, False, "bad", "NaN", "Infinity", "-.01"])
def test_unknown_and_invalid_money_is_not_zero(value, tmp_path):
    assert b._money(value) is None
    with pytest.raises(ValueError, match="INVALID_RESERVATION"):
        ledger(tmp_path).reserve("a", value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pilot_cap_usd": "3.01"},
        {"pilot_cap_usd": None},
        {"campaign_cap_usd": "20.01"},
        {"campaign_cap_usd": None},
        {"balance_ceiling_usd": "17.49"},
        {"balance_ceiling_usd": "NaN"},
    ],
)
def test_dependency_legacy_maxima_are_not_pilot_authority(kwargs, tmp_path):
    with pytest.raises(ValueError, match="NOT_AUTHORIZED"):
        b.BudgetLedger(tmp_path / "ledger.json", **kwargs)


def test_reserve_identity_cancel_and_restart(tmp_path):
    book = ledger(tmp_path)
    assert book.reserve("a", ".006", request_sha256="sha") is None
    prior = book.reserve("a", ".006", request_sha256="sha")
    assert prior["error_code"] == "REQUEST_ALREADY_RESERVED"
    with pytest.raises(ValueError, match="DIFFERENT_INPUT"):
        book.reserve("a", ".006", request_sha256="changed")
    with pytest.raises(ValueError, match="RESERVATION_REFUSED"):
        ledger(tmp_path).reserve("b", ".005")
    row = book.cancel("a")
    assert row["state"] == "CANCELLED" and book.cancel("a") == row
    assert book.reserve("a", ".006", request_sha256="sha") == row["result"]
    assert Decimal(book.summary()["exposure_usd"]) == 0
    with pytest.raises(ValueError, match="CANCELLED_REQUEST"):
        book.settle("a", "0")
    book.reserve("b", ".010")
    book.mark_dispatched("b")
    with pytest.raises(ValueError, match="NOT_DISPATCHABLE"):
        book.mark_dispatched("b")
    with pytest.raises(ValueError, match="CANNOT_CANCEL"):
        book.cancel("b")
    with pytest.raises(ValueError, match="UNKNOWN_IS_NOT_ZERO"):
        book.settle("b", None)
    settled = book.settle("b", ".009")
    assert book.settle("b", ".009") == settled
    with pytest.raises(ValueError, match="CONFLICTING_RECONCILIATION"):
        book.settle("b", ".008")
    with pytest.raises(ValueError, match="ALREADY_TERMINAL"):
        book.unresolved("b")
    ledger(tmp_path).reserve("c", ".001")
    assert Decimal(ledger(tmp_path).summary()["exposure_usd"]) == Decimal(".010")


def test_unknown_and_breach_are_persistent(tmp_path):
    book = ledger(tmp_path)
    book.reserve("a", ".005")
    book.mark_dispatched("a")
    book.unresolved("a", result={"status": "UNRESOLVED", "cost_usd": None})
    with pytest.raises(ValueError, match="CHARGE_HOLDS"):
        ledger(tmp_path).reserve("b", "0")
    approved = ledger(tmp_path, authorized_prior_unknown_ids=("a",))
    approved.reserve("b", ".005")
    approved.mark_dispatched("b")
    approved.unresolved("b")
    with pytest.raises(ValueError, match="CHARGE_HOLDS"):
        approved.reserve("c", "0")
    assert Decimal(book.summary()["held_usd"]) == Decimal(".010")
    breach = book.settle("a", ".006")
    assert breach["error_code"] == "BILLED_COST_EXCEEDS_RESERVATION"
    assert book.settle("a", ".006") == breach
    assert Decimal(book.summary()["exposure_usd"]) == Decimal(".011")
    with pytest.raises(ValueError, match="CHARGE_HOLDS"):
        approved.reserve("c", "0")


def test_schema_and_caps_cannot_silently_reset(tmp_path):
    book = ledger(tmp_path)
    book.reserve("a", "0")
    with pytest.raises(ValueError, match="LEDGER_CAP_MISMATCH"):
        b.BudgetLedger(book.path, ".02", ".010").snapshot()
    fixture = json.loads(book.path.read_bytes())
    fixture["schema"] = "wrong"
    book.path.write_text(json.dumps(fixture))
    with pytest.raises(ValueError, match="LEDGER_SCHEMA_MISMATCH"):
        book.snapshot()


def test_atomic_competing_reservations(tmp_path):
    book = ledger(tmp_path)

    def reserve(index):
        try:
            book.reserve(str(index), ".003")
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=6) as pool:
        accepted = list(pool.map(reserve, range(6)))
    assert sum(accepted) == 3
    assert Decimal(book.summary()["exposure_usd"]) == Decimal(".009")


@pytest.mark.skipif(os.name != "nt", reason="Windows lock implementation")
def test_windows_lock_retry_and_timeout(tmp_path, monkeypatch):
    import msvcrt

    real = msvcrt.locking
    attempts = []

    def once(handle, mode, size):
        if mode == msvcrt.LK_NBLCK and not attempts:
            attempts.append(mode)
            raise OSError("busy")
        return real(handle, mode, size)

    monkeypatch.setattr(msvcrt, "locking", once)
    monkeypatch.setattr(b.time, "sleep", lambda _: None)
    assert ledger(tmp_path).snapshot()["requests"] == {}
    assert attempts

    def always(*_):
        raise OSError("busy")

    monkeypatch.setattr(msvcrt, "locking", always)
    ticks = iter((0, 11))
    monkeypatch.setattr(b.time, "monotonic", lambda: next(ticks))
    with pytest.raises(RuntimeError, match="LEDGER_LOCK_TIMEOUT"):
        ledger(tmp_path).snapshot()
