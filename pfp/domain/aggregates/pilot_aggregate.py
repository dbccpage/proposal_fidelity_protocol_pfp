"""Pilot Aggregate Root governing stimulus, evaluation, and lifecycle consistency.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional

from omega_engine_pfp.domain.types.pilot_response import PilotResponse
from omega_engine_pfp.domain.value_objects.numerics import BoundedTemperature
from omega_engine_pfp.domain.value_objects.identifiers import CheckerIdVO
from omega_engine_pfp.domain.value_objects.numerics import DifficultyRung
from omega_engine_pfp.domain.value_objects.taxonomy import EvaluationStatusVO
from omega_engine_pfp.domain.value_objects.numerics import MicroUsdSpend
from omega_engine_pfp.domain.value_objects.identifiers import PilotId
from omega_engine_pfp.domain.value_objects.identifiers import PromptId
from omega_engine_pfp.domain.value_objects.identifiers import RequestId
from omega_engine_pfp.domain.value_objects.numerics import StageNumber
from omega_engine_pfp.domain.value_objects.taxonomy import TaskFamilyVO
from omega_engine_pfp.domain.value_objects.taxonomy import TrialStatusVO
from .base import AggregateRoot

_UNCHANGED = object()


@dataclass
class PilotAggregate(AggregateRoot):
    """Aggregate Root managing end-to-end consistency of a PFP Pilot.

    Invariants:
    1. INV_PILOT_01: Identity consistency across pilot coordinates and stimulus.
    2. INV_PILOT_02: A COMPLETED or PASS trial requires non-empty execution evidence.
    3. INV_PILOT_03: An ACCEPTED evaluation requires an observed answer matching
       expected ground truth, including the existing checker's representation rules.
    """

    pilot_id: PilotId
    prompt_id: PromptId
    request_id: RequestId
    difficulty_rung: DifficultyRung
    checker_id: CheckerIdVO
    task_family: TaskFamilyVO
    target_spend: MicroUsdSpend
    temperature: BoundedTemperature
    seed_prompt: str
    expected_answer: Any
    expected_outcome: str = "ACCEPTED"
    trial_status: TrialStatusVO = TrialStatusVO("NOT_RUN")
    evaluation_status: EvaluationStatusVO = EvaluationStatusVO("NOT_RUN")
    extracted_answer: Any = None
    execution_receipt_evidence: str = ""
    target: str = "demo_000"
    completed_stages_count: StageNumber = StageNumber(1)
    response: Optional[PilotResponse] = None

    def __post_init__(self) -> None:
        self.validate_invariants()

    def with_transition(
        self,
        trial_status: Optional[TrialStatusVO] = None,
        evaluation_status: Optional[EvaluationStatusVO] = None,
        extracted_answer: Any = _UNCHANGED,
        execution_receipt_evidence: Optional[str] = None,
        **kwargs: Any,
    ) -> PilotAggregate:
        """Return a validated copy; omitted answer retains, explicit None clears it."""
        new_agg = deepcopy(self)
        if trial_status is not None:
            new_agg.trial_status = trial_status
        if evaluation_status is not None:
            new_agg.evaluation_status = evaluation_status
        if extracted_answer is not _UNCHANGED:
            new_agg.extracted_answer = extracted_answer
        if execution_receipt_evidence is not None:
            new_agg.execution_receipt_evidence = execution_receipt_evidence
        elif "raw_response" in kwargs and kwargs["raw_response"]:
            new_agg.execution_receipt_evidence = str(kwargs["raw_response"])
        elif "reason" in kwargs and kwargs["reason"]:
            new_agg.execution_receipt_evidence = str(kwargs["reason"])

        new_agg.validate_invariants()
        return new_agg

    def validate_invariants(self) -> None:
        """Validate aggregate consistency boundaries."""
        self.validate_response_binding()
        if not isinstance(self.seed_prompt, str) or not self.seed_prompt.strip():
            raise ValueError("PilotAggregate requires non-empty seed_prompt")

        # Evidence must be supplied or retained; this does not authenticate its origin.
        if self.trial_status.value in {"COMPLETED", "PASS"} and (
            not isinstance(self.execution_receipt_evidence, str)
            or not self.execution_receipt_evidence.strip()
        ):
            raise ValueError("INV_PILOT_02 violation: COMPLETED/PASS trial must have execution receipt evidence")

        # INV_PILOT_03: ACCEPTED status requires exact answer match
        if self.evaluation_status.value == "ACCEPTED":
            if self.extracted_answer is None or not self._answer_matches():
                raise ValueError(
                    f"INV_PILOT_03 violation: ACCEPTED status with mismatch: "
                    f"extracted={self.extracted_answer!r} != expected={self.expected_answer!r}"
                )

    def validate_response_binding(self) -> None:
        """Bind retained response identifiers without trusting its recorded verdict."""
        if self.response is None:
            return
        if not isinstance(self.response, PilotResponse):
            raise ValueError("INV_PILOT_01 violation: response must be a PilotResponse")
        if (
            self.response.pilot_id != self.pilot_id.value
            or self.response.request_id != self.request_id.value
            or self.response.evaluation.checker_id != self.checker_id.value
        ):
            raise ValueError("INV_PILOT_01 violation: response pilot/request/checker binding mismatch")

    def _answer_matches(self) -> bool:
        if self.extracted_answer == self.expected_answer:
            return True
        from ..pilots.fail_closed_gate import FailClosedRefusalGate

        checked = FailClosedRefusalGate.evaluate_candidate_payload(
            checker_id=self.checker_id.value,
            expected_answer=self.expected_answer,
            payload=self.extracted_answer,
        )
        return checked.is_accepted and checked.extracted_answer == self.extracted_answer

    def record_execution(self, evidence: str, trial_status: TrialStatusVO = TrialStatusVO("COMPLETED")) -> None:
        """Record execution outcome, enforcing receipt evidence invariant."""
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Cannot record execution without evidence string")
        candidate = deepcopy(self)
        candidate.execution_receipt_evidence = evidence
        candidate.trial_status = trial_status
        candidate.validate_invariants()
        self.execution_receipt_evidence = candidate.execution_receipt_evidence
        self.trial_status = candidate.trial_status

    def evaluate_result(self, answer: Any, status: EvaluationStatusVO) -> None:
        """Evaluate stimulus response against ground truth."""
        candidate = deepcopy(self)
        candidate.extracted_answer = answer
        candidate.evaluation_status = status
        candidate.validate_invariants()
        self.extracted_answer = candidate.extracted_answer
        self.evaluation_status = candidate.evaluation_status

    @property
    def is_completed(self) -> bool:
        return self.trial_status.value == "COMPLETED"

    @property
    def is_accepted(self) -> bool:
        return self.evaluation_status.value == "ACCEPTED"
