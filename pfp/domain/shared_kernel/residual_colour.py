"""Shared Kernel: Residual colour enumeration for algebraic error tracking."""

from __future__ import annotations

from enum import Enum


class ResidualColour(str, Enum):
    """Residual colour indicator."""

    OPEN = "Open"
    CLOSED = "Closed"
    EXACT = "Exact"


RESIDUAL_COLOURS: frozenset[str] = frozenset(c.value for c in ResidualColour)
