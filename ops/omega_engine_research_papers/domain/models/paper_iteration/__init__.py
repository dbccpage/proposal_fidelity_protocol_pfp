"""Domain package for paper iteration and research packet evaluation.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .entities import ResearchEvaluation
    from .enums import AuthorityEffect, GateVerdict, LedgerLane, ResearchGate, ResearchMode, ResearchTerminal
    from .errors import AuthorityFirewallViolationError, InvalidGateReceiptError, PaperIterationDomainError, StrictProposerEvaluatorCollisionError
    from .protocols import GateEvaluatorProtocol, PaperEvaluationStoreProtocol
    from .value_objects import GateReceipt

__all__ = ['AuthorityEffect', 'AuthorityFirewallViolationError', 'GateEvaluatorProtocol', 'GateReceipt', 'GateVerdict', 'InvalidGateReceiptError', 'LedgerLane', 'PaperEvaluationStoreProtocol', 'PaperIterationDomainError', 'ResearchEvaluation', 'ResearchGate', 'ResearchMode', 'ResearchTerminal', 'StrictProposerEvaluatorCollisionError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ResearchEvaluation': ('.entities', 'ResearchEvaluation'),
    'AuthorityEffect': ('.enums', 'AuthorityEffect'),
    'GateVerdict': ('.enums', 'GateVerdict'),
    'LedgerLane': ('.enums', 'LedgerLane'),
    'ResearchGate': ('.enums', 'ResearchGate'),
    'ResearchMode': ('.enums', 'ResearchMode'),
    'ResearchTerminal': ('.enums', 'ResearchTerminal'),
    'AuthorityFirewallViolationError': ('.errors', 'AuthorityFirewallViolationError'),
    'InvalidGateReceiptError': ('.errors', 'InvalidGateReceiptError'),
    'PaperIterationDomainError': ('.errors', 'PaperIterationDomainError'),
    'StrictProposerEvaluatorCollisionError': ('.errors', 'StrictProposerEvaluatorCollisionError'),
    'GateEvaluatorProtocol': ('.protocols', 'GateEvaluatorProtocol'),
    'PaperEvaluationStoreProtocol': ('.protocols', 'PaperEvaluationStoreProtocol'),
    'GateReceipt': ('.value_objects', 'GateReceipt'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
