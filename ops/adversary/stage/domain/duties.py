"""Duty separation and actor responsibility tracking for the Adversary stage.

Enforces F-BIO-01: Propose actor may not hold Adjudicate for the same subject.
Two seats backed by the same model lineage count as one actor for this rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DutyType(str, Enum):
    PROPOSE = "Propose"
    REALIZE = "Realize"
    ADJUDICATE = "Adjudicate"


@dataclass(frozen=True, slots=True)
class ActorDutyReceiptV1:
    actor_id: str
    model_lineage_digest: str
    duty: DutyType
    subject_digest: str
    run_id: str
    authority_effect: str = "None"


class DutyValidatorV1:
    def __init__(self) -> None:
        # Map of subject_digest -> set of (actor_id, model_lineage_digest, duty)
        self._registered_duties: list[ActorDutyReceiptV1] = []

    def register_duty(self, receipt: ActorDutyReceiptV1) -> None:
        self.validate_duty_assignment(receipt)
        self._registered_duties.append(receipt)

    def validate_duty_assignment(self, receipt: ActorDutyReceiptV1) -> bool:
        """Validate that Propose and Adjudicate are held by disjoint actor lineages for a given subject."""
        for existing in self._registered_duties:
            if existing.subject_digest == receipt.subject_digest and existing.run_id == receipt.run_id:
                # Same actor or same model lineage
                same_actor_or_lineage = (
                    existing.actor_id == receipt.actor_id
                    or existing.model_lineage_digest == receipt.model_lineage_digest
                )
                if same_actor_or_lineage:
                    # Check collision between Propose and Adjudicate
                    is_conflict = (
                        (existing.duty == DutyType.PROPOSE and receipt.duty == DutyType.ADJUDICATE)
                        or (existing.duty == DutyType.ADJUDICATE and receipt.duty == DutyType.PROPOSE)
                    )
                    if is_conflict:
                        raise PermissionError(
                            "ROLE_SEPARATION_REQUIRED: Actor or model lineage holding Propose "
                            f"cannot hold Adjudicate for subject {receipt.subject_digest}"
                        )
        return True


__all__ = [
    "ActorDutyReceiptV1",
    "DutyType",
    "DutyValidatorV1",
]
