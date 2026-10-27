"""Examiner Class 1 & Class 2: Higher Operad Laws and Arbitrary N-Node Cyclic Graph Rejection.

Theoretical Minimum:
1. INVARIANT: Kahn's DAG scheduler and Operad Adapter must strictly reject all cyclic dependencies
   across arbitrary N-agent cycles (N in [2, 10]) and out-of-bound slot indexes.
2. BREAK: Graph scheduler loops infinitely on circular loops or silently omits cycle steps.
3. WITNESS: ValidateWorkflowsHandler returns Err with CYCLIC_WORKFLOW_DEPENDENCY; HigherOperadAdapter
   returns Err with SLOT_INDEX_OUT_OF_BOUNDS.
4. MUTATION: In validate_workflows.py, delete the 'if len(topological_order) < len(graph)' cycle check.
"""

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
from operads.domain.entities.operation_v3 import (
    OperationV3,
    PortSpecV3,
)
from operads.domain.value_objects import (
    AdmissionFacet,
    AuthorityEffect,
    ColourId,
    ContentDigest,
    DeclarationFacet,
    ExecutorBindingFacet,
    OperationId,
    SchemaBindingFacet,
    SchemaRef,
    SkillLifecycleV3,
    ValidationFacet,
)
from operads.infrastructure.operad.higher_operad_adapter import (
    HigherOperadAdapter,
)


class TestHigherOperadLawsAndCyclicGraphs(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = ValidateWorkflowsHandler()
        self.adapter = HigherOperadAdapter()
        self.digest = ContentDigest.sha256("0" * 64)
        self.lifecycle = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
            schema_digest=self.digest,
            executor_digest=self.digest,
        )

    def test_arbitrary_n_node_cycle_rejection_matrix(self) -> None:
        """Class 1: Asserts that arbitrary N-node cycles (N = 2 to 8) are always rejected."""
        for n in range(2, 9):
            nodes = [
                WorkflowNodeDTO(
                    node_id=f"agent_{i}",
                    operation_id=f"op_{i}",
                    inputs=("Data",),
                    outputs=("Data",),
                )
                for i in range(n)
            ]
            # Construct cycle: 0 -> 1 -> 2 -> ... -> (n-1) -> 0
            edges = [
                WorkflowEdgeDTO(
                    source_node_id=f"agent_{i}",
                    source_output="Data",
                    target_node_id=f"agent_{(i + 1) % n}",
                    target_input="Data",
                )
                for i in range(n)
            ]

            query = ValidateWorkflowsQuery(nodes=tuple(nodes), edges=tuple(edges))
            res = self.handler.handle(query)

            self.assertTrue(res.is_ok)
            dto = res.unwrap()
            self.assertFalse(dto.is_valid, f"Cycle of length {n} MUST fail validation")
            self.assertGreater(len(dto.cycles), 0, f"Cycle of length {n} must record cycle paths")
            self.assertEqual(len(dto.topological_order), 0, "Cyclic graph must yield empty topological sort")
            self.assertEqual(len(dto.execution_stages), 0, "Cyclic graph must yield empty execution stages")

    def test_out_of_bounds_slot_binding_rejection(self) -> None:
        """Class 2: Asserts that binding to a non-existent slot index is rejected."""
        root_op = OperationV3(
            operation_id=OperationId("root:op"),
            inputs=(
                PortSpecV3("in0", ColourId("Code"), SchemaRef("schema:v1"), self.digest, "", self.digest),
            ),
            output=PortSpecV3("out", ColourId("Receipt"), SchemaRef("schema:v1"), self.digest, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        child_op = OperationV3(
            operation_id=OperationId("child:op"),
            inputs=(),
            output=PortSpecV3("out", ColourId("Code"), SchemaRef("schema:v1"), self.digest, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )

        # Attempt to bind into slot index 99 (root only has slot 0)
        res = self.adapter.verify_composition(
            root_op=root_op,
            child_ops=(child_op,),
            slot_bindings=((99, child_op),),
        )

        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SLOT_INDEX_OUT_OF_BOUNDS")


if __name__ == "__main__":
    unittest.main()
