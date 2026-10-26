"""Unit tests for the autonomous omega_engine_pfp package.

Validates:
1. Clean Architecture boundary enforcement across domain, use_cases, infrastructure,
   controllers, and frontend.
2. PfpController orchestration of use cases via ROP Result monads.
3. CLI argument parsing and execution paths.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from typing import Any, Dict

from omega_engine_pfp.controllers.pfp_controller import PfpController
from omega_engine_pfp.domain.prompts.prompts import PromptPacket
from omega_engine_pfp.domain.kernel.result import RefusalCode
from omega_engine_pfp.entrypoints.cli.pfp import build_parser
from omega_engine_pfp.domain.rewriting.rewrites import Boundary, RewriteRequest, Segment


class TestPfpPackage(unittest.TestCase):
    """Verifies the self-contained PFP Clean Architecture package."""

    def setUp(self) -> None:
        self.controller = PfpController()

    def test_01_assemble_prompt_use_case(self) -> None:
        """Assembles a prompt packet for stage 1."""
        seed_data = {"seed": "Compute the sum of 10 and 20."}
        res = self.controller.assemble_prompt(
            demo_id="demo_000",
            stage=1,
            seed_data=seed_data,
        )
        self.assertTrue(res.is_ok, f"Expected Ok, got: {res}")
        packet = res.unwrap()
        self.assertIsInstance(packet, PromptPacket)
        self.assertEqual(packet.stage, 1)
        self.assertTrue(len(packet.user_sha256) > 0)

    def test_02_evaluate_gates(self) -> None:
        """Evaluates 13 Woland tribunal gates with clean attestations."""
        clean_attestations = {
            "text": "simplicial carrier with exact boundary",
            "is_admitted": True,
            "masks_contradiction": False,
            "is_trivial_fixpoint": False,
            "round_number": 1,
            "nilpotency_verified": True,
            "duality_gap": 0,
            "requires_exact_zero": True,
            "has_coerced_witness": False,
            "unhealed_defect_count": 0,
            "defect_budget": 0,
            "fails_perturbation": False,
            "regress_depth": 0,
            "is_timid_refusal": False,
        }
        res = self.controller.evaluate_gates(
            candidate_id="cand_test_001",
            candidate_state=clean_attestations,
        )
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertTrue(receipt.all_passed)
        self.assertEqual(receipt.terminal_disposition, "AttestedPass")
        self.assertEqual(len(receipt.verdicts), 13)

    def test_03_evaluate_gates_fail_closed(self) -> None:
        """Fails closed when attestations are missing."""
        res = self.controller.evaluate_gates(
            candidate_id="cand_empty",
            candidate_state={},
        )
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertFalse(receipt.all_passed)
        self.assertEqual(receipt.terminal_disposition, "Refused")

    def test_04_run_demo(self) -> None:
        """Executes demo_000 through the unified demo runner."""
        res = self.controller.run_demo("demo_000")
        self.assertTrue(res.is_ok, f"Expected Ok demo run, got: {res}")
        receipt = res.unwrap()
        self.assertEqual(receipt.demo_id, "demo_000")
        self.assertTrue(receipt.all_passed)
        self.assertEqual(receipt.terminal_status, "Exact")

    def test_05_verify_contracts(self) -> None:
        """Loading declarations cannot verify candidate normal forms."""
        res = self.controller.verify_normal_forms()
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.HOST_VERIFIER_UNAVAILABLE)

    def test_06_rewrite_prompt(self) -> None:
        """Applies rewriting bindings to a prompt template."""
        from omega_engine_pfp.domain.rewriting.rewrites import Binding
        req = RewriteRequest(
            request_id="req_001",
            raw_prompt="Compute 2 + 2",
            segments=[
                Segment(role="task", boundary="<<task><q>>", text="Compute 2 + 2"),
            ],
            bindings=[Binding(symbol="x", target_role="output", description="output binding")],
        )
        res = self.controller.rewrite_prompt(req)
        self.assertTrue(res.is_ok, f"Expected Ok, got: {res}")
        receipt = res.unwrap()
        self.assertEqual(receipt.request_id, "req_001")
        self.assertEqual(receipt.segments_count, 1)

    def test_07_cli_parser(self) -> None:
        """Verifies CLI argument parser configurations."""
        parser = build_parser()
        args = parser.parse_args(["run-demo", "demo_000"])
        self.assertEqual(args.command, "run-demo")
        self.assertEqual(args.demo_id, "demo_000")

        args = parser.parse_args(["verify-contracts"])
        self.assertEqual(args.command, "verify-contracts")

        args = parser.parse_args(["evaluate-gates", "--candidate-id", "c1"])
        self.assertEqual(args.command, "evaluate-gates")
        self.assertEqual(args.candidate_id, "c1")


if __name__ == "__main__":
    unittest.main()
