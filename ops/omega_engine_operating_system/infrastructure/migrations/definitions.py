"""Migration definitions and value types for OEOS SQLite persistence.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ...domain.task import (
    _IDENTIFIER,
    TaskInvariantError,
    _ExactTypeValue,
    _require_digest,
    _require_exact_int,
    _require_exact_str,
    _require_timestamp,
    digest_payload,
)

SCHEMA_MIGRATION_RECEIPT = "omega.oeos.migration-receipt.v1"


@dataclass(frozen=True, slots=True, eq=False)
class MigrationDefinitionV1(_ExactTypeValue):
    """Specification of an ordered schema migration."""

    version: int
    name: str
    sql_up: str
    sql_down: str

    def __post_init__(self) -> None:
        _require_exact_int(self.version, "version", 1, 10_000)
        _require_exact_str(self.name, "name", _IDENTIFIER)
        if not self.sql_up or not self.sql_up.strip():
            raise TaskInvariantError(
                "INVALID_MIGRATION", "sql_up must be non-empty"
            )
        if not self.sql_down or not self.sql_down.strip():
            raise TaskInvariantError(
                "INVALID_MIGRATION", "sql_down must be non-empty"
            )

    @property
    def checksum(self) -> str:
        """Deterministic sha256 checksum of normalized sql_up bytes."""
        normalized = self.sql_up.strip().encode("utf-8")
        return "sha256:" + hashlib.sha256(normalized).hexdigest()


@dataclass(frozen=True, slots=True, eq=False)
class MigrationReceiptV1(_ExactTypeValue):
    """Receipt proving execution of a schema migration."""

    version: int
    name: str
    checksum: str
    action: str  # "APPLIED" or "ROLLED_BACK"
    executed_at_utc: str
    schema: str = SCHEMA_MIGRATION_RECEIPT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_MIGRATION_RECEIPT:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "migration receipt schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "migration receipts grant no authority",
            )
        _require_exact_int(self.version, "version", 1, 10_000)
        _require_exact_str(self.name, "name", _IDENTIFIER)
        _require_digest(self.checksum, "checksum")
        if self.action not in ("APPLIED", "ROLLED_BACK"):
            raise TaskInvariantError(
                "INVALID_ACTION", "action must be APPLIED or ROLLED_BACK"
            )
        _require_timestamp(self.executed_at_utc, "executed_at_utc")

    def to_canonical(self) -> dict[str, object]:
        return {
            "action": self.action,
            "authority_effect": self.authority_effect,
            "checksum": self.checksum,
            "executed_at_utc": self.executed_at_utc,
            "name": self.name,
            "schema": self.schema,
            "version": self.version,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())


# ============================================================================
# Migration 0001: Initial Task Store
# ============================================================================

MIGRATION_0001_SQL_UP = """
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

MIGRATION_0001_SQL_DOWN = """
DROP TRIGGER IF EXISTS oeos_outbox_v1_immutable_intent;
DROP TRIGGER IF EXISTS oeos_outbox_v1_no_delete;
DROP TRIGGER IF EXISTS oeos_events_v1_no_delete;
DROP TRIGGER IF EXISTS oeos_events_v1_no_update;
DROP TABLE IF EXISTS oeos_outbox_v1;
DROP TABLE IF EXISTS oeos_events_v1;
DROP TABLE IF EXISTS oeos_tasks_v1;
"""


# ============================================================================
# Migration 0002: Governed Agentic Program Records
# ============================================================================

