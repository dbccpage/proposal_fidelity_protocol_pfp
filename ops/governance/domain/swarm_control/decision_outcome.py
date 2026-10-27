"""Decision Outcome Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class DecisionOutcome(str, Enum):
    ACCEPT = "ACCEPT"
    HOLD = "HOLD"
    REJECT = "REJECT"
