"""Domain errors for the Polarized Operadic Triad.

AuthorityEffect: None.
"""

from __future__ import annotations


class OperadError(Exception):
    """Base domain error for operad operations."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class ProhibitedRepairError(OperadError):
    """Raised when an interrogative morphism (O^-) attempts to emit a patch.

    Enforces Law 4 (Detection-Repair Orthogonality): Anti-skills and interrogative
    morphisms map candidates to findings and obligations only, and are strictly
    forbidden from generating repair patches.
    """


class ProhibitedEvaluationError(OperadError):
    """Raised when a corrective repair morphism (O_repair) attempts to evaluate correctness.

    Enforces Law 3 (Zero Self-Promoted Authority): Repair morphisms map subjects
    and findings to candidate patches only, and are strictly forbidden from issuing
    verdicts or evaluating correctness.
    """


class SliceViolationError(OperadError):
    """Raised when an agent or morphism operates outside its licensed capability slice."""


class OperadRoleViolationError(OperadError):
    """Raised when an operadic component violates its declared polarity or role contract."""


class IllTypedCompositionError(OperadError):
    """Raised when partial composition f circle_i g violates color/type matching."""


class ArityMismatchError(OperadError):
    """Raised when an operation's inputs do not match its declared arity."""


__all__ = [
    "ArityMismatchError",
    "IllTypedCompositionError",
    "OperadError",
    "OperadRoleViolationError",
    "ProhibitedEvaluationError",
    "ProhibitedRepairError",
    "SliceViolationError",
]
