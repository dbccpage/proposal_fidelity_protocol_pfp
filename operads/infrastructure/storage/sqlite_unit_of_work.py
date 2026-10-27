"""SQLite-WAL implementation of OeopUnitOfWorkPort and JournalPort."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from operations.domain.rop.result import Err, Ok, Result

from ...application.ports.journal_port import JournalPort
from ...application.ports.unit_of_work_port import OeopUnitOfWorkPort
from ...domain.entities.catalog_v3 import EstateCatalogV3
from ...domain.entities.composition_v3 import CompositionV3
from ...domain.entities.operation_v3 import OperationV3, PortSpecV3
from ...domain.entities.skill_document_v3 import SkillDocumentV3
from ...domain.errors.domain_errors import DomainInvariantError, OeopDomainError
from ...domain.events.domain_events import DomainEventV3
from ...domain.value_objects.authority import AuthorityEffect
from ...domain.value_objects.content_digest import ContentDigest
from ...domain.value_objects.identifier import (
    ColourId,
    DocumentId,
    EstateRef,
    IdempotencyKey,
    OperandId,
    OperationId,
    SchemaRef,
    SkillId,
)
from ...domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)


class SqliteUnitOfWork(OeopUnitOfWorkPort, JournalPort):
    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def close(self) -> None:
        if self._conn:
            self._conn.close()

    def __enter__(self) -> SqliteUnitOfWork:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _init_db(self) -> None:
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=FULL;")
        self._conn.execute("PRAGMA busy_timeout=30000;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS catalogs_v3 (
                    catalog_id TEXT PRIMARY KEY,
                    estate_ref TEXT NOT NULL,
                    epoch INTEGER NOT NULL,
                    compiled_at TEXT NOT NULL,
                    catalog_digest TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS events_v3 (
                    event_id TEXT PRIMARY KEY,
                    stream_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    causation_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS idempotency_v3 (
                    idempotency_key TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    response_json TEXT NOT NULL
                );
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox_v3 (
                    outbox_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT
                );
            """)
            # Additive migration: retain every historical event and delivery row.
            columns = {row[1] for row in self._conn.execute("PRAGMA table_info(outbox_v3)")}
            for name, declaration in (
                ("lease_token", "TEXT"), ("lease_owner", "TEXT"),
                ("lease_until", "REAL"), ("next_attempt_at", "REAL NOT NULL DEFAULT 0"),
                ("attempt_count", "INTEGER NOT NULL DEFAULT 0"),
            ):
                if name not in columns:
                    self._conn.execute(f"ALTER TABLE outbox_v3 ADD COLUMN {name} {declaration}")

    def claim_pending_outbox(
        self, worker_id: str, *, now: float, lease_seconds: float = 30,
        limit: int = 100, destinations: Tuple[str, ...] = (),
    ) -> Result[Tuple[dict, ...], OeopDomainError]:
        """Atomically claim eligible rows; each claim has a fresh fencing token.

        Cooperating workers use a shared UTC epoch clock. Lease expiry permits
        redelivery, so subscribers still require idempotent effects.
        """
        if (type(worker_id) is not str or not worker_id.strip()
                or type(limit) is not int or not 0 < limit <= 10000
                or type(now) not in (int, float) or not math.isfinite(now) or not 0 <= now <= 253402300799
                or type(lease_seconds) not in (int, float)
                or not math.isfinite(lease_seconds) or not 0 < lease_seconds <= 86400
                or type(destinations) is not tuple
                or any(type(topic) is not str or not topic.strip() for topic in destinations)):
            return Err(DomainInvariantError(code="OUTBOX_LEASE_INVALID", message="Invalid worker, clock or lease"))
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute("BEGIN IMMEDIATE")
                    params: list[object] = [now, now]
                    topic_filter = ""
                    if destinations:
                        topic_filter = " AND o.destination IN (" + ",".join("?" for _ in destinations) + ")"
                        params.extend(destinations)
                    params.append(limit)
                    rows = self._conn.execute(
                        "SELECT o.outbox_id,o.event_id,o.destination,o.created_at,o.attempt_count,"
                        "e.stream_id,e.event_type,e.correlation_id,e.causation_id,e.occurred_at,e.payload_json "
                        "FROM outbox_v3 o LEFT JOIN events_v3 e ON o.event_id=e.event_id "
                        "WHERE o.delivered_at IS NULL AND o.next_attempt_at<=? "
                        "AND (o.lease_until IS NULL OR o.lease_until<=?)" + topic_filter
                        + " ORDER BY o.created_at,o.outbox_id LIMIT ?", params,
                    ).fetchall()
                    claimed = []
                    for row in rows:
                        token = uuid4().hex
                        self._conn.execute(
                            "UPDATE outbox_v3 SET lease_token=?,lease_owner=?,lease_until=?,"
                            "attempt_count=attempt_count+1 WHERE outbox_id=?",
                            (token, worker_id, now + lease_seconds, row["outbox_id"]),
                        )
                        message = dict(row)
                        message.update(lease_token=token, attempt_count=row["attempt_count"] + 1)
                        claimed.append(message)
                return Ok(tuple(claimed))
            except sqlite3.Error as error:
                return Err(DomainInvariantError(code="OUTBOX_LEASE_FAILED", message=str(error)))

    def finish_outbox_lease(
        self, outbox_id: str, lease_token: str, *, now: float,
        retry_after: float | None = None,
    ) -> Result[None, OeopDomainError]:
        """Acknowledge or release only the live matching claim; stale workers refuse."""
        if (type(now) not in (int, float) or not math.isfinite(now) or not 0 <= now <= 253402300799
                or type(lease_token) is not str or not lease_token
                or (retry_after is not None and (type(retry_after) not in (int, float)
                    or not math.isfinite(retry_after) or retry_after < 0))):
            return Err(DomainInvariantError(code="OUTBOX_LEASE_INVALID", message="Invalid clock or retry delay"))
        with self._lock:
            try:
                with self._conn:
                    delivered = datetime.fromtimestamp(now, timezone.utc).isoformat() if retry_after is None else None
                    cursor = self._conn.execute(
                        "UPDATE outbox_v3 SET delivered_at=?,next_attempt_at=?,lease_token=NULL,"
                        "lease_owner=NULL,lease_until=NULL WHERE outbox_id=? AND lease_token=? "
                        "AND lease_until>? AND delivered_at IS NULL",
                        (delivered, now + (retry_after or 0), outbox_id, lease_token, now),
                    )
                    if cursor.rowcount != 1:
                        return Err(DomainInvariantError(code="OUTBOX_LEASE_LOST", message="Claim expired or changed"))
                return Ok(None)
            except (sqlite3.Error, ValueError, OverflowError) as error:
                return Err(DomainInvariantError(code="OUTBOX_LEASE_FAILED", message=str(error)))

    def check_idempotency(
        self,
        key: IdempotencyKey,
        request_digest: str,
    ) -> Result[Optional[dict], OeopDomainError]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT request_digest, response_json FROM idempotency_v3 WHERE idempotency_key = ?",
                (str(key),),
            )
            row = cur.fetchone()
            if row is None:
                return Ok(None)
            if row["request_digest"] != request_digest:
                return Err(DomainInvariantError(
                    code="IDEMPOTENCY_CONFLICT",
                    message=f"Idempotency key {key} already used with differing request digest",
                ))
            data = json.loads(row["response_json"])
            return Ok(data)

    def append_events(
        self,
        stream_id: str,
        expected_version: Optional[int],
        events: Tuple[DomainEventV3, ...],
    ) -> Result[int, OeopDomainError]:
        with self._lock:
            try:
                with self._conn:
                    if expected_version is not None:
                        self._conn.execute("BEGIN IMMEDIATE")
                        current_version = self._conn.execute(
                            "SELECT COUNT(*) AS event_count FROM events_v3 WHERE stream_id = ?",
                            (stream_id,),
                        ).fetchone()["event_count"]
                        if current_version != expected_version:
                            return Err(DomainInvariantError(
                                code="CONCURRENCY_CONFLICT",
                                message=(
                                    f"Stream {stream_id} is at version {current_version}, "
                                    f"not expected version {expected_version}"
                                ),
                            ))

                    for event in events:
                        self._conn.execute(
                            """
                            INSERT INTO events_v3 (event_id, stream_id, event_type, correlation_id, causation_id, occurred_at, payload_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                event.event_id,
                                stream_id,
                                type(event).__name__,
                                str(event.correlation_id),
                                str(event.causation_id),
                                event.occurred_at.isoformat(),
                                json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"),
                                           ensure_ascii=False, allow_nan=False),
                            ),
                        )
                return Ok(len(events))
            except Exception as e:
                return Err(DomainInvariantError(code="EVENT_APPEND_FAILED", message=str(e)))

    def get_catalog(self, catalog_id: str) -> Result[Optional[EstateCatalogV3], OeopDomainError]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM catalogs_v3 WHERE catalog_id = ?",
                (catalog_id,),
            )
            row = cur.fetchone()
            if row is None:
                return Ok(None)
            return self._deserialize_catalog(row)

    def get_latest_catalog(
        self,
        estate_ref: Optional[str] = None,
    ) -> Result[Optional[EstateCatalogV3], OeopDomainError]:
        with self._lock:
            if estate_ref is None:
                cur = self._conn.execute(
                    "SELECT * FROM catalogs_v3 ORDER BY epoch DESC, compiled_at DESC LIMIT 1"
                )
            else:
                cur = self._conn.execute(
                    """
                    SELECT * FROM catalogs_v3
                    WHERE estate_ref = ?
                    ORDER BY epoch DESC, compiled_at DESC
                    LIMIT 1
                    """,
                    (estate_ref,),
                )
            row = cur.fetchone()
            if row is None:
                return Ok(None)
            return self._deserialize_catalog(row)

    def fetch_pending_outbox(
        self,
        limit: int = 100,
        preferred_destinations: Tuple[str, ...] = (),
    ) -> Result[Tuple[dict, ...], OeopDomainError]:
        """Fetch unleased undelivered messages, preferring deliverable topics.

        Pending messages without a subscriber remain pending for at-least-once
        delivery.  They must not, however, occupy every row of a bounded poll
        when a later message has an active subscriber.
        Leased rows belong to their fenced worker, including after expiry until
        a cooperating worker reclaims them through claim_pending_outbox.
        """
        with self._lock:
            try:
                order_by = "o.created_at ASC"
                params: list[object] = []
                if preferred_destinations:
                    placeholders = ", ".join("?" for _ in preferred_destinations)
                    order_by = (
                        f"CASE WHEN o.destination IN ({placeholders}) THEN 0 ELSE 1 END, "
                        "o.created_at ASC"
                    )
                    params.extend(preferred_destinations)
                params.append(limit)
                cur = self._conn.execute(
                    f"""
                    SELECT o.outbox_id, o.event_id, o.destination, o.created_at,
                           e.stream_id, e.event_type, e.correlation_id, e.causation_id, e.occurred_at, e.payload_json
                    FROM outbox_v3 o
                    LEFT JOIN events_v3 e ON o.event_id = e.event_id
                    WHERE o.delivered_at IS NULL AND o.lease_token IS NULL
                    ORDER BY {order_by}
                    LIMIT ?
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
                messages = tuple(dict(r) for r in rows)
                return Ok(messages)
            except Exception as e:
                return Err(DomainInvariantError(code="OUTBOX_FETCH_FAILED", message=str(e)))

    def mark_outbox_delivered(
        self,
        outbox_id: str,
        delivered_at: Optional[datetime] = None,
    ) -> Result[None, OeopDomainError]:
        """Mark an outbox message as successfully delivered."""
        now_dt = delivered_at or datetime.now(timezone.utc)
        with self._lock:
            try:
                with self._conn:
                    cursor = self._conn.execute(
                        "UPDATE outbox_v3 SET delivered_at = ? WHERE outbox_id = ? AND lease_token IS NULL",
                        (now_dt.isoformat(), outbox_id),
                    )
                    if cursor.rowcount != 1:
                        return Err(DomainInvariantError(code="OUTBOX_LEASE_REQUIRED", message="A matching lease is required"))
                return Ok(None)
            except Exception as e:
                return Err(DomainInvariantError(code="OUTBOX_MARK_FAILED", message=str(e)))

    def save_catalog(
        self,
        catalog: EstateCatalogV3,
        events: Tuple[DomainEventV3, ...],
        idempotency_key: Optional[IdempotencyKey] = None,
        request_digest: str = "",
        response_data: Optional[dict] = None,
        expected_version: Optional[int] = None,
    ) -> Result[None, OeopDomainError]:
        with self._lock:
            try:
                with self._conn:
                    if idempotency_key is not None:
                        cur = self._conn.execute(
                            "SELECT request_digest FROM idempotency_v3 WHERE idempotency_key = ?",
                            (str(idempotency_key),),
                        )
                        row = cur.fetchone()
                        if row is not None:
                            if row["request_digest"] == request_digest:
                                return Ok(None)
                            return Err(DomainInvariantError(
                                code="IDEMPOTENCY_CONFLICT",
                                message=f"Idempotency key {idempotency_key} already used with differing request digest",
                            ))

                    if expected_version is not None:
                        self._conn.execute("BEGIN IMMEDIATE")
                        current_version = self._conn.execute(
                            """
                            SELECT COALESCE(MAX(epoch), 0) AS catalog_version
                            FROM catalogs_v3
                            WHERE estate_ref = ?
                            """,
                            (str(catalog.estate_ref),),
                        ).fetchone()["catalog_version"]
                        if current_version != expected_version:
                            return Err(DomainInvariantError(
                                code="CONCURRENCY_CONFLICT",
                                message=(
                                    f"Estate {catalog.estate_ref} is at version {current_version}, "
                                    f"not expected version {expected_version}"
                                ),
                            ))

                    serialized = self._serialize_catalog(catalog)
                    self._conn.execute(
                        """
                        INSERT INTO catalogs_v3 (catalog_id, estate_ref, epoch, compiled_at, catalog_digest, payload_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            catalog.catalog_id,
                            str(catalog.estate_ref),
                            catalog.epoch,
                            catalog.compiled_at.isoformat(),
                            str(catalog.catalog_digest),
                            json.dumps(serialized),
                        ),
                    )

                    for event in events:
                        self._conn.execute(
                            """
                            INSERT INTO events_v3 (event_id, stream_id, event_type, correlation_id, causation_id, occurred_at, payload_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                event.event_id,
                                f"catalog_{catalog.catalog_id}",
                                type(event).__name__,
                                str(event.correlation_id),
                                str(event.causation_id),
                                event.occurred_at.isoformat(),
                                json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"),
                                           ensure_ascii=False, allow_nan=False),
                            ),
                        )
                        self._conn.execute(
                            """
                            INSERT INTO outbox_v3 (outbox_id, event_id, destination, created_at)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                f"out_{event.event_id}",
                                event.event_id,
                                "events.oewas.v3",
                                datetime.now(timezone.utc).isoformat(),
                            ),
                        )

                    if idempotency_key is not None and response_data is not None:
                        self._conn.execute(
                            """
                            INSERT INTO idempotency_v3 (idempotency_key, request_digest, created_at, response_json)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                str(idempotency_key),
                                request_digest,
                                datetime.now(timezone.utc).isoformat(),
                                json.dumps(response_data),
                            ),
                        )

                return Ok(None)
            except Exception as e:
                return Err(DomainInvariantError(code="UOW_COMMIT_FAILED", message=str(e)))


    def _port_to_dict(self, port: PortSpecV3) -> dict:
        return {
            "name": port.name,
            "colour_id": port.colour_id.value,
            "schema_ref": port.schema_ref.value,
            "schema_digest": port.schema_digest.hex_digest,
            "validator_ref": port.validator_ref,
            "validator_digest": port.validator_digest.hex_digest,
        }

    def _dict_to_port(self, d: dict) -> PortSpecV3:
        raw_sd = d.get("schema_digest", "0" * 64)
        raw_vd = d.get("validator_digest", "0" * 64)
        return PortSpecV3(
            name=d.get("name", "port"),
            colour_id=ColourId(d.get("colour_id", "Data")),
            schema_ref=SchemaRef(d.get("schema_ref", "schema:v1")),
            schema_digest=ContentDigest.sha256(raw_sd.split(":")[-1] if ":" in raw_sd else raw_sd),
            validator_ref=d.get("validator_ref", ""),
            validator_digest=ContentDigest.sha256(raw_vd.split(":")[-1] if ":" in raw_vd else raw_vd),
        )

    def _lifecycle_to_dict(self, lc: SkillLifecycleV3) -> dict:
        return {
            "declaration": lc.declaration.value,
            "schema_binding": lc.schema_binding.value,
            "executor_binding": lc.executor_binding.value,
            "validation": lc.validation.value,
            "admission": lc.admission.value,
            "schema_digest": lc.schema_digest.hex_digest if lc.schema_digest else "",
            "executor_digest": lc.executor_digest.hex_digest if lc.executor_digest else "",
        }

    def _dict_to_lifecycle(self, d: dict) -> SkillLifecycleV3:
        raw_sd = d.get("schema_digest")
        raw_ed = d.get("executor_digest")
        return SkillLifecycleV3(
            declaration=DeclarationFacet(d.get("declaration", "Declared")),
            schema_binding=SchemaBindingFacet(d.get("schema_binding", "Bound")),
            executor_binding=ExecutorBindingFacet(d.get("executor_binding", "Bound")),
            validation=ValidationFacet(d.get("validation", "Validated")),
            admission=AdmissionFacet(d.get("admission", "Unadmitted")),
            schema_digest=ContentDigest.sha256(raw_sd.split(":")[-1] if ":" in raw_sd else raw_sd) if raw_sd else None,
            executor_digest=ContentDigest.sha256(raw_ed.split(":")[-1] if ":" in raw_ed else raw_ed) if raw_ed else None,
        )

    def _serialize_catalog(self, catalog: EstateCatalogV3) -> dict:
        ops_dict = {}
        for op_id, op in catalog.operations.items():
            ops_dict[str(op_id)] = {
                "operation_id": str(op.operation_id),
                "inputs": [self._port_to_dict(p) for p in op.inputs],
                "output": self._port_to_dict(op.output),
                "operand_refs": [str(r) for r in op.operand_refs],
                "lifecycle": self._lifecycle_to_dict(op.lifecycle),
                "residual_status": op.residual_status,
                "effects": list(op.effects),
                "tool_refs": list(op.tool_refs),
                "authority_effect": op.authority_effect.value,
                "authority_ceiling": op.authority_ceiling.value,
                "invocation_grade": op.invocation_grade,
                "description": op.description,
            }
            if op.replacement_operation_id is not None:
                ops_dict[str(op_id)]["replacement_operation_id"] = str(op.replacement_operation_id)
        skills_dict = {}
        for s_id, doc in catalog.skills.items():
            skills_dict[str(s_id)] = {
                "document_id": str(doc.document_id),
                "source_relative_path": doc.source_relative_path,
                "raw_digest": doc.raw_digest.hex_digest,
                "semantic_digest": doc.semantic_digest.hex_digest,
                "operation_ids": [str(op.operation_id) for op in doc.operations],
                "compositions": [
                    {
                        "composition_id": comp.composition_id,
                        "term_kind": comp.term_kind,
                        "root_operation_id": str(comp.root_operation_id),
                        "child_operation_ids": [str(op_id) for op_id in comp.child_operation_ids],
                        "slot_bindings": [[slot, str(op_id)] for slot, op_id in comp.slot_bindings],
                        "expected_boundary": comp.expected_boundary,
                    }
                    for comp in doc.compositions
                ],
            }
        return {
            "catalog_id": catalog.catalog_id,
            "estate_ref": str(catalog.estate_ref),
            "epoch": catalog.epoch,
            "skills": skills_dict,
            "operations": ops_dict,
            "aliases": {k: str(v) for k, v in catalog.aliases.items()},
        }

    def _deserialize_catalog(self, row: sqlite3.Row) -> Result[EstateCatalogV3, OeopDomainError]:
        payload = json.loads(row["payload_json"])
        skills: Dict[SkillId, SkillDocumentV3] = {}
        operations: Dict[OperationId, OperationV3] = {}

        raw_skills = payload.get("skills", {})
        if isinstance(raw_skills, dict):
            for s_str, s_data in raw_skills.items():
                s_id = SkillId(s_str)
                skills[s_id] = SkillDocumentV3(
                    document_id=DocumentId(s_data.get("document_id", f"doc_{s_str}")),
                    skill_id=s_id,
                    source_relative_path=s_data.get("source_relative_path", ""),
                    raw_digest=ContentDigest.sha256(s_data.get("raw_digest", "0"*64).split(":")[-1]),
                    semantic_digest=ContentDigest.sha256(s_data.get("semantic_digest", "0"*64).split(":")[-1]),
                    compositions=tuple(
                        CompositionV3(
                            composition_id=comp["composition_id"],
                            term_kind=comp["term_kind"],
                            root_operation_id=OperationId(comp["root_operation_id"]),
                            child_operation_ids=tuple(
                                OperationId(op_id) for op_id in comp["child_operation_ids"]
                            ),
                            slot_bindings=tuple(
                                (slot, OperationId(op_id)) for slot, op_id in comp["slot_bindings"]
                            ),
                            expected_boundary=comp["expected_boundary"],
                        )
                        for comp in s_data.get("compositions", ())
                    ),
                )
        elif isinstance(raw_skills, list):
            for s_str in raw_skills:
                s_id = SkillId(s_str)
                skills[s_id] = SkillDocumentV3(
                    document_id=DocumentId(f"doc_{s_str}"),
                    skill_id=s_id,
                    source_relative_path="",
                    raw_digest=ContentDigest.empty_sha256(),
                    semantic_digest=ContentDigest.empty_sha256(),
                )

        for op_str, op_data in payload.get("operations", {}).items():
            op_id = OperationId(op_str)
            inputs = tuple(self._dict_to_port(p) for p in op_data.get("inputs", []))
            output = self._dict_to_port(op_data.get("output", {}))
            operand_refs = tuple(OperandId(r) for r in op_data.get("operand_refs", []))
            lifecycle = self._dict_to_lifecycle(op_data.get("lifecycle", {}))
            operations[op_id] = OperationV3(
                operation_id=op_id,
                inputs=inputs,
                output=output,
                operand_refs=operand_refs,
                lifecycle=lifecycle,
                residual_status=op_data.get("residual_status", "unknown"),
                effects=tuple(op_data.get("effects", [])),
                tool_refs=tuple(op_data.get("tool_refs", [])),
                authority_effect=AuthorityEffect(op_data.get("authority_effect", "None")),
                authority_ceiling=AuthorityEffect(op_data.get("authority_ceiling", "None")),
                invocation_grade=op_data.get("invocation_grade", "entry"),
                description=op_data.get("description", ""),
                replacement_operation_id=(OperationId(op_data["replacement_operation_id"])
                                          if "replacement_operation_id" in op_data else None),
            )

        for skill_id, document in skills.items():
            if isinstance(raw_skills, dict):
                document.operations = tuple(
                    operations[OperationId(op_id)]
                    for op_id in raw_skills[str(skill_id)].get("operation_ids", ())
                )

        catalog = EstateCatalogV3(
            catalog_id=row["catalog_id"],
            estate_ref=EstateRef(row["estate_ref"]),
            epoch=row["epoch"],
            compiled_at=datetime.fromisoformat(row["compiled_at"]),
            skills=skills,
            operations=operations,
            capability_slices={},
            aliases={k: OperationId(v) for k, v in payload.get("aliases", {}).items()},
            catalog_digest=ContentDigest.sha256(row["catalog_digest"].split(":")[-1] if ":" in row["catalog_digest"] else row["catalog_digest"]),
        )
        return Ok(catalog)
