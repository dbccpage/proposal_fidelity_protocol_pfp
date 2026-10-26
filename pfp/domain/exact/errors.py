"""Exact arithmetic domain errors and refusals.

Classification: Domain Exact Kernel.
AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_pfp.domain.exceptions import DomainError


class ExactRefusal(DomainError):
    """A refusal by exact code and optional detail prose."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class ExactError(ExactRefusal):
    """Exact arithmetic or serialization refused a value (RR-FLOAT, etc.)."""


__all__ = ["ExactError", "ExactRefusal"]
