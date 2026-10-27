"""Migration runner for OEOS SQLite persistence.

Executes and verifies ordered schema migrations within BEGIN IMMEDIATE transactions,
asserting checksum integrity and generating immutable execution receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from ...application.ports import TaskStoreError
from ...domain.task import utc_now
from .definitions import (
    MIGRATIONS,
    MigrationDefinitionV1,
    MigrationReceiptV1,
)

INIT_MIGRATION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS oeos_schema_migrations_v1 (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    checksum TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL
);
"""


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.executescript(INIT_MIGRATION_TABLE_SQL)


def get_applied_migrations(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Return list of applied migration rows ordered by version."""
    _ensure_migration_table(conn)
    cursor = conn.execute(
        "SELECT version, name, checksum, applied_at_utc FROM oeos_schema_migrations_v1 ORDER BY version ASC"
    )
    rows = cursor.fetchall()
    return [
        {
            "version": row[0] if isinstance(row, tuple) else row["version"],
            "name": row[1] if isinstance(row, tuple) else row["name"],
            "checksum": row[2] if isinstance(row, tuple) else row["checksum"],
            "applied_at_utc": row[3] if isinstance(row, tuple) else row["applied_at_utc"],
        }
        for row in rows
    ]


def get_migration_status(
    conn: sqlite3.Connection,
    definitions: tuple[MigrationDefinitionV1, ...] = MIGRATIONS,
) -> list[dict[str, Any]]:
    """Return comprehensive status for all defined migrations."""
    applied_map = {m["version"]: m for m in get_applied_migrations(conn)}
    status: list[dict[str, Any]] = []

    for defn in definitions:
        applied = applied_map.get(defn.version)
        if applied is not None:
            checksum_matches = applied["checksum"] == defn.checksum
            status.append(
                {
                    "version": defn.version,
                    "name": defn.name,
                    "status": "APPLIED" if checksum_matches else "CHECKSUM_MISMATCH",
                    "expected_checksum": defn.checksum,
                    "applied_checksum": applied["checksum"],
                    "applied_at_utc": applied["applied_at_utc"],
                }
            )
        else:
            status.append(
                {
                    "version": defn.version,
                    "name": defn.name,
                    "status": "PENDING",
                    "expected_checksum": defn.checksum,
                    "applied_checksum": None,
                    "applied_at_utc": None,
                }
            )
    return status


def apply_migrations(
    conn: sqlite3.Connection,
    definitions: tuple[MigrationDefinitionV1, ...] = MIGRATIONS,
) -> list[MigrationReceiptV1]:
    """Apply any pending migrations in ascending version sequence atomically."""
    _ensure_migration_table(conn)
    applied = {m["version"]: m for m in get_applied_migrations(conn)}
    receipts: list[MigrationReceiptV1] = []

    # Validate already applied migrations
    for defn in definitions:
        if defn.version in applied:
            existing = applied[defn.version]
            if existing["name"] != defn.name:
                raise TaskStoreError(
                    "MIGRATION_NAME_MISMATCH",
                    f"migration {defn.version} name changed from {existing['name']} to {defn.name}",
                )
            if existing["checksum"] != defn.checksum:
                raise TaskStoreError(
                    "MIGRATION_CHECKSUM_MISMATCH",
                    f"migration {defn.version} checksum mismatch: applied {existing['checksum']} != current {defn.checksum}",
                )

    # Apply pending migrations
    for defn in sorted(definitions, key=lambda m: m.version):
        if defn.version in applied:
            continue

        now = utc_now()
        with conn:
            conn.executescript(defn.sql_up)
            conn.execute(
                """
                INSERT INTO oeos_schema_migrations_v1 (version, name, checksum, applied_at_utc)
                VALUES (?, ?, ?, ?)
                """,
                (defn.version, defn.name, defn.checksum, now),
            )

        receipt = MigrationReceiptV1(
            version=defn.version,
            name=defn.name,
            checksum=defn.checksum,
            action="APPLIED",
            executed_at_utc=now,
        )
        receipts.append(receipt)

    return receipts


def rollback_migration(
    conn: sqlite3.Connection,
    target_version: int,
    definitions: tuple[MigrationDefinitionV1, ...] = MIGRATIONS,
) -> list[MigrationReceiptV1]:
    """Roll back migrations in descending version sequence down to target_version."""
    _ensure_migration_table(conn)
    applied_list = get_applied_migrations(conn)
    applied_versions = {m["version"] for m in applied_list}
    defn_map = {m.version: m for m in definitions}

    to_rollback = [
        v for v in sorted(applied_versions, reverse=True) if v > target_version
    ]
    receipts: list[MigrationReceiptV1] = []

    for v in to_rollback:
        if v not in defn_map:
            raise TaskStoreError(
                "UNKNOWN_MIGRATION_DEFINITION",
                f"cannot rollback unmapped migration version {v}",
            )
        defn = defn_map[v]
        now = utc_now()
        with conn:
            conn.executescript(defn.sql_down)
            conn.execute(
                "DELETE FROM oeos_schema_migrations_v1 WHERE version = ?",
                (defn.version,),
            )

        receipt = MigrationReceiptV1(
            version=defn.version,
            name=defn.name,
            checksum=defn.checksum,
            action="ROLLED_BACK",
            executed_at_utc=now,
        )
        receipts.append(receipt)

    return receipts


__all__ = [
    "apply_migrations",
    "get_applied_migrations",
    "get_migration_status",
    "rollback_migration",
]
