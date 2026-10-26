from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ASTDefect:
    """Discrete defect detected while projecting Python source into a dependency complex."""

    defect_type: str
    source_module: str
    target_module: Optional[str]
    description: str
    weight: float = 1.0


@dataclass
class ASTEvaluationReport:
    """Numerical obstruction report emitted by the configured functional kernel."""

    phi_1: float
    gamma_2: float
    active_obstruction_count: int
    active_obstructions: List[str]
    is_exact: bool
    is_closed: bool
    chain_condition_holds: bool
    complex_stats: Dict[str, int]
    evidence_sha256: str
    authority_effect: str = "None"

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
