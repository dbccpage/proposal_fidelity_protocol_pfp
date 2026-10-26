"""Aggregate Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class AggregateError(ValueError):
    def __init__(self, residual: str) -> None:
        self.residual = residual
        super().__init__(residual)
