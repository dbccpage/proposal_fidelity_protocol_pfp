"""FastAPI HTTP ASGI test fixture simulating asynchronous multi-tenant HTTP requests."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

import httpx
from fastapi import FastAPI

from omega_engine_operads.infrastructure.bootstrap import OeopContainer
from omega_engine_operads.infrastructure.capability_catalog_compiler import (
    compile_capability_catalog,
    write_host_projections,
)


class TestAsgiMultiTenantCompileCatalog(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "asgi_multitenant_wal.db")

        # Create skill fixtures in the workspace
        skills_dir = self.workspace_root / ".agents" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, 4):
            skill_folder = skills_dir / f"skill-tenant-{i}"
            skill_folder.mkdir(parents=True, exist_ok=True)
            (skill_folder / "SKILL.md").write_text(
                f"""---
name: skill-tenant-{i}
description: Tenant {i} catalog isolation fixture.
operad_source_colours: [Code]
operad_target_colour: State
operad_arity: 1
operad_residual: unknown
---
# Skill Tenant {i}
```oewas.operand.v3
operand_id: op_tenant_{i}
kind: instruction
body: "Tenant {i} isolation rule"
```

```oewas.operation.v3
operation_id: "skill-tenant-{i}:run"
inputs:
  - name: input_data
    colour_id: Code
    schema_ref: schema:data:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: output_data
  colour_id: State
  schema_ref: schema:state:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - op_tenant_{i}
declaration: Declared
schema_binding: Bound
executor_binding: Bound
validation: Validated
admission: Unadmitted
residual_status: verified
authority_effect: None
authority_ceiling: None
description: "Executes tenant {i} pipeline"
```
""",
                encoding="utf-8",
            )

        # The filesystem reader consumes a declared catalog, not arbitrary files.
        (self.workspace_root / ".agents" / "skill_operads").mkdir()
        catalog = compile_capability_catalog(
            self.workspace_root,
            tracked_paths=tuple(
                f".agents/skills/skill-tenant-{i}/SKILL.md" for i in range(1, 4)
            ),
        )
        write_host_projections(self.workspace_root, catalog)

        # Initialize Container and FastAPI app
        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )
        self.app = FastAPI(title="OEOP ASGI Test App")
        self.app.include_router(self.container.router)

    async def asyncTearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    async def test_concurrent_multitenant_compile_catalog_requests(self) -> None:
        tenants = [
            "tenant_alpha",
            "tenant_beta",
            "tenant_gamma",
            "tenant_delta",
            "tenant_epsilon",
        ]
        transport = httpx.ASGITransport(app=self.app, client=("127.0.0.1", 49152))

        async with httpx.AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:

            async def tenant_request(tenant_id: str) -> httpx.Response:
                payload = {
                    "estate_ref": "canonical",
                    "correlation_id": f"corr-{tenant_id}",
                    "causation_id": f"cause-{tenant_id}",
                    "idempotency_key": f"idem-{tenant_id}",
                }
                headers = {"X-Tenant-ID": tenant_id}
                return await client.post(
                    "/api/oeop/v3/compile_catalog", json=payload, headers=headers
                )

            # Fire simultaneous requests across all tenants concurrently
            responses = await asyncio.gather(*(tenant_request(t) for t in tenants))

        self.assertEqual(len(responses), len(tenants))
        for resp in responses:
            self.assertEqual(resp.status_code, 200, f"Request failed: {resp.text}")
            data = resp.json()
            self.assertIn("catalog_id", data)
            self.assertEqual(data["estate_ref"], "canonical")
            self.assertGreaterEqual(data["total_skills"], 3)
            self.assertTrue(data["catalog_digest"].startswith("sha256:"))
            self.assertEqual(len(data["catalog_digest"].split(":")[-1]), 64)

    async def test_concurrent_idempotent_multitenant_requests(self) -> None:
        transport = httpx.ASGITransport(app=self.app, client=("127.0.0.1", 49152))
        shared_key = "idem-shared-multitenant"

        async with httpx.AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:

            async def idempotent_req(client_idx: int) -> httpx.Response:
                payload = {
                    "estate_ref": "canonical",
                    "correlation_id": f"corr-client-{client_idx}",
                    "causation_id": "cause-concurrent",
                    "idempotency_key": shared_key,
                }
                return await client.post("/api/oeop/v3/catalogs:compile", json=payload)

            responses = await asyncio.gather(*(idempotent_req(i) for i in range(8)))

        self.assertEqual(len(responses), 8)
        self.assertEqual(responses[0].status_code, 200, responses[0].text)
        first_catalog_id = responses[0].json()["catalog_id"]
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["catalog_id"], first_catalog_id)


if __name__ == "__main__":
    unittest.main()
