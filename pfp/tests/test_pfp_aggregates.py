"""Unit Tests for PFP Domain Aggregates and Invariant Boundaries.

AuthorityEffect: None.
Verifies:
1. PilotAggregate invariant validation (INV_PILOT_01, INV_PILOT_02, INV_PILOT_03).
2. SpanPartitionAggregate continuity and coverage validation.
3. CycleBalanceQuartetAggregate digest binding validation.
"""

from __future__ import annotations

import unittest

from omega_engine_pfp.domain.aggregates.cycle_balance_aggregate import CycleBalanceQuartetAggregate
from omega_engine_pfp.domain.aggregates.pilot_aggregate import PilotAggregate
from omega_engine_pfp.domain.aggregates.rewriting_aggregate import SpanPartitionAggregate
from omega_engine_pfp.domain.value_objects.numerics import BoundedTemperature
from omega_engine_pfp.domain.value_objects.topology import ByteSpanVO
from omega_engine_pfp.domain.value_objects.identifiers import CheckerIdVO
from omega_engine_pfp.domain.value_objects.numerics import DifficultyRung
from omega_engine_pfp.domain.value_objects.taxonomy import EvaluationStatusVO
from omega_engine_pfp.domain.value_objects.numerics import MicroUsdSpend
from omega_engine_pfp.domain.value_objects.identifiers import PilotId
from omega_engine_pfp.domain.value_objects.identifiers import PromptId
from omega_engine_pfp.domain.value_objects.identifiers import RequestId
from omega_engine_pfp.domain.value_objects.identifiers import Sha256Digest
from omega_engine_pfp.domain.value_objects.taxonomy import SpanRoleVO
from omega_engine_pfp.domain.value_objects.taxonomy import TaskFamilyVO
from omega_engine_pfp.domain.value_objects.taxonomy import TrialStatusVO


class TestPilotAggregateInvariants(unittest.TestCase):
    """Test consistency invariants on PilotAggregate."""

    def setUp(self) -> None:
        self.pilot_id = PilotId("pilot_0000001")
        self.prompt_id = PromptId("prompt_0000001")
        self.request_id = RequestId("req-001")
        self.rung = DifficultyRung(1)
        self.checker = CheckerIdVO("PFP-01-EXACT-LINALG")
        self.family = TaskFamilyVO("linear_algebra")
        self.spend = MicroUsdSpend(0)
        self.temp = BoundedTemperature(0.0)

    def test_valid_creation(self) -> None:
        agg = PilotAggregate(
            pilot_id=self.pilot_id,
            prompt_id=self.prompt_id,
            request_id=self.request_id,
            difficulty_rung=self.rung,
            checker_id=self.checker,
            task_family=self.family,
            target_spend=self.spend,
            temperature=self.temp,
            seed_prompt="Compute the rank of matrix A.",
            expected_answer=2,
        )
        self.assertFalse(agg.is_completed)
        self.assertFalse(agg.is_accepted)

    def test_inv_pilot_02_completed_requires_evidence(self) -> None:
        agg = PilotAggregate(
            pilot_id=self.pilot_id,
            prompt_id=self.prompt_id,
            request_id=self.request_id,
            difficulty_rung=self.rung,
            checker_id=self.checker,
            task_family=self.family,
            target_spend=self.spend,
            temperature=self.temp,
            seed_prompt="Compute the rank of matrix A.",
            expected_answer=2,
        )
        # Attempting to set COMPLETED without evidence must fail
        with self.assertRaises(ValueError) as ctx:
            agg.trial_status = TrialStatusVO("COMPLETED")
            agg.validate_invariants()
        self.assertIn("INV_PILOT_02", str(ctx.exception))

        # Recording execution with evidence succeeds
        agg.record_execution(evidence="Offline execution receipt sha256:abc")
        self.assertTrue(agg.is_completed)

    def test_inv_pilot_03_accepted_requires_matching_answer(self) -> None:
        agg = PilotAggregate(
            pilot_id=self.pilot_id,
            prompt_id=self.prompt_id,
            request_id=self.request_id,
            difficulty_rung=self.rung,
            checker_id=self.checker,
            task_family=self.family,
            target_spend=self.spend,
            temperature=self.temp,
            seed_prompt="Compute the rank of matrix A.",
            expected_answer=2,
        )
        agg.record_execution(evidence="receipt_valid")

        # Wrong answer with ACCEPTED status must fail
        with self.assertRaises(ValueError) as ctx:
            agg.evaluate_result(answer=3, status=EvaluationStatusVO("ACCEPTED"))
        self.assertIn("INV_PILOT_03", str(ctx.exception))

        # Correct answer with ACCEPTED status succeeds
        agg.evaluate_result(answer=2, status=EvaluationStatusVO("ACCEPTED"))
        self.assertTrue(agg.is_accepted)


class TestSpanPartitionAggregateInvariants(unittest.TestCase):
    """Test continuity invariants on SpanPartitionAggregate."""

    def test_valid_partition(self) -> None:
        spans = [
            (ByteSpanVO(0, 10), SpanRoleVO("PREAMBLE")),
            (ByteSpanVO(10, 30), SpanRoleVO("STIMULUS")),
            (ByteSpanVO(30, 45), SpanRoleVO("EPILOGUE")),
        ]
        agg = SpanPartitionAggregate.from_pairs(spans, total_length=45)
        self.assertEqual(len(agg.partitions), 3)

    def test_discontinuous_partition_rejected(self) -> None:
        spans = [
            (ByteSpanVO(0, 10), SpanRoleVO("PREAMBLE")),
            (ByteSpanVO(15, 30), SpanRoleVO("STIMULUS")),  # Gap between 10 and 15
        ]
        with self.assertRaises(ValueError) as ctx:
            SpanPartitionAggregate.from_pairs(spans, total_length=30)
        self.assertIn("Discontinuous partition", str(ctx.exception))

    def test_not_starting_at_zero_rejected(self) -> None:
        spans = [
            (ByteSpanVO(5, 30), SpanRoleVO("STIMULUS")),
        ]
        with self.assertRaises(ValueError) as ctx:
            SpanPartitionAggregate.from_pairs(spans, total_length=30)
        self.assertIn("First span must start at 0", str(ctx.exception))


class TestCycleBalanceQuartetAggregateInvariants(unittest.TestCase):
    """Test cryptographic digest binding on CycleBalanceQuartetAggregate."""

    def test_valid_quartet_binding(self) -> None:
        p_digest = Sha256Digest("1" * 64)
        c_digest = Sha256Digest("2" * 64)
        v_digest = Sha256Digest("3" * 64)
        r_digest = Sha256Digest("2" * 64)

        quartet = CycleBalanceQuartetAggregate(
            problem_digest=p_digest,
            candidate_digest=c_digest,
            candidate_problem_digest=p_digest,
            verifier_digest=v_digest,
            receipt_candidate_digest=r_digest,
            is_verified=True,
        )
        self.assertTrue(quartet.is_verified)

    def test_candidate_mismatch_rejected(self) -> None:
        p_digest = Sha256Digest("1" * 64)
        c_digest = Sha256Digest("2" * 64)
        wrong_p_digest = Sha256Digest("4" * 64)
        v_digest = Sha256Digest("3" * 64)

        with self.assertRaises(ValueError) as ctx:
            CycleBalanceQuartetAggregate(
                problem_digest=p_digest,
                candidate_digest=c_digest,
                candidate_problem_digest=wrong_p_digest,
                verifier_digest=v_digest,
            )
        self.assertIn("INV_CB_01 violation", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
