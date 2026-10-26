"""Outcome Status Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class OutcomeStatus(str, Enum):
    COMPLETED = "completed"
    DELEGATED = "delegated"
