"""Runtime checkable protocols for symbol_game ports."""

from __future__ import annotations

# The canonical typed port; `ports.py` no longer defines a rival.
from .code_change_repository import ICodeChangeRepository
from .ports import (
    CanonicalSerializerProtocol,
    EvaluatorPort,
    ICecBridgeAdapter,
    IEventBus,
    ILearningRepository,
    IOutbox,
    IPromptRepository,
    IResearchRepository,
    IScoringEvaluator,
    ITurnRepository,
    ObstructionLedgerProtocol,
    PacketEnvelopeProtocol,
    ProjectorPort,
    SolverPort,
    StoragePort,
)

__all__ = [
    "CanonicalSerializerProtocol",
    "EvaluatorPort",
    "ICecBridgeAdapter",
    "ICodeChangeRepository",
    "IEventBus",
    "ILearningRepository",
    "IOutbox",
    "IPromptRepository",
    "IResearchRepository",
    "IScoringEvaluator",
    "ITurnRepository",
    "ObstructionLedgerProtocol",
    "PacketEnvelopeProtocol",
    "ProjectorPort",
    "SolverPort",
    "StoragePort",
]
