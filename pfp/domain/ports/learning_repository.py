"""Learning Repository Port Protocol."""

from __future__ import annotations

from typing import Protocol

from ..aggregates.learning_policy import FrozenCorpus, PolicyScore, RoutingHypothesis


class ILearningRepository(Protocol):
    """Protocol for Learning Policy, Corpus, and Score persistence."""

    def save_frozen_corpus(self, corpus: FrozenCorpus) -> None:
        ...

    def get_frozen_corpus(self, corpus_id: str) -> FrozenCorpus | None:
        ...

    def save_policy_score(self, score: PolicyScore) -> None:
        ...

    def save_hypothesis(self, hypothesis: RoutingHypothesis) -> None:
        ...
