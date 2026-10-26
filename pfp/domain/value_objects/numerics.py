"""Strongly typed Domain Numeric Value Objects.

AuthorityEffect: None.
Eliminates primitive obsession for integer bounds, rungs, budgets, and temperatures.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .base import ValueObject


def _require_pure_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a strict int, got {type(value).__name__}")
    return value


@dataclass(frozen=True)
class DifficultyRung(ValueObject):
    """Discrete problem difficulty rung strictly bounded in [1, 5]."""

    value: int

    def __post_init__(self) -> None:
        val = _require_pure_int("DifficultyRung", self.value)
        if val < 1 or val > 5:
            raise ValueError(f"DifficultyRung must be between 1 and 5 inclusive, got {val}")

    def __int__(self) -> int:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.int_schema(ge=1, le=5),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class MicroUsdSpend(ValueObject):
    """Exact non-negative monetary spend in micro-USD (1 USD = 1,000,000 micro-USD).

    Eliminates floating-point rounding errors and drift in budget accounting.
    """

    value: int

    def __post_init__(self) -> None:
        val = _require_pure_int("MicroUsdSpend", self.value)
        if val < 0:
            raise ValueError(f"MicroUsdSpend cannot be negative, got {val}")

    @classmethod
    def from_usd(cls, usd: float | int | Decimal) -> MicroUsdSpend:
        if isinstance(usd, (int, float, Decimal)):
            micros = int(round(float(usd) * 1_000_000))
            return cls(value=micros)
        raise TypeError(f"Cannot convert {type(usd).__name__} to MicroUsdSpend")

    def to_usd(self) -> float:
        return self.value / 1_000_000.0

    def __int__(self) -> int:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.int_schema(ge=0),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class BoundedTemperature(ValueObject):
    """Sampling temperature strictly bounded in [0.0, 2.0]."""

    value: float

    def __post_init__(self) -> None:
        if type(self.value) not in (int, float):
            raise TypeError(f"BoundedTemperature must be float or int, got {type(self.value).__name__}")
        f_val = float(self.value)
        if f_val < 0.0 or f_val > 2.0:
            raise ValueError(f"BoundedTemperature must be between 0.0 and 2.0, got {f_val}")
        object.__setattr__(self, "value", f_val)

    def __float__(self) -> float:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.float_schema(ge=0.0, le=2.0),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class StageNumber(ValueObject):
    """Pipeline stage number strictly bounded in [1, 11] (the public stages of pfp-staged.0.3)."""

    value: int

    def __post_init__(self) -> None:
        val = _require_pure_int("StageNumber", self.value)
        if val < 1 or val > 11:
            raise ValueError(f"StageNumber must be between 1 and 11 inclusive, got {val}")

    def __int__(self) -> int:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.int_schema(ge=1, le=11),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class StratumLevel(ValueObject):
    """Epistemic S(n) stratum index strictly bounded in [0, 6]."""

    value: int

    def __post_init__(self) -> None:
        val = _require_pure_int("StratumLevel", self.value)
        if val < 0 or val > 6:
            raise ValueError(f"StratumLevel must be between 0 and 6 inclusive, got {val}")

    def __int__(self) -> int:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.int_schema(ge=0, le=6),
            )
        except ImportError:
            return None
