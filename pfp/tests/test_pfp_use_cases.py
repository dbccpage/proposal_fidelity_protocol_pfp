"""Unit tests for PFP Use Cases.

Tests:
  1. AssemblePromptUseCase
  2. ExecuteStagePipelineUseCase
  3. EvaluateAdversaryGatesUseCase
  4. RunDemoUseCase
  5. VerifyPfpContractsUseCase
  6. RewritePromptUseCase

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import unittest
from typing import Any, Dict, Mapping

from pfp.domain.contracts.gates import AdversaryGateId
from pfp.domain.prompts.prompts import PromptPacket
from pfp.domain.kernel.result import RefusalCode, TerminalStatus
from pfp.domain.rewriting.rewrites import Binding, RewriteRequest, Segment
from pfp.domain.stages.stages import Stage5Response
from pfp.infrastructure import (
    UnifiedPfpDemoRunner,
)
from pfp.infrastructure.gate_evaluators import AdversaryTribunalGateEvaluator
from pfp.infrastructure.providers import OfflineDeterministicPfpProvider
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.use_cases.assemble_prompt import AssemblePromptUseCase
from pfp.use_cases.evaluate_gates import EvaluateAdversaryGatesUseCase
from pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase
from pfp.use_cases.rewrite_prompt import RewritePromptUseCase
from pfp.use_cases.run_demo import RunDemoUseCase
from pfp.use_cases.verify_contracts import VerifyPfpContractsUseCase

_CLEAN_ATTESTATIONS = {
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


class _HostVerifier:
    """Test double for the Stage 5 host check; it returns a fixed verdict."""

    def __init__(self, verdict: str, exact: bool, should_continue: bool = True) -> None:
        self.verdict = verdict
        self.exact = exact
        self.should_continue = should_continue

    def verify(self, demo_id: str, prior_responses: Mapping[int, Dict[str, Any]]) -> Stage5Response:
        assert sorted(prior_responses) == [1, 2, 3, 4]
        return Stage5Response(
            demo_id=demo_id,
            should_continue=self.should_continue,
            host_verdict=self.verdict,
            exact_checks_passed=self.exact,
            surviving_candidates=[prior_responses[4]["candidate_id"]] if self.verdict == "PASS" else [],
        )


class _StopsAtStage(OfflineDeterministicPfpProvider):
    def __init__(self, stop_stage: int) -> None:
        self.stop_stage = stop_stage

    def generate_candidate(self, packet: PromptPacket, temperature: float = 0.0) -> str:
        reply = json.loads(super().generate_candidate(packet, temperature))
        if packet.stage == self.stop_stage:
            reply["should_continue"] = False
        return json.dumps(reply)


class TestPfpUseCases(unittest.TestCase):
    """Test use cases decoupled from infrastructure implementations."""

    def setUp(self) -> None:
        self.storage = PfpFileSystemStorageAdapter()

    def test_01_assemble_prompt_use_case(self) -> None:
        use_case = AssemblePromptUseCase(storage=self.storage)
        res = use_case.assemble("demo_000", stage=1, seed_data={"seed": "V={0,1}"})
        self.assertTrue(res.is_ok)
        packet = res.unwrap()
        self.assertEqual(packet.demo_id, "demo_000")
        self.assertEqual(packet.stage, 1)
        self.assertTrue(len(packet.system) > 0)

    def _pipeline(
        self, host_verifier: object = None, provider: object = None
    ) -> ExecuteStagePipelineUseCase:
        return ExecuteStagePipelineUseCase(
            storage=self.storage,
            provider=provider or OfflineDeterministicPfpProvider(),
            catalog=self.storage,
            host_verifier=host_verifier,
        )

    def test_02_execute_stage_pipeline_use_case(self) -> None:
        use_case = self._pipeline(host_verifier=_HostVerifier("PASS", True))
        res = use_case.run_pipeline("demo_000", initial_seed={"carrier": "V={0,1}"})
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertEqual(receipt.demo_id, "demo_000")
        self.assertEqual(receipt.completed_stages, tuple(range(1, 12)))
        self.assertTrue(receipt.all_stages_passed)
        # No stage 6 witness was host-replayed, so the run cannot claim VERIFIED.
        self.assertEqual(receipt.final_terminal_status, TerminalStatus.VERIFIED_WITH_RESIDUALS)

    def test_02b_pipeline_without_host_verifier_refuses_at_stage_5(self) -> None:
        res = self._pipeline().run_pipeline("demo_000", initial_seed={})
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.HOST_VERIFIER_UNAVAILABLE)
        self.assertEqual(res.unwrap_err().stage, 5)

    def test_02c_pipeline_refuses_unknown_demo(self) -> None:
        res = self._pipeline(host_verifier=_HostVerifier("PASS", True)).run_pipeline(
            "no_such_demo_xyz", initial_seed={}
        )
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.UNKNOWN_DEMO)

    def test_02e_host_stop_at_stage_5_ends_pipeline(self) -> None:
        res = self._pipeline(
            host_verifier=_HostVerifier("PASS", True, should_continue=False)
        ).run_pipeline("demo_000", initial_seed={})
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertFalse(receipt.all_stages_passed)
        self.assertEqual(receipt.completed_stages, (1, 2, 3, 4, 5))

    def test_02f_adversary_gate_without_prior_failures_attestation_fails_closed(self) -> None:
        spec = next(
            g
            for g in self.storage.list_gate_specs()
            if g.gate_id == AdversaryGateId.PFP_13_ADVERSARY.value
        )
        verdict = AdversaryTribunalGateEvaluator().evaluate_gate(spec, {})
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.refusal_code, RefusalCode.MISSING_ATTESTATION.value)

    def test_02g_float_attestation_is_rejected_with_reason(self) -> None:
        spec = next(g for g in self.storage.list_gate_specs() if "PRIMAL_DUAL" in g.gate_id)
        verdict = AdversaryTribunalGateEvaluator().evaluate_gate(
            spec, {"duality_gap": 0.0, "requires_exact_zero": True}
        )
        self.assertFalse(verdict.passed)
        self.assertIn("float rejected", verdict.observation)

    def test_02d_pipeline_without_catalog_refuses(self) -> None:
        use_case = ExecuteStagePipelineUseCase(
            storage=self.storage,
            provider=OfflineDeterministicPfpProvider(),
            host_verifier=_HostVerifier("PASS", True),
        )
        res = use_case.run_pipeline("demo_000", initial_seed={})
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.CATALOG_UNAVAILABLE)

    def test_02e_host_rejection_is_a_refusal(self) -> None:
        for verdict, exact in (("FAIL", False), ("PASS", False), ("FAIL", True)):
            res = self._pipeline(host_verifier=_HostVerifier(verdict, exact)).run_pipeline(
                "demo_000", initial_seed={}
            )
            self.assertTrue(res.is_err, (verdict, exact))
            self.assertEqual(res.unwrap_err().code, RefusalCode.HOST_CHECK_FAILED)

    def test_02f_model_stopping_early_is_not_a_pass(self) -> None:
        res = self._pipeline(
            host_verifier=_HostVerifier("PASS", True), provider=_StopsAtStage(2)
        ).run_pipeline("demo_000", initial_seed={})
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertFalse(receipt.all_stages_passed)
        self.assertEqual(receipt.completed_stages, (1, 2))
        self.assertEqual(receipt.final_terminal_status, TerminalStatus.BLOCKED_BY_EVIDENCE)

    def test_03_evaluate_adversary_gates_use_case(self) -> None:
        gate_evaluator = AdversaryTribunalGateEvaluator()
        use_case = EvaluateAdversaryGatesUseCase(gate_evaluator=gate_evaluator)
        res = use_case.evaluate("candidate_001", candidate_state=dict(_CLEAN_ATTESTATIONS))
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertTrue(receipt.all_passed)
        self.assertEqual(receipt.terminal_disposition, "AttestedPass")
        self.assertEqual(len(receipt.verdicts), 13)

    def test_03b_gates_fail_closed_on_missing_attestations(self) -> None:
        use_case = EvaluateAdversaryGatesUseCase(gate_evaluator=AdversaryTribunalGateEvaluator())
        receipt = use_case.evaluate("candidate_001", candidate_state={"claims": []}).unwrap()
        self.assertFalse(receipt.all_passed)
        self.assertEqual(receipt.terminal_disposition, "Refused")
        refused = [v for v in receipt.verdicts if v.refusal_code == "MISSING_ATTESTATION"]
        self.assertEqual(len(refused), 12)

    def test_03c_gates_reject_bool_as_int_and_each_missing_field(self) -> None:
        evaluator = AdversaryTribunalGateEvaluator()
        state = dict(_CLEAN_ATTESTATIONS, round_number=True)
        receipt = evaluator.evaluate_tribunal("c", state)
        scope_guard = next(v for v in receipt.verdicts if "SCOPE_GUARD" in v.gate_id)
        self.assertEqual(scope_guard.refusal_code, "MISSING_ATTESTATION")
        for field in _CLEAN_ATTESTATIONS:
            partial = {k: v for k, v in _CLEAN_ATTESTATIONS.items() if k != field}
            self.assertFalse(evaluator.evaluate_tribunal("c", partial).all_passed, field)

    def test_04_run_demo_use_case(self) -> None:
        demo_runner = UnifiedPfpDemoRunner()
        use_case = RunDemoUseCase(catalog=self.storage, runner=demo_runner)

        # Single demo
        single_res = use_case.run_by_id("demo_000")
        self.assertTrue(single_res.is_ok)
        self.assertTrue(single_res.unwrap().all_passed)

        # All demos
        all_res = use_case.run_all()
        self.assertTrue(all_res.is_ok)
        receipts = all_res.unwrap()
        self.assertEqual(len(receipts), 6)
        historical=next(r for r in receipts if r.demo_id=="demo_002")
        self.assertFalse(historical.all_passed)
        self.assertTrue(any("HISTORICAL_SOURCE_BYTES_UNAVAILABLE" in (c.error_message or "")
                            for c in historical.checks))
        retired = next(r for r in receipts if r.demo_id == "demo_003")
        self.assertFalse(retired.all_passed)
        self.assertEqual(retired.terminal_status, "Refused")
        self.assertTrue(all(not check.passed for check in retired.checks))
        self.assertTrue(all(r.all_passed for r in receipts if r.demo_id not in {"demo_002", "demo_003"}))

    def test_05_verify_contracts_use_case(self) -> None:
        use_case = VerifyPfpContractsUseCase(storage=self.storage)
        res = use_case.verify_all_normal_forms()
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.HOST_VERIFIER_UNAVAILABLE)

    def test_06_rewrite_prompt_use_case(self) -> None:
        use_case = RewritePromptUseCase()
        seg = Segment(role="task", boundary="<task>", text="Solve seed")
        bind = Binding(symbol="d0", target_role="task", description="boundary symbol")
        req = RewriteRequest(
            request_id="req_01",
            raw_prompt="Initial text",
            segments=[seg],
            bindings=[bind],
        )
        res = use_case.rewrite(req)
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertEqual(receipt.request_id, "req_01")
        self.assertEqual(receipt.segments_count, 1)


if __name__ == "__main__":
    unittest.main()
