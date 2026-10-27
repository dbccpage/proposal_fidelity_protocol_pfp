"""Authority Fence Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class AuthorityFenceError(ValueError):
    """Refusal for authority fence violations."""

    def __init__(self, residual: str) -> None:
        self.residual = residual
        super().__init__(residual)
