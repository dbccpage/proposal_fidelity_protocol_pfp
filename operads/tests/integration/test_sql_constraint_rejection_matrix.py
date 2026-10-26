"""Landau Class 1 & Class 2: SQL Constraint Rejection Matrix & Monotonic Epoch Invariants.

Theoretical Minimum:
1. INVARIANT: Attempting to insert duplicate catalog_id, event_id, or outbox message_id must violate
   PRIMARY KEY constraints, abort the Unit of Work transaction, and leave the database in its pre-transaction state.
2. BREAK: SQLite table schema drops PRIMARY KEY or silently replaces duplicates.
3. WITNESS: save_catalog returns Err(StorageError) with STORAGE_TRANSACTION_FAILED and 0 records are modified.
4. MUTATION: In sqlite_unit_of_work.py, change 'INSERT INTO catalogs_v3' to 'INSERT OR REPLACE INTO catalogs_v3'.
"""

from __future__ import annotations

from datetime import datetime, timezone
import unittest

from omega_engine_operads.domain.entities import (
    EstateCatalogV3,
    OperationV3,
    PortSpecV3,
)
from omega_engine_operads.domain.events import (
    CatalogCompiledV3,
    EstateCapturedV3,
)
from omega_engine_operads.domain.value_objects import (
    AdmissionFacet,
    AuthorityEffect,
    ColourId,
    ContentDigest,
    DeclarationFacet,
    EstateRef,
    ExecutorBindingFacet,
    IdempotencyKey,
    OperationId,
    SchemaBindingFacet,
    SchemaRef,
    SkillLifecycleV3,
    ValidationFacet,
)
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


class TestSqlConstraintRejectionMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.uow = SqliteUnitOfWork(db_path=":memory:")
        self.digest = ContentDigest.sha256("0" * 64)
        self.port = PortSpecV3("in", ColourId("Data"), SchemaRef("schema:v1"), self.digest, "", self.digest)
        self.lifecycle = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
            schema_digest=self.digest,
            executor_digest=self.digest,
        )

    def tearDown(self) -> None:
        self.uow.close()

    def _create_catalog(self, catalog_id: str, epoch: int) -> EstateCatalogV3:
        op = OperationV3(
            operation_id=OperationId("op_1"),
            inputs=(self.port,),
            output=self.port,
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        return EstateCatalogV3(
            catalog_id=catalog_id,
            estate_ref=EstateRef("canonical"),
            epoch=epoch,
            compiled_at=datetime.now(timezone.utc),
            skills={},
            operations={OperationId("op_1"): op},
            capability_slices={},
            aliases={},
            catalog_digest=self.digest,
        )

    def test_duplicate_catalog_id_primary_key_rejection(self) -> None:
        """Class 2: Asserts that inserting a duplicate catalog_id fails with transaction rollback."""
        cat1 = self._create_catalog("cat-unique-01", epoch=1)
        res1 = self.uow.save_catalog(catalog=cat1, events=(), idempotency_key=IdempotencyKey("idem-1"), request_digest="req1")
        self.assertTrue(res1.is_ok)

        # Attempt to insert identical catalog_id in a different transaction
        cat2 = self._create_catalog("cat-unique-01", epoch=2)
        res2 = self.uow.save_catalog(catalog=cat2, events=(), idempotency_key=IdempotencyKey("idem-2"), request_digest="req2")
        self.assertTrue(res2.is_err, "Duplicate catalog_id MUST trigger a storage transaction failure")
        err = res2.unwrap_err()
        self.assertEqual(err.code, "UOW_COMMIT_FAILED")

        # Verify conservation: original record at epoch 1 was NOT overwritten
        get_res = self.uow.get_catalog("cat-unique-01")
        self.assertTrue(get_res.is_ok)
        self.assertEqual(get_res.unwrap().epoch, 1)

    def test_duplicate_event_id_primary_key_rejection(self) -> None:
        """Class 2: Asserts that duplicate event IDs in domain event log are rejected."""
        cat = self._create_catalog("cat-unique-02", epoch=1)
        evt1 = EstateCapturedV3.create("evt-duplicate-01", "corr-1", "cause-1", document_count=1)
        res1 = self.uow.save_catalog(catalog=cat, events=(evt1,), idempotency_key=IdempotencyKey("idem-3"), request_digest="req3")
        self.assertTrue(res1.is_ok)

        # Attempt second save with an event reusing evt-duplicate-01
        cat_next = self._create_catalog("cat-unique-03", epoch=2)
        evt_clash = CatalogCompiledV3.create("evt-duplicate-01", "corr-2", "cause-2", catalog_id="cat-unique-03")
        res2 = self.uow.save_catalog(catalog=cat_next, events=(evt_clash,), idempotency_key=IdempotencyKey("idem-4"), request_digest="req4")
        self.assertTrue(res2.is_err)
        self.assertEqual(res2.unwrap_err().code, "UOW_COMMIT_FAILED")

        # Verify cat-unique-03 was rolled back and never created
        self.assertIsNone(self.uow.get_catalog("cat-unique-03").unwrap())

    def test_concurrent_idempotency_key_rejection(self) -> None:
        """Class 2: Asserts that idempotency table enforces unique keys for distinct request digests."""
        cat1 = self._create_catalog("cat-idem-01", epoch=1)
        res1 = self.uow.save_catalog(
            catalog=cat1,
            events=(),
            idempotency_key=IdempotencyKey("same-idem-key"),
            request_digest="digest_A",
            response_data={"status": "ok"},
        )
        self.assertTrue(res1.is_ok)

        # Query existing idempotency record
        idem_res = self.uow.check_idempotency(IdempotencyKey("same-idem-key"), "digest_A")
        self.assertTrue(idem_res.is_ok)
        self.assertIsNotNone(idem_res.unwrap())

        # Check with mismatched digest returns IDEMPOTENCY_CONFLICT
        conflict_res = self.uow.check_idempotency(IdempotencyKey("same-idem-key"), "digest_mismatch")
        self.assertTrue(conflict_res.is_err)
        self.assertEqual(conflict_res.unwrap_err().code, "IDEMPOTENCY_CONFLICT")

        # Attempt to insert same idempotency key with conflicting request digest in save_catalog
        cat2 = self._create_catalog("cat-idem-02", epoch=2)
        res2 = self.uow.save_catalog(
            catalog=cat2,
            events=(),
            idempotency_key=IdempotencyKey("same-idem-key"),
            request_digest="digest_B",
            response_data={"status": "ok"},
        )
        # Note: in save_catalog, check_idempotency with differing digest returns IDEMPOTENCY_CONFLICT before transaction
        self.assertTrue(res2.is_err, "Reused idempotency key with new digest MUST fail")
        self.assertEqual(res2.unwrap_err().code, "IDEMPOTENCY_CONFLICT")


if __name__ == "__main__":
    unittest.main()
