"""Precedent matching and reference trail evaporation.

Enforces:
- F-DOMAIN-01: Hard domain eligibility check (excludes Shelved, Dormant, or unadmitted prompts).
- F-SELECT-02: Unmeasured prompts receive exploration quota among eligible population.
- F-BIO-04: Evaporation is per contribution, epoch-based, and view-only.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple


class ReferenceTrailEvaporationCalculatorV1:
    """Calculates exact rational evaporated weights for reference trail uses."""

    def __init__(self, half_life_epochs: int = 10) -> None:
        if half_life_epochs <= 0:
            raise ValueError("half_life_epochs must be positive")
        self.half_life_epochs = half_life_epochs

    def calculate_weight(
        self,
        uses: Sequence[Tuple[int, int]],
        current_epoch: int,
    ) -> Fraction:
        total_weight = Fraction(0, 1)
        for epoch, count in uses:
            elapsed = max(0, current_epoch - epoch)
            half_lives = elapsed // self.half_life_epochs
            # Exact rational decay: (1/2)^half_lives
            decay = Fraction(1, 2**half_lives)
            total_weight += Fraction(count, 1) * decay
        return total_weight


def is_candidate_eligible(c: Dict[str, Any], query_domain: Optional[str] = None) -> bool:
    """Check if candidate satisfies retrieval eligibility and hard domain eligibility."""
    # 1. Retrieval eligibility: must not be Shelved or Dormant
    retrieval = c.get("retrieval_eligibility", "Active")
    if retrieval in ("Shelved", "Dormant"):
        return False

    # 2. Domain placement: must not be PROPOSED or unadmitted
    placement = c.get("domain_placement") or c.get("placement", {}).get("disposition")
    if placement in ("PROPOSED", "INDEXED_UNREAD", "QUARANTINED"):
        return False

    # If query domain specified, verify read scope
    if query_domain is not None:
        scope = c.get("read_scope") or c.get("placement", {}).get("read_scope", [])
        if scope and query_domain not in scope:
            return False

    return True


class PrecedentMatcherV1:
    """Selects prompt precedents respecting exploration quotas for unmeasured candidates."""

    def __init__(self, exploration_quota_slots: int = 1) -> None:
        self.exploration_quota_slots = exploration_quota_slots

    def select_precedents(
        self,
        candidates: Sequence[Dict[str, Any]],
        count: int = 2,
        query_domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # Filter eligible candidates first
        eligible = [c for c in candidates if is_candidate_eligible(c, query_domain)]

        unmeasured = [c for c in eligible if c.get("maturity") == "Unmeasured"]
        mature = [c for c in eligible if c.get("maturity") != "Unmeasured"]

        # Sort mature candidates by pareto front ascending, then by rank descending
        mature.sort(
            key=lambda c: (
                c.get("pareto_front", 999),
                -float(c.get("ancestral_rank", 0)),
                c.get("id", ""),
            )
        )

        quota = min(self.exploration_quota_slots, len(unmeasured), count)
        selected: List[Dict[str, Any]] = []

        # 1. Allocate exploration quota to unmeasured candidates
        selected.extend(unmeasured[:quota])

        # 2. Fill remaining slots from mature candidates
        remaining_slots = count - len(selected)
        selected.extend(mature[:remaining_slots])

        return selected


__all__ = [
    "PrecedentMatcherV1",
    "ReferenceTrailEvaporationCalculatorV1",
    "is_candidate_eligible",
]
