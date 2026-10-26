"""
problem_runner.py
=================

Use case for multi-round problem reduction and specimen claim evaluation.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ..functional_boundary import require_rust_functional
from .symbol_turn_service import SymbolGameExecutionService


class ProblemRunnerUseCase:
    """Use case coordinating multi-step discrete and cochain problem reductions."""

    def __init__(
        self,
        turn_service: Optional[SymbolGameExecutionService] = None,
        target_dir: Optional[Path] = None,
    ) -> None:
        self.turn_service = turn_service or SymbolGameExecutionService()
        self.target_dir = target_dir or Path.cwd()

    def run_problem(
        self,
        problem_input: str | Dict[str, Any],
        task_id: Optional[str] = None,
        max_steps: int = 4,
    ) -> Dict[str, Any]:
        """Refuse named functional output until a Rust-backed adapter exists."""
        require_rust_functional("ProblemRunnerUseCase.run_problem")

    def run_specimen_mt000(self) -> Dict[str, Any]:
        """Runs the mt_000 live specimen claim reduction."""
        mt000_claims = {
            "title": "Specimen mt_000: Finite Discrete Residual Geometry",
            "claims": [
                "1-cochain omega decomposes as exact coboundary d0(alpha) plus harmonic obstruction",
                "Obstruction norm phi_1 measures non-exact residue across cell complex boundaries",
                "Multi-agent cognitive debate exposes boundary leaks before licensing proposal",
            ],
            "carrier": "witten-airy-critical-five-slot-v1",
        }
        return self.run_problem(
            problem_input=mt000_claims,
            task_id="specimen_mt000_reduction",
            max_steps=3,
        )
