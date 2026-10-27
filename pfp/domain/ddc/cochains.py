"""Graded Cochains (C^0, C^1, C^2) with exact rational coefficients.

Implements graded cochain spaces over Q (using Python's exact Fraction representation):
- C^0: 0-cochains on vertices (potentials, local namings)
- C^1: 1-cochains on directed edges (differential 1-forms, edge claims)
- C^2: 2-cochains on oriented faces (2-forms, curvature defects)

All algebraic operations (+, -, scalar multiplication, weighted L1 norms) are exact
and preserve rational numbers with zero floating-point error.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import (
    Any,
    Dict,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

NumberLike = Union[int, Fraction, float]


def _to_fraction(val: Any) -> Fraction:
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val)
    if isinstance(val, float):
        return Fraction.from_float(val).limit_denominator(1_000_000)
    if isinstance(val, str):
        return Fraction(val)
    return Fraction(val)


FUNCTIONAL_OWNER = "engine/crates_rs/core_functional/src"


class FunctionalBoundaryUnavailable(RuntimeError):
    """No Rust-backed adapter is available for a DDC functional request."""

    code = "FUNCTIONAL_BOUNDARY_UNAVAILABLE"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or (
                f"{self.code}: Python DDC cannot calculate Phi1, Gamma2, Xi, or L1 norms; "
                f"{FUNCTIONAL_OWNER} is the sole calculator and no Rust-backed "
                "DDC adapter is wired."
            )
        )


@dataclass(frozen=True)
class Cochain0:
    """0-Cochain over complex vertices with exact rational values.

    Maps vertex names v to exact Fraction values f(v).
    """

    values: Mapping[str, Fraction]

    def __post_init__(self) -> None:
        clean = {str(k): _to_fraction(v) for k, v in self.values.items()}
        object.__setattr__(self, "values", clean)

    def get(self, v: str) -> Fraction:
        return self.values.get(v, Fraction(0))

    def __getitem__(self, v: str) -> Fraction:
        return self.get(v)

    def __contains__(self, v: str) -> bool:
        return v in self.values

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def support(self) -> Set[str]:
        """Set of vertices with non-zero potential."""
        return {v for v, val in self.values.items() if val != Fraction(0)}

    def l1_norm(self) -> Fraction:
        """Refuse Python L1 norm calculation; core_functional is the sole authority."""
        raise FunctionalBoundaryUnavailable()


    def __add__(self, other: Cochain0) -> Cochain0:
        if not isinstance(other, Cochain0):
            return NotImplemented
        keys = set(self.values.keys()) | set(other.values.keys())
        return Cochain0({k: self.get(k) + other.get(k) for k in keys})

    def __sub__(self, other: Cochain0) -> Cochain0:
        if not isinstance(other, Cochain0):
            return NotImplemented
        keys = set(self.values.keys()) | set(other.values.keys())
        return Cochain0({k: self.get(k) - other.get(k) for k in keys})

    def __neg__(self) -> Cochain0:
        return Cochain0({k: -val for k, val in self.values.items()})

    def __mul__(self, scalar: NumberLike) -> Cochain0:
        s = _to_fraction(scalar)
        return Cochain0({k: val * s for k, val in self.values.items()})

    def __rmul__(self, scalar: NumberLike) -> Cochain0:
        return self.__mul__(scalar)

    def to_dict(self) -> Dict[str, Fraction]:
        return dict(self.values)

    @classmethod
    def zero(cls, vertices: Sequence[str]) -> Cochain0:
        return cls({v: Fraction(0) for v in vertices})


@dataclass(frozen=True)
class Cochain1:
    """1-Cochain over directed edges with exact rational values.

    Maps directed edge tuples (u, v) to exact Fraction values h(u, v).
    """

    values: Mapping[Tuple[str, str], Fraction]

    def __post_init__(self) -> None:
        clean = {(str(u), str(v)): _to_fraction(val) for (u, v), val in self.values.items()}
        object.__setattr__(self, "values", clean)

    def get(self, u: str, v: str) -> Fraction:
        """Returns the value on directed edge (u, v).

        Defaults to Fraction(0) if not explicitly present.
        """
        return self.values.get((u, v), Fraction(0))

    def __getitem__(self, edge: Tuple[str, str]) -> Fraction:
        return self.get(edge[0], edge[1])

    def __contains__(self, edge: Tuple[str, str]) -> bool:
        return (edge[0], edge[1]) in self.values

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        return iter(self.values)

    def support(self) -> Set[Tuple[str, str]]:
        """Set of edges where cochain value is non-zero."""
        return {e for e, val in self.values.items() if val != Fraction(0)}

    def l1_norm(
        self,
        weights: Optional[Mapping[Tuple[str, str], NumberLike]] = None,
    ) -> Fraction:
        """Refuse Python L1 norm calculation; core_functional is the sole authority."""
        raise FunctionalBoundaryUnavailable()


    def __add__(self, other: Cochain1) -> Cochain1:
        if not isinstance(other, Cochain1):
            return NotImplemented
        keys = set(self.values.keys()) | set(other.values.keys())
        return Cochain1({k: self.get(k[0], k[1]) + other.get(k[0], k[1]) for k in keys})

    def __sub__(self, other: Cochain1) -> Cochain1:
        if not isinstance(other, Cochain1):
            return NotImplemented
        keys = set(self.values.keys()) | set(other.values.keys())
        return Cochain1({k: self.get(k[0], k[1]) - other.get(k[0], k[1]) for k in keys})

    def __neg__(self) -> Cochain1:
        return Cochain1({k: -val for k, val in self.values.items()})

    def __mul__(self, scalar: NumberLike) -> Cochain1:
        s = _to_fraction(scalar)
        return Cochain1({k: val * s for k, val in self.values.items()})

    def __rmul__(self, scalar: NumberLike) -> Cochain1:
        return self.__mul__(scalar)

    def to_dict(self) -> Dict[Tuple[str, str], Fraction]:
        return dict(self.values)

    @classmethod
    def zero(cls, edges: Sequence[Tuple[str, str]]) -> Cochain1:
        return cls({e: Fraction(0) for e in edges})


@dataclass(frozen=True)
class Cochain2:
    """2-Cochain over oriented 2-simplices with exact rational values.

    Maps face tuples (u, v, w) to exact Fraction values c(u, v, w).
    """

    values: Mapping[Tuple[str, str, str], Fraction]

    def __post_init__(self) -> None:
        clean = {
            (str(u), str(v), str(w)): _to_fraction(val)
            for (u, v, w), val in self.values.items()
        }
        object.__setattr__(self, "values", clean)

    def get(self, u: str, v: str, w: str) -> Fraction:
        return self.values.get((u, v, w), Fraction(0))

    def __getitem__(self, face: Tuple[str, str, str]) -> Fraction:
        return self.get(face[0], face[1], face[2])

    def __contains__(self, face: Tuple[str, str, str]) -> bool:
        return (face[0], face[1], face[2]) in self.values

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[Tuple[str, str, str]]:
        return iter(self.values)

    def support(self) -> Set[Tuple[str, str, str]]:
        """Set of faces where 2-cochain value is non-zero."""
        return {f for f, val in self.values.items() if val != Fraction(0)}

    def l1_norm(self) -> Fraction:
        """Refuse Python L1 norm calculation; core_functional is the sole authority."""
        raise FunctionalBoundaryUnavailable()


    def __add__(self, other: Cochain2) -> Cochain2:
        if not isinstance(other, Cochain2):
            return NotImplemented
        keys = set(self.values.keys()) | set(other.values.keys())
        return Cochain2({k: self.get(k[0], k[1], k[2]) + other.get(k[0], k[1], k[2]) for k in keys})

    def __sub__(self, other: Cochain2) -> Cochain2:
        if not isinstance(other, Cochain2):
            return NotImplemented
        keys = set(self.values.keys()) | set(other.values.keys())
        return Cochain2({k: self.get(k[0], k[1], k[2]) - other.get(k[0], k[1], k[2]) for k in keys})

    def __neg__(self) -> Cochain2:
        return Cochain2({k: -val for k, val in self.values.items()})

    def __mul__(self, scalar: NumberLike) -> Cochain2:
        s = _to_fraction(scalar)
        return Cochain2({k: val * s for k, val in self.values.items()})

    def __rmul__(self, scalar: NumberLike) -> Cochain2:
        return self.__mul__(scalar)

    def to_dict(self) -> Dict[Tuple[str, str, str], Fraction]:
        return dict(self.values)

    @classmethod
    def zero(cls, faces: Sequence[Tuple[str, str, str]]) -> Cochain2:
        return cls({f: Fraction(0) for f in faces})
