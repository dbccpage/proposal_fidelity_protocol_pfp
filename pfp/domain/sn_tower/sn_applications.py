"""Downstream Domain Applications of S(n) Tower Architecture.

Absorbed into pure domain layer for Track 020 and PFP demo integration.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Set, Tuple


def topological_relational_join(
    table_a: Set[Tuple[str, str]],
    table_b: Set[Tuple[str, str]],
) -> Set[Tuple[str, str, str]]:
    """Compute relational join as simplicial edge incidence pullback.

    Joins table_a (entity, department) and table_b (department, building)
    along the shared department attribute.
    """
    return {(name, dept, bldg) for (name, dept) in table_a for (d2, bldg) in table_b if dept == d2}


class SessionChannel:
    """Linear-typed single-use session channel with state transition tracking."""

    def __init__(self) -> None:
        self.state: str = "INIT"
        self.is_closed: bool = False

    def send(self, payload: str) -> None:
        """Send message across channel, transitioning state to SENT."""
        if self.is_closed:
            raise AssertionError("Linear violation: cannot send on closed channel!")
        self.state = "SENT"

    def recv(self) -> str:
        """Receive acknowledgment, closing the channel."""
        if self.state != "SENT":
            raise AssertionError("Protocol violation: no message to receive!")
        self.state = "CLOSED"
        self.is_closed = True
        return "ACK"


@dataclass(frozen=True)
class DownstreamApplication:
    """Downstream application model enforcing non-authority and layer fences."""

    name: str
    domain: str
    authority_effect: str = "None"
    layer: int = 3

    def verify_fences(self) -> bool:
        """Check authority effect is strictly None and layer is at or above 3."""
        return self.authority_effect == "None" and self.layer >= 3


class ReggeMetric:
    """Discrete Regge metric positive-definiteness evaluator."""

    @staticmethod
    def equilateral_gram_determinant(edge_squared_scale: float = 1.0) -> float:
        """Compute Gram matrix determinant for an equilateral 2-simplex."""
        s = edge_squared_scale
        return (s * s) - ((s * 0.5) * (s * 0.5))

    @staticmethod
    def equilateral_gram_trace(edge_squared_scale: float = 1.0) -> float:
        """Compute Gram matrix trace for an equilateral 2-simplex."""
        return 2.0 * edge_squared_scale

    @classmethod
    def verify_positivity(cls, edge_squared_scale: float = 1.0) -> bool:
        """Check Gram matrix determinant and trace are strictly positive."""
        det = cls.equilateral_gram_determinant(edge_squared_scale)
        trace = cls.equilateral_gram_trace(edge_squared_scale)
        return det > 0.0 and trace > 0.0


class ReggeCurvature:
    """Discrete Regge curvature and hinge deficit angle calculator."""

    @staticmethod
    def deficit_angle(dihedrals: Sequence[float]) -> float:
        """Calculate hinge deficit angle epsilon_h = 2*pi - sum(theta_i)."""
        return 2.0 * math.pi - sum(dihedrals)

    @classmethod
    def is_flat_hinge(cls, dihedrals: Sequence[float], tol: float = 1e-9) -> bool:
        """Check if sum of dihedral angles equals 2*pi within numeric tolerance."""
        deficit = cls.deficit_angle(dihedrals)
        return math.isclose(deficit, 0.0, abs_tol=tol)

    @classmethod
    def verify_flatness(cls, dihedrals: Sequence[float], tol: float = 1e-9) -> bool:
        """Verify flatness within numeric tolerance."""
        return cls.is_flat_hinge(dihedrals, tol)

    @classmethod
    def is_positive_curvature(cls, dihedrals: Sequence[float]) -> bool:
        """Check if deficit angle is strictly positive."""
        return cls.deficit_angle(dihedrals) > 0.0
