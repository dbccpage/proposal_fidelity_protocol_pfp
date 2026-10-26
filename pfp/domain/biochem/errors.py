"""Domain errors for Biochemical Swarm Gates.

AuthorityEffect: None.
"""

from __future__ import annotations


class BiochemError(Exception):
    """Base domain error for biochemical swarm operations."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class ZeroFloatViolationError(BiochemError, TypeError):
    """Raised when floating-point arithmetic or float values violate the Zero-Float law.

    Under nf.runtime.zfnf, all discrete state decisions, Hill quorum switches,
    and kinetic proofreading computations must strictly use exact rationals (Fraction).
    Inherits from TypeError to satisfy standard type checking invariants.
    """


class DissociationError(BiochemError):
    """Raised or reported when kinetic proofreading forces substrate dissociation."""


__all__ = [
    "BiochemError",
    "DissociationError",
    "ZeroFloatViolationError",
]
