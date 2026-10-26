#!/usr/bin/env python3
"""Domain Enumerations for the operad Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class OperadColour(str, Enum):
    """Admitted finite colors in the colored operad fibration."""

    AUDIT = "Audit"
    CODE = "Code"
    CONTRACT = "Contract"
    DIAGRAM = "Diagram"
    LEDGER = "Ledger"
    PAPER = "Paper"
    POST = "Post"
    PROOF = "Proof"
    RECEIPT = "Receipt"
    STATE = "State"


class ResidualEffect(str, Enum):
    """Declared residual behavior of an operad morphism."""

    UNKNOWN = "unknown"
    CONTRACTIVE = "contractive"
    NEUTRAL = "neutral"
    DILATIVE = "dilative"


class MorphismExecutionStatus(str, Enum):
    """Execution outcome status of a morphism application."""

    SUCCESS = "SUCCESS"
    CONTRACTIVE_PASS = "CONTRACTIVE_PASS"
    NEUTRAL_PASS = "NEUTRAL_PASS"
    REFUSED = "REFUSED"
    FAILED = "FAILED"
