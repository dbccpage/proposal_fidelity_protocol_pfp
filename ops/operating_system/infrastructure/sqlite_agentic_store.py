"""Durable SQLite store for OEOS route plans, skill events, experience, and arena trials.

Implements atomic persistence, trigger-enforced append-only constraints,
and canonical JSON serialization.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from types import TracebackType
from typing import Self

from ..application.ports import TaskStoreError
from ..domain import (
    ExperienceRecordV1,
    RoutePlanV1,
    SkillUseEventV1,
    TrialReceiptV1,
    canonical_json,
)
from .migrations import apply_migrations


class SqliteAgenticStore:
    """Thread-safe SQLite store for OEOS governed agentic program records."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._lock = RLock()
        self._conn = sqlite3.connect(
            self._db_path, timeout=30.0, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._initialize()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback
        self.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @property
    def connection(self) -> sqlite3.Connection:
        """Internal connection access for migration checks."""
        return self._conn

    def _initialize(self) -> None:
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        # Apply all migrations through the canonical runner
        apply_migrations(self._conn)

    # ========================================================================
    # RoutePlanV1 Operations
    # ========================================================================

    def save_route_plan(self, plan: RoutePlanV1) -> None:
        """Save a RoutePlanV1; duplicate route_plan_id or canonical_digest is refused."""
        if type(plan) is not RoutePlanV1:
            raise TaskStoreError(
                "INVALID_ROUTE_PLAN", "plan must be an instance of RoutePlanV1"
            )
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO oeos_route_plans_v1 (
                            route_plan_id, task_id, envelope_digest,
                            capability_snapshot_digest, selected_route,
                            candidate_routes_json, policy_digest,
                            canonical_digest, route_plan_json, created_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            plan.route_plan_id,
                            plan.task_id,
                            plan.envelope_digest,
                            plan.capability_snapshot_digest,
                            plan.selected_route,
                            json.dumps(list(plan.candidate_routes), sort_keys=True),
                            plan.policy_digest,
                            plan.canonical_digest,
                            canonical_json(plan.to_canonical()),
                            plan.created_at_utc,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                raise TaskStoreError(
                    "ROUTE_PLAN_CONFLICT", f"route plan conflict: {exc}"
                ) from exc
            except sqlite3.Error as exc:
                raise TaskStoreError(
                    "STORE_ERROR", f"failed to store route plan: {exc}"
                ) from exc

    def get_route_plan(self, route_plan_id: str) -> RoutePlanV1 | None:
        """Retrieve a RoutePlanV1 by route_plan_id."""
        with self._lock:
            row = self._conn.execute(
                "SELECT route_plan_json FROM oeos_route_plans_v1 WHERE route_plan_id = ?",
                (route_plan_id,),
            ).fetchone()
            if row is None:
                return None
            data = json.loads(row["route_plan_json"])
            return RoutePlanV1.from_canonical(data)

    def route_plans_for_task(self, task_id: str) -> tuple[RoutePlanV1, ...]:
        """Retrieve all RoutePlanV1 records associated with a task_id."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT route_plan_json FROM oeos_route_plans_v1 WHERE task_id = ? ORDER BY created_at_utc ASC",
                (task_id,),
            ).fetchall()
            return tuple(
                RoutePlanV1.from_canonical(json.loads(row["route_plan_json"]))
                for row in rows
            )

    # ========================================================================
    # SkillUseEventV1 Operations
    # ========================================================================

    def append_skill_event(self, event: SkillUseEventV1) -> None:
        """Append a SkillUseEventV1 to the immutable ledger."""
        if type(event) is not SkillUseEventV1:
            raise TaskStoreError(
                "INVALID_SKILL_EVENT",
                "event must be an instance of SkillUseEventV1",
            )
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO oeos_skill_events_v1 (
                            event_id, task_id, skill_id, sequence,
                            from_phase, to_phase, evidence_digest,
                            previous_event_digest, event_digest,
                            event_json, occurred_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.event_id,
                            event.task_id,
                            event.skill_id,
                            event.sequence,
                            event.from_phase.value if event.from_phase else None,
                            event.to_phase.value,
                            event.evidence_digest,
                            event.previous_event_digest,
                            event.event_digest,
                            canonical_json(event.to_canonical()),
                            event.occurred_at_utc,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                raise TaskStoreError(
                    "SKILL_EVENT_CONFLICT", f"skill event conflict: {exc}"
                ) from exc
            except sqlite3.Error as exc:
                raise TaskStoreError(
                    "STORE_ERROR", f"failed to append skill event: {exc}"
                ) from exc

    def get_skill_event(self, event_id: str) -> SkillUseEventV1 | None:
        """Retrieve a SkillUseEventV1 by event_id."""
        with self._lock:
            row = self._conn.execute(
                "SELECT event_json FROM oeos_skill_events_v1 WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if row is None:
                return None
            data = json.loads(row["event_json"])
            return SkillUseEventV1.from_canonical(data)

    def get_skill_events(
        self, task_id: str, skill_id: str
    ) -> tuple[SkillUseEventV1, ...]:
        """Retrieve ordered stream of SkillUseEventV1 for a specific task and skill."""
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT event_json FROM oeos_skill_events_v1
                WHERE task_id = ? AND skill_id = ?
                ORDER BY sequence ASC
                """,
                (task_id, skill_id),
            ).fetchall()
            return tuple(
                SkillUseEventV1.from_canonical(json.loads(row["event_json"]))
                for row in rows
            )

    # ========================================================================
    # ExperienceRecordV1 Operations
    # ========================================================================

    def save_experience_record(self, record: ExperienceRecordV1) -> None:
        """Save an ExperienceRecordV1 projection."""
        if type(record) is not ExperienceRecordV1:
            raise TaskStoreError(
                "INVALID_EXPERIENCE_RECORD",
                "record must be an instance of ExperienceRecordV1",
            )
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO oeos_experience_records_v1 (
                            experience_id, receipt_digest, task_id,
                            task_family, redaction_profile_digest,
                            redacted_summary, observed_capabilities_json,
                            record_digest, record_json, projected_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.experience_id,
                            record.receipt_digest,
                            record.task_id,
                            record.task_family,
                            record.redaction_profile_digest,
                            record.redacted_summary,
                            json.dumps(list(record.observed_capabilities), sort_keys=True),
                            record.canonical_digest,
                            canonical_json(record.to_canonical()),
                            record.projected_at_utc,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                raise TaskStoreError(
                    "EXPERIENCE_CONFLICT", f"experience record conflict: {exc}"
                ) from exc
            except sqlite3.Error as exc:
                raise TaskStoreError(
                    "STORE_ERROR", f"failed to store experience record: {exc}"
                ) from exc

    def get_experience_record(
        self, experience_id: str
    ) -> ExperienceRecordV1 | None:
        """Retrieve an ExperienceRecordV1 by experience_id."""
        with self._lock:
            row = self._conn.execute(
                "SELECT record_json FROM oeos_experience_records_v1 WHERE experience_id = ?",
                (experience_id,),
            ).fetchone()
            if row is None:
                return None
            data = json.loads(row["record_json"])
            return ExperienceRecordV1.from_canonical(data)

    def query_experience_by_family(
        self, task_family: str, limit: int = 50
    ) -> tuple[ExperienceRecordV1, ...]:
        """Query experience records for a specific task family."""
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT record_json FROM oeos_experience_records_v1
                WHERE task_family = ?
                ORDER BY projected_at_utc DESC
                LIMIT ?
                """,
                (task_family, limit),
            ).fetchall()
            return tuple(
                ExperienceRecordV1.from_canonical(json.loads(row["record_json"]))
                for row in rows
            )

    # ========================================================================
    # TrialReceiptV1 Operations
    # ========================================================================

    def save_trial_receipt(self, receipt: TrialReceiptV1) -> None:
        """Save a TrialReceiptV1."""
        if type(receipt) is not TrialReceiptV1:
            raise TaskStoreError(
                "INVALID_TRIAL_RECEIPT",
                "receipt must be an instance of TrialReceiptV1",
            )
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO oeos_arena_trials_v1 (
                            trial_id, competitor_id, corpus_manifest_digest,
                            passed_case_count, total_case_count,
                            trial_evidence_digest, trial_digest,
                            trial_json, completed_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            receipt.trial_id,
                            receipt.competitor_id,
                            receipt.corpus_manifest_digest,
                            receipt.passed_case_count,
                            receipt.total_case_count,
                            receipt.trial_evidence_digest,
                            receipt.canonical_digest,
                            canonical_json(receipt.to_canonical()),
                            receipt.completed_at_utc,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                raise TaskStoreError(
                    "TRIAL_CONFLICT", f"trial receipt conflict: {exc}"
                ) from exc
            except sqlite3.Error as exc:
                raise TaskStoreError(
                    "STORE_ERROR", f"failed to store trial receipt: {exc}"
                ) from exc

    def get_trial_receipt(self, trial_id: str) -> TrialReceiptV1 | None:
        """Retrieve a TrialReceiptV1 by trial_id."""
        with self._lock:
            row = self._conn.execute(
                "SELECT trial_json FROM oeos_arena_trials_v1 WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
            if row is None:
                return None
            data = json.loads(row["trial_json"])
            return TrialReceiptV1.from_canonical(data)

    def trials_for_competitor(
        self, competitor_id: str
    ) -> tuple[TrialReceiptV1, ...]:
        """Retrieve all TrialReceiptV1 records for a competitor."""
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT trial_json FROM oeos_arena_trials_v1
                WHERE competitor_id = ?
                ORDER BY completed_at_utc ASC
                """,
                (competitor_id,),
            ).fetchall()
            return tuple(
                TrialReceiptV1.from_canonical(json.loads(row["trial_json"]))
                for row in rows
            )


__all__ = ["SqliteAgenticStore"]
