"""Contract tests for OeopApiV3 Python Facade."""

import unittest
from omega_engine_operads.infrastructure.bootstrap import (
    create_oeop_container,
)


class OeopApiV3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = create_oeop_container()
        self.api = self.container.api

    def test_api_compile_and_verify_catalog(self) -> None:
        res = self.api.compile_catalog(
            estate_ref="canonical",
            correlation_id="corr-api-1",
            causation_id="cause-api-1",
            idempotency_key="idem-api-1",
        )
        self.assertTrue(res.is_ok)
        dto = res.unwrap()
        self.assertEqual(dto.epoch, 1)

        # Verify
        v_res = self.api.verify_catalog(
            catalog_id=dto.catalog_id,
            correlation_id="corr-api-1",
            causation_id="cause-api-1",
        )
        self.assertTrue(v_res.is_ok)
        self.assertTrue(v_res.unwrap().is_valid)

    def test_api_validate_workflows_valid_dag(self) -> None:
        nodes = [
            {
                "node_id": "n1",
                "operation_id": "op1",
                "inputs": ["in1"],
                "outputs": ["out1"],
                "output_colours": {"out1": "Receipt"},
            },
            {
                "node_id": "n2",
                "operation_id": "op2",
                "inputs": ["in2"],
                "outputs": ["out2"],
                "input_colours": {"in2": "Receipt"},
            },
        ]
        edges = [
            {"source_node_id": "n1", "source_output": "out1", "target_node_id": "n2", "target_input": "in2"}
        ]
        res = self.api.validate_workflows(nodes=nodes, edges=edges)
        self.assertTrue(res.is_ok)
        self.assertTrue(res.unwrap().is_valid)
