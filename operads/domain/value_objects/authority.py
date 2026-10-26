"""Authority effect levels for OEWAS V3 operations and terms."""

from __future__ import annotations

from enum import Enum


class AuthorityEffect(str, Enum):
    NONE = "None"
    EVIDENCE_ONLY = "EvidenceOnly"
    FACT_ONLY = "FactOnly"
    STATE_TRANSITION = "StateTransition"


AUTHORITY_RANK = {
    AuthorityEffect.NONE: 0,
    AuthorityEffect.EVIDENCE_ONLY: 1,
    AuthorityEffect.FACT_ONLY: 2,
    AuthorityEffect.STATE_TRANSITION: 3,
}
