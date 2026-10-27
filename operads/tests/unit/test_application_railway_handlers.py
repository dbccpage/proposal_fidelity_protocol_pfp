"""Unit tests for Application command and query railway handlers."""

from pathlib import Path
import tempfile
import unittest
from operads.application.dtos import (
    CompileCatalogCommand,
    GetCatalogQuery,
    ValidateWorkflowsQuery,
    VerifyCatalogCommand,
    WorkflowEdgeDTO,
    WorkflowNodeDTO,
)
from operads.domain.value_objects import (
    CausationId,
    CorrelationId,
    EstateRef,
    IdempotencyKey,
)
from operads.infrastructure.bootstrap import (
    OeopContainer,
    create_oeop_container,
)


class ApplicationRailwayHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = create_oeop_container()

    def test_compile_and_verify_catalog_railway_success(self) -> None:
        cmd = CompileCatalogCommand(
            estate_ref=EstateRef("canonical"),
            correlation_id=CorrelationId("corr-1"),
            causation_id=CausationId("cause-1"),
            idempotency_key=IdempotencyKey("idem-1"),
        )
        res = self.container.compile_catalog_handler.handle(cmd)
        self.assertTrue(res.is_ok)
        dto = res.unwrap()
        self.assertTrue(dto.catalog_id.startswith("cat_"))
        self.assertEqual(dto.epoch, 1)

        # Verify catalog
        verify_cmd = VerifyCatalogCommand(
            catalog_id=dto.catalog_id,
            correlation_id=CorrelationId("corr-1"),
            causation_id=CausationId("cause-1"),
        )
        v_res = self.container.verify_catalog_handler.handle(verify_cmd)
        self.assertTrue(v_res.is_ok)
        self.assertTrue(v_res.unwrap().is_valid)

    def test_default_container_uses_the_repository_root(self) -> None:
        expected_root = Path(__file__).resolve().parents[3]
        self.assertEqual(self.container.workspace_root.resolve(), expected_root)

    def test_compile_catalog_rejects_a_stale_expected_version(self) -> None:
        container = OeopContainer(db_path=":memory:")
        try:
            first = container.api.compile_catalog(
                expected_version=0,
                idempotency_key="version-one",
            )
            self.assertTrue(first.is_ok)
            self.assertEqual(first.unwrap().epoch, 1)

            stale = container.api.compile_catalog(
                expected_version=0,
                idempotency_key="stale-version",
            )
            self.assertTrue(stale.is_err)
            self.assertEqual(stale.unwrap_err().code, "CONCURRENCY_CONFLICT")
            self.assertEqual(stale.unwrap_err().status_code, 409)

            current = container.api.compile_catalog(
                expected_version=1,
                idempotency_key="version-two",
            )
            self.assertTrue(current.is_ok)
            self.assertEqual(current.unwrap().epoch, 2)
        finally:
            container.uow.close()

    def test_get_catalog_not_found_returns_error_rail(self) -> None:
        q = GetCatalogQuery(catalog_id="non-existent")
        res = self.container.get_catalog_handler.handle(q)
        self.assertTrue(res.is_err)
        err = res.unwrap_err()
        self.assertEqual(err.status_code, 404)
        self.assertEqual(err.code, "CATALOG_NOT_FOUND")

    def test_validate_workflows_cycle_detection(self) -> None:
        # A -> B -> C -> A
        nodes = (
            WorkflowNodeDTO("node_a", "op_a", ("in",), ("out",)),
            WorkflowNodeDTO("node_b", "op_b", ("in",), ("out",)),
            WorkflowNodeDTO("node_c", "op_c", ("in",), ("out",)),
        )
        edges = (
            WorkflowEdgeDTO("node_a", "out", "node_b", "in"),
            WorkflowEdgeDTO("node_b", "out", "node_c", "in"),
            WorkflowEdgeDTO("node_c", "out", "node_a", "in"),
        )
        query = ValidateWorkflowsQuery(nodes=nodes, edges=edges)
        res = self.container.validate_workflows_handler.handle(query)
        self.assertTrue(res.is_ok)
        dto = res.unwrap()
        self.assertFalse(dto.is_valid)
        self.assertGreater(len(dto.cycles), 0)
