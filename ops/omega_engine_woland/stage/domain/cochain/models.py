"""
models.py
=========

AST Cochain Complex Domain Models and Obstruction Evaluation Reports.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ASTDefect:
    """Discrete defect detected while projecting source into a dependency cochain complex."""

    defect_type: str
    source_module: str
    target_module: Optional[str]
    description: str
    weight: float = 1.0

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.defect_type == other.defect_type
            and self.source_module == other.source_module
            and self.target_module == other.target_module
            and self.description == other.description
            and self.weight == other.weight
        )

    def __hash__(self) -> int:
        return hash((type(self), self.defect_type, self.source_module, self.target_module, self.description, self.weight))


@dataclass
class ASTEvaluationReport:
    """Numerical obstruction report emitted by the configured functional cochain kernel."""

    phi_1: float
    gamma_2: float
    active_obstruction_count: int
    active_obstructions: List[str]
    is_exact: bool
    is_closed: bool
    chain_condition_holds: bool
    complex_stats: Dict[str, int]
    evidence_sha256: str
    defects: List[ASTDefect] = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.defects is None:
            self.defects = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phi_1": round(self.phi_1, 6),
            "gamma_2": round(self.gamma_2, 6),
            "active_obstruction_count": self.active_obstruction_count,
            "active_obstructions": self.active_obstructions,
            "is_exact": self.is_exact,
            "is_closed": self.is_closed,
            "chain_condition_holds": self.chain_condition_holds,
            "complex_stats": self.complex_stats,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
        }
