"""Domain errors for constrained decoding, polygraph confluence, and antimorphic reversal.

AuthorityEffect: None.
Zero outward dependencies.
"""
from __future__ import annotations

from enum import Enum


class DecodingRefusalCode(str, Enum):
    ZERO_RETAINED_MASS = "ZERO_RETAINED_MASS"
    ZERO_FLOAT_VIOLATION = "ZERO_FLOAT_VIOLATION"
    WRONG_ARITY = "WRONG_ARITY"
    INCONSISTENT_PROBABILITY = "INCONSISTENT_PROBABILITY"
    DISCONTINUOUS_REWRITE_CHAIN = "DISCONTINUOUS_REWRITE_CHAIN"
    DIVERGENT_JOIN_MISMATCH = "DIVERGENT_JOIN_MISMATCH"
    UNREGISTERED_REWRITE_RULE = "UNREGISTERED_REWRITE_RULE"
    REGISTERED_REWRITE_MISMATCH = "REGISTERED_REWRITE_MISMATCH"
    INVOLUTION_VIOLATION = "INVOLUTION_VIOLATION"
    PROTECTED_DISTINCTION_COLLAPSE = "PROTECTED_DISTINCTION_COLLAPSE"
    QUARANTINE_PROMOTION_FORBIDDEN = "QUARANTINE_PROMOTION_FORBIDDEN"


class DecodingError(Exception):
    """Base exception for decoding bounded context."""

    def __init__(self, message: str, code: DecodingRefusalCode | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ZeroFloatViolationError(DecodingError, TypeError):
    """Raised when a floating-point value violates the ZERO-FLOAT law in discrete evaluation."""

    def __init__(self, message: str = "ZERO-FLOAT Law violated: discrete evaluation requires Fraction or int") -> None:
        super().__init__(message, code=DecodingRefusalCode.ZERO_FLOAT_VIOLATION)


class RefusedZeroRetainedMassError(DecodingError):
    """Raised when retained probability mass drops to 0/1 or carrier support is empty."""

    def __init__(self, message: str = "REFUSED_ZERO_RETAINED_MASS: Retained probability mass is 0/1; empty support") -> None:
        super().__init__(message, code=DecodingRefusalCode.ZERO_RETAINED_MASS)


class InvolutionIdentityError(DecodingError):
    """Raised when edge or path involution identity fails (((e)^dagger)^dagger != e)."""

    def __init__(self, message: str = "INVOLUTION_VIOLATION: Involution law ((e)^dag)^dag = e failed") -> None:
        super().__init__(message, code=DecodingRefusalCode.INVOLUTION_VIOLATION)


class ProtectedDistinctionCollapseError(DecodingError):
    """Raised when a down-map projection collapses an essential protected distinction."""

    def __init__(self, message: str = "PROTECTED_DISTINCTION_COLLAPSE: Projection collapses protected boundary") -> None:
        super().__init__(message, code=DecodingRefusalCode.PROTECTED_DISTINCTION_COLLAPSE)


__all__ = [
    "DecodingError",
    "DecodingRefusalCode",
    "InvolutionIdentityError",
    "ProtectedDistinctionCollapseError",
    "RefusedZeroRetainedMassError",
    "ZeroFloatViolationError",
]
