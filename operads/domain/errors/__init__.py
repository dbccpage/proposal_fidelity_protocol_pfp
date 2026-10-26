"""Typed domain errors for OEWAS V3."""

from .domain_errors import (
    AuthorityCeilingExceededError,
    DomainInvariantError,
    InvalidCompositionError,
    OeopDomainError,
    SchemaMismatchError,
    UnresolvedResidualError,
)

__all__ = [
    "AuthorityCeilingExceededError",
    "DomainInvariantError",
    "InvalidCompositionError",
    "OeopDomainError",
    "SchemaMismatchError",
    "UnresolvedResidualError",
]
