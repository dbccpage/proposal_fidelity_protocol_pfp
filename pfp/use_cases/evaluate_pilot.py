"""Deep Pilot Evaluation Use Case for PFP.

Orchestrates fail-closed evaluation, invariant bounds checking, and state transitions
directly on PilotAggregate instances.
Zero infrastructure imports; depends strictly on domain aggregates, value objects, and ports.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.kernel.ports import PfpGateEvaluatorPort, PfpStoragePort
from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.pilots.fail_closed_gate import FailClosedRefusalGate, GateEvaluationResult
from ..domain.value_objects.taxonomy import EvaluationStatusVO, TrialStatusVO
from .evaluate_pilot_suite import sanitize_raw_reply


class EvaluatePilotUseCase:
    """Deep module orchestrating pilot evaluation and state transition.

    Hides internal token audit, candidate payload grading, invariant enforcement,
    and history recording behind a minimal interface:
        execute(pilot: PilotAggregate) -> Result[PilotAggregate, DomainError]
    """

    def __init__(
        self,
        storage: Optional[PfpStoragePort] = None,
        gate_evaluator: Optional[PfpGateEvaluatorPort] = None,
        runner: Optional[Any] = None,
    ) -> None:
        self.storage = storage
        self.gate_evaluator = gate_evaluator
        self.runner = runner

    def execute(self, pilot: PilotAggregate) -> Result[PilotAggregate, DomainError]:
        """Evaluate a PilotAggregate, audit prompt, verify gate invariants, and return updated aggregate."""
        if not isinstance(pilot, PilotAggregate):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected PilotAggregate instance, received {type(pilot).__name__}",
                )
            )

        try:
            try:
                pilot.validate_response_binding()
            except ValueError as exc:
                return Result.err(
                    DomainError(code=RefusalCode.SCHEMA_VIOLATION, message=str(exc))
                )

            # 1. Audit prompt text for corruption, hype, or problem-bound obstruction
            prompt_text = getattr(pilot, "seed_prompt", "") or (
                pilot.ingress.prompt_text if hasattr(pilot, "ingress") else ""
            )
            checker_id = pilot.checker_id.value if hasattr(pilot, "checker_id") else (
                pilot.host_gate.checker_id if hasattr(pilot, "host_gate") else "PFP-01-EXACT-LINALG"
            )

            prompt_audit = FailClosedRefusalGate.audit_prompt_tokens(prompt_text, checker_id)
            if prompt_audit is not None:
                eval_status, refusal_code, reason = prompt_audit
                status_str = eval_status.value if hasattr(eval_status, "value") else str(eval_status)
                refused_pilot = pilot.with_transition(
                    trial_status=TrialStatusVO("REFUSED"),
                    evaluation_status=EvaluationStatusVO(status_str if status_str in ("ACCEPTED", "WRONG_ANSWER", "FALSE_CERTAINTY", "MALFORMED", "NOT_RUN", "REFUSED") else "REFUSED"),
                    extracted_answer=None,
                    execution_receipt_evidence=f"Prompt token audit failed: {reason}",
                )
                return Result.ok(refused_pilot)

            # 2. Evaluate candidate payload if responses/receipts exist
            candidate_payload = None
            typed_candidate = False
            if pilot.response is not None:
                raw = pilot.response.raw_reply
                if raw is None or (isinstance(raw, str) and not raw.strip()):
                    return Result.ok(
                        pilot.with_transition(
                            trial_status=TrialStatusVO("NOT_RUN"),
                            evaluation_status=EvaluationStatusVO("NOT_RUN"),
                            extracted_answer=None,
                            execution_receipt_evidence="Typed response has no raw reply for evaluation",
                        )
                    )
                _, valid_json, _, candidate_payload = sanitize_raw_reply(raw)
                if not valid_json:
                    return Result.ok(
                        pilot.with_transition(
                            trial_status=TrialStatusVO("FAILED"),
                            evaluation_status=EvaluationStatusVO("MALFORMED"),
                            extracted_answer=None,
                            execution_receipt_evidence="Typed response raw reply is not valid strict JSON",
                        )
                    )
                typed_candidate = True
            elif hasattr(pilot, "execution_receipt") and pilot.execution_receipt and getattr(pilot.execution_receipt, "response_payload", None):
                candidate_payload = pilot.execution_receipt.response_payload.model_dump()
            elif hasattr(pilot, "observations") and pilot.observations:
                last_obs = pilot.observations[-1]
                if getattr(last_obs, "extracted_terms", None):
                    candidate_payload = last_obs.extracted_terms

            if typed_candidate or candidate_payload is not None:
                gate_result: GateEvaluationResult = FailClosedRefusalGate.evaluate_candidate_payload(
                    checker_id=checker_id,
                    expected_answer=pilot.expected_answer,
                    payload=candidate_payload,
                )
                if gate_result.is_accepted:
                    accepted_pilot = pilot.with_transition(
                        trial_status=TrialStatusVO("PASS"),
                        evaluation_status=EvaluationStatusVO("ACCEPTED"),
                        extracted_answer=gate_result.extracted_answer,
                        execution_receipt_evidence=gate_result.reason or "Evaluation checks passed ground truth",
                    )
                    return Result.ok(accepted_pilot)
                else:
                    status_val = gate_result.status.value if hasattr(gate_result.status, "value") else str(gate_result.status)
                    trial_val = "REFUSED" if status_val == "REFUSED" else "FAILED"
                    failed_pilot = pilot.with_transition(
                        trial_status=TrialStatusVO(trial_val),
                        evaluation_status=EvaluationStatusVO(status_val if status_val in ("ACCEPTED", "WRONG_ANSWER", "FALSE_CERTAINTY", "MALFORMED", "NOT_RUN", "REFUSED") else "MALFORMED"),
                        extracted_answer=gate_result.extracted_answer,
                        execution_receipt_evidence=gate_result.reason or "Evaluation check failed",
                    )
                    return Result.ok(failed_pilot)

            # A clean stimulus is not evidence of an executed or checked proposal.
            pending_pilot = pilot.with_transition(
                trial_status=TrialStatusVO("NOT_RUN"),
                evaluation_status=EvaluationStatusVO("NOT_RUN"),
                extracted_answer=None,
                execution_receipt_evidence="No candidate payload available for evaluation",
            )
            return Result.ok(pending_pilot)

        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.INFRASTRUCTURE_FAILURE,
                    message=f"Pilot evaluation encounter exception: {str(exc)}",
                )
            )

    def execute_batch(
        self, pilots: Sequence[PilotAggregate]
    ) -> Result[Tuple[PilotAggregate, ...], DomainError]:
        """Execute evaluation over a sequence of PilotAggregates with fail-closed short-circuiting."""
        evaluated: List[PilotAggregate] = []
        for p in pilots:
            res = self.execute(p)
            if res.is_err:
                return Result.err(res.unwrap_err())
            evaluated.append(res.unwrap())
        return Result.ok(tuple(evaluated))
