"""Install the golden normal-forms SQLite schema.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from omega_engine_governance.infrastructure.storage.schema_totality import install_totality_fences

from .contract_paths import NORMAL_FORMS_DIR

SCHEMA_SQL = NORMAL_FORMS_DIR / "_golden_nfs" / "normal_forms_schema.sql"


def install_schema(conn: sqlite3.Connection) -> None:
    if not SCHEMA_SQL.is_file():
        raise FileNotFoundError(SCHEMA_SQL)
    schema_sql = SCHEMA_SQL.read_text(encoding="utf-8")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_sql)
    conn.execute("PRAGMA foreign_keys = ON;")
    install_totality_fences(conn, schema_sql)
    conn.commit()
