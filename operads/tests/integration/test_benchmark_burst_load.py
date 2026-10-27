"""Benchmark test measuring latency percentiles and memory overhead under 100+ parallel agentic request bursts."""

from __future__ import annotations

import asyncio
import tempfile
import time
import tracemalloc
import unittest
from pathlib import Path

import httpx
from fastapi import FastAPI

from operads.infrastructure.bootstrap import OeopContainer


class TestBenchmarkBurstLoad(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "benchmark_wal.db")

        # Create skill fixtures in workspace
        skills_dir = self.workspace_root / ".agents" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, 6):
            sdir = skills_dir / f"bench-skill-{i}"
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_text(
                f"""# Benchmark Skill {i}
```oewas.operation.v3
operation_id: "bench-skill-{i}:execute"
inputs:
  - name: code_in
    colour_id: Code
    schema_ref: schema:source:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: receipt_out
  colour_id: Receipt
  schema_ref: schema:receipt:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs: []
declaration: Declared
schema_binding: Bound
executor_binding: Bound
validation: Validated
admission: Admitted
residual_status: verified
authority_effect: None
authority_ceiling: None
description: "Benchmark workload operation {i}"
```
""",
                encoding="utf-8",
            )

        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )
        self.app = FastAPI(title="OEWAS Benchmark App")
        self.app.include_router(self.container.router)

    async def asyncTearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    async def test_sustained_100_plus_request_burst_load(self) -> None:
        total_requests = 120
        concurrency_batch_size = 30
        latencies: list[float] = []

        transport = httpx.ASGITransport(app=self.app, client=("127.0.0.1", 49152))

        # Start memory tracking
        tracemalloc.start()
        _mem_start_current, _mem_start_peak = tracemalloc.get_traced_memory()

        start_wall_time = time.perf_counter()

        async with httpx.AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:

            async def single_agentic_request(req_idx: int) -> float:
                t0 = time.perf_counter()
                expected_status = 200

                # Rotate across compile_catalog, licensed terms, and workflow validation
                if req_idx % 3 == 0:
                    payload = {
                        "estate_ref": "canonical",
                        "correlation_id": f"corr-burst-{req_idx}",
                        "causation_id": "cause-burst",
                        "idempotency_key": f"idem-burst-{req_idx}",
                    }
                    res = await client.post(
                        "/api/oeop/v3/compile_catalog", json=payload
                    )
                elif req_idx % 3 == 1:
                    expected_status = 422
                    payload = {
                        "agent_id": f"agent_{req_idx % 5}",
                        "term_expr": f"gamma(bench-skill-{1 + (req_idx % 5)}:execute)",
                        "correlation_id": f"corr-term-{req_idx}",
                        "causation_id": "cause-term",
                    }
                    res = await client.post("/api/oeop/v3/terms:compile", json=payload)
                else:
                    payload = {
                        "nodes": [
                            {
                                "node_id": "n1",
                                "operation_id": "bench-skill-1:execute",
                                "inputs": ["Code"],
                                "outputs": ["Receipt"],
                            },
                            {
                                "node_id": "n2",
                                "operation_id": "bench-skill-2:execute",
                                "inputs": ["Receipt"],
                                "outputs": ["Audit"],
                            },
                        ],
                        "edges": [
                            {
                                "source_node_id": "n1",
                                "source_output": "Receipt",
                                "target_node_id": "n2",
                                "target_input": "Receipt",
                            },
                        ],
                    }
                    res = await client.post(
                        "/api/oeop/v3/workflows:validate", json=payload
                    )

                t1 = time.perf_counter()
                self.assertEqual(
                    res.status_code,
                    expected_status,
                    f"Request {req_idx} failed: {res.text}",
                )
                if expected_status == 422:
                    self.assertEqual(
                        res.json()["detail"]["code"], "LICENSE_WITNESS_REQUIRED"
                    )
                return (t1 - t0) * 1000.0  # ms

            # Execute in asynchronous concurrent batches
            for batch_start in range(0, total_requests, concurrency_batch_size):
                batch_tasks = [
                    single_agentic_request(i)
                    for i in range(
                        batch_start,
                        min(batch_start + concurrency_batch_size, total_requests),
                    )
                ]
                batch_latencies = await asyncio.gather(*batch_tasks)
                latencies.extend(batch_latencies)

        total_wall_time = time.perf_counter() - start_wall_time
        _mem_end_current, mem_end_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Metrics computation
        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        rps = total_requests / total_wall_time
        peak_mb = mem_end_peak / (1024 * 1024)

        # Assertions for performance and memory invariants
        self.assertEqual(len(latencies), total_requests)
        self.assertGreater(rps, 15.0, f"Throughput too low: {rps:.2f} req/s")
        self.assertLess(p95, 1500.0, f"p95 latency exceeded SLA: {p95:.2f}ms")
        self.assertLess(peak_mb, 50.0, f"Peak memory exceeded limit: {peak_mb:.2f}MB")


if __name__ == "__main__":
    unittest.main()
