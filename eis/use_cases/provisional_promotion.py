"""Thin DTO adapter for native observation support and review eligibility.

AuthorityEffect: None. Rust owns deduplication, correlation and exact search.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from omega_engine_epistemic_immune_system.infrastructure.native_domain import native_admission


@dataclass(frozen=True)
class PromotionResult:
    candidate_id: str
    new_custody: str
    review_queued: bool
    has_admission_record: bool = False
    enforcement_authorized: bool = False


class ProvisionalPromotionEngineV1:
    def promote_candidate_if_eligible(
        self, candidate_id: str, support_count: int | str, diagnostic_scope: list[str]
    ) -> PromotionResult:
        outcome = native_admission(
            "promote",
            candidate_id=candidate_id,
            support_count=support_count,
            diagnostic_scope=diagnostic_scope,
        )
        outcome.pop("authority_effect", None)
        return PromotionResult(**outcome)


@dataclass(frozen=True)
class RawObservationV1:
    occurrence_id: str
    generating_model_id: str = ""
    scaffold_digest: str = ""
    precedent_set_digest: str = ""
    inheritance_root: str = ""
    is_propagated_reference: bool = False


@dataclass(frozen=True)
class SupportResult:
    support_count: int | str
    eligible_for_provisional: bool
    authority_effect: str = "None"


class ObservationSupportPolicyV1:
    def register_observation(self, obs: RawObservationV1) -> None:
        native_admission("support", observations=[asdict(obs)])

    def compute_support(self, observations: Sequence[RawObservationV1]) -> SupportResult:
        return SupportResult(
            **native_admission("support", observations=[asdict(obs) for obs in observations])
        )


__all__ = [
    "ObservationSupportPolicyV1",
    "PromotionResult",
    "ProvisionalPromotionEngineV1",
    "RawObservationV1",
    "SupportResult",
]
