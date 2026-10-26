"""Shared Kernel: RegimeKind enum and Regime Value Object."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError


class RegimeKind(str, Enum):
    """Execution regime under which prompt or turn candidate is evaluated."""

    BRANCH_U_UNDECIDABLE = "branch_u_undecidable"
    BRANCH_O_OBSERVATIONAL = "branch_o_observational"
    BRANCH_Q_OPAQUE_NORMALIZER = "branch_q_opaque_normalizer"
    FENCE_ONLY = "fence_only"
    CODE_CHANGE = "code_change"
    RESEARCH_CLAIM = "research_claim"
    CUSTOM_BOUND = "custom_bound"
    CODA_L1 = "coda_l1"
    CODA_REGGE_MC_4D = "coda_regge_mc_4d"
    SYMBOL_ONLY = "symbol_only"
    FINITE_LIBRARY = "finite_library"


REGIME_KINDS: frozenset[str] = frozenset(k.value for k in RegimeKind)


@dataclass(frozen=True, slots=True, eq=False)
class Regime:
    """Enriched Value Object representing an evaluation regime."""

    value: str = RegimeKind.SYMBOL_ONLY.value

    VALID_REGIMES: ClassVar[frozenset[str]] = REGIME_KINDS

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"Regime must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip().lower()
        if val not in self.VALID_REGIMES:
            raise InvariantViolationError(
                f"Invalid Regime {val!r}: must be one of {sorted(self.VALID_REGIMES)}"
            )
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def symbol_only(cls) -> Regime:
        return cls(RegimeKind.SYMBOL_ONLY.value)

    @classmethod
    def fence_only(cls) -> Regime:
        return cls(RegimeKind.FENCE_ONLY.value)

    @classmethod
    def coda_l1(cls) -> Regime:
        return cls(RegimeKind.CODA_L1.value)

    @classmethod
    def from_str(cls: type[Self], val: str | Self | RegimeKind) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, RegimeKind):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str or RegimeKind, got {type(val).__name__}"
            )
        return cls(val)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Regime(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
