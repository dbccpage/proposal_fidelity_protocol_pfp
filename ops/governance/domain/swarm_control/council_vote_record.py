"""Council Vote Record Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .council_vote_choice import CouncilVoteChoice


@dataclass(frozen=True, slots=True)
class CouncilVoteRecord:
    member_id: str
    vote: CouncilVoteChoice
    rationale: str = ""
    signature: str = ""
    timestamp_utc: str = ""
