from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceFreshnessState(str, Enum):
    FRESH = "FRESH"
    STALE_AFTER_REBASE = "STALE_AFTER_REBASE"
    STALE_AFTER_HEAD_CHANGE = "STALE_AFTER_HEAD_CHANGE"
    NOT_RERUN_AFTER_RECONCILIATION = "NOT_RERUN_AFTER_RECONCILIATION"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True, slots=True)
class EvidenceFreshnessAssessment:
    obligation_id: str
    state: EvidenceFreshnessState
    bound_head: str
    observed_head: str
    is_usable_for_gate: bool
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EvidenceFreshnessAssessment)
        return (
            self.obligation_id == other.obligation_id
            and self.state == other.state
            and self.bound_head == other.bound_head
            and self.observed_head == other.observed_head
            and self.is_usable_for_gate == other.is_usable_for_gate
            and self.reason == other.reason
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "state": self.state.value,
            "bound_head": self.bound_head,
            "observed_head": self.observed_head,
            "is_usable_for_gate": self.is_usable_for_gate,
            "reason": self.reason,
        }


def assess_evidence_freshness(
    obligation_id: str,
    bound_head: str,
    observed_head: str,
    *,
    is_reconciled: bool = False,
    is_rebased: bool = False,
) -> EvidenceFreshnessAssessment:
    """Evaluates evidence freshness upon rebind or head observation.
    
    Guarantees that old test passes cannot float across unverified head movements.
    """
    if is_reconciled:
        return EvidenceFreshnessAssessment(
            obligation_id=obligation_id,
            state=EvidenceFreshnessState.NOT_RERUN_AFTER_RECONCILIATION,
            bound_head=bound_head,
            observed_head=observed_head,
            is_usable_for_gate=False,
            reason="Tree was modified by exact-blob reconciliation; tests have not been rerun on reconciled tree",
        )

    if is_rebased:
        return EvidenceFreshnessAssessment(
            obligation_id=obligation_id,
            state=EvidenceFreshnessState.STALE_AFTER_REBASE,
            bound_head=bound_head,
            observed_head=observed_head,
            is_usable_for_gate=False,
            reason="Branch base was advanced by rebase; obligations require re-verification",
        )

    if bound_head != observed_head:
        return EvidenceFreshnessAssessment(
            obligation_id=obligation_id,
            state=EvidenceFreshnessState.STALE_AFTER_HEAD_CHANGE,
            bound_head=bound_head,
            observed_head=observed_head,
            is_usable_for_gate=False,
            reason=f"Observed HEAD '{observed_head}' differs from receipt bound HEAD '{bound_head}'",
        )

    return EvidenceFreshnessAssessment(
        obligation_id=obligation_id,
        state=EvidenceFreshnessState.FRESH,
        bound_head=bound_head,
        observed_head=observed_head,
        is_usable_for_gate=True,
        reason="Evidence is byte-exact and matches observed HEAD",
    )
