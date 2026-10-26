"""CAS evidence and a durable, serial learning queue."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from omega_engine_operads.domain.autopoiesis.learning import (
    LEARNER_VERSION,
    LearningBlocked,
    LearningEpisodeV1,
    LearningSessionPort,
    ReviewedLesson,
    canonical,
    digest,
)

from .file_harvest_vault import FileHarvestVault


class LearningSession(LearningSessionPort):
    """Learning operations bound to one store transaction."""

    def __init__(self, store: LearningStore, db: sqlite3.Connection) -> None:
        self.store = store
        self.db = db

    def lookup_lesson(self, lesson_id: str) -> ReviewedLesson | None:
        row = self.db.execute(
            "SELECT outcome, url, candidate FROM lessons WHERE id=?", (lesson_id,)
        ).fetchone()
        return ReviewedLesson(*row) if row else None

    def record_lesson(
        self, lesson_id: str, candidate_id: str, outcome: str, url: str | None = None
    ) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO lessons VALUES (?, ?, ?, ?)",
            (lesson_id, candidate_id, outcome, url),
        )

    def finish(self, job_id: str, receipt: dict) -> dict:
        return self.store.finish(self.db, job_id, receipt)


class LearningStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.vault = FileHarvestVault(root / "evidence")
        self.database = root / "queue.sqlite3"
        self.worker_database = root / "worker.sqlite3"
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, episode TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'QUEUED', receipt TEXT);
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY, candidate TEXT NOT NULL,
                    outcome TEXT NOT NULL, url TEXT);
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            """)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database, timeout=60)

    def enqueue(self, episode: LearningEpisodeV1) -> str:
        job_id = digest([sorted({s.sha256 for s in episode.sources}), LEARNER_VERSION])
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO jobs(id, episode) VALUES (?, ?)",
                (job_id, canonical(asdict(episode)).decode()),
            )
        return job_id

    @contextmanager
    def serial(
        self, job_id: str, *, retry: bool = False
    ) -> Iterator[tuple[LearningSessionPort, dict | None]]:
        # A separate SQLite writer lock serializes expensive work while the
        # queue remains writable. OS crash recovery releases this lock; a
        # queued episode is never lost behind a long model call.
        worker = sqlite3.connect(self.worker_database, timeout=60)
        try:
            try:
                worker.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as exc:
                raise LearningBlocked("QUEUE_BUSY_EPISODE_RETAINED") from exc
            with self.connect() as db:
                row = db.execute(
                    "SELECT status, receipt FROM jobs WHERE id=?", (job_id,)
                ).fetchone()
                previous = json.loads(row[1]) if row and row[1] else None
                if previous and not (retry and row[0] in {"BLOCKED", "FAILED"}):
                    yield LearningSession(self, db), previous
                    return
                yield LearningSession(self, db), None
        finally:
            worker.rollback()
            worker.close()

    def finish(self, db: sqlite3.Connection, job_id: str, receipt: dict) -> dict:
        receipt = {
            "schema": "omega.autop.receipt.v2",
            "learner_version": LEARNER_VERSION,
            "job_id": job_id,
            "authority_effect": "None",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **receipt,
        }
        receipt_id = digest(receipt)
        receipt["receipt_id"] = receipt_id
        destination = self.root / "receipts" / f"{receipt_id}.json"
        destination.parent.mkdir(exist_ok=True)
        self.vault._immutable_write(destination, canonical(receipt))
        db.execute(
            "UPDATE jobs SET status=?, receipt=? WHERE id=?",
            (receipt["overall_status"], canonical(receipt).decode(), job_id),
        )
        return receipt

    def finish_receipt(self, job_id: str, receipt: dict) -> dict:
        with self.connect() as db:
            return self.finish(db, job_id, receipt)

    def observe(self, payload: dict) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO observations VALUES (?, ?)",
                (digest(payload), canonical(payload).decode()),
            )

    def pending(self) -> list[dict]:
        with self.connect() as db:
            return [
                {"job_id": r[0], "status": r[1], "episode": json.loads(r[2])}
                for r in db.execute(
                    "SELECT id, status, episode FROM jobs WHERE status IN "
                    "('QUEUED','BLOCKED','FAILED') ORDER BY rowid"
                )
            ]
