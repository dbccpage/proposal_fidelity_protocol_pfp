"""Council Resolution Verification Result Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .council_resolution_status import CouncilResolutionStatus


@dataclass(frozen=True, slots=True)
class CouncilResolutionVerificationResult:
    """Legacy arithmetic result; status never establishes configured admission."""

    council_id: str
    resolution_id: str
    motion: str
    status: CouncilResolutionStatus
    aye_count: int
    nay_count: int
    abstain_count: int
    total_votes: int
    authority_effect: str = field(default="None", init=False)
    advisory_only: bool = field(default=True, init=False)
