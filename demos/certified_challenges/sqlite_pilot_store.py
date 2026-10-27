"""SQLite storage engine for challenge runs from two harnesses with deterministic offline replay.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PilotRunRecord:
    run_id: str
    challenge_id: str
    harness: str  # "PFP" | "ADVERSARY"
    model_id: str
    case_id: str
    outcome: str  # "ACCEPTED" | "WARRANTED_REFUSAL" | "REJECTED" | "INFRA_ERROR"
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    checkers: list[dict[str, Any]]
    usage: dict[str, Any]
    cost_usd: float | None
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SqlitePilotStore:
    """Manages SQLite persistence for pilot challenge runs and deterministic replay."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS pilot_runs (
        run_id TEXT PRIMARY KEY,
        challenge_id TEXT NOT NULL,
        harness TEXT NOT NULL,
        model_id TEXT NOT NULL,
        case_id TEXT NOT NULL,
        outcome TEXT NOT NULL,
        input_json TEXT NOT NULL,
        output_json TEXT NOT NULL,
        checkers_json TEXT NOT NULL,
        usage_json TEXT NOT NULL,
        cost_usd REAL,
        created_at_utc TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_pilot_runs_challenge ON pilot_runs(challenge_id);
    CREATE INDEX IF NOT EXISTS idx_pilot_runs_harness ON pilot_runs(harness);
    CREATE INDEX IF NOT EXISTS idx_pilot_runs_case ON pilot_runs(case_id);
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

    def record_run(self, record: PilotRunRecord) -> None:
        created_at = record.created_at_utc or _utc_now()
        sql = """
        INSERT OR REPLACE INTO pilot_runs (
            run_id, challenge_id, harness, model_id, case_id, outcome,
            input_json, output_json, checkers_json, usage_json, cost_usd, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            conn.execute(
                sql,
                (
                    record.run_id,
                    record.challenge_id,
                    record.harness,
                    record.model_id,
                    record.case_id,
                    record.outcome,
                    json.dumps(record.input_data, sort_keys=True),
                    json.dumps(record.output_data, sort_keys=True),
                    json.dumps(record.checkers, sort_keys=True),
                    json.dumps(record.usage, sort_keys=True),
                    record.cost_usd,
                    created_at,
                ),
            )
            conn.commit()

    def get_run(self, run_id: str) -> PilotRunRecord | None:
        sql = "SELECT * FROM pilot_runs WHERE run_id = ?"
        with self._get_connection() as conn:
            row = conn.execute(sql, (run_id,)).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def list_runs(
        self,
        *,
        challenge_id: str | None = None,
        harness: str | None = None,
    ) -> list[PilotRunRecord]:
        query = "SELECT * FROM pilot_runs WHERE 1=1"
        params: list[Any] = []
        if challenge_id:
            query += " AND challenge_id = ?"
            params.append(challenge_id)
        if harness:
            query += " AND harness = ?"
            params.append(harness)
        query += " ORDER BY created_at_utc ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def replay_run(
        self,
        run_id: str,
        checkers: Sequence[tuple[str, Callable[[Any, Any], tuple[bool, str]]]],
    ) -> dict[str, Any]:
        """Deterministically replays a stored run against checkers with zero network activity."""
        record = self.get_run(run_id)
        if record is None:
            raise KeyError(f"Run ID not found in store: {run_id}")

        case = record.input_data
        answer = record.output_data

        replayed_checkers: list[dict[str, Any]] = []
        all_passed = True
        for name, checker in checkers:
            try:
                ok, msg = checker(case, answer)
                replayed_checkers.append({"checker": name, "ok": ok, "message": msg})
                if not ok:
                    all_passed = False
            except Exception as exc:  # noqa: BLE001
                replayed_checkers.append({"checker": name, "ok": False, "message": f"CRASH: {exc}"})
                all_passed = False

        return {
            "run_id": run_id,
            "challenge_id": record.challenge_id,
            "harness": record.harness,
            "replayed_checkers": replayed_checkers,
            "all_passed": all_passed,
            "original_outcome": record.outcome,
        }

    def _row_to_record(self, row: sqlite3.Row) -> PilotRunRecord:
        return PilotRunRecord(
            run_id=row["run_id"],
            challenge_id=row["challenge_id"],
            harness=row["harness"],
            model_id=row["model_id"],
            case_id=row["case_id"],
            outcome=row["outcome"],
            input_data=json.loads(row["input_json"]),
            output_data=json.loads(row["output_json"]),
            checkers=json.loads(row["checkers_json"]),
            usage=json.loads(row["usage_json"]),
            cost_usd=row["cost_usd"],
            created_at_utc=row["created_at_utc"],
        )


__all__ = [
    "PilotRunRecord",
    "SqlitePilotStore",
]
