"""Identity Domain Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class IdentityDomainV1(str, Enum):
    PROBLEM = "problem"
    PRESENTATION = "presentation"
    EXECUTION = "execution"
    EVIDENCE = "evidence"
    DECISION = "decision"
    APPLICATION = "application"
