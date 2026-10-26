"""Domain exceptions and error hierarchy for the Symbol Game bounded context.

AuthorityEffect: None.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base domain exception for the Symbol Game bounded context."""


class InvariantViolationError(DomainError):
    """Raised when a core domain invariant is violated."""


class ForbiddenAuthorityError(InvariantViolationError):
    """Raised when an operation attempts unauthorized authority minting."""


class BudgetExhaustedError(DomainError):
    """Raised when turn or candidate step budgets are exhausted."""


class DigestFormatError(InvariantViolationError):
    """Raised when a content or domain digest format is invalid."""


class SecurityPathViolationError(InvariantViolationError):
    """Raised when an unsafe or escaping filesystem path is encountered."""


class PayloadSizeLimitExceededError(InvariantViolationError):
    """Raised when an envelope payload exceeds declared byte bounds."""


class DualWitnessRequiredError(InvariantViolationError):
    """Raised when exactness claims lack independent dual witnesses."""


class CanonicalizationError(ValueError, DomainError):
    """Raised when canonical encoding, sorting, or serialization fails."""


class RefusalError(DomainError):
    """Raised when an operational refusal cannot be processed."""


# Base aliases
SymbolGameError = DomainError
SymbolGameDomainError = DomainError


# Additional Symbol Game domain exceptions
class SymbolGameValidationError(SymbolGameError):
    """Raised when envelope, packet, or turn validation fails."""


class InvalidStateError(SymbolGameError):
    """Raised when an operation is attempted from or results in an invalid state."""


class DomainRuleViolationError(SymbolGameError):
    """Raised when a domain rule or invariant is violated."""


class ContractViolationError(SymbolGameError):
    """Raised when an operational or interface contract is violated."""


class EntityNotFoundError(SymbolGameError):
    """Raised when an entity cannot be found or resolved."""


class ConfigurationError(SymbolGameError):
    """Raised when domain configuration is invalid."""


class ExecutionTimeoutError(SymbolGameError):
    """Raised when an execution or processing step exceeds its timeout."""


class ResourceExhaustionError(SymbolGameError):
    """Raised when a resource, budget, or quota limit is exhausted."""


# Aliases for domain naming alignment
IllegalPathAccessError = SecurityPathViolationError
PacketSchemaError = CanonicalizationError

__all__ = [
    # Core hierarchy
    "SymbolGameError",
    "SymbolGameValidationError",
    "InvalidStateError",
    "DomainRuleViolationError",
    "ContractViolationError",
    "InvariantViolationError",
    "EntityNotFoundError",
    "ConfigurationError",
    "ExecutionTimeoutError",
    "ResourceExhaustionError",
    # Domain exceptions
    "BudgetExhaustedError",
    "CanonicalizationError",
    "DigestFormatError",
    "DomainError",
    "DualWitnessRequiredError",
    "ForbiddenAuthorityError",
    "IllegalPathAccessError",
    "PacketSchemaError",
    "PayloadSizeLimitExceededError",
    "RefusalError",
    "SecurityPathViolationError",
    "SymbolGameDomainError",
]
