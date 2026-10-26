"""Council Vote Choice Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class CouncilVoteChoice(str, Enum):
    AYE = "AYE"
    NAY = "NAY"
    YES = "AYE"
    NO = "NAY"
    ABSTAIN = "ABSTAIN"
