"""Allosteric Quorum Sensing & Monod-Wyman-Changeux Sigmoidal Gates.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Sequence

from omega_engine_pfp.domain.biochem.errors import ZeroFloatViolationError


@dataclass(frozen=True)
class HillParameters:
    """Exact rational Hill equation parameters under strict Zero-Float law.

    Equation: H(theta) = theta^n / (Kd^n + theta^n)
    Under nf.runtime.zfnf, Hill coefficient n is strictly restricted to n in {2, 4}
    so that H(theta) stays in Q without float approximations.
    """

    Kd: Fraction = Fraction(2, 1)
    n: int = 4
    activation_threshold: Fraction = Fraction(7, 10)
    quiescence_ceiling: Fraction = Fraction(1, 10)

    def __post_init__(self) -> None:
        # Strict Zero-Float Law: reject float Kd
        if isinstance(self.Kd, float):
            raise ZeroFloatViolationError(
                f"Float Kd={self.Kd!r} violates Zero-Float law; use Fraction"
            )
        # Reject float n
        if isinstance(self.n, float):
            raise ZeroFloatViolationError(
                f"Float Hill coefficient n={self.n!r} violates Zero-Float law; must be integer in {{2, 4}}"
            )
        # Reject float thresholds
        if isinstance(self.activation_threshold, float) or isinstance(self.quiescence_ceiling, float):
            raise ZeroFloatViolationError(
                "Float thresholds violate Zero-Float law; use Fraction"
            )

        # Enforce n in {2, 4}
        if self.n not in {2, 4}:
            raise ValueError(
                f"Hill coefficient n={self.n} not supported under exact rational normal form; "
                "must be integer in {2, 4}."
            )

        # Ensure Fraction types
        if not isinstance(self.Kd, Fraction):
            object.__setattr__(self, "Kd", Fraction(self.Kd))
        if not isinstance(self.activation_threshold, Fraction):
            object.__setattr__(self, "activation_threshold", Fraction(self.activation_threshold))
        if not isinstance(self.quiescence_ceiling, Fraction):
            object.__setattr__(self, "quiescence_ceiling", Fraction(self.quiescence_ceiling))

        # Enforce strictly positive Kd
        if self.Kd <= 0:
            raise ValueError("Kd must be strictly positive")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.Kd == other.Kd
            and self.n == other.n
            and self.activation_threshold == other.activation_threshold
            and self.quiescence_ceiling == other.quiescence_ceiling
        )


@dataclass(frozen=True)
class AllostericDecision:
    """Consensus decision emitted by the AllostericConsensusGate."""

    theta: Fraction
    hill_value: Fraction
    is_activated: bool
    is_quiescent: bool
    status: str
    disposition: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.theta == other.theta
            and self.hill_value == other.hill_value
            and self.is_activated == other.is_activated
            and self.is_quiescent == other.is_quiescent
            and self.status == other.status
            and self.disposition == other.disposition
        )


class AllostericConsensusGate:
    """Sigmoidal quorum consensus switch with zero floating-point arithmetic."""

    def __init__(self, parameters: HillParameters | None = None) -> None:
        self.parameters = parameters if parameters is not None else HillParameters()

    def compute_hill(self, theta: Fraction | int) -> Fraction:
        """Compute exact rational Hill value H(theta) = theta^n / (Kd^n + theta^n).

        Strictly rejects float inputs with ZeroFloatViolationError (TypeError).
        """
        if isinstance(theta, float):
            raise ZeroFloatViolationError(
                f"Float theta={theta!r} violates Zero-Float law; use Fraction or int"
            )

        theta_q = Fraction(theta)
        if theta_q < 0:
            raise ValueError(f"Signal theta={theta_q} must be non-negative")
        if theta_q == 0:
            return Fraction(0, 1)

        n = self.parameters.n
        kd_n = self.parameters.Kd ** n
        theta_n = theta_q ** n
        return theta_n / (kd_n + theta_n)

    def evaluate_signals(self, signals: Sequence[Fraction | int]) -> AllostericDecision:
        """Aggregate inspector signals and evaluate sigmoidal consensus decision."""
        theta = Fraction(0, 1)
        for s in signals:
            if isinstance(s, float):
                raise ZeroFloatViolationError(
                    f"Float signal={s!r} violates Zero-Float law; use Fraction"
                )
            theta += Fraction(s)

        hill_val = self.compute_hill(theta)
        is_activated = hill_val >= self.parameters.activation_threshold
        is_quiescent = hill_val <= self.parameters.quiescence_ceiling

        if is_activated:
            status = "ACTIVATED"
            disposition = "REFUSE"
        elif is_quiescent:
            status = "QUIESCENT"
            disposition = "TOLERATE"
        else:
            status = "SUB_THRESHOLD"
            disposition = "TOLERATE"

        return AllostericDecision(
            theta=theta,
            hill_value=hill_val,
            is_activated=is_activated,
            is_quiescent=is_quiescent,
            status=status,
            disposition=disposition,
        )


__all__ = [
    "AllostericConsensusGate",
    "AllostericDecision",
    "HillParameters",
]
