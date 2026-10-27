"""Durable atomic budget/attempt metadata. Prompts, replies and keys are not stored."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from adversary.domain.providers.ledger import initial_state


class SqliteBudgetLedger:
    def __init__(self, path: Path, *, budget_id: str) -> None:
        if type(budget_id) is not str or not budget_id:
            raise ValueError("budget_id must be a nonempty string")
        self.path, self.budget_id = path, budget_id
        connection = sqlite3.connect(path)
        try:
            connection.execute("CREATE TABLE IF NOT EXISTS provider_budget (id TEXT PRIMARY KEY, state TEXT NOT NULL)")
            connection.commit()
        finally:
            connection.close()

    @contextmanager
    def transaction(self, limit: int):
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        try:
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT state FROM provider_budget WHERE id=?", (self.budget_id,)).fetchone()
            state = json.loads(row[0]) if row else initial_state(limit)
            if state["limit"] != limit:
                raise ValueError("ledger budget limit differs from configured limit")
            yield state
            connection.execute(
                "INSERT INTO provider_budget VALUES (?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state",
                (self.budget_id, json.dumps(state, sort_keys=True, separators=(",", ":"))),
            )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
