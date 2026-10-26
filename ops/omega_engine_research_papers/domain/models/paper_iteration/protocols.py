# -*- coding: utf-8 -*-
"""protocols.py: Domain ports and interfaces for paper iteration and evaluation.

Clean Architecture Layer: Domain Ports / Interfaces
AuthorityEffect: None
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from .entities import ResearchEvaluation
from .enums import (
    ResearchGate,
    ResearchMode,
)
from .value_objects import GateReceipt


class GateEvaluatorProtocol(Protocol):
    """Abstract interface for evaluating an individual research gate."""

    def evaluate_gate(
        self,
        gate: ResearchGate,
        packet_data: Dict[str, Any],
        mode: ResearchMode,
    ) -> GateReceipt:
        ...


class PaperEvaluationStoreProtocol(Protocol):
    """Abstract interface for storing and retrieving research evaluations."""

    def save_evaluation(self, evaluation: ResearchEvaluation) -> None:
        ...

    def get_evaluation(self, evaluation_sha256: str) -> Optional[ResearchEvaluation]:
        ...
