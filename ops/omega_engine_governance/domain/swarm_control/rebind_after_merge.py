from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from omega_engine_governance.domain.swarm_control.evidence_freshness_rebind import (
    EvidenceFreshnessAssessment,
    assess_evidence_freshness,
)


@dataclass(frozen=True, slots=True)
class CandidateRebindResult:
    candidate_id: str
    previous_epoch_head: str
    new_epoch_head: str
    invalidated_assessments: tuple[EvidenceFreshnessAssessment, ...]
    is_ready_for_land: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CandidateRebindResult)
        return (
            self.candidate_id == other.candidate_id
            and self.previous_epoch_head == other.previous_epoch_head
            and self.new_epoch_head == other.new_epoch_head
            and self.invalidated_assessments == other.invalidated_assessments
            and self.is_ready_for_land == other.is_ready_for_land
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "previous_epoch_head": self.previous_epoch_head,
            "new_epoch_head": self.new_epoch_head,
            "invalidated_assessments": [a.to_dict() for a in self.invalidated_assessments],
            "is_ready_for_land": self.is_ready_for_land,
        }


def rebind_candidate_to_main_epoch(
    candidate_id: str,
    previous_epoch_head: str,
    new_epoch_head: str,
    active_obligation_ids: Mapping[str, str],
) -> CandidateRebindResult:
    """Advances candidate base epoch to newly landed mainline head.
    
    Invalidates all prior test evidence assessments, blocking subsequent land licenses
    until fresh execution receipts are gathered.
    """
    invalidated: list[EvidenceFreshnessAssessment] = []
    for obl_id, bound_head in active_obligation_ids.items():
        assessment = assess_evidence_freshness(
            obligation_id=obl_id,
            bound_head=bound_head,
            observed_head=new_epoch_head,
            is_rebased=True,
        )
        invalidated.append(assessment)

    return CandidateRebindResult(
        candidate_id=candidate_id,
        previous_epoch_head=previous_epoch_head,
        new_epoch_head=new_epoch_head,
        invalidated_assessments=tuple(invalidated),
        is_ready_for_land=False,  # Must be re-tested on new epoch before license issuance
    )
