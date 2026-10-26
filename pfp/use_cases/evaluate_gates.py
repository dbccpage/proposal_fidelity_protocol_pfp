"""Evaluate Woland Tribunal Gates Use Case.

Zero infrastructure imports; depends strictly on domain ports, aggregates, and value objects.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.contracts.gates import GateReceipt, WolandGateId
from ..domain.kernel.ports import PfpGateEvaluatorPort
from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.value_objects.identifiers import PilotId, RequestId


class EvaluateWolandGatesUseCase:
    """Evaluates candidate proposals and pilots against the Woland Tribunal 13 gates."""

    def __init__(self, gate_evaluator: PfpGateEvaluatorPort) -> None:
        self.gate_evaluator = gate_evaluator

    def evaluate(
        self,
        candidate_id: Union[str, PilotId, RequestId],
        candidate_state: Dict[str, Any],
    ) -> Result[GateReceipt, DomainError]:
        """Evaluate candidate state against tribunal gates."""
        try:
            cid = str(candidate_id.value if isinstance(candidate_id, (PilotId, RequestId)) else candidate_id)
            receipt = self.gate_evaluator.evaluate_tribunal(cid, candidate_state)
            return Result.ok(receipt)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.GATE_REJECTED,
                    message=f"Tribunal evaluation failed: {str(exc)}",
                )
            )

    def evaluate_pilot(
        self,
        pilot: PilotAggregate,
        gate_id: Optional[WolandGateId] = None,
        execution_receipt: Optional[Dict[str, Any]] = None,
    ) -> Result[GateReceipt, DomainError]:
        """Evaluate a PilotAggregate directly against tribunal gates."""
        if not isinstance(pilot, PilotAggregate):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected PilotAggregate, received {type(pilot).__name__}",
                )
            )
        candidate_id = getattr(pilot, "target", "") or pilot.pilot_id.value
        candidate_state = dict(execution_receipt) if execution_receipt else {
            "pilot_id": pilot.pilot_id.value,
            "demo_id": candidate_id,
            "status": pilot.trial_status.value,
            "checker_id": pilot.checker_id.value,
            "seed_prompt": pilot.seed_prompt,
        }
        if "demo_id" not in candidate_state:
            candidate_state["demo_id"] = candidate_id
        return self.evaluate(candidate_id, candidate_state)
