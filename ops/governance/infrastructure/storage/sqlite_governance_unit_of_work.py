"""SQLite WAL Unit of Work for Engine Governance.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from types import TracebackType
from typing import Any

from governance.domain.shared_kernel.entities.aggregate_root import AggregateRoot
from governance.domain.shared_kernel.events.domain_event import DomainEvent
from governance.infrastructure.storage.schema_totality import install_totality_fences

_SCHEMA_ADDITIONS: dict[str, dict[str, str]] = {
    "council_sessions": {"decision_json": "TEXT", "observations_json": "TEXT", "motion_text": "TEXT",
                         "finalization_request_json": "TEXT", "attendance_json": "TEXT",
                         "resumption_json": "TEXT",
                         "fixture_observations_json": "TEXT",
                         "action_proposals_json": "TEXT",
                         "action_owner_responses_json": "TEXT",
                         "action_attempts_json": "TEXT",
                         "action_reviews_json": "TEXT",
                         "action_follow_up_json": "TEXT",
                         "statements_json": "TEXT",
                         "appeal_json": "TEXT",
                         "storage_revision": "INTEGER NOT NULL DEFAULT 1"},
    "agent_identities": {
        "code_hash": "TEXT",
        "code_hash_kind": "TEXT",
        "version": "INTEGER NOT NULL DEFAULT 1",
    },
    "swarm_tasks": {"version": "INTEGER NOT NULL DEFAULT 1"},
    "change_proposals": {
        "target_ref": "TEXT NOT NULL DEFAULT 'main'",
        "carrier_oid": "TEXT",
        "carrier_oid_kind": "TEXT",
        "version": "INTEGER NOT NULL DEFAULT 1",
    },
    "evidence_records": {
        "observations_json": "TEXT NOT NULL DEFAULT '[]'",
        "version": "INTEGER NOT NULL DEFAULT 1",
    },
    "policy_compliance_records": {
        "justification": "TEXT NOT NULL DEFAULT ''",
        "adopter": "TEXT NOT NULL DEFAULT ''",
        "expires_at": "TEXT",
        "version": "INTEGER NOT NULL DEFAULT 1",
    },
}


class SqliteGovernanceUnitOfWork:
    """Manages transactional state mutations and atomic domain event journaling into SQLite WAL."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._in_transaction = False
        self._registered_aggregates: list[AggregateRoot[Any]] = []
        self._pending_events: list[tuple[DomainEvent, str]] = []

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        schema_path = Path(__file__).parent / "governance_schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        legacy_agent_schema = False
        legacy_evidence_schema = False
        for table_name, additions in _SCHEMA_ADDITIONS.items():
            existing_columns = {
                row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")
            }
            if table_name == "agent_identities":
                legacy_agent_schema = "code_hash" not in existing_columns
            if table_name == "evidence_records":
                legacy_evidence_schema = "observations_json" not in existing_columns
            for column_name, definition in additions.items():
                if column_name not in existing_columns:
                    conn.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
                    )
        if legacy_agent_schema:
            conn.execute(
                """
                UPDATE agent_identities
                SET code_hash = ceiling_level,
                    code_hash_kind = CASE
                        WHEN length(ceiling_level) = 40 THEN 'GIT_OID'
                        ELSE 'SHA256'
                    END
                WHERE code_hash IS NULL
                    AND length(ceiling_level) IN (40, 64)
                    AND ceiling_level NOT GLOB '*[^0-9A-Fa-f]*'
                """
            )
        if legacy_evidence_schema:
            legacy_rows = conn.execute(
                """
                SELECT evidence_id, artifact_ref, digest_hex, created_at
                FROM evidence_records
                WHERE observations_json = '[]'
                """
            ).fetchall()
            for row in legacy_rows:
                digest = row["digest_hex"]
                if digest == "0" * 64 or len(digest) not in (40, 64):
                    continue
                if any(char not in "0123456789abcdefABCDEF" for char in digest):
                    continue
                digest_kind = "GIT_OID" if len(digest) == 40 else "SHA256"
                observations_json = json.dumps(
                    [
                        {
                            "digest": digest,
                            "digest_kind": digest_kind,
                            "id": f"legacy-{row['evidence_id']}",
                            "locator": row["artifact_ref"],
                            "recorded_at": row["created_at"],
                        }
                    ],
                    sort_keys=True,
                )
                conn.execute(
                    """
                    UPDATE evidence_records
                    SET observations_json = ?
                    WHERE evidence_id = ?
                    """,
                    (observations_json, row["evidence_id"]),
                )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_gov_outbox_event_id "
            "ON governance_outbox(event_id)"
        )
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        install_totality_fences(conn, schema_sql)
        conn.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            try:
                self._apply_schema(conn)
            except Exception:
                conn.close()
                raise
            self._conn = conn
        return self._conn

    def register_aggregate(self, aggregate: AggregateRoot[Any]) -> None:
        """Registers an aggregate root so that uncommitted events are flushed upon commit."""
        if aggregate not in self._registered_aggregates:
            self._registered_aggregates.append(aggregate)

    def record_event(self, event: DomainEvent, aggregate_type: str = "UnknownAggregate") -> None:
        """Records an explicit domain event into the pending commit transaction."""
        self._pending_events.append((event, aggregate_type))

    def begin(self) -> SqliteGovernanceUnitOfWork:
        if not self._in_transaction:
            self.connection.execute("BEGIN IMMEDIATE")
            self._in_transaction = True
        return self

    def commit(self) -> None:
        """Atomically persists aggregate state, inserts event journals, and populates the outbox."""
        if not self._in_transaction:
            return

        conn = self.connection
        cursor = conn.cursor()

        try:
            for aggregate in self._registered_aggregates:
                aggregate_type = type(aggregate).__name__
                for event in aggregate.uncommitted_events():
                    self._pending_events.append((event, aggregate_type))

            for event, aggregate_type in self._pending_events:
                event_id = event.event_id.value
                aggregate_id = event.aggregate_id.value
                occurred_at = event.occurred_at.value
                version = event.version.value
                payload_data = {
                    "aggregate_id": aggregate_id,
                    "aggregate_type": aggregate_type,
                    "event_id": event_id,
                    "event_type": event.event_type,
                    "occurred_at": occurred_at,
                    "payload_digest": event.payload_digest.value,
                    "version": version,
                }
                payload_json = json.dumps(payload_data, sort_keys=True)

                cursor.execute(
                    """
                    INSERT INTO governance_events
                    (event_id, aggregate_id, aggregate_type, event_type, payload_json, version, occurred_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id) DO NOTHING
                    """,
                    (
                        event_id,
                        aggregate_id,
                        aggregate_type,
                        event.event_type,
                        payload_json,
                        version,
                        occurred_at,
                    ),
                )
                if cursor.rowcount == 0:
                    continue

                cursor.execute(
                    """
                    INSERT INTO governance_outbox
                    (outbox_id, event_id, event_type, payload_json, status, retry_count, created_at)
                    VALUES (?, ?, ?, ?, 'PENDING', 0, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        event_id,
                        event.event_type,
                        payload_json,
                        occurred_at,
                    ),
                )

            conn.commit()
        except Exception:
            self.rollback()
            raise

        self._in_transaction = False
        for aggregate in self._registered_aggregates:
            aggregate.clear_events()
        self._registered_aggregates.clear()
        self._pending_events.clear()

    def rollback(self) -> None:
        """Rolls back the active transaction and clears pending buffers."""
        if self._conn is not None and self._in_transaction:
            self._conn.rollback()
            self._in_transaction = False
        self._registered_aggregates.clear()
        self._pending_events.clear()

    def close(self) -> None:
        """Closes the underlying SQLite connection."""
        if self._conn is not None:
            if self._in_transaction:
                self.rollback()
            self._conn.close()
            self._conn = None

    def __enter__(self) -> SqliteGovernanceUnitOfWork:
        return self.begin()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
