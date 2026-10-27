"""Inbox deduplication and a trusted SQLite-local effect in one transaction.

A subscriber name identifies one stable projection. Its callback may read and
write durable tables in this same database, returning None/Ok for success or Err
for refusal. It must not send externally, change transaction/connection state,
or bypass the callback SQL guard. This is a trusted in-process callback contract,
not a Python sandbox. Delivery remains at-least-once; the local effect is deduped
by subscriber name and event ID. No multiworker lease or power-loss claim.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from threading import RLock
from typing import Callable

from operations.domain.rop.result import Err, Ok, Result

from ...domain.errors.domain_errors import DomainInvariantError, OeopDomainError

LocalEffect = Callable[[sqlite3.Connection, dict], None | Result[object, OeopDomainError]]
INBOX_TABLE = "subscriber_inbox_v1"
ENVELOPE_PROFILE = "oewas.inbox.envelope.v1"


def _validate_json(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("Event envelope object keys must be strings")
            _validate_json(child)
    elif isinstance(value, list):
        for child in value:
            _validate_json(child)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("Event envelope values must be JSON values")


def _effect_authorizer(
    action: int, table: str | None, _column: str | None, database: str | None, _source: str | None
) -> int:
    """Allow local DML/reads, denying transaction, schema and inbox changes.

    This prevents accidental commit/rollback/executescript and table misuse. A
    trusted Python callback can replace the authorizer, so this is no sandbox.
    """
    if action in {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE}:
        return (
            sqlite3.SQLITE_OK
            if database == "main" and table != INBOX_TABLE
            else sqlite3.SQLITE_DENY
        )
    if action in {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _envelope(message: dict) -> tuple[str, dict, str]:
    if not isinstance(message, dict):
        raise ValueError("Event envelope must be a mapping")
    event_id = message.get("event_id")
    if not isinstance(event_id, str) or not event_id or event_id.strip() != event_id:
        raise ValueError("event_id must be a nonempty, unpadded string")
    event = {key: value for key, value in message.items() if key not in {"outbox_id", "created_at"}}
    _validate_json(event)
    encoded = json.dumps(
        event, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    digest = hashlib.sha256(
        ENVELOPE_PROFILE.encode("ascii") + b"\0" + encoded.encode("utf-8")
    ).hexdigest()
    # Give the effect its own JSON value, excluding delivery-only fields. Binding
    # is to this canonical envelope, not Python object identity or JSON key order.
    return event_id, json.loads(encoded), digest


class SqliteInboxSubscriber:
    """A named, file-backed subscriber for one trusted SQLite-local effect.

    Keep the name stable across retries and reopen. Renaming it creates a new
    consumer and therefore a new effect. The digest covers every event envelope
    field except outbox_id/created_at; payload_json is bound exactly as supplied.
    Profile oewas.inbox.envelope.v1 accepts JSON values with string object keys
    and finite numbers. Python json.dumps sorts keys, uses compact separators,
    ensure_ascii=False and allow_nan=False, then SHA-256 binds the profile plus a
    NUL plus UTF-8 bytes. This is a named Python JSON profile, not RFC 8785. Missing,
    padded or nonstring event IDs and non-JSON coercions are refused. A dict has
    already discarded duplicate source keys; source decoding must refuse those
    before this port if it accepts raw JSON. This cannot recover richer event
    payloads that the producer did not persist.
    """

    def __init__(self, db_path: str, subscriber_name: str, effect: LocalEffect) -> None:
        if (
            not isinstance(subscriber_name, str)
            or not subscriber_name
            or subscriber_name.strip() != subscriber_name
        ):
            raise ValueError("subscriber_name must be a nonempty, unpadded string")
        if not db_path or db_path == ":memory:":
            raise ValueError("A file-backed database path is required")
        self._name = subscriber_name
        self._effect = effect
        self._lock = RLock()
        self._conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        with self._conn:
            self._conn.execute(f"""CREATE TABLE IF NOT EXISTS {INBOX_TABLE} (
                subscriber_name TEXT NOT NULL,
                event_id TEXT NOT NULL,
                envelope_digest TEXT NOT NULL,
                PRIMARY KEY (subscriber_name, event_id)
            )""")

    def __enter__(self) -> SqliteInboxSubscriber:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def _error(self, code: str, message: str) -> Err[OeopDomainError]:
        return Err(DomainInvariantError(code=code, message=message, locus=self._name))

    def __call__(self, message: dict) -> Result[None, OeopDomainError]:
        try:
            event_id, event, digest = _envelope(message)
        except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
            return self._error("INBOX_INVALID_EVENT", str(exc))

        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                existing = self._conn.execute(
                    f"SELECT envelope_digest FROM {INBOX_TABLE} WHERE subscriber_name=? AND event_id=?",
                    (self._name, event_id),
                ).fetchone()
                if existing is not None:
                    self._conn.rollback()
                    if existing[0] != digest:
                        return self._error(
                            "INBOX_EVENT_CONFLICT", f"Changed envelope for event_id {event_id}"
                        )
                    return Ok(None)

                self._conn.set_authorizer(_effect_authorizer)
                try:
                    outcome = self._effect(self._conn, event)
                finally:
                    self._conn.set_authorizer(None)
                if isinstance(outcome, Err):
                    self._conn.rollback()
                    return outcome
                if outcome is not None and not isinstance(outcome, Ok):
                    self._conn.rollback()
                    return self._error(
                        "INBOX_EFFECT_RESULT_INVALID", "Effect must return None, Ok or Err"
                    )
                self._conn.execute(
                    f"INSERT INTO {INBOX_TABLE} VALUES (?, ?, ?)",
                    (self._name, event_id, digest),
                )
                self._conn.commit()
                return Ok(None)
            except Exception as exc:
                self._conn.rollback()
                return self._error("INBOX_EFFECT_FAILED", str(exc))
