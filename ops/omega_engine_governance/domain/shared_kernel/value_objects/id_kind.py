"""Identifier Kind Enumeration.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class IdKind(str, Enum):
    """Domain taxonomy discriminating identifier types."""

    GENERIC = "GENERIC"
    DECISION = "DECISION"
    PROBLEM = "PROBLEM"
    PROPOSAL = "PROPOSAL"
    CANDIDATE = "CANDIDATE"
    EVIDENCE = "EVIDENCE"
    PACKET = "PACKET"
    LEASE = "LEASE"
    OWNER = "OWNER"
    PRINCIPAL = "PRINCIPAL"
    KEY_REF = "KEY_REF"
    PUBLIC_KEY_REF = "PUBLIC_KEY_REF"
    TOKEN = "TOKEN"
    ONE_USE_TOKEN = "ONE_USE_TOKEN"
    NONCE = "NONCE"
    RECEIPT = "RECEIPT"
    EVENT = "EVENT"
    REPO_WORKTREE = "REPO_WORKTREE"
    PR = "PR"
    REPO = "REPO"
    CHANGE = "CHANGE"
    CAMPAIGN = "CAMPAIGN"
    POLICY = "POLICY"
    AGENT = "AGENT"
    COUNCIL = "COUNCIL"
    RULE = "RULE"
    AUDIT = "AUDIT"
