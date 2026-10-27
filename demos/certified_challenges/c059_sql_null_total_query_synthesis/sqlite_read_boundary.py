"""Shared SQLite safety boundary, not a mathematical oracle for either judge."""

from __future__ import annotations

import sqlite3

_READ_ACTIONS = frozenset(
    {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }
)
_EXTERNAL_FUNCTIONS = frozenset({"load_extension", "readfile", "writefile"})


def _authorize_read(action, first, second, database, trigger):
    del database, trigger
    if action not in _READ_ACTIONS:
        return sqlite3.SQLITE_DENY
    if (
        action == sqlite3.SQLITE_FUNCTION
        and (second or first or "").casefold() in _EXTERNAL_FUNCTIONS
    ):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def restrict_to_read_queries(connection: sqlite3.Connection) -> None:
    """Install after trusted fixture population; candidates cannot disable it via SQL."""
    connection.set_authorizer(_authorize_read)
