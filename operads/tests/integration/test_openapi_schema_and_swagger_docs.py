"""Integration test for OpenAPI schema generation, Swagger UI docs, and ReDoc accessibility."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from operads.frontend.api.app import create_app


class TestOpenApiSchemaAndSwaggerDocs(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(db_path=":memory:")
        self.client = TestClient(self.app)

    def test_openapi_schema_generation(self) -> None:
        """Verifies that /openapi.json generates valid schema reflection without runtime errors."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)

        schema = response.json()
        self.assertEqual(schema["info"]["title"], "OEWAS V3 API")
        self.assertEqual(schema["info"]["version"], "3.0.0")

        paths = schema.get("paths", {})
        expected_routes = [
            "/api/oeop/v3/compile_catalog",
            "/api/oeop/v3/catalogs:compile",
            "/api/oeop/v3/catalogs/{catalog_id}:verify",
            "/api/oeop/v3/catalogs/{catalog_id}/projections:compile",
            "/api/oeop/v3/terms:compile",
            "/api/oeop/v3/workflows:validate",
            "/api/oeop/v3/catalogs/{catalog_id}",
            "/healthz",
        ]
        for route in expected_routes:
            self.assertIn(route, paths, f"Expected route {route} missing from OpenAPI schema")

        # Verify components / schemas are properly defined
        components = schema.get("components", {}).get("schemas", {})
        self.assertIn("CompileCatalogRequest", components)
        self.assertIn("VerifyCatalogRequest", components)
        self.assertIn("CompileProjectionRequest", components)
        self.assertIn("CompileLicensedTermRequest", components)
        self.assertIn("ValidateWorkflowsRequest", components)

    def test_swagger_ui_docs_accessible(self) -> None:
        """Verifies Swagger UI documentation page at /docs."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("swagger-ui", response.text.lower())

    def test_redoc_ui_accessible(self) -> None:
        """Verifies ReDoc documentation page at /redoc."""
        response = self.client.get("/redoc")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("redoc", response.text.lower())

    def test_health_check_endpoint(self) -> None:
        """Verifies /healthz endpoint."""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "oewas-v3"})


if __name__ == "__main__":
    unittest.main()
