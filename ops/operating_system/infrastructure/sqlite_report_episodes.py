"""Durable report-operation custody, with precharged attempts and atomic CAS.

Only the trusted application calls finish after native replay. Neither a stored
trace nor this database can mint a kernel ActionLicense. Replacing or externally
editing the database is outside the resume contract.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path


def encoded(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class SQLiteReportEpisodes:
    path: Path

    @contextmanager
    def _transaction(self):
        if str(self.path) in {"", ":memory:"}:
            raise ValueError("REPORT_DURABLE_STORAGE_REQUIRED")
        with closing(sqlite3.connect(self.path, timeout=10)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("""CREATE TABLE IF NOT EXISTS report_episode_v1 (
                episode TEXT PRIMARY KEY, bundle TEXT NOT NULL,
                allowance INTEGER NOT NULL CHECK(allowance BETWEEN 1 AND 4),
                consumed INTEGER NOT NULL CHECK(consumed BETWEEN 0 AND allowance),
                state TEXT NOT NULL, committed INTEGER NOT NULL CHECK(committed IN (0,1)))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS report_attempt_v1 (
                episode TEXT NOT NULL, attempt INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('reserved','running','refused','committed')),
                evidence TEXT, PRIMARY KEY(episode, attempt))""")
            yield conn

    def reserve(self, episode: str, bundle: dict, allowance: int) -> int:
        if (type(episode) is not str or not re.fullmatch(r"[a-zA-Z0-9._:-]{1,128}", episode)
                or type(allowance) is not int or not 1 <= allowance <= 4):
            raise ValueError("REPORT_EPISODE_INPUT")
        with self._transaction() as conn:
            row = conn.execute("SELECT bundle, allowance, consumed, committed FROM report_episode_v1 WHERE episode=?",
                               (episode,)).fetchone()
            if row is None:
                conn.execute("INSERT INTO report_episode_v1 VALUES (?, ?, ?, 0, ?, 0)",
                             (episode, encoded(bundle), allowance, encoded(bundle["descriptor"]["initial"])))
                consumed = 0
            else:
                retained, cap, consumed, committed = row
                if retained != encoded(bundle) or cap != allowance:
                    raise ValueError("REPORT_EPISODE_BINDING")
                if committed:
                    raise ValueError("REPORT_ALREADY_COMMITTED")
            if consumed >= allowance:
                raise ValueError("REPORT_EPISODE_EXHAUSTED")
            attempt = consumed + 1
            conn.execute("UPDATE report_episode_v1 SET consumed=? WHERE episode=?", (attempt, episode))
            conn.execute("INSERT INTO report_attempt_v1 VALUES (?, ?, 'reserved', NULL)", (episode, attempt))
            return attempt

    def claim(self, episode: str, attempt: int) -> dict:
        if type(attempt) is not int:
            raise ValueError("REPORT_ATTEMPT_INPUT")
        with self._transaction() as conn:
            updated = conn.execute("UPDATE report_attempt_v1 SET status='running' WHERE episode=? AND attempt=? AND status='reserved'",
                                   (episode, attempt)).rowcount
            if updated != 1:
                raise ValueError("REPORT_ATTEMPT_NOT_RESERVED")
            row = conn.execute("SELECT bundle FROM report_episode_v1 WHERE episode=?", (episode,)).fetchone()
            if row is None:
                raise ValueError("REPORT_EPISODE_MISSING")
            return json.loads(row[0])

    def finish(self, episode: str, attempt: int, evidence: dict, candidate: dict | None) -> bool:
        """Record every terminal attempt; at most one can install this target.

        A stale candidate becomes a retained refusal. State and authoritative
        native trace enter the same transaction, or neither enters it.
        """
        with self._transaction() as conn:
            row = conn.execute("SELECT bundle, state, committed FROM report_episode_v1 WHERE episode=?", (episode,)).fetchone()
            active = conn.execute("SELECT status FROM report_attempt_v1 WHERE episode=? AND attempt=?", (episode, attempt)).fetchone()
            if row is None or active != ("running",):
                raise ValueError("REPORT_ATTEMPT_NOT_RUNNING")
            installed = False
            if candidate is not None:
                bundle, state, committed = row
                initial = json.loads(bundle)["descriptor"]["initial"]
                if not committed and state == encoded(initial):
                    updated = conn.execute("UPDATE report_episode_v1 SET state=?, committed=1 WHERE episode=? AND state=? AND committed=0",
                                           (encoded(candidate["state"]), episode, state)).rowcount
                    installed = updated == 1
                if not installed:
                    evidence = {**evidence, "refusal": "REPORT_STATE_CONFLICT", "native_candidate": candidate}
            status = "committed" if installed else "refused"
            if installed:
                evidence = {**evidence, "native_commit": candidate}
            conn.execute("UPDATE report_attempt_v1 SET status=?, evidence=? WHERE episode=? AND attempt=?",
                         (status, encoded(evidence), episode, attempt))
            return installed

    def inspect(self, episode: str) -> dict:
        with self._transaction() as conn:
            row = conn.execute("SELECT bundle, allowance, consumed, state, committed FROM report_episode_v1 WHERE episode=?", (episode,)).fetchone()
            if row is None:
                raise ValueError("REPORT_EPISODE_MISSING")
            attempts = conn.execute("SELECT attempt, status, evidence FROM report_attempt_v1 WHERE episode=? ORDER BY attempt", (episode,)).fetchall()
            return {"bundle": json.loads(row[0]), "allowance": row[1], "consumed": row[2],
                    "state": json.loads(row[3]), "committed": bool(row[4]),
                    "attempts": [{"attempt": n, "status": status, "evidence": json.loads(e) if e else None}
                                 for n, status, e in attempts]}
