"""
residual_package.py
===================

Base Residual Carrier and ResidualTypedPackage (Role A).

AuthorityEffect: None.
pure_transform is strictly Φ-blind by contract.
observation_maps extract a typed Residual1Cochain for external valuation (Role B).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from .residual_sorts import Residual1Cochain, ResidualSort

Carrier = TypeVar("Carrier")


@dataclass(frozen=True)
class ResidualCarrier(Generic[Carrier]):
    """
    Immutable structured state (cochain, graph, poset, AST) typed by a ResidualSort.
    Passive carrier: never evaluates Φ internally.
    """

    residual_sort: ResidualSort
    payload: Carrier
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResidualTypedPackage(Generic[Carrier]):
    """
    Role A Generating Operation:
        R_in <--- E ---> R_out

    pure_transform:   Carrier -> Carrier (Stage 2: strictly Φ-blind)
    observation_maps: (pre, post) -> Residual1Cochain (Stage 3: extracts residual of package)
    residual_in:      Input residual sort / observation regime
    residual_out:     Output residual sort / observation regime
    nonclaim:         Explicit refusal of unearned authority and obstruction valuation.
    """

    residual_in: ResidualSort
    pure_transform: Callable[[Carrier], Carrier]
    observation_maps: Callable[[Carrier, Carrier], Residual1Cochain]
    residual_out: ResidualSort
    nonclaim: str = (
        "does not value obstruction class; does not issue residual-admissible transition token"
    )

    def apply_transform(self, carrier: Carrier) -> Carrier:
        """Stage 2 execution: Φ-blind pure transform."""
        return self.pure_transform(carrier)

    def extract_residual(self, pre: Carrier, post: Carrier) -> Residual1Cochain:
        """Stage 3 observation: extracts the residual 1-cochain."""
        return self.observation_maps(pre, post)
