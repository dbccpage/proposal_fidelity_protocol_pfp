"""Contract tests for FastAPI router mounted at /api/oeop/v3."""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from operads.infrastructure.bootstrap import (
    create_oeop_container,
)


class FastApiRouterContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = create_oeop_container()
        self.app = FastAPI(title="OEWAS V3 Test Server")
        self.app.include_router(self.container.router)
        self.client = TestClient(
            self.app, base_url="http://localhost", client=("127.0.0.1", 49152)
        )

    def test_post_compile_catalog_returns_200_and_payload(self) -> None:
        resp = self.client.post(
            "/api/oeop/v3/catalogs:compile",
            json={
                "estate_ref": "canonical",
                "correlation_id": "req-001",
                "causation_id": "init",
                "idempotency_key": "test-idem",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("catalog_id", data)
        self.assertEqual(data["epoch"], 1)

    def test_get_catalog_not_found_returns_404_json(self) -> None:
        resp = self.client.get("/api/oeop/v3/catalogs/non_existent_cat")
        self.assertEqual(resp.status_code, 404)
        detail = resp.json()["detail"]
        self.assertEqual(detail["code"], "CATALOG_NOT_FOUND")

    def test_post_validate_workflows_empty_graph_returns_valid(self) -> None:
        resp = self.client.post(
            "/api/oeop/v3/workflows:validate",
            json={"nodes": [], "edges": []},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_valid"])
