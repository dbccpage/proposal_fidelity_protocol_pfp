"""Shared Kernel: GateId Value Object for verification gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError
from .id import Identifier


@dataclass(frozen=True, slots=True)
class GateId(Identifier):
    """Identifier representing a verification gate (e.g. gate_syntax, gate_ownership)."""

    DEFAULT_GATES: ClassVar[tuple[str, ...]] = (
        "gate_syntax",
        "gate_ownership",
        "gate_contract",
    )

    @classmethod
    def syntax(cls: type[Self]) -> Self:
        return cls("gate_syntax")

    @classmethod
    def ownership(cls: type[Self]) -> Self:
        return cls("gate_ownership")

    @classmethod
    def contract(cls: type[Self]) -> Self:
        return cls("gate_contract")
