"""Discrete Difference Calculus (DDC) primitives and tape transitions.

Zero host I/O, zero external framework imports.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


class DifferencePrimitive(str, Enum):
    """The 8 canonical Difference Primitives of the CODA stack."""

    INHABIT = "INHABIT"
    SEPARATE = "SEPARATE"
    PERMUTE = "PERMUTE"
    CONTRACT = "CONTRACT"
    EXPAND = "EXPAND"
    PROJECT = "PROJECT"
    RETRACT = "RETRACT"
    TERMINATE = "TERMINATE"


@dataclass(frozen=True)
class DDCStep:
    """One atomic step in a discrete difference calculus transition."""

    step_index: int
    primitive: DifferencePrimitive
    cost: int
    carrier_in_size: int
    carrier_out_size: int
    obstruction_in: int
    obstruction_out: int
    fuel_remaining: int
    delta: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "delta", self.carrier_out_size - self.carrier_in_size)
        if self.cost < 0:
            raise ValueError("DDCStep cost must be non-negative")
        if self.fuel_remaining < 0:
            raise ValueError("DDCStep fuel cannot be negative")

    def is_contractive(self) -> bool:
        """Asserts non-increasing obstruction count."""
        return self.obstruction_out <= self.obstruction_in


@dataclass(frozen=True)
class DDCTape:
    """Ordered immutable execution tape of DDC steps."""

    tape_id: str
    steps: Tuple[DDCStep, ...]
    initial_fuel: int
    final_status: str = "PASS"

    @property
    def total_cost(self) -> int:
        return sum(s.cost for s in self.steps)

    @property
    def is_fuel_conserved(self) -> bool:
        if not self.steps:
            return True
        return (self.initial_fuel - self.total_cost) == self.steps[-1].fuel_remaining

    @property
    def is_monotone_contractive(self) -> bool:
        return all(s.is_contractive() for s in self.steps)
