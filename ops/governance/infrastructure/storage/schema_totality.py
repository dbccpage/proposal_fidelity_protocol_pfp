"""Non-destructive SQLite null-totality fences for declared schemas. AuthorityEffect: None."""

from __future__ import annotations

import sqlite3
from typing import Any


class SchemaContractError(ValueError):
    """A structural defect, never a mathematical proof or Genesis obstruction."""


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def tables(conn: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def columns(conn: sqlite3.Connection, table: str) -> list[tuple[Any, ...]]:
    return list(conn.execute(f"PRAGMA table_info({quote(table)})"))


def total_columns(info: list[tuple[Any, ...]]) -> list[str]:
    # INTEGER PRIMARY KEY aliases rowid: NULL input allocates a nonnull key.
    single_pk = sum(bool(r[5]) for r in info) == 1
    return [r[1] for r in info if r[3] or (r[5] and not (single_pk and r[2].upper() == "INTEGER"))]


def _row_fence(table: str, info: list[tuple[Any, ...]], prefix: str = "") -> str:
    """Variant fields become protected only in their declared CDC operation.

    This also migrates binary-flag predicates that IF NOT EXISTS cannot add to
    old tables. Each referenced name must belong to the expected heading.
    """

    def col(name: str) -> str:
        return prefix + quote(name)

    clauses = [f"{col(c)} IS NULL" for c in total_columns(info)]
    names = {r[1] for r in info}
    binary = {
        "sales_cdc_log": ("processed",),
        "extrema_repair_log": (
            "is_destructive",
            "cochain_available",
            "recomputation_fallback_executed",
        ),
        "quantile_repair_log": ("within_tolerance", "recomputation_fallback_executed"),
    }.get(table, ())
    for name in binary:
        if name in names:
            clauses.append(f"{col(name)} IS NULL OR {col(name)} NOT IN (0, 1)")
    if table == "sales_cdc_log" and {
        "op_type",
        "old_region",
        "new_region",
        "old_amount",
        "new_amount",
    }.issubset(names):
        for operation, fields in (
            ("INSERT", ("new_region", "new_amount")),
            ("DELETE", ("old_region", "old_amount")),
            ("UPDATE", ("old_region", "old_amount", "new_region", "new_amount")),
        ):
            missing = " OR ".join(f"{col(c)} IS NULL" for c in fields)
            clauses.append(f"({col('op_type')} IS NOT DISTINCT FROM '{operation}' AND ({missing}))")
    return " OR ".join(clauses)


def install_totality_fences(conn: sqlite3.Connection, schema_sql: str) -> None:
    """Guard legacy IF-NOT-EXISTS schemas without copying or coercing user data.

    Existing null facts cause a typed defect. Both INSERT and UPDATE are fenced.
    Optional columns remain optional. Run after additive column migrations.
    """
    with sqlite3.connect(":memory:") as expected:
        expected.executescript(schema_sql)
        declarations = [(name, columns(expected, name)) for name in tables(expected)]
    conn.execute("SAVEPOINT nf_install_totality")
    try:
        for table, info in declarations:
            required = total_columns(info)
            actual = {r[1] for r in columns(conn, table)}
            if not actual or not set(required).issubset(actual):
                raise SchemaContractError(f"{table}: missing declared columns")
            if not required:
                continue
            nulls = _row_fence(table, info)
            if conn.execute(f"SELECT 1 FROM {quote(table)} WHERE {nulls} LIMIT 1").fetchone():
                raise SchemaContractError(
                    f"{table}: legacy NULL or invalid protected fact; repair explicitly"
                )
            fence = _row_fence(table, info, "NEW.")
            for operation in ("INSERT", "UPDATE"):
                trigger = quote(f"nf_totality_{table}_{operation.lower()}")
                conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
                conn.execute(
                    f"CREATE TRIGGER {trigger} BEFORE {operation} ON {quote(table)} "
                    f"WHEN {fence} BEGIN SELECT RAISE(ABORT, 'null protected fact'); END"
                )
    except Exception:
        conn.execute("ROLLBACK TO nf_install_totality")
        conn.execute("RELEASE nf_install_totality")
        raise
    else:
        conn.execute("RELEASE nf_install_totality")
