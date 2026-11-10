"""Pilot-local OFFLINE simulated billing, never live provider authorization.

Derived from historical Git blob 04e8f7303bc56a68c8716730f2bac2bb663c2075
(SHA-256 67d45c138c87f4f525bc999f2852ea4fc416b99eef18c4975f0206f9e2c89193).
Historical bytes are not imported or executed. This derivative has its own schema.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Context, Decimal, localcontext
from pathlib import Path

SCHEMA = "sn09.offline-provider-ledger.v1"
OFFLINE_CAP = Decimal("0.010")
MAX_REQUESTS = 4096
MAX_LEDGER_BYTES = 8 * 1024**2
_MONEY_TOKEN = re.compile(r"(?:[0-9]{1,6}(?:\.[0-9]{1,9})?|\.[0-9]{1,9})")
_ROOT_FIELDS = {"schema", "pilot_cap_usd", "campaign_cap_usd", "balance_ceiling_usd", "requests"}
_ROW_REQUIRED = {
    "request_sha256",
    "model",
    "state",
    "reserved_usd",
    "cost_usd",
    "pricing_sha256",
    "reserved_at",
    "dispatched",
}
_ROW_OPTIONAL = {"dispatched_at", "updated_at", "cancelled_at", "result"}


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _money(value):
    """Exact bounded plain decimal strings; no float, bool or exponent coercion."""
    if type(value) is not str or _MONEY_TOKEN.fullmatch(value) is None:
        return None
    return Decimal(value)


def _atomic(path, value):
    raw = _canonical(value)
    if len(raw) > MAX_LEDGER_BYTES:
        raise ValueError("LEDGER_SIZE_LIMIT")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    created = False
    try:
        with temporary.open("xb") as handle:
            created = True
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        created = False
    finally:
        # A failed replacement must not leave our temporary data behind.
        if created:
            temporary.unlink(missing_ok=True)


@contextmanager
def _locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Non-append mode permits the established-state marker to be updated in place.
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(descriptor, "r+b") as handle:
        deadline = time.monotonic() + 10
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("LEDGER_LOCK_TIMEOUT")
                time.sleep(0.05)
        try:
            # Initialize only while owning byte zero. Locking past EOF is supported
            # by the Windows byte-range lock, and POSIX flock is independent of EOF.
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            yield handle
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("LEDGER_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("LEDGER_NONFINITE_JSON_CONSTANT")


def _text(value, *, empty=False):
    return type(value) is str and (empty or bool(value))


def _validate_row(key, row):
    if not _text(key) or type(row) is not dict:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if not _ROW_REQUIRED <= row.keys() or set(row) - (_ROW_REQUIRED | _ROW_OPTIONAL):
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if any(
        not _text(row[name], empty=name in {"model", "pricing_sha256"})
        for name in ("request_sha256", "model", "pricing_sha256", "reserved_at")
    ):
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if type(row["dispatched"]) is not bool:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    reserved, cost = _money(row["reserved_usd"]), _money(row["cost_usd"])
    state = row["state"]
    if (
        reserved is None
        or type(state) is not str
        or state not in {"RESERVED", "UNKNOWN", "SETTLED", "BREACH", "CANCELLED"}
    ):
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if row["dispatched"] and not _text(row.get("dispatched_at")):
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if state in {"RESERVED", "UNKNOWN", "CANCELLED"}:
        if row["cost_usd"] is not None:
            raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    elif cost is None or not row["dispatched"]:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if state == "UNKNOWN" and not row["dispatched"]:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if state == "CANCELLED" and row["dispatched"]:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if state == "SETTLED" and cost > reserved:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if state == "BREACH" and cost <= reserved:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    expected_fields = set(_ROW_REQUIRED)
    if row["dispatched"]:
        expected_fields.add("dispatched_at")
    if state in {"UNKNOWN", "SETTLED", "BREACH"}:
        expected_fields.update({"updated_at", "result"})
    if state == "CANCELLED":
        expected_fields.update({"cancelled_at", "result"})
    if set(row) != expected_fields:
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if any(
        not _text(row[name])
        for name in expected_fields
        if name in {"dispatched_at", "updated_at", "cancelled_at"}
    ):
        raise ValueError("LEDGER_REQUEST_SCHEMA_MISMATCH")
    if state != "RESERVED":
        result = row.get("result")
        expected_status = {
            "UNKNOWN": "UNRESOLVED",
            "SETTLED": "COMPLETE",
            "BREACH": "UNRESOLVED",
            "CANCELLED": "REFUSED",
        }[state]
        if (
            type(result) is not dict
            or result.get("request_id") != key
            or result.get("status") != expected_status
            or result.get("cost_usd") != row["cost_usd"]
        ):
            raise ValueError("LEDGER_RESULT_BINDING_MISMATCH")
        if state == "BREACH" and result.get("error_code") != "BILLED_COST_EXCEEDS_RESERVATION":
            raise ValueError("LEDGER_RESULT_BINDING_MISMATCH")


class BudgetLedger:
    """Durable offline accounting with an explicit USD 0.010 maximum per cap.

    The lock's established marker detects a missing data file while that marker
    survives. Deletion or forgery of both files is outside this local guarantee;
    this is not authenticated storage or authority to reset a campaign budget.
    """

    def __init__(
        self,
        path,
        pilot_cap_usd="0.010",
        campaign_cap_usd="0.010",
        *,
        authorized_prior_unknown_ids=(),
        balance_ceiling_usd="0.010",
    ):
        self.path = Path(path)
        self.pilot_cap = _money(pilot_cap_usd)
        self.campaign_cap = _money(campaign_cap_usd)
        self.balance_ceiling = _money(balance_ceiling_usd)
        if self.pilot_cap is None or self.campaign_cap is None:
            raise ValueError("BUDGET_CAP_NOT_AUTHORIZED")
        if self.balance_ceiling is None:
            raise ValueError("ACCOUNT_CEILING_NOT_AUTHORIZED")
        if type(authorized_prior_unknown_ids) not in {tuple, list, frozenset, set} or any(
            not _text(value) for value in authorized_prior_unknown_ids
        ):
            raise ValueError("PRIOR_UNKNOWN_AUTHORIZATION_REFUSED")
        self.authorized_prior_unknown_ids = frozenset(authorized_prior_unknown_ids)
        with _locked(self.path.with_suffix(".lock")) as lock:
            lock.seek(0)
            marker = lock.read(1)
            if marker not in {b"0", b"1"}:
                raise ValueError("LEDGER_LOCK_MARKER_CORRUPT")
            if self.path.exists():
                # Existing budget identity is checked before fresh-cap authorization.
                data = self._read()
            else:
                if marker == b"1":
                    raise ValueError("LEDGER_ESTABLISHED_STATE_MISSING")
                self._authorize_caps()
                data = {
                    "schema": SCHEMA,
                    "pilot_cap_usd": format(self.pilot_cap, "f"),
                    "campaign_cap_usd": format(self.campaign_cap, "f"),
                    "balance_ceiling_usd": format(self.balance_ceiling, "f"),
                    "requests": {},
                }
                if self.authorized_prior_unknown_ids:
                    raise ValueError("PRIOR_UNKNOWN_AUTHORIZATION_REFUSED")
                _atomic(self.path, data)
            prior_unknown = {
                key for key, row in data["requests"].items() if row["state"] == "UNKNOWN"
            }
            if not self.authorized_prior_unknown_ids <= prior_unknown:
                raise ValueError("PRIOR_UNKNOWN_AUTHORIZATION_REFUSED")
            lock.seek(0)
            lock.write(b"1")
            lock.flush()
            os.fsync(lock.fileno())

    def _authorize_caps(self):
        if self.pilot_cap > OFFLINE_CAP or self.campaign_cap > OFFLINE_CAP:
            raise ValueError("BUDGET_CAP_NOT_AUTHORIZED")
        if self.balance_ceiling > OFFLINE_CAP:
            raise ValueError("ACCOUNT_CEILING_NOT_AUTHORIZED")

    def _read(self):
        if not self.path.is_file():
            raise ValueError("LEDGER_ESTABLISHED_STATE_MISSING")
        try:
            with self.path.open("rb") as handle:
                raw = handle.read(MAX_LEDGER_BYTES + 1)
            if len(raw) > MAX_LEDGER_BYTES:
                raise ValueError("LEDGER_SIZE_LIMIT")
            data = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("LEDGER_JSON_CORRUPT") from error
        if type(data) is not dict or data.get("schema") != SCHEMA:
            raise ValueError("LEDGER_SCHEMA_MISMATCH")
        if set(data) != _ROOT_FIELDS or type(data["requests"]) is not dict:
            raise ValueError("LEDGER_SCHEMA_MISMATCH")
        if len(data["requests"]) > MAX_REQUESTS:
            raise ValueError("LEDGER_REQUEST_LIMIT")
        if (
            _money(data["pilot_cap_usd"]) != self.pilot_cap
            or _money(data["campaign_cap_usd"]) != self.campaign_cap
            or _money(data["balance_ceiling_usd"]) != self.balance_ceiling
        ):
            raise ValueError("LEDGER_CAP_MISMATCH")
        self._authorize_caps()
        for key, row in data["requests"].items():
            _validate_row(key, row)
            if _money(row["reserved_usd"]) > min(
                self.pilot_cap, self.campaign_cap, self.balance_ceiling
            ):
                raise ValueError("LEDGER_EXPOSURE_MISMATCH")
        with localcontext(Context(prec=50)):
            exposure = sum(
                (
                    Decimal(row["cost_usd"])
                    if row["state"] in {"SETTLED", "BREACH"}
                    else Decimal(row["reserved_usd"])
                    if row["state"] != "CANCELLED"
                    else Decimal(0)
                    for row in data["requests"].values()
                ),
                Decimal(0),
            )
            if not any(
                row["state"] == "BREACH" for row in data["requests"].values()
            ) and exposure > min(self.pilot_cap, self.campaign_cap, self.balance_ceiling):
                raise ValueError("LEDGER_EXPOSURE_MISMATCH")
        return data

    def snapshot(self):
        with _locked(self.path.with_suffix(".lock")):
            return self._read()

    def _refuse_holds(self, ledger):
        if any(
            row["state"] == "BREACH"
            or (row["state"] == "UNKNOWN" and key not in self.authorized_prior_unknown_ids)
            for key, row in ledger["requests"].items()
        ):
            raise ValueError("UNRESOLVED_CHARGE_HOLDS_DISPATCH")

    def reserve(self, request_id, amount_usd, *, request_sha256="", model="", pricing_sha256=""):
        amount = _money(amount_usd)
        if amount is None:
            raise ValueError("INVALID_RESERVATION")
        if not _text(request_id) or any(
            not _text(value, empty=True) for value in (request_sha256, model, pricing_sha256)
        ):
            raise ValueError("INVALID_REQUEST_IDENTITY")
        fingerprint = request_sha256 or _sha(_canonical([request_id, format(amount, "f"), model]))
        with _locked(self.path.with_suffix(".lock")):
            ledger = self._read()
            prior = ledger["requests"].get(request_id)
            if prior:
                if (
                    prior["request_sha256"] != fingerprint
                    or _money(prior["reserved_usd"]) != amount
                    or prior["model"] != model
                    or prior["pricing_sha256"] != pricing_sha256
                ):
                    raise ValueError("REQUEST_ID_REUSED_WITH_DIFFERENT_INPUT")
                return prior.get("result") or {
                    "status": "UNRESOLVED",
                    "error_code": "REQUEST_ALREADY_RESERVED",
                    "request_id": request_id,
                    "cost_usd": None,
                }
            self._refuse_holds(ledger)
            if len(ledger["requests"]) >= MAX_REQUESTS:
                raise ValueError("LEDGER_REQUEST_LIMIT")
            with localcontext(Context(prec=50)):
                exposure = sum(
                    (
                        Decimal(row["cost_usd"])
                        if row["state"] in {"SETTLED", "BREACH"}
                        else Decimal(row["reserved_usd"])
                        if row["state"] != "CANCELLED"
                        else Decimal(0)
                        for row in ledger["requests"].values()
                    ),
                    Decimal(0),
                )
                if exposure + amount > min(self.pilot_cap, self.campaign_cap, self.balance_ceiling):
                    raise ValueError("BUDGET_RESERVATION_REFUSED")
            ledger["requests"][request_id] = {
                "request_sha256": fingerprint,
                "model": model,
                "state": "RESERVED",
                "reserved_usd": format(amount, "f"),
                "cost_usd": None,
                "pricing_sha256": pricing_sha256,
                "reserved_at": _now(),
                "dispatched": False,
            }
            _atomic(self.path, ledger)
        return None

    def mark_dispatched(self, request_id):
        with _locked(self.path.with_suffix(".lock")):
            ledger = self._read()
            row = ledger["requests"][request_id]
            if row["state"] != "RESERVED" or row["dispatched"]:
                raise ValueError("REQUEST_NOT_DISPATCHABLE")
            self._refuse_holds(ledger)
            row.update(dispatched=True, dispatched_at=_now())
            _atomic(self.path, ledger)

    def settle(self, request_id, cost_usd, *, result=None):
        cost = _money(cost_usd)
        if cost is None:
            raise ValueError("UNKNOWN_IS_NOT_ZERO")
        if result is not None and type(result) is not dict:
            raise ValueError("INVALID_RESULT")
        with _locked(self.path.with_suffix(".lock")):
            ledger = self._read()
            row = ledger["requests"][request_id]
            if row["state"] == "CANCELLED":
                raise ValueError("CANCELLED_REQUEST_CANNOT_SETTLE")
            if row["state"] in {"SETTLED", "BREACH"}:
                if Decimal(row["cost_usd"]) != cost:
                    raise ValueError("CONFLICTING_RECONCILIATION")
                return row["result"]
            if not row["dispatched"]:
                raise ValueError("REQUEST_NOT_DISPATCHED")
            state = "BREACH" if cost > Decimal(row["reserved_usd"]) else "SETTLED"
            result = {
                **(result or {}),
                "request_id": request_id,
                "cost_usd": format(cost, "f"),
                "status": "COMPLETE",
            }
            if state == "BREACH":
                result.update(status="UNRESOLVED", error_code="BILLED_COST_EXCEEDS_RESERVATION")
            row.update(state=state, cost_usd=format(cost, "f"), result=result, updated_at=_now())
            _atomic(self.path, ledger)
        return result

    def unresolved(self, request_id, reason="BILLING_UNKNOWN", *, result=None):
        if not _text(reason) or (result is not None and type(result) is not dict):
            raise ValueError("INVALID_RESULT")
        with _locked(self.path.with_suffix(".lock")):
            ledger = self._read()
            row = ledger["requests"][request_id]
            if row["state"] not in {"RESERVED", "UNKNOWN"}:
                raise ValueError("REQUEST_ALREADY_TERMINAL")
            if not row["dispatched"]:
                raise ValueError("REQUEST_NOT_DISPATCHED")
            result = {
                **(result or {}),
                "request_id": request_id,
                "cost_usd": None,
                "status": "UNRESOLVED",
                "error_code": reason,
            }
            row.update(state="UNKNOWN", cost_usd=None, result=result, updated_at=_now())
            _atomic(self.path, ledger)
        return result

    def cancel(self, request_id):
        with _locked(self.path.with_suffix(".lock")):
            ledger = self._read()
            row = ledger["requests"][request_id]
            if row["state"] == "CANCELLED":
                return row
            if row["state"] != "RESERVED" or row["dispatched"]:
                raise ValueError("DISPATCHED_OR_TERMINAL_RESERVATION_CANNOT_CANCEL")
            row.update(
                state="CANCELLED",
                cancelled_at=_now(),
                result={
                    "request_id": request_id,
                    "status": "REFUSED",
                    "error_code": "CANCELLED_BEFORE_DISPATCH",
                    "cost_usd": None,
                    "cost_status": "NOT_DISPATCHED",
                },
            )
            _atomic(self.path, ledger)
        return row

    def summary(self):
        snapshot = self.snapshot()
        rows = list(snapshot["requests"].values())
        with localcontext(Context(prec=50)):
            spent = sum(
                (Decimal(row["cost_usd"]) for row in rows if row["state"] in {"SETTLED", "BREACH"}),
                Decimal(0),
            )
            held = sum(
                (
                    Decimal(row["reserved_usd"])
                    for row in rows
                    if row["state"] in {"RESERVED", "UNKNOWN"}
                ),
                Decimal(0),
            )
            return {
                "settled_usd": format(spent, "f"),
                "held_usd": format(held, "f"),
                "exposure_usd": format(spent + held, "f"),
                "unknown_request_ids": [
                    key for key, row in snapshot["requests"].items() if row["state"] == "UNKNOWN"
                ],
                "request_count": len(rows),
            }
