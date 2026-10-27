#!/usr/bin/env python3
"""Domain errors for the python_development_office Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

from operads.domain.operad.errors import DomainError


class SourceReadError(DomainError):
    """A source file could not be read as UTF-8."""

    def __init__(self, path: str, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(detail)


class PythonDevOfficeDomainError(ValueError):
    """Base exception for python development office domain invariant violations."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"PYTHON_DEV_OFFICE_DOMAIN_ERROR[{code}]: {detail}")


class ArchitecturePolicyViolationError(PythonDevOfficeDomainError):
    """Raised when an inward dependency or layer boundary invariant is breached."""

    def __init__(self, consumer: str, provider: str, detail: str) -> None:
        super().__init__(
            "ARCHITECTURE_INVERSION",
            f"module {consumer!r} illegally depends on {provider!r}: {detail}",
        )


class MalformedConfigurationError(PythonDevOfficeDomainError):
    """Raised when architecture configuration is structurally invalid or contains duplicates."""

    def __init__(self, detail: str) -> None:
        super().__init__("MALFORMED_CONFIG", detail)
