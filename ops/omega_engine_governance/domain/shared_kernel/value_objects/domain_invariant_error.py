"""Domain Invariant Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class DomainInvariantError(ValueError):
    """Refusal when a domain invariant or strongly-typed value constraint is violated."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)
