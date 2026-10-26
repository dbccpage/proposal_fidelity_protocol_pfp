"""Council Resolution V1 Domain Model.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .council_resolution_status import CouncilResolutionStatus
from .council_vote_record import CouncilVoteRecord


@dataclass(frozen=True, slots=True)
class CouncilResolutionV1:
    resolution_id: str
    council_id: str
    proposal_id: str
    candidate_id: str
    status: CouncilResolutionStatus
    votes: tuple[CouncilVoteRecord, ...]
    yes_count: int
    no_count: int
    abstain_count: int
    total_votes: int
    resolution_timestamp_utc: str
    authority_effect: str = "None"
