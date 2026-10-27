"""Integration test for Agent-to-Agent workflow DAG compilation and validation."""

from __future__ import annotations

import unittest

from operads.application.dtos.query_dtos import (
    ValidateWorkflowsQuery,
    WorkflowEdgeDTO,
    WorkflowNodeDTO,
)
from operads.application.queries.validate_workflows import (
    ValidateWorkflowsHandler,
)


class TestAgentToAgentDagCompilation(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = ValidateWorkflowsHandler()

    def test_multi_agent_parallel_collaborative_workflow_compilation(self) -> None:
        """Validates parallel branching and diamond join across 4 collaborating agents."""
        # 5-step collaborative workflow
        nodes = (
            WorkflowNodeDTO(
                node_id="step_author",
                operation_id="python-principal:write_code",
                inputs=("Prompt",),
                outputs=("Code",),
            ),
            WorkflowNodeDTO(
                node_id="step_unit_test",
                operation_id="python-tester:test_code",
                inputs=("Code",),
                outputs=("TestReceipt",),
            ),
            WorkflowNodeDTO(
                node_id="step_lint_audit",
                operation_id="docs-linter:audit_docs",
                inputs=("Code",),
                outputs=("LintReceipt",),
            ),
            WorkflowNodeDTO(
                node_id="step_blackrod_gate",
                operation_id="blackrod:verify_quality",
                inputs=("TestReceipt", "LintReceipt"),
                outputs=("AuditReceipt",),
            ),
            WorkflowNodeDTO(
                node_id="step_paper_release",
                operation_id="paper-release:publish",
                inputs=("AuditReceipt",),
                outputs=("ReleaseManifest",),
            ),
        )

        edges = (
            WorkflowEdgeDTO(
                source_node_id="step_author",
                source_output="Code",
                target_node_id="step_unit_test",
                target_input="Code",
            ),
            WorkflowEdgeDTO(
                source_node_id="step_author",
                source_output="Code",
                target_node_id="step_lint_audit",
                target_input="Code",
            ),
            WorkflowEdgeDTO(
                source_node_id="step_unit_test",
                source_output="TestReceipt",
                target_node_id="step_blackrod_gate",
                target_input="TestReceipt",
            ),
            WorkflowEdgeDTO(
                source_node_id="step_lint_audit",
                source_output="LintReceipt",
                target_node_id="step_blackrod_gate",
                target_input="LintReceipt",
            ),
            WorkflowEdgeDTO(
                source_node_id="step_blackrod_gate",
                source_output="AuditReceipt",
                target_node_id="step_paper_release",
                target_input="AuditReceipt",
            ),
        )

        query = ValidateWorkflowsQuery(nodes=nodes, edges=edges)
        res = self.handler.handle(query)

        self.assertTrue(res.is_ok)
        dto = res.unwrap()

        self.assertTrue(dto.is_valid)
        self.assertEqual(dto.node_count, 5)
        self.assertEqual(dto.edge_count, 5)
        self.assertEqual(len(dto.cycles), 0)
        self.assertEqual(len(dto.colour_mismatches), 0)
        self.assertEqual(len(dto.orphaned_edges), 0)

        # Verify parallel execution stages
        self.assertEqual(len(dto.execution_stages), 4)
        self.assertEqual(dto.execution_stages[0], ("step_author",))
        self.assertEqual(set(dto.execution_stages[1]), {"step_lint_audit", "step_unit_test"})
        self.assertEqual(dto.execution_stages[2], ("step_blackrod_gate",))
        self.assertEqual(dto.execution_stages[3], ("step_paper_release",))

        # Verify linear topological sort order
        self.assertEqual(dto.topological_order[0], "step_author")
        self.assertEqual(dto.topological_order[-1], "step_paper_release")

    def test_cycle_detection_in_agent_delegation(self) -> None:
        """Detects circular feedback loops between agents."""
        nodes = (
            WorkflowNodeDTO(node_id="agent_a", operation_id="op_a", inputs=("Data",), outputs=("Data",)),
            WorkflowNodeDTO(node_id="agent_b", operation_id="op_b", inputs=("Data",), outputs=("Data",)),
            WorkflowNodeDTO(node_id="agent_c", operation_id="op_c", inputs=("Data",), outputs=("Data",)),
        )
        edges = (
            WorkflowEdgeDTO(source_node_id="agent_a", source_output="Data", target_node_id="agent_b", target_input="Data"),
            WorkflowEdgeDTO(source_node_id="agent_b", source_output="Data", target_node_id="agent_c", target_input="Data"),
            WorkflowEdgeDTO(source_node_id="agent_c", source_output="Data", target_node_id="agent_a", target_input="Data"),
        )
        query = ValidateWorkflowsQuery(nodes=nodes, edges=edges)
        res = self.handler.handle(query)
        self.assertTrue(res.is_ok)
        dto = res.unwrap()

        self.assertFalse(dto.is_valid)
        self.assertGreater(len(dto.cycles), 0)
        self.assertEqual(len(dto.execution_stages), 0)

    def test_colour_mismatch_and_orphan_edge_detection(self) -> None:
        """Detects incompatible data types between connected agent ports and missing node references."""
        nodes = (
            WorkflowNodeDTO(
                node_id="agent_source",
                operation_id="op_src",
                inputs=("source_prompt",),
                outputs=("source_code",),
                output_colours=(("source_code", "Code"),),
            ),
            WorkflowNodeDTO(
                node_id="agent_target",
                operation_id="op_tgt",
                inputs=("target_receipt",),
                outputs=("target_audit",),
                input_colours=(("target_receipt", "Receipt"),),
            ),
        )
        edges = (
            # Type mismatch: Code -> Receipt.
            WorkflowEdgeDTO(source_node_id="agent_source", source_output="source_code", target_node_id="agent_target", target_input="target_receipt"),
            # Orphaned edge: pointing to non-existent node
            WorkflowEdgeDTO(source_node_id="agent_source", source_output="source_code", target_node_id="ghost_agent", target_input="target_input"),
        )
        query = ValidateWorkflowsQuery(nodes=nodes, edges=edges)
        res = self.handler.handle(query)
        self.assertTrue(res.is_ok)
        dto = res.unwrap()

        self.assertFalse(dto.is_valid)
        self.assertGreater(len(dto.colour_mismatches), 0)
        self.assertGreater(len(dto.orphaned_edges), 0)


if __name__ == "__main__":
    unittest.main()
