"""Explicit-root JSONL ingestion and SQLite provenance. AuthorityEffect: None."""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterator, Mapping

from pciv.domain.prompt_ecology.protocols import (
    DefectWitnessV1,
    SourceRecordV1,
)


class JsonlTelemetrySource:
    def __init__(self, root: Path, *, max_record_bytes: int = 1_048_576) -> None:
        if max_record_bytes <= 0:
            raise ValueError("RECORD_BYTE_BUDGET_REQUIRED")
        self.root = root.resolve()
        self.max_record_bytes = max_record_bytes

    def read_batch(
        self, checkpoints: Mapping[str, tuple[int, str]], limit: int,
    ) -> Iterator[SourceRecordV1]:
        remaining = limit
        for path in sorted(self.root.rglob("*.jsonl"), key=lambda p: str(p).encode("utf-8")):
            if not path.resolve().is_relative_to(self.root):
                raise ValueError("TELEMETRY_PATH_ESCAPES_ROOT")
            name = path.relative_to(self.root).as_posix()
            offset, expected_prefix = checkpoints.get(name, (0, ""))
            with path.open("rb") as stream:
                prefix = hashlib.sha256()
                consumed = 0
                while consumed < offset:
                    chunk = stream.read(min(offset - consumed, self.max_record_bytes))
                    if not chunk:
                        raise ValueError("TELEMETRY_SOURCE_REWRITTEN")
                    prefix.update(chunk)
                    consumed += len(chunk)
                if expected_prefix and prefix.hexdigest() != expected_prefix:
                    raise ValueError("TELEMETRY_SOURCE_REWRITTEN")
                while remaining > 0:
                    raw = stream.readline(self.max_record_bytes + 1)
                    if not raw:
                        break
                    if len(raw) > self.max_record_bytes:
                        raise ValueError("TELEMETRY_RECORD_TOO_LARGE")
                    if not raw.endswith(b"\n"):
                        # An actively appended line is not committed until its LF.
                        break
                    prefix.update(raw)
                    next_offset = offset + len(raw)
                    yield SourceRecordV1(name, offset, next_offset, prefix.hexdigest(), raw)
                    offset = next_offset
                    remaining -= 1
            if remaining == 0:
                return


class SqliteMetabolismStore:
    def __init__(self, database: Path) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database)
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                path TEXT NOT NULL, offset INTEGER NOT NULL, raw BLOB NOT NULL,
                source_sha256 TEXT NOT NULL, residual TEXT,
                PRIMARY KEY(path, offset));
            CREATE TABLE IF NOT EXISTS checkpoints (
                path TEXT PRIMARY KEY, offset INTEGER NOT NULL, prefix_sha256 TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS witnesses (
                defect TEXT NOT NULL, observation TEXT NOT NULL, checker TEXT NOT NULL,
                witness TEXT NOT NULL, source_sha256 TEXT NOT NULL,
                PRIMARY KEY(defect, observation));
            CREATE TABLE IF NOT EXISTS candidates (
                defect TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, payload TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.connection.close()

    def checkpoints(self) -> dict[str, tuple[int, str]]:
        return {path: (offset, digest) for path, offset, digest in self.connection.execute(
            "SELECT path, offset, prefix_sha256 FROM checkpoints ORDER BY path"
        )}

    def record(
        self, source: SourceRecordV1, witness: DefectWitnessV1 | None,
        required_support: int, residual: str | None,
    ) -> str | None:
        digest = hashlib.sha256(source.raw).hexdigest()
        with self.connection:
            prior = self.connection.execute(
                "SELECT source_sha256 FROM sources WHERE path=? AND offset=?",
                (source.path, source.offset),
            ).fetchone()
            if prior is not None:
                if prior[0] != digest:
                    raise ValueError("TELEMETRY_SOURCE_REWRITTEN")
                return None
            checkpoint = self.connection.execute(
                "SELECT offset FROM checkpoints WHERE path=?", (source.path,),
            ).fetchone()
            expected_offset = checkpoint[0] if checkpoint else 0
            if source.offset != expected_offset:
                raise ValueError("TELEMETRY_CHECKPOINT_CONFLICT")
            self.connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?)",
                (source.path, source.offset, source.raw, digest, residual),
            )
            self.connection.execute(
                "INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?)",
                (source.path, source.next_offset, source.prefix_sha256),
            )
            if witness is None:
                return None
            prior_witness = self.connection.execute(
                "SELECT checker, witness FROM witnesses WHERE defect=? AND observation=?",
                (witness.defect_id, witness.observation_id),
            ).fetchone()
            if prior_witness is not None and prior_witness != (witness.checker_digest, witness.witness_digest):
                raise ValueError("OBSERVATION_IDENTITY_CONFLICT")
            self.connection.execute(
                "INSERT OR IGNORE INTO witnesses VALUES (?, ?, ?, ?, ?)",
                (witness.defect_id, witness.observation_id, witness.checker_digest, witness.witness_digest, digest),
            )
            rows = self.connection.execute(
                "SELECT observation, checker, witness, source_sha256 FROM witnesses WHERE defect=? ORDER BY observation",
                (witness.defect_id,),
            ).fetchall()
            already = self.connection.execute(
                "SELECT 1 FROM candidates WHERE defect=?", (witness.defect_id,),
            ).fetchone()
            if len(rows) < required_support or already:
                return None
            payload = json.dumps({
                "defect_id": witness.defect_id, "support": rows,
                "required_support": required_support, "custody": "Candidate",
                "authority_effect": "None",
            }, sort_keys=True, separators=(",", ":"))
            candidate_id = "candidate_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
            self.connection.execute(
                "INSERT INTO candidates VALUES (?, ?, ?)", (witness.defect_id, candidate_id, payload),
            )
            return candidate_id
