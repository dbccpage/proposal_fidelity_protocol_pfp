"""Durable producer collection for the intelligence lifecycle.

The collector records a small, idempotent work obligation before downstream
learning or digestion is attempted.  It deliberately does not infer that a
directory is sealed: native lifecycle evaluation owns that transition.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operating_system.adapters.intelligence_custody.ic_routing import (
    intelligence_path,
    intelligence_source_locator,
)
from adversary.domain.intelligence_digestion import (
    IntelligenceCollectionReceipt,
)

COLLECTION_EVENT_SCHEMA = "core.intelligence.collection-event.v1"
COLLECTION_WORK_SCHEMA = "core.intelligence.collection-work.v1"
REVIEW_SCOPE = "core.intelligence.digestion.v1"


class IntelligenceCollectionError(RuntimeError):
    """The durable collection store could not acknowledge a source."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _required_string(name: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        raise IntelligenceCollectionError(f"INTELLIGENCE_COLLECTION_INVALID:{name}")
    return value.strip()


def _stored_source_status(connection: sqlite3.Connection, event_id: str) -> str:
    row = connection.execute(
        """
        SELECT source_status
        FROM intelligence_collection_events
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()
    if row is None:
        raise IntelligenceCollectionError("INTELLIGENCE_COLLECTION_REPLAY_NOT_FOUND")
    return str(row[0])


class DurableIntelligenceCollector:
    """SQLite-backed ingress queue with an immutable event and pending work row.

    SQLite is the collection authority for this first increment.  A JSONL
    projection would be a derived view, never a replacement for this committed
    queue.  The primary key makes duplicate completion notifications idempotent
    while preserving distinct terminal outcomes as distinct observations.
    """

    def __init__(self, repo_root: Path | str, database: Path | str | None = None) -> None:
        self.repo_root = Path(repo_root).resolve()
        if database is not None:
            self.database = Path(database).resolve()
        else:
            permanent = self.repo_root / "_ic/nara/permanent_records/intelligence_state.sqlite3"
            if permanent.exists():
                self.database = permanent
            else:
                self.database = intelligence_path(
                    self.repo_root, "_intelligence/oeos/snapshots/intelligence_state.sqlite3"
                )
        try:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS intelligence_collection_events (
                        event_id TEXT PRIMARY KEY,
                        source_key TEXT NOT NULL,
                        producer_id TEXT NOT NULL,
                        source_locator TEXT NOT NULL,
                        source_status TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        origin TEXT NOT NULL,
                        observed_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS intelligence_collection_identity
                    ON intelligence_collection_events
                    (producer_id, source_locator, outcome, origin);
                    CREATE TABLE IF NOT EXISTS intelligence_digestion_work (
                        work_key TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL UNIQUE,
                        state TEXT NOT NULL,
                        attempts INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_lifecycle_state TEXT,
                        last_detail_json TEXT,
                        FOREIGN KEY(event_id)
                            REFERENCES intelligence_collection_events(event_id)
                    );
                    """
                )
                self._ensure_work_columns(connection)
        except (OSError, sqlite3.Error) as exc:
            raise IntelligenceCollectionError(
                f"INTELLIGENCE_COLLECTION_UNAVAILABLE:{type(exc).__name__}:{exc}"
            ) from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30)
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _ensure_work_columns(connection: sqlite3.Connection) -> None:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(intelligence_digestion_work)")
        }
        for name, declaration in (
            ("updated_at", "TEXT NOT NULL DEFAULT ''"),
            ("last_lifecycle_state", "TEXT"),
            ("last_detail_json", "TEXT"),
        ):
            if name not in columns:
                connection.execute(
                    f"ALTER TABLE intelligence_digestion_work ADD COLUMN {name} {declaration}"
                )

    def _locator(self, run_directory: str | Path) -> tuple[str, str]:
        candidate = Path(run_directory).expanduser().resolve(strict=False)
        try:
            candidate.relative_to(self.repo_root)
        except ValueError as exc:
            raise IntelligenceCollectionError(
                "INTELLIGENCE_COLLECTION_SOURCE_OUTSIDE_ROOT"
            ) from exc
        locator = intelligence_source_locator(self.repo_root, candidate)
        if not locator or locator == ".":
            raise IntelligenceCollectionError("INTELLIGENCE_COLLECTION_SOURCE_INVALID")
        if candidate.is_dir():
            return locator, "AVAILABLE"
        if candidate.exists():
            return locator, "NOT_A_DIRECTORY"
        return locator, "MISSING"

    def collect(
        self,
        run_directory: str | Path,
        *,
        outcome: str,
        origin: str,
        producer_id: str,
    ) -> IntelligenceCollectionReceipt:
        """Commit the collection event and its pending digestion work together."""
        producer = _required_string("producer_id", producer_id)
        terminal_outcome = _required_string("outcome", outcome)
        event_origin = _required_string("origin", origin)
        locator, source_status = self._locator(run_directory)
        source_key = _digest(
            {
                "producer_id": producer,
                "source_class": "run_bundle",
                "source_locator": locator,
            }
        )
        event_id = _digest(
            {
                "schema_version": COLLECTION_EVENT_SCHEMA,
                "source_key": source_key,
                "outcome": terminal_outcome,
                "origin": event_origin,
            }
        )
        work_key = _digest(
            {
                "schema_version": COLLECTION_WORK_SCHEMA,
                "source_key": source_key,
                "event_id": event_id,
                "review_scope": REVIEW_SCOPE,
            }
        )
        observed_at = _now()
        payload: dict[str, Any] = {
            "schema_version": COLLECTION_EVENT_SCHEMA,
            "event_id": event_id,
            "source_key": source_key,
            "producer_id": producer,
            "source_class": "run_bundle",
            "source_locator": locator,
            "source_status": source_status,
            "outcome": terminal_outcome,
            "origin": event_origin,
            "review_scope": REVIEW_SCOPE,
            "observed_at": observed_at,
            "authority_effect": "None",
        }
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO intelligence_collection_events
                    (event_id, source_key, producer_id, source_locator, source_status,
                     outcome, origin, observed_at, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        source_key,
                        producer,
                        locator,
                        source_status,
                        terminal_outcome,
                        event_origin,
                        observed_at,
                        _canonical(payload).decode("utf-8"),
                    ),
                )
                created = cursor.rowcount == 1
                connection.execute(
                    """
                    INSERT OR IGNORE INTO intelligence_digestion_work
                    (work_key, event_id, state, created_at, updated_at)
                    VALUES (?, ?, 'PENDING', ?, ?)
                    """,
                    (work_key, event_id, observed_at, observed_at),
                )
                if not created:
                    source_status = _stored_source_status(connection, event_id)
        except (OSError, sqlite3.Error) as exc:
            raise IntelligenceCollectionError(
                f"INTELLIGENCE_COLLECTION_UNAVAILABLE:{type(exc).__name__}:{exc}"
            ) from exc
        return IntelligenceCollectionReceipt(
            event_id=event_id,
            work_key=work_key,
            source_locator=locator,
            source_status=source_status,
            created=created,
        )

    def pending_work(self) -> list[dict[str, str]]:
        """Inspection seam for the supervisor and focused tests."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT work.work_key, work.event_id, work.state, work.created_at,
                           event.producer_id, event.source_locator, event.source_status,
                           event.outcome, work.last_lifecycle_state, work.last_detail_json
                    FROM intelligence_digestion_work AS work
                    JOIN intelligence_collection_events AS event ON event.event_id = work.event_id
                    WHERE work.state = 'PENDING'
                    ORDER BY work.created_at, work.work_key
                    """
                ).fetchall()
        except (OSError, sqlite3.Error) as exc:
            raise IntelligenceCollectionError(
                f"INTELLIGENCE_COLLECTION_UNAVAILABLE:{type(exc).__name__}:{exc}"
            ) from exc
        return [
            {
                "work_key": str(row[0]),
                "event_id": str(row[1]),
                "state": str(row[2]),
                "created_at": str(row[3]),
                "producer_id": str(row[4]),
                "source_locator": str(row[5]),
                "source_status": str(row[6]),
                "outcome": str(row[7]),
                "last_lifecycle_state": str(row[8] or ""),
                "last_detail_json": str(row[9] or ""),
            }
            for row in rows
        ]

    def record_lifecycle(
        self,
        work_key: str,
        *,
        lifecycle_state: str,
        detail: Mapping[str, Any],
    ) -> None:
        """Keep a work item pending while recording its latest native result."""
        state = _required_string("lifecycle_state", lifecycle_state)
        updated_at = _now()
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE intelligence_digestion_work
                    SET last_lifecycle_state = ?, last_detail_json = ?, updated_at = ?
                    WHERE work_key = ? AND state = 'PENDING'
                    """,
                    (state, _canonical(detail).decode("utf-8"), updated_at, work_key),
                )
                if cursor.rowcount != 1:
                    raise IntelligenceCollectionError("INTELLIGENCE_COLLECTION_WORK_NOT_PENDING")
        except (OSError, sqlite3.Error) as exc:
            raise IntelligenceCollectionError(
                f"INTELLIGENCE_COLLECTION_UNAVAILABLE:{type(exc).__name__}:{exc}"
            ) from exc

    def complete_work(
        self,
        work_key: str,
        *,
        lifecycle_state: str,
        detail: Mapping[str, Any],
    ) -> None:
        """Retire a work item only after its source has left the active queue."""
        state = _required_string("lifecycle_state", lifecycle_state)
        updated_at = _now()
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE intelligence_digestion_work
                    SET state = 'COMPLETED', last_lifecycle_state = ?,
                        last_detail_json = ?, updated_at = ?
                    WHERE work_key = ?
                    """,
                    (state, _canonical(detail).decode("utf-8"), updated_at, work_key),
                )
                if cursor.rowcount != 1:
                    raise IntelligenceCollectionError("INTELLIGENCE_COLLECTION_WORK_NOT_FOUND")
        except (OSError, sqlite3.Error) as exc:
            raise IntelligenceCollectionError(
                f"INTELLIGENCE_COLLECTION_UNAVAILABLE:{type(exc).__name__}:{exc}"
            ) from exc
