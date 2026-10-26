"""Shared Kernel: Residual Drop Value Object for discrete coboundary decay tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Self

from ..exceptions import InvariantViolationError


@dataclass(frozen=True, slots=True)
class ResidualDropV1:
    """Discrete residual drop measurements: (delta_phi1, delta_gamma2, delta_xi)."""

    delta_phi1: float
    delta_gamma2: float
    delta_xi: float

    def __post_init__(self) -> None:
        for name, val in (
            ("delta_phi1", self.delta_phi1),
            ("delta_gamma2", self.delta_gamma2),
            ("delta_xi", self.delta_xi),
        ):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise InvariantViolationError(
                    f"ResidualDropV1 {name} must be numeric, got {type(val).__name__}"
                )

    @classmethod
    def create(
        cls: type[Self],
        *,
        delta_phi1: float,
        delta_gamma2: float = 0.0,
        delta_xi: float = 0.0,
    ) -> Self:
        return cls(
            delta_phi1=float(delta_phi1),
            delta_gamma2=float(delta_gamma2),
            delta_xi=float(delta_xi),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "delta_phi1": self.delta_phi1,
            "delta_gamma2": self.delta_gamma2,
            "delta_xi": self.delta_xi,
        }

    @classmethod
    def from_dict(cls: type[Self], data: Mapping[str, Any]) -> Self:
        return cls(
            delta_phi1=float(data.get("delta_phi1", 0.0)),
            delta_gamma2=float(data.get("delta_gamma2", 0.0)),
            delta_xi=float(data.get("delta_xi", 0.0)),
        )

    @classmethod
    def from_float(cls: type[Self], val: float | int | Self) -> Self:
        if isinstance(val, cls):
            return val
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise InvariantViolationError(
                f"{cls.__name__}.from_float requires numeric float/int, got {type(val).__name__}"
            )
        return cls(delta_phi1=float(val), delta_gamma2=0.0, delta_xi=0.0)

    @classmethod
    def from_numeric(cls: type[Self], val: float | int | Self) -> Self:
        return cls.from_float(val)

    def __float__(self) -> float:
        return float(self.delta_phi1 + self.delta_gamma2 + self.delta_xi)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return (
            self.delta_phi1 == other.delta_phi1
            and self.delta_gamma2 == other.delta_gamma2
            and self.delta_xi == other.delta_xi
        )

    def __hash__(self) -> int:
        return hash((type(self), self.delta_phi1, self.delta_gamma2, self.delta_xi))

    def is_strictly_contractive(self) -> bool:
        """Predicate checking if all components decayed or stayed constant with at least one strictly positive drop."""
        return (
            self.delta_phi1 >= 0.0
            and self.delta_gamma2 >= 0.0
            and self.delta_xi >= 0.0
            and (self.delta_phi1 + self.delta_gamma2 + self.delta_xi > 0.0)
        )


ResidualDrop = ResidualDropV1
