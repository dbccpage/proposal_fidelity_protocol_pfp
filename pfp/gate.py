"""Candidate evaluation gate and kinetic proofreading discipline for Symbol Game.

Enforces F-BIO-02: A candidate digest marked REJECTED cannot be re-evaluated
by the same frozen checker set in the same generation (STAGE_REENTRY_REFUSED).
Only INCONCLUSIVE may retry within the declared budget.
"""

from __future__ import annotations

from enum import Enum


class EvaluationDisposition(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class CandidateEvaluationGateV1:
    def __init__(self, frozen_checker_set_id: str) -> None:
        self.frozen_checker_set_id = frozen_checker_set_id
        # Map candidate_digest -> EvaluationDisposition
        self._history: dict[str, EvaluationDisposition] = {}

    def record_verdict(self, candidate_digest: str, disposition: EvaluationDisposition) -> None:
        self._history[candidate_digest] = disposition

    def evaluate_candidate(self, candidate_digest: str) -> EvaluationDisposition:
        prior_verdict = self._history.get(candidate_digest)
        if prior_verdict == EvaluationDisposition.REJECTED:
            raise PermissionError(
                f"STAGE_REENTRY_REFUSED: Candidate {candidate_digest} was marked REJECTED "
                f"by frozen checker set {self.frozen_checker_set_id} and cannot be re-evaluated"
            )
        return prior_verdict or EvaluationDisposition.INCONCLUSIVE


__all__ = ["CandidateEvaluationGateV1", "EvaluationDisposition"]
