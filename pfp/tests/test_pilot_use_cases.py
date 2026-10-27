"""Tests for PFP Use Cases migrated to accept and return PilotAggregate and ValueObjects.

Verifies:
  1. EvaluatePilotUseCase accepts PilotAggregate and returns Result[PilotAggregate, DomainError].
  2. AssemblePromptUseCase accepts PilotAggregate, PilotId, StageNumber.
  3. EvaluateAdversaryGatesUseCase accepts PilotAggregate and PilotId.
  4. ExecuteStagePipelineUseCase accepts and returns typed PilotAggregate and PilotId.
  5. RewritePromptUseCase accepts PilotAggregate and SpanPartitionAggregate directly.
  6. RunDemoUseCase accepts PilotAggregate and PilotId directly.
  7. VerifyPfpContractsUseCase accepts PilotAggregate and NormalFormId directly.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from typing import Any, Dict, Mapping

from pfp.domain.aggregates.pilot_aggregate import PilotAggregate
from pfp.domain.aggregates.rewriting_aggregate import SpanPartitionAggregate
from pfp.domain.contracts.gates import AdversaryGateId
from pfp.domain.kernel.result import RefusalCode
from pfp.domain.prompts.prompts import PromptPacket
from pfp.domain.stages.stages import Stage5Response
from pfp.domain.value_objects.numerics import BoundedTemperature
from pfp.domain.value_objects.topology import ByteSpanVO
from pfp.domain.value_objects.identifiers import CheckerIdVO
from pfp.domain.value_objects.numerics import DifficultyRung
from pfp.domain.value_objects.taxonomy import EvaluationStatusVO
from pfp.domain.value_objects.numerics import MicroUsdSpend
from pfp.domain.value_objects.identifiers import NormalFormId
from pfp.domain.value_objects.identifiers import PilotId
from pfp.domain.value_objects.identifiers import PromptId
from pfp.domain.value_objects.identifiers import RequestId
from pfp.domain.value_objects.taxonomy import SpanRoleVO
from pfp.domain.value_objects.numerics import StageNumber
from pfp.domain.value_objects.taxonomy import TaskFamilyVO
from pfp.domain.value_objects.taxonomy import TrialStatusVO
from pfp.infrastructure.pilot_runners.pilot_dispatch import UnifiedPfpDemoRunner
from pfp.infrastructure.gate_evaluators import AdversaryTribunalGateEvaluator
from pfp.infrastructure.providers import OfflineDeterministicPfpProvider
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.use_cases.assemble_prompt import AssemblePromptUseCase
from pfp.use_cases.evaluate_gates import EvaluateAdversaryGatesUseCase
from pfp.use_cases.evaluate_pilot import EvaluatePilotUseCase
from pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase
from pfp.use_cases.rewrite_prompt import RewritePromptUseCase
from pfp.use_cases.run_demo import RunDemoUseCase
from pfp.use_cases.verify_contracts import VerifyPfpContractsUseCase


def _make_sample_pilot(
    pilot_id_hex: str = "a" * 64,
    eval_status: str = "ACCEPTED",
    target: str = "demo_000",
) -> PilotAggregate:
    extracted = "V={0,1}" if eval_status == "ACCEPTED" else None
    return PilotAggregate(
        pilot_id=PilotId(pilot_id_hex),
        prompt_id=PromptId("prompt_0000001"),
        request_id=RequestId("req-001"),
        difficulty_rung=DifficultyRung(1),
        checker_id=CheckerIdVO("PFP-01-EXACT-LINALG"),
        task_family=TaskFamilyVO("linear_algebra"),
        target_spend=MicroUsdSpend(0),
        temperature=BoundedTemperature(0.0),
        seed_prompt="Solve arithmetic problem V={0,1}",
        expected_answer="V={0,1}",
        extracted_answer=extracted,
        evaluation_status=EvaluationStatusVO(eval_status),
        target=target,
        expected_outcome="PASS",
        execution_receipt_evidence="Initial verified execution evidence",
    )


class _MockHostVerifier:
    def __init__(self, verdict: str = "PASS", exact: bool = True) -> None:
        self.verdict = verdict
        self.exact = exact

    def verify(self, demo_id: str, prior_responses: Mapping[int, Dict[str, Any]]) -> Stage5Response:
        return Stage5Response(
            demo_id=demo_id,
            should_continue=True,
            host_verdict=self.verdict,
            exact_checks_passed=self.exact,
            surviving_candidates=[prior_responses[4]["candidate_id"]] if self.verdict == "PASS" else [],
        )


class TestPilotUseCasesMigration(unittest.TestCase):
    """Test use case methods accepting and returning PilotAggregate and ValueObjects."""

    def setUp(self) -> None:
        self.storage = PfpFileSystemStorageAdapter()
        self.provider = OfflineDeterministicPfpProvider()
        self.gate_evaluator = AdversaryTribunalGateEvaluator()
        self.runner = UnifiedPfpDemoRunner()

    def test_evaluate_pilot_use_case_with_pilot_aggregate(self) -> None:
        use_case = EvaluatePilotUseCase(
            storage=self.storage,
            gate_evaluator=self.gate_evaluator,
            runner=self.runner,
        )
        pilot = _make_sample_pilot(eval_status="ACCEPTED")
        res = use_case.execute(pilot)
        self.assertTrue(res.is_ok)
        result_pilot = res.unwrap()
        self.assertIsInstance(result_pilot, PilotAggregate)
        self.assertEqual(result_pilot.pilot_id, pilot.pilot_id)
        self.assertEqual(result_pilot.trial_status, TrialStatusVO("NOT_RUN"))
        self.assertEqual(result_pilot.evaluation_status, EvaluationStatusVO("NOT_RUN"))
        self.assertIsNone(result_pilot.extracted_answer)

    def test_clean_prompt_cannot_supply_a_missing_proposal(self) -> None:
        pilot = _make_sample_pilot()
        result = EvaluatePilotUseCase().execute(pilot).unwrap()
        self.assertEqual(result.trial_status, TrialStatusVO("NOT_RUN"))
        self.assertIsNone(result.extracted_answer)
        self.assertIn("No candidate payload", result.execution_receipt_evidence)

    def test_assemble_prompt_use_case_with_pilot_aggregate(self) -> None:
        use_case = AssemblePromptUseCase(storage=self.storage)
        pilot = _make_sample_pilot()
        res = use_case.assemble_pilot(pilot, stage=StageNumber(1))
        self.assertTrue(res.is_ok)
        packet = res.unwrap()
        self.assertIsInstance(packet, PromptPacket)
        self.assertEqual(packet.demo_id, pilot.target)
        self.assertEqual(packet.stage, 1)

    def test_assemble_prompt_use_case_with_value_objects(self) -> None:
        use_case = AssemblePromptUseCase(storage=self.storage)
        p_id = PilotId("b" * 64)
        s_num = StageNumber(2)
        res = use_case.assemble(demo_id=p_id, stage=s_num, seed_data={"seed": "123"})
        self.assertTrue(res.is_ok)
        packet = res.unwrap()
        self.assertEqual(packet.demo_id, p_id.value)
        self.assertEqual(packet.stage, 2)

    def test_evaluate_adversary_gates_use_case_with_pilot_aggregate(self) -> None:
        use_case = EvaluateAdversaryGatesUseCase(self.gate_evaluator)
        pilot = _make_sample_pilot()
        receipt_dict = {
            "demo_id": pilot.target,
            "gate_receipts": {},
            "all_checks_passed": True,
            "authority_effect": "None",
        }
        res = use_case.evaluate_pilot(
            pilot=pilot,
            gate_id=AdversaryGateId.CARRIER_GROUNDING,
            execution_receipt=receipt_dict,
        )
        self.assertTrue(res.is_ok)
        gate_receipt = res.unwrap()
        self.assertEqual(gate_receipt.demo_id, pilot.target)

    def test_execute_stage_pipeline_use_case_with_pilot_aggregate(self) -> None:
        use_case = ExecuteStagePipelineUseCase(
            storage=self.storage,
            provider=self.provider,
            catalog=self.storage,
            host_verifier=_MockHostVerifier(),
        )
        pilot = _make_sample_pilot(target="demo_000")
        res = use_case.execute_pilot(pilot)
        self.assertTrue(res.is_ok)
        updated_pilot = res.unwrap()
        self.assertIsInstance(updated_pilot, PilotAggregate)
        self.assertEqual(updated_pilot.pilot_id, pilot.pilot_id)
        self.assertGreaterEqual(updated_pilot.completed_stages_count.value, 1)

    def test_execute_stage_pipeline_use_case_receipt_value_objects(self) -> None:
        use_case = ExecuteStagePipelineUseCase(
            storage=self.storage,
            provider=self.provider,
            catalog=self.storage,
            host_verifier=_MockHostVerifier(),
        )
        p_id = PilotId("demo_000")
        res = use_case.execute(demo_id=p_id)
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertEqual(receipt.pilot_id_vo, p_id)
        self.assertIsInstance(receipt.completed_stages_vo, StageNumber)

    def test_stopped_pipeline_cannot_mark_pilot_pass(self) -> None:
        class StopsAtHost(_MockHostVerifier):
            def verify(self, demo_id, prior_responses):
                return (
                    super()
                    .verify(demo_id, prior_responses)
                    .model_copy(update={"should_continue": False})
                )

        use_case = ExecuteStagePipelineUseCase(
            storage=self.storage,
            provider=self.provider,
            catalog=self.storage,
            host_verifier=StopsAtHost(),
        )
        pilot = _make_sample_pilot(target="demo_000")
        result = use_case.execute_pilot(pilot).unwrap()
        self.assertEqual(result.completed_stages_count.value, 5)
        self.assertEqual(result.trial_status, TrialStatusVO("NOT_RUN"))

    def test_rewrite_prompt_use_case_with_pilot_aggregate(self) -> None:
        use_case = RewritePromptUseCase()
        pilot = _make_sample_pilot()
        res = use_case.rewrite(pilot)
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertEqual(receipt.request_id, pilot.pilot_id.value)
        self.assertEqual(receipt.root_boundary, "<root>boundary_tree_v1</root>")

    def test_rewrite_prompt_use_case_with_span_partition_aggregate(self) -> None:
        use_case = RewritePromptUseCase()
        spans = [
            (ByteSpanVO(0, 10), SpanRoleVO("PREAMBLE")),
            (ByteSpanVO(10, 30), SpanRoleVO("STIMULUS")),
            (ByteSpanVO(30, 45), SpanRoleVO("EPILOGUE")),
        ]
        partition = SpanPartitionAggregate.from_pairs(spans, total_length=45)
        res = use_case.rewrite(partition)
        self.assertTrue(res.is_ok)
        receipt = res.unwrap()
        self.assertEqual(receipt.root_boundary, "<root>partition_boundary_v1</root>")
        self.assertEqual(receipt.segments_count, 3)

    def test_run_demo_use_case_with_pilot_aggregate(self) -> None:
        use_case = RunDemoUseCase(catalog=self.storage, runner=self.runner)
        pilot = _make_sample_pilot(target="demo_000")
        res = use_case.run_pilot(pilot)
        self.assertTrue(res.is_ok)
        updated_pilot = res.unwrap()
        self.assertIsInstance(updated_pilot, PilotAggregate)
        self.assertEqual(updated_pilot.pilot_id, pilot.pilot_id)

    def test_verify_contracts_use_case_with_pilot_aggregate(self) -> None:
        use_case = VerifyPfpContractsUseCase(storage=self.storage)
        pilot = _make_sample_pilot()
        res = use_case.verify_pilot(pilot)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.HOST_VERIFIER_UNAVAILABLE)
        self.assertEqual(pilot.trial_status, TrialStatusVO("NOT_RUN"))
        self.assertEqual(pilot.execution_receipt_evidence, "Initial verified execution evidence")

    def test_verify_contracts_use_case_with_normal_form_id(self) -> None:
        use_case = VerifyPfpContractsUseCase(storage=self.storage)
        nf_id = NormalFormId("nf.coda.eqnf")
        res = use_case.verify_normal_form(nf_id)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, RefusalCode.HOST_VERIFIER_UNAVAILABLE)
        self.assertIn(nf_id.value, res.unwrap_err().message)


if __name__ == "__main__":
    unittest.main()
