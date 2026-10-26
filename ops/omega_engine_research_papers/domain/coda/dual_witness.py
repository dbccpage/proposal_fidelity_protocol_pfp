"""Exact Dual Witness Certificates and Duality Gap Zero Verification.

Enforces exact rational arithmetic in fractions.Fraction without float approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple


@dataclass(frozen=True)
class DualWitnessCertificate:
    """Exact rational dual witness certificate for L1 quotient optimization."""

    primal_potential: Tuple[Fraction, ...]
    dual_flow: Tuple[Fraction, ...]
    primal_cost: Fraction
    dual_value: Fraction
    duality_gap: Fraction
    is_optimal: bool
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")
        computed_gap = abs(self.primal_cost - self.dual_value)
        if computed_gap != self.duality_gap:
            raise ValueError(
                f"Declared duality gap {self.duality_gap} does not match computed |primal - dual| {computed_gap}"
            )


class ExactDualWitnessValidator:
    """Validates that a candidate dual witness certifies optimality under exact rational arithmetic."""

    @staticmethod
    def verify(
        primal_potential: Tuple[Fraction, ...],
        dual_flow: Tuple[Fraction, ...],
        primal_cost: Fraction,
        dual_value: Fraction,
    ) -> DualWitnessCertificate:
        gap = abs(primal_cost - dual_value)
        # Optimal if and only if exact duality gap is zero and dual box constraint |w_e| <= 1 holds
        is_box_feasible = all(abs(val) <= Fraction(1, 1) for val in dual_flow)
        is_optimal = (gap == Fraction(0, 1)) and is_box_feasible

        return DualWitnessCertificate(
            primal_potential=primal_potential,
            dual_flow=dual_flow,
            primal_cost=primal_cost,
            dual_value=dual_value,
            duality_gap=gap,
            is_optimal=is_optimal,
            authority_effect="None",
        )
