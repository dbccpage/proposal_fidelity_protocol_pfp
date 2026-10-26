"""Provisional promotion engine and observation support policy domain layer (U16).

AuthorityEffect: None.
Pure domain logic: enforces support >= 3 under ObservationSupportPolicyV1
using exact maximum independent set (MIS) branch-and-bound over host-bound
correlation keys, with strict causal duplicate collapse and rejection of
propagated references.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .ports import ProvisionalPromotionPolicyPort


@dataclass(frozen=True)
class PromotionResult:
    """Result of candidate promotion eligibility evaluation."""

    candidate_id: str
    new_custody: str
    review_queued: bool
    has_admission_record: bool = False
    enforcement_authorized: bool = False
    authority_effect: str = "None"


class ProvisionalPromotionEngineV1:
    """Evaluates candidate support for provisional promotion and queues review."""

    def __init__(self, *, policy: ProvisionalPromotionPolicyPort | None = None) -> None:
        self._policy = policy

    def promote_candidate_if_eligible(
        self, candidate_id: str, support_count: int | str, diagnostic_scope: list[str]
    ) -> PromotionResult:
        if self._policy is not None:
            return self._policy.promote(candidate_id, support_count, diagnostic_scope)
        if type(candidate_id) is not str:
            raise ValueError("candidate_id must be a string")
        placeholder = (
            candidate_id.startswith("defect:defect:")
            or "placeholder" in candidate_id.lower()
        )
        eligible = isinstance(support_count, int) and not isinstance(support_count, bool)
        custody = (
            "Placeholder refuses promotion"
            if placeholder
            else "Provisional"
            if eligible and support_count >= 3
            else "Candidate"
        )
        return PromotionResult(
            candidate_id=candidate_id,
            new_custody=custody,
            review_queued=custody == "Provisional",
        )


@dataclass(frozen=True)
class RawObservationV1:
    """Raw observation with host-bound correlation keys."""

    occurrence_id: str
    generating_model_id: str = ""
    scaffold_digest: str = ""
    precedent_set_digest: str = ""
    inheritance_root: str = ""
    is_propagated_reference: bool = False


@dataclass(frozen=True)
class SupportResult:
    """Support calculation result under graph independent set policy."""

    support_count: int | str
    eligible_for_provisional: bool
    authority_effect: str = "None"


class ObservationSupportPolicyV1:
    """Computes support count as the maximum independent set of the observation conflict graph."""

    def __init__(self, *, policy: ProvisionalPromotionPolicyPort | None = None) -> None:
        self._policy = policy

    def register_observation(self, obs: RawObservationV1) -> None:
        if self._policy is not None:
            self._policy.register_observation(obs)
            return
        _reject_propagated((obs,))

    def compute_support(self, observations: Sequence[RawObservationV1]) -> SupportResult:
        if self._policy is not None:
            return self._policy.compute_support(observations)
        checked = tuple(observations)
        _reject_propagated(checked)
        nodes = _deduplicated(checked)
        if len(nodes) > 32:
            return SupportResult(
                support_count="SUPPORT_BUDGET_EXHAUSTED at >32 deduplicated observations",
                eligible_for_provisional=False,
            )
        support_count = _maximum_independent_set(nodes)
        return SupportResult(
            support_count=support_count,
            eligible_for_provisional=support_count >= 3,
        )


def _reject_propagated(observations: Sequence[RawObservationV1]) -> None:
    if any(observation.is_propagated_reference for observation in observations):
        raise ValueError(
            "PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION: "
            "Inherited or propagated references cannot count toward support"
        )


def _correlation_keys(observation: RawObservationV1) -> tuple[str, str, str, str]:
    return (
        observation.generating_model_id,
        observation.scaffold_digest,
        observation.precedent_set_digest,
        observation.inheritance_root,
    )


def _deduplicated(
    observations: Sequence[RawObservationV1],
) -> tuple[RawObservationV1, ...]:
    occurrences: set[str] = set()
    keys_seen: set[tuple[str, str, str, str]] = set()
    nodes: list[RawObservationV1] = []
    for observation in observations:
        if observation.occurrence_id and observation.occurrence_id in occurrences:
            continue
        if observation.occurrence_id:
            occurrences.add(observation.occurrence_id)
        keys = _correlation_keys(observation)
        if keys in keys_seen:
            continue
        keys_seen.add(keys)
        nodes.append(observation)
    return tuple(nodes)


def _conflicts(left: RawObservationV1, right: RawObservationV1) -> bool:
    return any(
        left_key and left_key == right_key
        for left_key, right_key in zip(
            _correlation_keys(left), _correlation_keys(right), strict=True
        )
    )


def _maximum_independent_set(nodes: Sequence[RawObservationV1]) -> int:
    edges = tuple(
        sum(
            1 << other_index
            for other_index, other in enumerate(nodes)
            if node_index != other_index and _conflicts(node, other)
        )
        for node_index, node in enumerate(nodes)
    )

    def search(mask: int, count: int, best: int) -> int:
        if count + mask.bit_count() <= best:
            return best
        if mask == 0:
            return max(best, count)
        pivot = (mask & -mask).bit_length() - 1
        remainder = mask & ~(1 << pivot)
        with_pivot = search(remainder & ~edges[pivot], count + 1, best)
        return search(remainder, count, with_pivot)

    return search((1 << len(nodes)) - 1, 0, 0)


__all__ = [
    "ObservationSupportPolicyV1",
    "PromotionResult",
    "ProvisionalPromotionEngineV1",
    "RawObservationV1",
    "SupportResult",
]
