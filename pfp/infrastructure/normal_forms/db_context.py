"""SQLite connection and transaction fence for normal-form evaluation.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Union


class NormalFormsDbContext:
    """Own a SQLite connection and its transaction fence."""

    def __init__(
        self,
        in_memory: bool = True,
        db_path: Optional[Union[str, Path]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        self._owned = conn is None
        if conn is not None:
            self._conn = conn
        else:
            path = ":memory:" if in_memory else str(db_path or "normal_forms.db")
            self._conn = sqlite3.connect(path)
            self._conn.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database connection is closed.")
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        if self._conn is None:
            raise RuntimeError("Database connection is closed.")
        with self._conn:
            yield self._conn.cursor()

    def cursor(self) -> sqlite3.Cursor:
        if self._conn is None:
            raise RuntimeError("Database connection is closed.")
        return self._conn.cursor()

    def commit(self) -> None:
        if self._conn is not None:
            self._conn.commit()

    def close(self) -> None:
        if self._owned and self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    def __enter__(self) -> NormalFormsDbContext:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
