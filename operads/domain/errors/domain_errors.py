"""Typed domain errors and invariant violations for OEWAS V3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class OeopDomainError(Exception):
    code: str
    message: str
    locus: str = ""
    details: Tuple[Tuple[str, str], ...] = ()

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}" if not self.locus else f"[{self.code} @ {self.locus}] {self.message}"


@dataclass(frozen=True)
class DomainInvariantError(OeopDomainError):
    pass


@dataclass(frozen=True)
class SchemaMismatchError(OeopDomainError):
    pass


@dataclass(frozen=True)
class UnresolvedResidualError(OeopDomainError):
    pass


@dataclass(frozen=True)
class AuthorityCeilingExceededError(OeopDomainError):
    pass


@dataclass(frozen=True)
class InvalidCompositionError(OeopDomainError):
    pass
