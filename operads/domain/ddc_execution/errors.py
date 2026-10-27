#!/usr/bin/env python3
"""Domain errors for the operad Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

from operads.domain.operad.errors import DomainError


class OperadDomainError(DomainError, ValueError):
    """Base exception for operadic domain and invariant failures."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"OPERAD_DOMAIN_ERROR[{code}]: {detail}")


class Refusal(OperadDomainError):
    """Typed refusal at an execution or parser port boundary."""

    def __init__(self, code: str, message: str, locus: str = "ddc_execution") -> None:
        super().__init__(code, message)
        self.message = message
        self.locus = locus


class UnknownMorphismError(OperadDomainError):
    """Raised when an operation or metaskill identifier is not registered."""

    def __init__(self, skill_id: str) -> None:
        super().__init__(
            "UNKNOWN_MORPHISM",
            f"Operation or metaskill {skill_id!r} is not registered in operad signature",
        )


class ArityMismatchError(OperadDomainError):
    """Raised when supplied inputs do not match declared operation arity."""

    def __init__(self, skill_id: str, declared_arity: int, actual_arity: int) -> None:
        super().__init__(
            "ARITY_MISMATCH",
            f"Morphism {skill_id!r} expects arity {declared_arity}, got {actual_arity}",
        )


class ColourMismatchError(OperadDomainError):
    """Raised when an input artifact colour violates the declared source colour."""

    def __init__(self, slot: int, expected: str, actual: str) -> None:
        super().__init__(
            "COLOUR_MISMATCH",
            f"Input at slot {slot} has colour {actual!r}, expected {expected!r}",
        )


class PermissionDeniedError(OperadDomainError):
    """Raised when an agent lacks authorization for a morphism or colour escape occurs."""

    def __init__(self, agent_id: str, detail: str) -> None:
        super().__init__("PERMISSION_DENIED", f"Agent {agent_id!r}: {detail}")


class ResidualHonestyError(OperadDomainError):
    """Raised when a morphism claims a contractive invariant without the required evidence."""

    def __init__(self, skill_id: str, runs_found: int, runs_required: int) -> None:
        super().__init__(
            "RESIDUAL_HONESTY_VIOLATION",
            f"Skill {skill_id!r} has only {runs_found}/{runs_required} contractive runs; residual must remain 'unknown'",
        )


class TraceLedgerStorageError(OperadDomainError):
    """Raised when reading or writing evidence_trace.json fails."""

    def __init__(self, path: str, detail: str) -> None:
        super().__init__("TRACE_LEDGER_ERROR", f"Trace storage at {path!r}: {detail}")
