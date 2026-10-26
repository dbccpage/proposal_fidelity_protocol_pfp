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


class TypedRefusalError(RefusalError):
    """A typed refusal raised below a facade, carried with its own code and cause.

    Facades that return ``Result[..., DomainError]`` wrap a refusal that is not
    itself a ``DomainError`` (for example ``RustFunctionalRequired``) in this
    type rather than in a bare ``DomainError(str(exc))``, so the refusal code and
    the original exception survive the railway.
    """

    def __init__(self, cause: BaseException) -> None:
        code = getattr(cause, "code", None)
        if type(code) is not str or not code:
            raise TypeError("TypedRefusalError wraps only exceptions with a string code")
        super().__init__(f"{code}: {cause}")
        self.code = code
        self.cause = cause
        self.__cause__ = cause


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


class LedgerError(DomainError):
    """Base exception for append-only ledger integrity and persistence operations."""


class LedgerTruncationError(LedgerError):
    """Raised when an append-only ledger has suffered tail truncation or missing records."""


class LedgerIntegrityError(LedgerError):
    """Raised when ledger records suffer bit flips, hash chain breaks, or tampering."""


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
    "LedgerError",
    "LedgerIntegrityError",
    "LedgerTruncationError",
    "PacketSchemaError",
    "PayloadSizeLimitExceededError",
    "RefusalError",
    "SecurityPathViolationError",
    "SymbolGameDomainError",
    "TypedRefusalError",
]

