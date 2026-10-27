"""Integration tests for SQLite-WAL Unit of Work and Journal."""

import json
import unittest
from datetime import datetime, timezone

import pytest

from operads.domain.entities import (
    EstateCatalogV3,
    OperationV3,
    PortSpecV3,
)
from operads.domain.events import (
    CatalogCompiledV3,
    CompositionBoundV3,
    EstateCapturedV3,
    OperationDeclaredV3,
)
from operads.domain.value_objects import (
    AdmissionFacet,
    AuthorityEffect,
    CausationId,
    ColourId,
    ContentDigest,
    CorrelationId,
    DeclarationFacet,
    EstateRef,
    ExecutorBindingFacet,
    IdempotencyKey,
    OperationId,
    SchemaBindingFacet,
    SchemaRef,
    SkillId,
    SkillLifecycleV3,
    ValidationFacet,
)
from operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


class SqliteUnitOfWorkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.uow = SqliteUnitOfWork(db_path=":memory:")
        self.dummy_digest = ContentDigest.sha256("0" * 64)
        self.dummy_port = PortSpecV3(
            name="in",
            colour_id=ColourId("Data"),
            schema_ref=SchemaRef("schema:v1"),
            schema_digest=self.dummy_digest,
            validator_ref="",
            validator_digest=self.dummy_digest,
        )
        self.lifecycle = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
            schema_digest=self.dummy_digest,
            executor_digest=self.dummy_digest,
        )

    def test_save_and_retrieve_catalog(self) -> None:
        op = OperationV3(
            operation_id=OperationId("op_1"),
            inputs=(self.dummy_port,),
            output=self.dummy_port,
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        catalog = EstateCatalogV3(
            catalog_id="cat-test-01",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=datetime.now(timezone.utc),
            skills={},
            operations={OperationId("op_1"): op},
            capability_slices={},
            aliases={"legacy_op": OperationId("op_1")},
            catalog_digest=self.dummy_digest,
        )
        events = (
            EstateCapturedV3.create("evt-1", "corr-1", "cause-1", document_count=1),
            CatalogCompiledV3.create("evt-2", "corr-1", "cause-1", catalog_id="cat-test-01"),
        )
        save_res = self.uow.save_catalog(
            catalog=catalog,
            events=events,
            idempotency_key=IdempotencyKey("idem-test"),
            request_digest="req_digest_123",
            response_data={"status": "ok"},
        )
        self.assertTrue(save_res.is_ok)

        # Retrieve catalog
        get_res = self.uow.get_catalog("cat-test-01")
        self.assertTrue(get_res.is_ok)
        retrieved = get_res.unwrap()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.catalog_id, "cat-test-01")
        self.assertEqual(retrieved.epoch, 1)
        self.assertEqual(retrieved.estate_ref, EstateRef("canonical"))
        self.assertEqual(retrieved.aliases, {"legacy_op": OperationId("op_1")})
        self.assertIn(OperationId("op_1"), retrieved.operations)

        # Deep operation and port hydration verification
        retrieved_op = retrieved.operations[OperationId("op_1")]
        self.assertEqual(retrieved_op.operation_id, op.operation_id)
        self.assertEqual(len(retrieved_op.inputs), 1)
        self.assertEqual(retrieved_op.inputs[0].name, "in")
        self.assertEqual(retrieved_op.inputs[0].colour_id, ColourId("Data"))
        self.assertEqual(retrieved_op.inputs[0].schema_ref, SchemaRef("schema:v1"))
        self.assertEqual(retrieved_op.inputs[0].schema_digest, self.dummy_digest)
        self.assertEqual(retrieved_op.output.name, "in")
        self.assertEqual(retrieved_op.output.colour_id, ColourId("Data"))
        self.assertEqual(retrieved_op.output.schema_ref, SchemaRef("schema:v1"))
        self.assertEqual(retrieved_op.output.schema_digest, self.dummy_digest)
        self.assertEqual(retrieved_op.authority_effect, AuthorityEffect.NONE)
        self.assertEqual(retrieved_op.authority_ceiling, AuthorityEffect.NONE)
        self.assertEqual(retrieved_op.residual_status, "verified")
        self.assertEqual(retrieved_op.lifecycle.declaration, DeclarationFacet.DECLARED)
        self.assertEqual(retrieved_op.lifecycle.schema_binding, SchemaBindingFacet.BOUND)
        self.assertEqual(retrieved_op.lifecycle.executor_binding, ExecutorBindingFacet.BOUND)
        self.assertEqual(retrieved_op.lifecycle.validation, ValidationFacet.VALIDATED)
        self.assertEqual(retrieved_op.lifecycle.admission, AdmissionFacet.ADMITTED)

    def test_idempotency_duplicate_and_conflict(self) -> None:
        self.uow.save_catalog(
            catalog=EstateCatalogV3(
                catalog_id="cat-01",
                estate_ref=EstateRef("canonical"),
                epoch=1,
                compiled_at=datetime.now(timezone.utc),
                skills={},
                operations={},
                capability_slices={},
                aliases={},
                catalog_digest=self.dummy_digest,
            ),
            events=(),
            idempotency_key=IdempotencyKey("key-1"),
            request_digest="hash_original",
            response_data={"catalog_id": "cat-01"},
        )

        # Same key, same digest -> returns prior response data
        chk_same = self.uow.check_idempotency(IdempotencyKey("key-1"), "hash_original")
        self.assertTrue(chk_same.is_ok)
        self.assertEqual(chk_same.unwrap(), {"catalog_id": "cat-01"})

        # Same key, differing digest -> returns IDEMPOTENCY_CONFLICT error
        chk_diff = self.uow.check_idempotency(IdempotencyKey("key-1"), "hash_tampered")
        self.assertTrue(chk_diff.is_err)
        self.assertEqual(chk_diff.unwrap_err().code, "IDEMPOTENCY_CONFLICT")

    def test_append_events_enforces_expected_stream_version(self) -> None:
        first = EstateCapturedV3.create("evt-stream-1", "corr", "cause", document_count=1)
        initial = self.uow.append_events("catalog-stream", 0, (first,))
        self.assertTrue(initial.is_ok)
        self.assertEqual(initial.unwrap(), 1)

        stale = self.uow.append_events("catalog-stream", 0, (
            CatalogCompiledV3.create("evt-stream-2", "corr", "cause", catalog_id="cat-stream"),
        ))
        self.assertTrue(stale.is_err)
        self.assertEqual(stale.unwrap_err().code, "CONCURRENCY_CONFLICT")

        current = self.uow.append_events("catalog-stream", 1, (
            CatalogCompiledV3.create("evt-stream-3", "corr", "cause", catalog_id="cat-stream"),
        ))
        self.assertTrue(current.is_ok)


