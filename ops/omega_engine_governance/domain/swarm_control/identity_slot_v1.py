"""Identity Slot Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class IdentitySlotV1(str, Enum):
    PROBLEM = "problem"
    PRESENTATION = "presentation"
    EXECUTION = "execution"
    EVIDENCE = "evidence"
    DECISION = "decision"
    APPLICATION = "application"