MIGRATION_0002_SQL_UP = """
CREATE TABLE IF NOT EXISTS oeos_route_plans_v1 (
    route_plan_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    envelope_digest TEXT NOT NULL,
    capability_snapshot_digest TEXT NOT NULL,
    selected_route TEXT NOT NULL,
    candidate_routes_json TEXT NOT NULL,
    policy_digest TEXT NOT NULL,
    canonical_digest TEXT NOT NULL UNIQUE,
    route_plan_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_oeos_route_plans_task_id
ON oeos_route_plans_v1(task_id);

CREATE INDEX IF NOT EXISTS idx_oeos_route_plans_selected_route
ON oeos_route_plans_v1(selected_route);

CREATE TRIGGER IF NOT EXISTS oeos_route_plans_v1_no_update
BEFORE UPDATE ON oeos_route_plans_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS route plans are append-only');
END;

CREATE TRIGGER IF NOT EXISTS oeos_route_plans_v1_no_delete
BEFORE DELETE ON oeos_route_plans_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS route plans are append-only');
END;

CREATE TABLE IF NOT EXISTS oeos_skill_events_v1 (
    event_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    from_phase TEXT,
    to_phase TEXT NOT NULL,
    evidence_digest TEXT NOT NULL,
    previous_event_digest TEXT NOT NULL,
    event_digest TEXT NOT NULL UNIQUE,
    event_json TEXT NOT NULL,
    occurred_at_utc TEXT NOT NULL,
    UNIQUE (task_id, skill_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_oeos_skill_events_task_skill
ON oeos_skill_events_v1(task_id, skill_id, sequence);

CREATE TRIGGER IF NOT EXISTS oeos_skill_events_v1_no_update
BEFORE UPDATE ON oeos_skill_events_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS skill event ledger is append-only');
END;

CREATE TRIGGER IF NOT EXISTS oeos_skill_events_v1_no_delete
BEFORE DELETE ON oeos_skill_events_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS skill event ledger is append-only');
END;

CREATE TABLE IF NOT EXISTS oeos_experience_records_v1 (
    experience_id TEXT PRIMARY KEY,
    receipt_digest TEXT NOT NULL,
    task_id TEXT NOT NULL,
    task_family TEXT NOT NULL,
    redaction_profile_digest TEXT NOT NULL,
    redacted_summary TEXT NOT NULL,
    observed_capabilities_json TEXT NOT NULL,
    record_digest TEXT NOT NULL UNIQUE,
    record_json TEXT NOT NULL,
    projected_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_oeos_experience_task_family
ON oeos_experience_records_v1(task_family);

CREATE INDEX IF NOT EXISTS idx_oeos_experience_receipt_digest
ON oeos_experience_records_v1(receipt_digest);

CREATE TRIGGER IF NOT EXISTS oeos_experience_records_v1_no_update
BEFORE UPDATE ON oeos_experience_records_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS experience records are append-only');
END;

CREATE TRIGGER IF NOT EXISTS oeos_experience_records_v1_no_delete
BEFORE DELETE ON oeos_experience_records_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS experience records are append-only');
END;

CREATE TABLE IF NOT EXISTS oeos_arena_trials_v1 (
    trial_id TEXT PRIMARY KEY,
    competitor_id TEXT NOT NULL,
    corpus_manifest_digest TEXT NOT NULL,
    passed_case_count INTEGER NOT NULL CHECK (passed_case_count >= 0),
    total_case_count INTEGER NOT NULL CHECK (total_case_count >= 1),
    trial_evidence_digest TEXT NOT NULL,
    trial_digest TEXT NOT NULL UNIQUE,
    trial_json TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL,
    CHECK (passed_case_count <= total_case_count)
);

CREATE INDEX IF NOT EXISTS idx_oeos_arena_competitor
ON oeos_arena_trials_v1(competitor_id);

CREATE INDEX IF NOT EXISTS idx_oeos_arena_corpus
ON oeos_arena_trials_v1(corpus_manifest_digest);

CREATE TRIGGER IF NOT EXISTS oeos_arena_trials_v1_no_update
BEFORE UPDATE ON oeos_arena_trials_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS arena trials are append-only');
END;

CREATE TRIGGER IF NOT EXISTS oeos_arena_trials_v1_no_delete
BEFORE DELETE ON oeos_arena_trials_v1
BEGIN
    SELECT RAISE(ABORT, 'OEOS arena trials are append-only');
END;
"""

MIGRATION_0002_SQL_DOWN = """
DROP TRIGGER IF EXISTS oeos_arena_trials_v1_no_delete;
DROP TRIGGER IF EXISTS oeos_arena_trials_v1_no_update;
DROP INDEX IF EXISTS idx_oeos_arena_corpus;
DROP INDEX IF EXISTS idx_oeos_arena_competitor;
DROP TABLE IF EXISTS oeos_arena_trials_v1;

DROP TRIGGER IF EXISTS oeos_experience_records_v1_no_delete;
DROP TRIGGER IF EXISTS oeos_experience_records_v1_no_update;
DROP INDEX IF EXISTS idx_oeos_experience_receipt_digest;
DROP INDEX IF EXISTS idx_oeos_experience_task_family;
DROP TABLE IF EXISTS oeos_experience_records_v1;

DROP TRIGGER IF EXISTS oeos_skill_events_v1_no_delete;
DROP TRIGGER IF EXISTS oeos_skill_events_v1_no_update;
DROP INDEX IF EXISTS idx_oeos_skill_events_task_skill;
DROP TABLE IF EXISTS oeos_skill_events_v1;

DROP TRIGGER IF EXISTS oeos_route_plans_v1_no_delete;
DROP TRIGGER IF EXISTS oeos_route_plans_v1_no_update;
DROP INDEX IF EXISTS idx_oeos_route_plans_selected_route;
DROP INDEX IF EXISTS idx_oeos_route_plans_task_id;
DROP TABLE IF EXISTS oeos_route_plans_v1;
"""


MIGRATIONS: tuple[MigrationDefinitionV1, ...] = (
    MigrationDefinitionV1(
        version=1,
        name="initial_task_store",
        sql_up=MIGRATION_0001_SQL_UP,
        sql_down=MIGRATION_0001_SQL_DOWN,
    ),
    MigrationDefinitionV1(
        version=2,
        name="agentic_program_records",
        sql_up=MIGRATION_0002_SQL_UP,
        sql_down=MIGRATION_0002_SQL_DOWN,
    ),
)


__all__ = [
    "MIGRATIONS",
    "MigrationDefinitionV1",
    "MigrationReceiptV1",
    "SCHEMA_MIGRATION_RECEIPT",
]