@pytest.mark.parametrize("producer", ["journal", "catalog"])
def test_event_payloads_survive_both_producers_and_reopen(tmp_path, producer):
    path = str(tmp_path / "event-payload.sqlite3")
    timestamp = datetime(2026, 10, 12, 12, 30, tzinfo=timezone.utc)
    common = {
        "occurred_at": timestamp,
        "correlation_id": CorrelationId("corr-payload"),
        "causation_id": CausationId("cause-payload"),
    }
    events = (
        EstateCapturedV3(
            event_id="event-captured", **common, estate_ref=EstateRef("estate-é"),
            document_count=3, raw_digest=ContentDigest.sha256("a" * 64),
        ),
        CatalogCompiledV3(
            event_id="event-catalog", **common, catalog_id="catalog-payload", epoch=3,
            total_skills=3, total_operations=7, catalog_digest=ContentDigest.sha256("b" * 64),
        ),
        OperationDeclaredV3(
            event_id="event-operation", **common, operation_id=OperationId("op-audit"),
            skill_id=SkillId("skill-audit"), colour_in=("Code", "State"), colour_out="Audit",
            authority_ceiling=AuthorityEffect.EVIDENCE_ONLY,
        ),
        CompositionBoundV3(
            event_id="event-composition", **common, composition_id="composition-ordered",
            source_operation_ids=(OperationId("op-left"), OperationId("op-right")),
        ),
    )
    expected_fields = {
        "event-captured": {
            "event_type": "EstateCapturedV3", "estate_ref": "estate-é", "document_count": 3,
            "raw_digest": "sha256:" + "a" * 64,
        },
        "event-catalog": {
            "event_type": "CatalogCompiledV3", "catalog_id": "catalog-payload", "epoch": 3,
            "total_skills": 3, "total_operations": 7, "catalog_digest": "sha256:" + "b" * 64,
        },
        "event-operation": {
            "event_type": "OperationDeclaredV3", "operation_id": "op-audit", "skill_id": "skill-audit",
            "colour_in": ["Code", "State"], "colour_out": "Audit", "authority_ceiling": "EvidenceOnly",
        },
        "event-composition": {
            "event_type": "CompositionBoundV3", "composition_id": "composition-ordered",
            "term_kind": "primitive", "source_operation_ids": ["op-left", "op-right"],
        },
    }
    legacy_payload = '{"event_type": "EstateCapturedV3"}'
    with SqliteUnitOfWork(path) as uow:
        with uow._conn:
            uow._conn.execute(
                "INSERT INTO events_v3 VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("event-legacy", "legacy", "EstateCapturedV3", "corr-old", "cause-old",
                 "2026-10-10T00:00:00+00:00", legacy_payload),
            )
        if producer == "journal":
            result = uow.append_events("payload-stream", 0, events)
        else:
            catalog = EstateCatalogV3(
                catalog_id="catalog-payload", estate_ref=EstateRef("estate-é"), epoch=3,
                compiled_at=timestamp, skills={}, operations={}, capability_slices={}, aliases={},
                catalog_digest=ContentDigest.sha256("b" * 64),
            )
            result = uow.save_catalog(catalog, events)
        assert result.is_ok, result

    with SqliteUnitOfWork(path) as reopened:
        rows = reopened._conn.execute("SELECT event_id, payload_json FROM events_v3").fetchall()
        payloads = {row["event_id"]: row["payload_json"] for row in rows}
        assert payloads.pop("event-legacy") == legacy_payload
        assert set(payloads) == set(expected_fields)
        for event_id, expected in expected_fields.items():
            assert json.loads(payloads[event_id]) == {
                "event_id": event_id, "occurred_at": "2026-10-12T12:30:00+00:00",
                "correlation_id": "corr-payload", "causation_id": "cause-payload",
                "authority_effect": "None", "schema_version": 1, **expected,
            }
        pending = reopened.fetch_pending_outbox().unwrap()
        if producer == "catalog":
            assert {message["event_id"]: message["payload_json"] for message in pending} == payloads
        else:
            assert pending == ()  # Journal appends do not manufacture outbox delivery.
