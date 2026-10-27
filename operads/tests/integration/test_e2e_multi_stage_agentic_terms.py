"""End-to-End Integration Test: Multi-stage agentic terms dispatched through OeopApiV3 into SQLite WAL."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
import unittest

from operads.domain.value_objects.identifier import OperationId
from operads.infrastructure.bootstrap import OeopContainer


class TestE2EMultiStageAgenticTerms(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "oewas_test_wal.db")

        # Create realistic skill directories with lossless OEWAS V3 declarations
        skills_dir = self.workspace_root / ".agents" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        # 1. Primitive Skill: Audit Code
        audit_dir = skills_dir / "audit-code"
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / "SKILL.md").write_text(
            """# Audit Code Skill
Inspects codebase and generates architectural audit.

```oewas.operand.v3
operand_id: op_audit_inst
kind: instruction
body: "Enforce Clean Architecture boundaries and zero-shim rules"
dependencies: []
emitted_observations: ["boundary_clean", "no_circular_deps"]
```

```oewas.operation.v3
operation_id: "audit-code:inspect"
inputs:
  - name: code_in
    colour_id: Code
    schema_ref: schema:source:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: audit_out
  colour_id: Audit
  schema_ref: schema:audit:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - op_audit_inst
declaration: Declared
schema_binding: Bound
executor_binding: Bound
validation: Validated
admission: Admitted
residual_status: verified
authority_effect: None
authority_ceiling: None
description: "Audits AST boundaries"
```
""",
            encoding="utf-8",
        )

        # 2. Primitive Skill: Verify Proof
        verify_dir = skills_dir / "verify-proof"
        verify_dir.mkdir(parents=True, exist_ok=True)
        (verify_dir / "SKILL.md").write_text(
            """# Verify Proof Skill
Verifies formal cochain lifts and audit reports.

```oewas.operand.v3
operand_id: op_verify_inst
kind: instruction
body: "Verify proof term and evidence receipts"
dependencies: []
emitted_observations: ["proof_checked"]
```

```oewas.operation.v3
operation_id: "verify-proof:lift"
inputs:
  - name: proof_in
    colour_id: Proof
    schema_ref: schema:proof:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
  - name: audit_in
    colour_id: Audit
    schema_ref: schema:audit:v1
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: receipt_out
  colour_id: Receipt
  schema_ref: schema:receipt:v1
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
operand_refs:
  - op_verify_inst
declaration: Declared
schema_binding: Bound
executor_binding: Bound
validation: Validated
admission: Admitted
residual_status: verified
authority_effect: None
authority_ceiling: EvidenceOnly
description: "Verifies proof and audit receipts"
```
""",
            encoding="utf-8",
        )

        # 3. Meta-Skill: Composite Pipeline with Operadic Composition
        meta_dir = skills_dir / "meta-pipeline"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "SKILL.md").write_text(
            """# Meta Pipeline Skill
Composes audit-code and verify-proof into an operadic workflow.

