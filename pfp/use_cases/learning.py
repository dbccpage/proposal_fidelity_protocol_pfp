"""Learning Policy and Routing Use Cases."""

from __future__ import annotations

import hashlib
from typing import Sequence

from ..domain import (
    AuthorityEffect,
    FrozenCorpus,
    PolicyScore,
)


class FreezeCorpusUseCase:
    """Freezes evaluation sample set into content-addressed FrozenCorpus."""

    def execute(self, corpus_id: str, sample_ids: Sequence[str]) -> FrozenCorpus:
        sorted_samples = sorted(set(sample_ids))
        joined = ",".join(sorted_samples)
        corpus_sha256 = hashlib.sha256(joined.encode("utf-8")).hexdigest()

        return FrozenCorpus(
            corpus_id=corpus_id,
            corpus_sha256=corpus_sha256,
            sample_ids=tuple(sorted_samples),
            authority_effect=AuthorityEffect.NONE.value,
        )


class EvaluatePolicyUseCase:
    """Computes empirical score metrics for a policy against a frozen corpus."""

    def execute(
        self,
        policy_id: str,
        corpus: FrozenCorpus,
        successes: int,
        total: int,
        residual_drops: Sequence[float],
    ) -> PolicyScore:
        success_rate = (successes / total) if total > 0 else 0.0
        avg_drop = (sum(residual_drops) / len(residual_drops)) if residual_drops else 0.0
        efficiency = success_rate * (1.0 + avg_drop)

        return PolicyScore(
            policy_id=policy_id,
            corpus_id=corpus.corpus_id,
            success_rate=success_rate,
            average_residual_drop=avg_drop,
            efficiency=efficiency,
            authority_effect=AuthorityEffect.NONE.value,
        )
