"""Pure cochain math, boundary matrix, integer chain, and dual certificate.

Zero host I/O, zero external framework imports.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence, Tuple


def require_integer(value: object) -> None:
    if type(value) is not int:
        raise TypeError("Expected an integer; coercion of witnesses is forbidden")


def require_rational(value: object) -> None:
    if type(value) not in (int, Fraction):
        raise TypeError("Expected an exact integer or Fraction")


def validate_shape(rows: int, cols: int, data: Sequence[Sequence[object]], check_entry) -> None:
    require_integer(rows)
    require_integer(cols)
    if rows < 0 or cols < 0 or len(data) != rows:
        raise ValueError("Invalid matrix dimensions")
    for row in data:
        if len(row) != cols:
            raise ValueError("Ragged matrix or incorrect column count")
        for value in row:
            check_entry(value)


@dataclass(frozen=True)
class BoundaryMatrix:
    """Exact rational boundary matrix d_k acting on chains or cochains."""

    rows: int
    cols: int
    data: Tuple[Tuple[Fraction, ...], ...]

    def __post_init__(self) -> None:
        validate_shape(self.rows, self.cols, self.data, require_rational)

    @classmethod
    def from_nested_ints(cls, raw: Sequence[Sequence[int]]) -> BoundaryMatrix:
        rows = len(raw)
        cols = len(raw[0]) if rows > 0 else 0
        for row in raw:
            for val in row:
                require_integer(val)
        data = tuple(tuple(Fraction(val) for val in row) for row in raw)
        return cls(rows=rows, cols=cols, data=data)

    def multiply_vector(self, vec: Sequence[Fraction]) -> Tuple[Fraction, ...]:
        if len(vec) != self.cols:
            raise ValueError(f"Matrix cols {self.cols} != vector length {len(vec)}")
        for value in vec:
            require_rational(value)
        out = []
        for r in range(self.rows):
            s = Fraction(0)
            for c in range(self.cols):
                s += self.data[r][c] * vec[c]
            out.append(s)
        return tuple(out)

    def transpose(self) -> BoundaryMatrix:
        if self.rows == 0:
            return BoundaryMatrix(rows=0, cols=0, data=())
        t_data = tuple(
            tuple(self.data[r][c] for r in range(self.rows)) for c in range(self.cols)
        )
        return BoundaryMatrix(rows=self.cols, cols=self.rows, data=t_data)


@dataclass(frozen=True)
class IntegerChain:
    """Exact integer chain c in C_k."""

    dimension: int
    coefficients: Tuple[int, ...]

    def __post_init__(self) -> None:
        require_integer(self.dimension)
        if self.dimension < 0:
            raise ValueError("Chain dimension must be non-negative")
        for coeff in self.coefficients:
            require_integer(coeff)

    @property
    def length(self) -> int:
        return len(self.coefficients)


@dataclass(frozen=True)
class Cochain:
    """Exact rational cochain omega in C^k."""

    dimension: int
    values: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        require_integer(self.dimension)
        if self.dimension < 0:
            raise ValueError("Cochain dimension must be non-negative")
        for val in self.values:
            require_rational(val)

    @classmethod
    def from_ints(cls, dimension: int, values: Sequence[int]) -> Cochain:
        require_integer(dimension)
        for val in values:
            require_integer(val)
        return cls(dimension=dimension, values=tuple(Fraction(v) for v in values))

    def evaluate_chain(self, chain: IntegerChain) -> Fraction:
        if self.dimension != chain.dimension:
            raise ValueError("Dimension mismatch between cochain and chain")
        if len(self.values) != chain.length:
            raise ValueError("Length mismatch between cochain and chain")
        total = Fraction(0)
        for val, coeff in zip(self.values, chain.coefficients):
            total += val * coeff
        return total


@dataclass(frozen=True)
class IntegerMatrix:
    """Exact integer matrix for Smith Normal Form computations."""

    rows: int
    cols: int
    data: Tuple[Tuple[int, ...], ...]

    def __post_init__(self) -> None:
        validate_shape(self.rows, self.cols, self.data, require_integer)


@dataclass(frozen=True)
class SmithNormalFormResult:
    """Result of Smith Normal Form decomposition S = U * A * V."""

    d_matrix: IntegerMatrix
    u_matrix: IntegerMatrix
    v_matrix: IntegerMatrix
    invariant_factors: Tuple[int, ...]
    rank: int


@dataclass(frozen=True)
class DualCertificate:
    """Dual certificate verifying feasibility or optimality under linear constraints."""

    dual_multipliers: Tuple[Fraction, ...]
    primal_residual: Fraction
    dual_residual: Fraction
    is_primal_feasible: bool
    is_dual_feasible: bool
    duality_gap: Fraction
