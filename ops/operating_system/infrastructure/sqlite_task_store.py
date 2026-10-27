"""SQLite-WAL task, event, and outbox transaction for OEOS v1.

Every aggregate mutation appends its lifecycle events, updates the task
snapshot, and writes the matching dispatch intents in one ``BEGIN IMMEDIATE``
transaction. Event rows are append-only by SQLite trigger. The per-task chain
proves internal consistency only; callers must pin a tip outside this database
to detect tail truncation.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from types import TracebackType
from typing import Self

from ..application.ports import TaskStoreError
from ..domain import (
    CapabilitySnapshotV1,
    EncryptedArtifactRefV1,
    HarnessEventV1,
    TaskAggregateV1,
    TaskEnvelopeV1,
    TaskInvariantError,
    TaskStateV1,
    canonical_json,
    digest_payload,
)


class SqliteTaskStore:
    """Durable task store implementing the OEOS application port."""

    destination = "events.oeos.v1"

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._lock = RLock()
        self._conn = sqlite3.connect(
            self._db_path, timeout=30.0, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._initialize()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback
        self.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _initialize(self) -> None:
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS oeos_tasks_v1 (
                    task_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    envelope_digest TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    capability_snapshot_digest TEXT NOT NULL,
                    capability_snapshot_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    cancellation_requested INTEGER NOT NULL CHECK (
                        cancellation_requested IN (0, 1)
                    ),
                    chain_tip TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS oeos_events_v1 (
                    task_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_digest TEXT NOT NULL UNIQUE,
                    event_json TEXT NOT NULL,
                    occurred_at_utc TEXT NOT NULL,
                    PRIMARY KEY (task_id, sequence),
                    FOREIGN KEY (task_id) REFERENCES oeos_tasks_v1(task_id)
                );

                CREATE TABLE IF NOT EXISTS oeos_outbox_v1 (
                    outbox_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    event_sequence INTEGER NOT NULL,
                    event_digest TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    delivered_at_utc TEXT,
                    FOREIGN KEY (task_id, event_sequence)
                        REFERENCES oeos_events_v1(task_id, sequence)
                );

                CREATE TRIGGER IF NOT EXISTS oeos_events_v1_no_update
                BEFORE UPDATE ON oeos_events_v1
                BEGIN
                    SELECT RAISE(ABORT, 'OEOS event ledger is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS oeos_events_v1_no_delete
                BEFORE DELETE ON oeos_events_v1
                BEGIN
                    SELECT RAISE(ABORT, 'OEOS event ledger is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS oeos_outbox_v1_no_delete
                BEFORE DELETE ON oeos_outbox_v1
                BEGIN
                    SELECT RAISE(ABORT, 'OEOS outbox intent is durable');
                END;

                CREATE TRIGGER IF NOT EXISTS oeos_outbox_v1_immutable_intent
                BEFORE UPDATE ON oeos_outbox_v1
                WHEN NEW.outbox_id != OLD.outbox_id
                  OR NEW.task_id != OLD.task_id
                  OR NEW.event_sequence != OLD.event_sequence
                  OR NEW.event_digest != OLD.event_digest
                  OR NEW.destination != OLD.destination
                  OR NEW.created_at_utc != OLD.created_at_utc
                  OR OLD.delivered_at_utc IS NOT NULL
                  OR NEW.delivered_at_utc IS NULL
                BEGIN
                    SELECT RAISE(ABORT, 'OEOS outbox intent is immutable');
                END;
                """
            )
            self._conn.execute("BEGIN IMMEDIATE")
            columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(oeos_tasks_v1)")}
            if "encrypted_input_ref_json" not in columns:
                self._conn.execute("ALTER TABLE oeos_tasks_v1 ADD COLUMN encrypted_input_ref_json TEXT")

    @staticmethod
    def _outbox_id(event: HarnessEventV1) -> str:
        return digest_payload(
            "core.oeos.outbox-intent.v1",
            {"destination": SqliteTaskStore.destination, "event": event.event_digest},
        )

    def _insert_event(self, event: HarnessEventV1) -> None:
        self._conn.execute(
            """
            INSERT INTO oeos_events_v1 (
                task_id, sequence, event_digest, event_json, occurred_at_utc
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                event.task_id,
                event.sequence,
                event.event_digest,
                canonical_json(event.to_canonical()),
                event.occurred_at_utc,
            ),
        )
        self._conn.execute(
            """
            INSERT INTO oeos_outbox_v1 (
                outbox_id, task_id, event_sequence, event_digest,
                destination, created_at_utc, delivered_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                self._outbox_id(event),
                event.task_id,
                event.sequence,
                event.event_digest,
                self.destination,
                event.occurred_at_utc,
            ),
        )

    def create(self, task: TaskAggregateV1) -> tuple[TaskAggregateV1, bool]:
        if type(task) is not TaskAggregateV1 or task.version != 1:
            raise TaskStoreError(
                "INVALID_NEW_AGGREGATE", "new task must contain submission only"
            )
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                existing = self._conn.execute(
                    "SELECT task_id, envelope_digest FROM oeos_tasks_v1 WHERE idempotency_key = ?",
                    (task.envelope.idempotency_key,),
                ).fetchone()
                if existing is not None:
                    if existing["envelope_digest"] != task.envelope.canonical_digest:
                        raise TaskStoreError(
                            "IDEMPOTENCY_CONFLICT",
                            "idempotency key was already used with different content",
                        )
                    self._conn.rollback()
                    loaded = self.load(str(existing["task_id"]))
                    if loaded is None:
                        raise TaskStoreError(
                            "STORE_CORRUPT", "idempotency row lost its task"
                        )
                    return loaded, False
                collision = self._conn.execute(
                    "SELECT 1 FROM oeos_tasks_v1 WHERE task_id = ?",
                    (task.envelope.task_id,),
                ).fetchone()
                if collision is not None:
                    raise TaskStoreError("TASK_ID_CONFLICT", "task ID already exists")
                first = task.events[0]
                self._conn.execute(
                    """
                    INSERT INTO oeos_tasks_v1 (
                        task_id, idempotency_key, envelope_digest, envelope_json,
                        capability_snapshot_digest, capability_snapshot_json,
                        state, version, cancellation_requested, chain_tip,
                        created_at_utc, updated_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.envelope.task_id,
                        task.envelope.idempotency_key,
                        task.envelope.canonical_digest,
                        canonical_json(task.envelope.to_canonical()),
                        task.capability_snapshot.canonical_digest,
                        canonical_json(task.capability_snapshot.to_canonical()),
                        task.state.value,
                        task.version,
                        int(task.cancellation_requested),
                        task.chain_tip,
                        first.occurred_at_utc,
                        first.occurred_at_utc,
                    ),
                )
                self._insert_event(first)
                self._conn.commit()
                return task, True
            except TaskStoreError:
                if self._conn.in_transaction:
                    self._conn.rollback()
                raise
            except sqlite3.Error as exc:
                if self._conn.in_transaction:
                    self._conn.rollback()
                raise TaskStoreError("TASK_CREATE_FAILED", type(exc).__name__) from exc

    def save(self, task: TaskAggregateV1, *, expected_version: int) -> None:
        if type(task) is not TaskAggregateV1:
            raise TaskStoreError("INVALID_AGGREGATE", "exact TaskAggregateV1 required")
        if type(expected_version) is not int or task.version <= expected_version:
            raise TaskStoreError("INVALID_EXPECTED_VERSION", "save requires new events")
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                row = self._conn.execute(
                    """
                    SELECT version, envelope_digest, capability_snapshot_digest, chain_tip
                    FROM oeos_tasks_v1 WHERE task_id = ?
                    """,
                    (task.envelope.task_id,),
                ).fetchone()
                if row is None:
                    raise TaskStoreError("TASK_NOT_FOUND", "task does not exist")
                if int(row["version"]) != expected_version:
                    raise TaskStoreError(
                        "CONCURRENCY_CONFLICT",
                        "stored task version differs from expected",
                    )
                if (
                    row["envelope_digest"] != task.envelope.canonical_digest
                    or row["capability_snapshot_digest"]
                    != task.capability_snapshot.canonical_digest
                    or row["chain_tip"]
                    != task.events[expected_version - 1].event_digest
                ):
                    raise TaskStoreError(
                        "AGGREGATE_IDENTITY_DRIFT", "immutable task fields differ"
                    )
                stored_events = self._conn.execute(
                    "SELECT event_digest FROM oeos_events_v1 WHERE task_id = ? ORDER BY sequence",
                    (task.envelope.task_id,),
                ).fetchall()
                if tuple(item["event_digest"] for item in stored_events) != tuple(
                    event.event_digest for event in task.events[:expected_version]
                ):
                    raise TaskStoreError(
                        "EVENT_PREFIX_MISMATCH", "stored event prefix differs"
                    )
                for event in task.events[expected_version:]:
                    self._insert_event(event)
                self._conn.execute(
                    """
                    UPDATE oeos_tasks_v1
                    SET state = ?, version = ?, cancellation_requested = ?,
                        chain_tip = ?, updated_at_utc = ?, encrypted_input_ref_json = ?
                    WHERE task_id = ? AND version = ?
                    """,
                    (
                        task.state.value,
                        task.version,
                        int(task.cancellation_requested),
                        task.chain_tip,
                        task.events[-1].occurred_at_utc,
                        canonical_json(task.encrypted_input_ref.to_canonical())
                        if task.encrypted_input_ref is not None else None,
                        task.envelope.task_id,
                        expected_version,
                    ),
                )
                if self._conn.execute("SELECT changes()").fetchone()[0] != 1:
                    raise TaskStoreError(
                        "CONCURRENCY_CONFLICT", "task update lost its version"
                    )
                self._conn.commit()
            except TaskStoreError:
                if self._conn.in_transaction:
                    self._conn.rollback()
                raise
            except sqlite3.Error as exc:
                if self._conn.in_transaction:
                    self._conn.rollback()
                raise TaskStoreError("TASK_SAVE_FAILED", type(exc).__name__) from exc

    def _decode_json(self, text: str, code: str) -> dict[str, object]:
        try:
            value = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise TaskStoreError(code, "stored JSON is unreadable") from exc
        if type(value) is not dict or canonical_json(value) != text:
            raise TaskStoreError(code, "stored JSON is not canonical")
        return value

    def _event_rows(self, task_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT event_json, event_digest FROM oeos_events_v1
            WHERE task_id = ? ORDER BY sequence
            """,
            (task_id,),
        ).fetchall()

    def _decode_events(self, rows: list[sqlite3.Row]) -> tuple[HarnessEventV1, ...]:
        events = []
        for row in rows:
            try:
                event = HarnessEventV1.from_canonical(
                    self._decode_json(row["event_json"], "EVENT_DECODE_FAILED")
                )
            except (TaskInvariantError, TaskStoreError) as exc:
                raise TaskStoreError("EVENT_DECODE_FAILED", type(exc).__name__) from exc
            if row["event_digest"] != event.event_digest:
                raise TaskStoreError(
                    "EVENT_DIGEST_MISMATCH", "indexed event digest differs"
                )
            events.append(event)
        return tuple(events)

    def events(self, task_id: str) -> tuple[HarnessEventV1, ...]:
        with self._lock:
            return self._decode_events(self._event_rows(task_id))

    def load(self, task_id: str) -> TaskAggregateV1 | None:
        with self._lock:
            try:
                # Keep the denormalized snapshot and its event prefix in one
                # SQLite read transaction. A second process may own another
                # connection even though this adapter serializes its own calls.
                self._conn.execute("BEGIN")
                row = self._conn.execute(
                    "SELECT * FROM oeos_tasks_v1 WHERE task_id = ?", (task_id,)
                ).fetchone()
                if row is None:
                    self._conn.commit()
                    return None
                event_rows = self._event_rows(task_id)
                self._conn.commit()
            except sqlite3.Error as exc:
                if self._conn.in_transaction:
                    self._conn.rollback()
                raise TaskStoreError("TASK_LOAD_FAILED", type(exc).__name__) from exc
        envelope_value = self._decode_json(
            row["envelope_json"], "ENVELOPE_DECODE_FAILED"
        )
        snapshot_value = self._decode_json(
            row["capability_snapshot_json"], "SNAPSHOT_DECODE_FAILED"
        )
        try:
            envelope = TaskEnvelopeV1.from_canonical(envelope_value)
            snapshot = CapabilitySnapshotV1.from_canonical(snapshot_value)
            events = self._decode_events(event_rows)
            input_json = row["encrypted_input_ref_json"]
            input_reference = (
                EncryptedArtifactRefV1.from_canonical(
                    self._decode_json(input_json, "OPERATOR_INPUT_DECODE_FAILED")
                )
                if input_json is not None else None
            )
            task = TaskAggregateV1(
                envelope=envelope,
                capability_snapshot=snapshot,
                state=TaskStateV1(row["state"]),
                version=int(row["version"]),
                cancellation_requested=bool(row["cancellation_requested"]),
                events=events,
                encrypted_input_ref=input_reference,
            )
        except (TaskInvariantError, TypeError, ValueError) as exc:
            raise TaskStoreError("AGGREGATE_DECODE_FAILED", type(exc).__name__) from exc
        if (
            row["envelope_digest"] != envelope.canonical_digest
            or row["capability_snapshot_digest"] != snapshot.canonical_digest
            or row["chain_tip"] != task.chain_tip
        ):
            raise TaskStoreError(
                "AGGREGATE_DIGEST_MISMATCH", "stored aggregate digest differs"
            )
        return task

    def tasks_in_state(self, state: TaskStateV1) -> tuple[str, ...]:
        if type(state) is not TaskStateV1:
            raise TaskStoreError("INVALID_STATE", "exact TaskStateV1 required")
        with self._lock:
            rows = self._conn.execute(
                "SELECT task_id FROM oeos_tasks_v1 WHERE state = ? ORDER BY created_at_utc, task_id",
                (state.value,),
            ).fetchall()
        return tuple(row["task_id"] for row in rows)

    def pending_outbox(self, limit: int = 100) -> tuple[dict[str, object], ...]:
        if type(limit) is not int or not 1 <= limit <= 10_000:
            raise TaskStoreError(
                "INVALID_OUTBOX_LIMIT", "outbox limit is outside bounds"
            )
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT outbox_id, task_id, event_sequence, event_digest,
                       destination, created_at_utc
                FROM oeos_outbox_v1
                WHERE delivered_at_utc IS NULL
                ORDER BY created_at_utc, task_id, event_sequence
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def mark_outbox_delivered(self, outbox_id: str, delivered_at_utc: str) -> None:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                """
                UPDATE oeos_outbox_v1 SET delivered_at_utc = ?
                WHERE outbox_id = ? AND delivered_at_utc IS NULL
                """,
                (delivered_at_utc, outbox_id),
            )
            if cursor.rowcount != 1:
                raise TaskStoreError("OUTBOX_NOT_PENDING", "outbox item is not pending")

    def diagnostic(self) -> dict[str, object]:
        with self._lock:
            check = str(self._conn.execute("PRAGMA quick_check").fetchone()[0])
            tasks = int(
                self._conn.execute("SELECT COUNT(*) FROM oeos_tasks_v1").fetchone()[0]
            )
            pending = int(
                self._conn.execute(
                    "SELECT COUNT(*) FROM oeos_outbox_v1 WHERE delivered_at_utc IS NULL"
                ).fetchone()[0]
            )
        return {
            "pending_outbox": pending,
            "status": "HEALTHY" if check == "ok" else "DEGRADED",
            "task_count": tasks,
        }


__all__ = ["SqliteTaskStore"]
