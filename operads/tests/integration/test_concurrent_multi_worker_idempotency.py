"""Concurrent multi-worker stress test verifying outbox idempotency and WAL safety."""

from __future__ import annotations

import concurrent.futures
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest

from omega_engine_operads.domain.entities.catalog_v3 import EstateCatalogV3
from omega_engine_operads.domain.entities.operation_v3 import OperationV3, PortSpecV3
from omega_engine_operads.domain.events.domain_events import (
    CatalogCompiledV3,
    EstateCapturedV3,
)
from omega_engine_operads.domain.value_objects.authority import AuthorityEffect
from omega_engine_operads.domain.value_objects.content_digest import ContentDigest
from omega_engine_operads.domain.value_objects.identifier import (
    ColourId,
    EstateRef,
    IdempotencyKey,
    OperationId,
    SchemaRef,
)
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


class TestConcurrentMultiWorkerIdempotency(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "concurrent_test_wal.db")

        # Initialize base UoW to create schema
        with SqliteUnitOfWork(db_path=self.db_path):
            pass

        self.dummy_digest = ContentDigest.sha256("a" * 64)
        self.dummy_port = PortSpecV3(
            name="port",
            colour_id=ColourId("Code"),
            schema_ref=SchemaRef("schema:test:v1"),
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

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def _create_catalog(self, catalog_id: str) -> EstateCatalogV3:
        op = OperationV3(
            operation_id=OperationId(f"op_{catalog_id}"),
            inputs=(self.dummy_port,),
            output=self.dummy_port,
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        return EstateCatalogV3(
            catalog_id=catalog_id,
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=datetime.now(timezone.utc),
            skills={},
            operations={OperationId(f"op_{catalog_id}"): op},
            capability_slices={},
            aliases={},
            catalog_digest=self.dummy_digest,
        )

    def test_concurrent_simultaneous_distinct_writes(self) -> None:
        num_workers = 10

        def worker_task(worker_id: int) -> bool:
            catalog_id = f"cat-worker-{worker_id}"
            catalog = self._create_catalog(catalog_id)
            events = (
                EstateCapturedV3.create(f"evt-cap-{worker_id}", f"corr-{worker_id}", "cause-init", document_count=1),
                CatalogCompiledV3.create(f"evt-comp-{worker_id}", f"corr-{worker_id}", "cause-init", catalog_id=catalog_id),
            )
            # Each worker connects to the shared SQLite WAL database
            with SqliteUnitOfWork(db_path=self.db_path) as uow:
                res = uow.save_catalog(
                    catalog=catalog,
                    events=events,
                    idempotency_key=IdempotencyKey(f"idem-key-{worker_id}"),
                    request_digest=f"req_digest_{worker_id}",
                    response_data={"catalog_id": catalog_id, "worker": worker_id},
                )
                return res.is_ok

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), num_workers)
        self.assertTrue(all(results), "All concurrent write tasks must succeed in WAL mode")

        # Verify database integrity across all tables
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cat_count = conn.execute("SELECT COUNT(*) as cnt FROM catalogs_v3").fetchone()["cnt"]
        self.assertEqual(cat_count, num_workers)

        evt_count = conn.execute("SELECT COUNT(*) as cnt FROM events_v3").fetchone()["cnt"]
        self.assertEqual(evt_count, num_workers * 2)

        outbox_count = conn.execute("SELECT COUNT(*) as cnt FROM outbox_v3").fetchone()["cnt"]
        self.assertEqual(outbox_count, num_workers * 2)

        idem_count = conn.execute("SELECT COUNT(*) as cnt FROM idempotency_v3").fetchone()["cnt"]
        self.assertEqual(idem_count, num_workers)

        conn.close()

    def test_concurrent_identical_idempotency_key_writes(self) -> None:
        num_workers = 10
        shared_key = IdempotencyKey("shared-idem-key")
        shared_digest = "shared_request_hash_abc"
        shared_catalog = self._create_catalog("shared-catalog-01")

        def idempotent_worker(worker_id: int) -> dict | None:
            with SqliteUnitOfWork(db_path=self.db_path) as uow:
                # First check idempotency
                chk = uow.check_idempotency(shared_key, shared_digest)
                if chk.is_ok and chk.unwrap() is not None:
                    return chk.unwrap()

                # Otherwise perform save
                events = (
                    EstateCapturedV3.create(f"evt-shared-cap-{worker_id}", "corr-shared", "cause-init", document_count=1),
                    CatalogCompiledV3.create(f"evt-shared-comp-{worker_id}", "corr-shared", "cause-init", catalog_id="shared-catalog-01"),
                )
                save_res = uow.save_catalog(
                    catalog=shared_catalog,
                    events=events,
                    idempotency_key=shared_key,
                    request_digest=shared_digest,
                    response_data={"catalog_id": "shared-catalog-01", "status": "completed"},
                )
                if save_res.is_ok:
                    return {"catalog_id": "shared-catalog-01", "status": "completed"}

                # If another worker committed first during the race, fetch the idempotent response
                retry_chk = uow.check_idempotency(shared_key, shared_digest)
                if retry_chk.is_ok and retry_chk.unwrap() is not None:
                    return retry_chk.unwrap()
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(idempotent_worker, i) for i in range(num_workers)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(responses), num_workers)
        for resp in responses:
            self.assertIsNotNone(resp)
            self.assertEqual(resp.get("catalog_id"), "shared-catalog-01")

        # Verify exactly 1 idempotency entry exists
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        idem_rows = conn.execute("SELECT * FROM idempotency_v3 WHERE idempotency_key = ?", (str(shared_key),)).fetchall()
        self.assertEqual(len(idem_rows), 1)

        saved_data = json.loads(idem_rows[0]["response_json"])
        self.assertEqual(saved_data["catalog_id"], "shared-catalog-01")

        # Verify conflicting digest is rejected
        with SqliteUnitOfWork(db_path=self.db_path) as uow:
            conflict_res = uow.check_idempotency(shared_key, "conflicting_request_hash_xyz")
            self.assertTrue(conflict_res.is_err)
            self.assertEqual(conflict_res.unwrap_err().code, "IDEMPOTENCY_CONFLICT")

        conn.close()


if __name__ == "__main__":
    unittest.main()
