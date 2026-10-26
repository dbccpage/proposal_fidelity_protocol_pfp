"""Decision Status Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class DecisionStatusV1(str, Enum):
    NOT_YET_CREATED = "NOT_YET_CREATED"
    ACCEPTED = "ACCEPTED"
    HELD = "HELD"
    REJECTED = "REJECTED"
