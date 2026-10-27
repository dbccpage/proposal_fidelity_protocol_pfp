#!/usr/bin/env python3
"""Domain errors for the residual_algebra Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations


class ResidualAlgebraDomainError(ValueError):
    """Base exception for residual algebra domain invariant violations."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"RESIDUAL_ALGEBRA_DOMAIN_ERROR[{code}]: {detail}")


class GaugeIsolationError(ResidualAlgebraDomainError):
    """Raised when gauge transformation leaks uncontracted invariants across boundary."""

    def __init__(self, detail: str) -> None:
        super().__init__("GAUGE_ISOLATION_BREACH", detail)


class ExactnessWitnessError(ResidualAlgebraDomainError):
    """Raised when an exactness witness fails rational or cryptographic verification."""

    def __init__(self, detail: str) -> None:
        super().__init__("EXACTNESS_WITNESS_INVALID", detail)


class ResidualValuationError(ResidualAlgebraDomainError):
    """Raised when cochain valuation detects illegal authority or ungrounded float mass."""

    def __init__(self, detail: str) -> None:
        super().__init__("RESIDUAL_VALUATION_ERROR", detail)
