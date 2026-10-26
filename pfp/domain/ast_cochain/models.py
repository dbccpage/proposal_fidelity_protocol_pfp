"""Pure domain models for Asymmetric LGGR & Clean Architecture AST 1-Skeleton (Prompt 11).

AuthorityEffect: None.
ZERO-FLOAT Law: Cochain defects and obstructions operate strictly in fractions.Fraction.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction


class LggrVerdict(Enum):
    """LGGR arbiter verdict evaluating local vs global consistency."""

    PASS = "PASS"
    REFUSED_LOCAL_GREEN_GLOBAL_RED = "REFUSED_LOCAL_GREEN_GLOBAL_RED"
    LOCAL_RED = "LOCAL_RED"


@dataclass(frozen=True)
class DependencyEdge:
    """1-simplex directed dependency edge in the AST module complex."""

    source_module: str
    target_module: str
    source_layer: str
    target_layer: str
    is_outward_leakage: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.source_module,
            self.target_module,
            self.source_layer,
            self.target_layer,
            self.is_outward_leakage,
        ) == (
            other.source_module,
            other.target_module,
            other.source_layer,
            other.target_layer,
            other.is_outward_leakage,
        )


@dataclass(frozen=True)
class AstCochainReceipt:
    """Receipt evaluating 1-cochain boundary leakage and 1-cycle obstruction."""

    phi_1_boundary_leakage: Fraction
    gamma_2_cycle_obstruction: Fraction
    total_modules_analyzed: int
    total_edges_evaluated: int
    verdict: LggrVerdict
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if isinstance(self.phi_1_boundary_leakage, float) or isinstance(
            self.gamma_2_cycle_obstruction, float
        ):
            raise TypeError("ZERO-FLOAT Law: cochain defects must be Fraction, not float")
        if not isinstance(self.phi_1_boundary_leakage, Fraction) or not isinstance(
            self.gamma_2_cycle_obstruction, Fraction
        ):
            raise TypeError("ZERO-FLOAT Law: cochain defects must be Fraction instances")

    @property
    def is_clean_architecture_exact(self) -> bool:
        """Returns True if both boundary leakage and cycle obstruction strictly vanish."""
        return (
            self.phi_1_boundary_leakage == Fraction(0, 1)
            and self.gamma_2_cycle_obstruction == Fraction(0, 1)
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.phi_1_boundary_leakage,
            self.gamma_2_cycle_obstruction,
            self.total_modules_analyzed,
            self.total_edges_evaluated,
            self.verdict,
            self.authority_effect,
        ) == (
            other.phi_1_boundary_leakage,
            other.gamma_2_cycle_obstruction,
            other.total_modules_analyzed,
            other.total_edges_evaluated,
            other.verdict,
            other.authority_effect,
        )
