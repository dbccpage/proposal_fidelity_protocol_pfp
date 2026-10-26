#!/usr/bin/env python3
"""Canonical research evaluation types and non-authoritative terminal selection.

Decomposed into pure Clean Architecture modules under domain/paper_iteration:
- enums: ResearchGate, GateVerdict, ResearchTerminal, LedgerLane, ResearchMode, AuthorityEffect
- value_objects: GateReceipt
- entities: ResearchEvaluation
- errors: PaperIterationDomainError, InvalidGateReceiptError
- protocols: GateEvaluatorProtocol, PaperEvaluationStoreProtocol

AuthorityEffect: None.
"""

from __future__ import annotations

from .entities import ResearchEvaluation
from .enums import (
    AuthorityEffect,
    GateVerdict,
    LedgerLane,
    ResearchGate,
    ResearchMode,
    ResearchTerminal,
)
from .errors import (
    AuthorityFirewallViolationError,
    InvalidGateReceiptError,
    PaperIterationDomainError,
    StrictProposerEvaluatorCollisionError,
)
from .protocols import (
    GateEvaluatorProtocol,
    PaperEvaluationStoreProtocol,
)
from .value_objects import GateReceipt

__all__ = [
    "AuthorityEffect",
    "AuthorityFirewallViolationError",
    "GateEvaluatorProtocol",
    "GateReceipt",
    "GateVerdict",
    "InvalidGateReceiptError",
    "LedgerLane",
    "PaperEvaluationStoreProtocol",
    "PaperIterationDomainError",
    "ResearchEvaluation",
    "ResearchGate",
    "ResearchMode",
    "ResearchTerminal",
    "StrictProposerEvaluatorCollisionError",
]
