"""Comprehensive End-to-End full lifecycle system test for OEWAS V3.

Executes the complete estate compilation, workflow DAG validation, projection export,
cryptographic signing, outbox message dispatch, and CLI query inspection.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from operads.application.dtos.query_dtos import (
    ValidateWorkflowsQuery,
    WorkflowEdgeDTO,
    WorkflowNodeDTO,
)
from operads.frontend.cli.main import main
from operads.infrastructure.bootstrap import OeopContainer
from operads.infrastructure.providers.manifest_signature_provider import (
    ManifestSignatureProvider,
)
from operads.infrastructure.storage.outbox_dispatcher import (
    OutboxMessageDispatcher,
)


class TestE2EFullLifecycleRoundtrip(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "e2e_lifecycle.db")
        self.signing_key = b"sentinel_master_signing_key_secret_2026"

        # 1. Author skill documents on disk
        author_dir = self.workspace_root / ".agents" / "skills" / "author-skill"
        author_dir.mkdir(parents=True, exist_ok=True)
        (author_dir / "SKILL.md").write_text(
            """# Author Skill: Specification Generator
Generates clean architecture domain specifications.

```oewas.operation.v3
operation_id: "author:generate_spec"
inputs:
  - name: "prompt"
    colour_id: "Prompt"
    schema_ref: "schema:prompt:v1"
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: "spec"
  colour_id: "Spec"
  schema_ref: "schema:spec:v1"
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
```
""",
            encoding="utf-8",
        )

        tester_dir = self.workspace_root / ".agents" / "skills" / "tester-skill"
        tester_dir.mkdir(parents=True, exist_ok=True)
        (tester_dir / "SKILL.md").write_text(
            """# Tester Skill: Specification Verifier
Audits and verifies specifications against prime rules.

```oewas.operation.v3
operation_id: "tester:verify_spec"
inputs:
  - name: "spec"
    colour_id: "Spec"
    schema_ref: "schema:spec:v1"
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: "receipt"
  colour_id: "Receipt"
  schema_ref: "schema:receipt:v1"
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
```
""",
            encoding="utf-8",
        )

        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )

    def tearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    def test_full_lifecycle_roundtrip(self) -> None:
        """Executes complete end-to-end estate compilation, DAG scheduling, signing, dispatch, and CLI queries."""
        api = self.container.api

        # Stage 1: Compile Estate Catalog
        compile_res = api.compile_catalog(
            estate_ref="canonical",
            correlation_id="e2e-corr-001",
            causation_id="e2e-cause-init",
            idempotency_key="e2e-idem-key-01",
        )
        self.assertTrue(compile_res.is_ok, f"Compile failed: {compile_res.unwrap_err() if compile_res.is_err else ''}")
        cat_dto = compile_res.unwrap()
        self.assertEqual(cat_dto.total_skills, 2)
        self.assertEqual(cat_dto.total_operations, 2)
        self.assertEqual(cat_dto.epoch, 1)

        # Stage 2: Validate Multi-Agent Workflow DAG
        dag_query = ValidateWorkflowsQuery(
            nodes=(
                WorkflowNodeDTO(
                    node_id="node_author",
                    operation_id="author:generate_spec",
                    inputs=("Prompt",),
                    outputs=("Spec",),
                ),
                WorkflowNodeDTO(
                    node_id="node_tester",
                    operation_id="tester:verify_spec",
                    inputs=("Spec",),
                    outputs=("Receipt",),
                ),
            ),
            edges=(
                WorkflowEdgeDTO(
                    source_node_id="node_author",
                    source_output="Spec",
                    target_node_id="node_tester",
                    target_input="Spec",
                ),
            ),
        )
        dag_res = api._validate_workflows.handle(dag_query)
        self.assertTrue(dag_res.is_ok)
        dag_dto = dag_res.unwrap()
        self.assertTrue(dag_dto.is_valid)
        self.assertEqual(dag_dto.execution_stages, (("node_author",), ("node_tester",)))
        self.assertEqual(dag_dto.topological_order, ("node_author", "node_tester"))

        # Stage 3: Export Projection Manifest
        proj_res = api.compile_projection(
            catalog_id=cat_dto.catalog_id,
            target_format="json",
            correlation_id="e2e-corr-001",
            causation_id="e2e-cause-proj",
        )
        self.assertTrue(proj_res.is_ok)
        proj_dto = proj_res.unwrap()
        self.assertEqual(proj_dto.target_format, "json")

        # Stage 4: Cryptographic Signing & Signature Verification
        sig_provider = ManifestSignatureProvider()
        envelope = sig_provider.sign_manifest(
            manifest_id="e2e_manifest_01",
            catalog_id=proj_dto.catalog_id,
            epoch=cat_dto.epoch,
            target_format="json",
            payload=proj_dto.payload,
            signer_id="author:sentinel:primary",
            secret_key=self.signing_key,
        )
        verify_res = sig_provider.verify_envelope(envelope, secret_key=self.signing_key)
        self.assertTrue(verify_res.is_ok)
        self.assertTrue(verify_res.unwrap())

        # Stage 5: Outbox Message Dispatching
        received_dispatches: list[dict] = []
        dispatcher = OutboxMessageDispatcher(self.container.uow)
        dispatcher.subscribe("events.oewas.v3", lambda msg: received_dispatches.append(msg))

        dispatch_res = dispatcher.dispatch_pending()
        self.assertTrue(dispatch_res.is_ok)
        report = dispatch_res.unwrap()
        self.assertGreater(report.delivered_count, 0)
        self.assertEqual(report.failed_count, 0)
        self.assertEqual(len(received_dispatches), report.delivered_count)

        # Stage 6: CLI Query & Verification Inspection
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        cli_argv = [
            "--workspace", str(self.workspace_root),
            "--db-path", self.db_path,
            "--json",
            "verify-catalog",
            cat_dto.catalog_id,
        ]
        with patch.object(sys, "stdout", stdout_buf), patch.object(sys, "stderr", stderr_buf):
            rc = main(cli_argv)

        self.assertEqual(rc, 0, f"CLI exited with {rc}, stderr: {stderr_buf.getvalue()}")
        cli_payload = json.loads(stdout_buf.getvalue())
        self.assertEqual(cli_payload["status"], "ok")
        self.assertEqual(cli_payload["catalog_id"], cat_dto.catalog_id)
        self.assertTrue(cli_payload["is_valid"])


if __name__ == "__main__":
    unittest.main()
