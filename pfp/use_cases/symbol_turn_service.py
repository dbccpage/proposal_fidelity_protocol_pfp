"""Application use cases for Symbol Game manifold projection and step execution."""

from __future__ import annotations

import hashlib
from typing import Optional

from ..domain.bridge.sbe import SBEAnalyzer
from ..domain.bridge.symbol_game_packets import SymbolGamePacketCompiler
from ..domain.models import SymbolGameEnvelope, SymbolGameStepOutcome


class SymbolGameExecutionService:
    """Service orchestrating the Symbol Game retraction manifold and packet compilation."""

    def __init__(self, sbe_analyzer: Optional[SBEAnalyzer] = None) -> None:
        self.sbe = sbe_analyzer or SBEAnalyzer()

    def execute_symbol_turn(self, envelope: SymbolGameEnvelope) -> SymbolGameStepOutcome:
        SymbolGamePacketCompiler.compile_text_problem(
            task_id=envelope.task_id,
            text_content=envelope.initial_input,
        )
        report = self.sbe.analyze_text(envelope.initial_input)
        evidence = hashlib.sha256(f"{envelope.task_id}:{envelope.initial_input}:{report.purity}".encode("utf-8")).hexdigest()

        return SymbolGameStepOutcome(
            step_id=f"step_{envelope.task_id[:8]}",
            purity=report.purity,
            l1_obstruction=report.l1_coherence,
            # Purity is a floating-point text observable, not an exact check.
            # A single text is a pure state, so purity is always 1.0; treating
            # it as exactness would certify every prompt. Nothing here is
            # certified, so the turn is held, never marked exact or selected.
            is_exact=False,
            verdict="HOLD",
            evidence_sha256=f"sha256:{evidence}",
            authority_effect="None",
        )
