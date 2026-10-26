"""Council Resolution Status Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class CouncilResolutionStatus(str, Enum):
    APPROVED = "APPROVED"
    RATIFIED = "RATIFIED"
    REJECTED = "REJECTED"
    QUORUM_NOT_MET = "QUORUM_NOT_MET"
    SPLIT_NO_MAJORITY = "SPLIT_NO_MAJORITY"
