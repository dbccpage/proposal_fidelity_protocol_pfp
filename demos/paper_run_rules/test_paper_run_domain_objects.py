"""The paper-run value objects: enums, errors, immutable nodes, claim IR and run plan.

Ported from an internal test suite. AuthorityEffect: None.
"""

from __future__ import annotations

import unittest

from paperrun.claim_ir import ClaimIRDocument, ClaimIRItem
from paperrun.claim_node import ClaimNode
from paperrun.enums import (
    AUTHORITY_EFFECT,
    ClaimKind,
    ObligationDisposition,
    ObligationKind,
    Role,
)
from paperrun.errors import PaperRunGraphError
from paperrun.obligation_node import ObligationNode
from paperrun.paper_run_graph import PaperRunGraph
from paperrun.run_plan import RunPlan
from paperrun.transition_event import TransitionEvent


class TestPaperRunDomainObjects(unittest.TestCase):
    """Each value object works on its own and refuses mutation."""

    def test_enums_identity_and_string_values(self) -> None:
        self.assertEqual(Role.PROPOSER, "proposer")
        self.assertEqual(ClaimKind.THEOREM, "theorem")
        self.assertEqual(ObligationKind.LEAN_KERNEL, "lean_kernel")
        self.assertEqual(ObligationDisposition.DISCHARGED, "discharged")
        self.assertEqual(AUTHORITY_EFFECT, "None")

    def test_errors_subclassing(self) -> None:
        err = PaperRunGraphError("Test error")
        self.assertIsInstance(err, ValueError)
        self.assertEqual(str(err), "Test error")

    def test_claim_node_immutability_and_serialization(self) -> None:
        claim = ClaimNode(
            claim_id="CLM-001",
            kind=ClaimKind.THEOREM,
            claim_ceiling="MECHANIZED_CORE_ONLY",
            mechanization_class="LEAN4_CORE",
            lean_na_reason="",
        )
        self.assertEqual(claim.claim_id, "CLM-001")
        self.assertEqual(claim.kind, "theorem")
        d = claim.to_dict()
        self.assertEqual(d["claim_id"], "CLM-001")
        with self.assertRaises(Exception):
            claim.claim_id = "MUTATED"  # type: ignore[misc]

    def test_obligation_node_immutability_and_serialization(self) -> None:
        obl = ObligationNode(
            obligation_id="OBL-001",
            claim_id="CLM-001",
            kind=ObligationKind.LEAN_KERNEL,
            disposition=ObligationDisposition.UNCHECKED,
        )
        self.assertEqual(obl.obligation_id, "OBL-001")
        self.assertEqual(obl.disposition, "unchecked")
        d = obl.to_dict()
        self.assertEqual(d["obligation_id"], "OBL-001")
        with self.assertRaises(Exception):
            obl.obligation_id = "MUTATED"  # type: ignore[misc]

    def test_transition_event_construction(self) -> None:
        event = TransitionEvent(
            role=Role.PROPOSER,
            event_type="candidate_patch",
            carrier_hash="0123456789abcdef",
            candidate_hash="fedcba9876543210",
        )
        self.assertEqual(event.role, "proposer")
        self.assertEqual(event.carrier_hash, "0123456789abcdef")
        with self.assertRaises(Exception):
            event.role = "mutated"  # type: ignore[misc]

    def test_claim_ir_conversion(self) -> None:
        item = ClaimIRItem(
            claim_id="C-TEST",
            mechanization_class="LEAN_FULL",
            lean_na_reason="",
            title="Test Claim",
        )
        node = item.to_claim_node()
        self.assertEqual(node.claim_id, "C-TEST")
        self.assertEqual(node.kind, "mechanization")
        self.assertEqual(node.claim_ceiling, "MECHANIZED_CORE_ONLY")

        yaml_doc = """
schema_version: claim_ir/v1
claims:
  - claim_id: C-YAML
    mechanization_class: SCOPE_FENCE
"""
        doc = ClaimIRDocument.from_yaml(yaml_doc)
        nodes = doc.to_claim_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].claim_id, "C-YAML")
        self.assertEqual(nodes[0].kind, "scope_fence")
        self.assertEqual(nodes[0].claim_ceiling, "SCOPE_FENCE")

    def test_paper_run_graph_and_run_plan_integration(self) -> None:
        claim = ClaimNode(
            claim_id="CLM-001",
            kind=ClaimKind.THEOREM,
            claim_ceiling="MECHANIZED_CORE_ONLY",
        )
        graph = PaperRunGraph.create(
            paper_root="/path/to/paper",
            carrier_hash="abc123",
            claims=[claim],
        )
        self.assertEqual(len(graph.claims), 1)
        self.assertGreater(len(graph.obligations), 0)

        plan = RunPlan(
            graph=graph,
            required_stage_ids=["S0_SKELETON", "S1_CODE"],
        )
        plan_dict = plan.to_dict()
        self.assertEqual(plan_dict["carrier_hash"], "abc123")
        self.assertEqual(plan_dict["paper_root"], "/path/to/paper")
        self.assertEqual(plan_dict["required_stage_ids"], ["S0_SKELETON", "S1_CODE"])
        yaml_out = plan.to_yaml()
        self.assertIn("abc123", yaml_out)


if __name__ == "__main__":
    unittest.main()
