#!/usr/bin/env python3
"""Domain errors for the packaging Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations


class PackagingDomainError(ValueError):
    """Base exception for agent system packaging and inventory invariants."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"PACKAGING_DOMAIN_ERROR[{code}]: {detail}")


class QuarantineViolationError(PackagingDomainError):
    """Raised when an asset in quarantine is routed or executed improperly."""

    def __init__(self, route: str) -> None:
        super().__init__("QUARANTINE_VIOLATION", f"asset {route!r} is under quarantine and cannot be routed")


class InventoryValidationError(PackagingDomainError):
    """Raised when an inventory manifest fails structural or byte-level validation."""

    def __init__(self, detail: str) -> None:
        super().__init__("INVENTORY_VALIDATION_FAILED", detail)
