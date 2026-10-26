# -*- coding: utf-8 -*-
"""protocols.py: Domain ports and interfaces for residual algebra and multicategory transformations.

Clean Architecture Layer: Domain Ports / Interfaces
AuthorityEffect: None
"""

from __future__ import annotations

from typing import Any, List, Protocol, Tuple

from omega_engine_woland.domain.residual_algebra.residual_sorts import (
    Residual1Cochain,
)


class ObstructionValuatorProtocol(Protocol):
    """Abstract interface for evaluating residual cochains into valuation receipts."""

    def value_cochain(
        self,
        cochain: Residual1Cochain,
        *,
        gamma_2: float = 0.0,
        phi_ret: float = 0.0,
        phi_claim: float = 0.0,
        is_exact_rational: bool = False,
    ) -> Any: ...

    def value_cochains(
        self,
        cochains: Tuple[Residual1Cochain, ...] | List[Residual1Cochain],
    ) -> Any: ...


class GaugeTransformerProtocol(Protocol):
    """Abstract interface for gauge change transformations and naturality verification."""

    def apply_gauge(
        self,
        cochain: Residual1Cochain,
        source_gauge: str,
        target_gauge: str,
    ) -> Residual1Cochain: ...


class AdversarialBoutProtocol(Protocol):
    """Abstract interface for adversarial bout execution and pullback evaluation."""

    def run_bout(
        self,
        package: Any,
        proposer_cochain: Residual1Cochain,
        adversary_cochain: Residual1Cochain,
    ) -> Any: ...


class FreeMulticategoryProtocol(Protocol):
    """Abstract interface for operadic multicategory term evaluation."""

    def evaluate_term(self, term: Any) -> Residual1Cochain: ...