```oewas.composition.v3
composition_id: comp_meta_pipeline
term_kind: tree
root_operation_id: "verify-proof:lift"
child_operation_ids:
  - "audit-code:inspect"
slot_bindings:
  - [1, "audit-code:inspect"]
expected_boundary: "(Proof, Code) -> Receipt"
```
""",
            encoding="utf-8",
        )

        # Initialize Container and API Facade
        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )
        self.api = self.container.api

    def tearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    def test_e2e_full_lifecycle_multi_stage_agentic_terms(self) -> None:
        # Stage 1: Compile Estate Catalog from Workspace
        compile_res = self.api.compile_catalog(
            estate_ref="canonical",
            correlation_id="corr-e2e-001",
            causation_id="init-e2e",
            idempotency_key="idem-e2e-001",
        )
        self.assertTrue(compile_res.is_ok, f"Compilation failed: {compile_res}")
        catalog_dto = compile_res.unwrap()
        self.assertIsNotNone(catalog_dto.catalog_id)
        self.assertGreaterEqual(catalog_dto.total_skills, 3)
        self.assertGreaterEqual(catalog_dto.total_operations, 2)

        catalog_id = catalog_dto.catalog_id

        # Stage 2: Verify Catalog and Operadic Compositions
        verify_res = self.api.verify_catalog(
            catalog_id=catalog_id,
            correlation_id="corr-e2e-002",
            causation_id="cause-verify",
        )
        self.assertTrue(verify_res.is_ok, f"Verification failed: {verify_res}")
        verify_dto = verify_res.unwrap()
        self.assertTrue(verify_dto.is_valid)
        self.assertEqual(len(verify_dto.errors), 0)
        self.assertGreaterEqual(verify_dto.total_operations_verified, 2)

        # Stage 3: Compile Projection Manifest
        proj_res = self.api.compile_projection(
            catalog_id=catalog_id,
            target_format="operad_v1",
            correlation_id="corr-e2e-003",
        )
        self.assertTrue(proj_res.is_ok, f"Projection failed: {proj_res}")
        proj_dto = proj_res.unwrap()
        self.assertEqual(proj_dto.target_format, "operad_v1")
        self.assertTrue(len(proj_dto.manifest_digest) == 64)

        # Stage 4: Refuse an unbound license request rather than minting authorization.
        term_res = self.api.compile_licensed_term(
            agent_id="thanatos",
            term_expr="gamma(verify-proof:lift; audit-code:inspect)",
            correlation_id="corr-e2e-004",
        )
        self.assertTrue(term_res.is_err)
        self.assertEqual(term_res.unwrap_err().code, "LICENSE_WITNESS_REQUIRED")

        # Stage 5: Validate Workflow Directed Graph (Valid Pipeline vs Cycle)
        valid_nodes = [
            {"node_id": "n1", "operation_id": "audit-code:inspect", "inputs": ["Code"], "outputs": ["Audit"]},
            {"node_id": "n2", "operation_id": "verify-proof:lift", "inputs": ["Proof", "Audit"], "outputs": ["Receipt"]},
        ]
        valid_edges = [
            {"source_node_id": "n1", "source_output": "Audit", "target_node_id": "n2", "target_input": "Audit"},
        ]
        wf_res = self.api.validate_workflows(nodes=valid_nodes, edges=valid_edges)
        self.assertTrue(wf_res.is_ok)
        wf_dto = wf_res.unwrap()
        self.assertTrue(wf_dto.is_valid)
        self.assertEqual(wf_dto.node_count, 2)
        self.assertEqual(wf_dto.edge_count, 1)

        # Test cycle detection: n2 -> n1 -> n2
        cyclic_edges = [
            {"source_node_id": "n1", "source_output": "Audit", "target_node_id": "n2", "target_input": "Audit"},
            {"source_node_id": "n2", "source_output": "Receipt", "target_node_id": "n1", "target_input": "Code"},
        ]
        cycle_res = self.api.validate_workflows(nodes=valid_nodes, edges=cyclic_edges)
        self.assertTrue(cycle_res.is_ok)
        cycle_dto = cycle_res.unwrap()
        self.assertFalse(cycle_dto.is_valid)
        self.assertGreater(len(cycle_dto.cycles), 0)

        # Stage 6: Verify Direct SQLite WAL Journal, Events & Outbox Persistence
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Catalogs table
        cat_rows = conn.execute("SELECT * FROM catalogs_v3 WHERE catalog_id = ?", (catalog_id,)).fetchall()
        self.assertEqual(len(cat_rows), 1)
        cat_row = cat_rows[0]
        self.assertEqual(cat_row["estate_ref"], "canonical")

        # Events journal table
        events = conn.execute("SELECT * FROM events_v3 WHERE correlation_id = 'corr-e2e-001'").fetchall()
        self.assertGreaterEqual(len(events), 2)
        event_types = {e["event_type"] for e in events}
        self.assertIn("EstateCapturedV3", event_types)
        self.assertIn("CatalogCompiledV3", event_types)

        # Outbox table
        outbox_rows = conn.execute("SELECT * FROM outbox_v3").fetchall()
        self.assertGreaterEqual(len(outbox_rows), 2)

        # Idempotency table
        idem_rows = conn.execute("SELECT * FROM idempotency_v3 WHERE idempotency_key = 'idem-e2e-001'").fetchall()
        self.assertEqual(len(idem_rows), 1)
        idem_resp = json.loads(idem_rows[0]["response_json"])
        self.assertEqual(idem_resp["catalog_id"], catalog_id)

        conn.close()

        # Stage 7: Query Handler Catalog Retrieval with Complete Object Fidelity
        get_res = self.api.get_catalog(catalog_id=catalog_id)
        self.assertTrue(get_res.is_ok)
        retrieved_catalog = get_res.unwrap()
        self.assertEqual(retrieved_catalog.catalog_id, catalog_id)
        self.assertIn(OperationId("audit-code:inspect"), retrieved_catalog.operations)
        self.assertIn(OperationId("verify-proof:lift"), retrieved_catalog.operations)

        audit_op = retrieved_catalog.operations[OperationId("audit-code:inspect")]
        self.assertEqual(audit_op.output.colour_id.value, "Audit")
        self.assertEqual(audit_op.residual_status, "verified")


if __name__ == "__main__":
    unittest.main()
