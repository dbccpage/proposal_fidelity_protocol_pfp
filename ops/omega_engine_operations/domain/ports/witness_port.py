"""Domain port and value objects for exact rational witness verification.

AuthorityEffect: None.
Clean Architecture Layer: Domain Ports / Value Objects.
Strict Invariants:
1. Exact rational arithmetic over integers: floating-point values are strictly rejected.
2. Value objects enforce exact-type equality (type(self) is type(other)).
3. All descriptors emit AuthorityEffect == "None".
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from omega_engine_operations.domain.rop.result import Refusal, Result

WITNESS_PORT_DEPRECATED_REFUSAL = Refusal(
    code="OPERATIONS_MATH_SHIM_DEPRECATED",
    message=(
        "Direct operations mathematics evaluation is deprecated; route requests to "
        "omega_solvers via RustWitnessAdapter or OEOS Rust host FFI."
    ),
    locus="omega_engine_operations.domain.ports.witness_port",
)


def emit_witness_port_deprecation_warning(subject: str) -> None:
    warnings.warn(
        f"{subject} in omega_engine_operations.domain.ports.witness_port is deprecated. "
        "Delegate exact rational calculations to omega_solvers via RustWitnessAdapter.",
        category=DeprecationWarning,
        stacklevel=3,
    )


class RationalError(Exception):
    """Base domain error for exact rational operations."""


class FloatForbiddenError(RationalError, TypeError):
    """Raised when an IEEE-754 float is passed where an exact rational is required."""


class WitnessVerificationError(RationalError):
    """Raised when witness verification fails domain structural invariants."""


@dataclass(frozen=True)
class ExactRational:
    """Strongly-typed exact rational number p/q over integers.

    Enforces exact integer representations, irreducible canonical form
    (gcd(p, q) == 1 with q > 0), and strict rejection of IEEE-754 floats.
    """

    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        emit_witness_port_deprecation_warning("ExactRational")
        if isinstance(self.numerator, float) or isinstance(self.denominator, float):
            raise FloatForbiddenError("Floating-point values are strictly forbidden in ExactRational")
        if type(self.numerator) is not int:
            raise FloatForbiddenError(
                f"numerator must be an exact integer, got {type(self.numerator).__name__}"
            )
        if type(self.denominator) is not int:
            raise FloatForbiddenError(
                f"denominator must be an exact integer, got {type(self.denominator).__name__}"
            )
        if self.denominator == 0:
            raise ZeroDivisionError("ExactRational denominator cannot be zero")

        # Normalize sign and reduce via GCD
        num = self.numerator
        den = self.denominator
        if den < 0:
            num = -num
            den = -den
        common = math.gcd(abs(num), den)
        object.__setattr__(self, "numerator", num // common)
        object.__setattr__(self, "denominator", den // common)

    @classmethod
    def from_str(cls, val_str: str) -> ExactRational:
        """Parse rational string representation 'p/q' or 'p'."""
        if not isinstance(val_str, str):
            raise TypeError(f"val_str must be a string, got {type(val_str).__name__}")
        cleaned = val_str.strip()
        if not cleaned:
            raise ValueError("Cannot parse empty rational string")
        if "." in cleaned:
            raise FloatForbiddenError(f"Floating-point representation forbidden in rational string: {val_str}")
        if "/" in cleaned:
            parts = cleaned.split("/")
            if len(parts) != 2:
                raise ValueError(f"Malformed rational string: {val_str}")
            return cls(int(parts[0].strip()), int(parts[1].strip()))
        return cls(int(cleaned), 1)

    def to_string(self) -> str:
        """Canonical string representation 'p/q'."""
        return f"{self.numerator}/{self.denominator}"

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"ExactRational({self.numerator}, {self.denominator})"

    def __add__(self, other: ExactRational) -> ExactRational:
        if type(self) is not type(other):
            return NotImplemented
        return ExactRational(
            self.numerator * other.denominator + other.numerator * self.denominator,
            self.denominator * other.denominator,
        )

    def __sub__(self, other: ExactRational) -> ExactRational:
        if type(self) is not type(other):
            return NotImplemented
        return ExactRational(
            self.numerator * other.denominator - other.numerator * self.denominator,
            self.denominator * other.denominator,
        )

    def __mul__(self, other: ExactRational) -> ExactRational:
        if type(self) is not type(other):
            return NotImplemented
        return ExactRational(
            self.numerator * other.numerator,
            self.denominator * other.denominator,
        )

    def __neg__(self) -> ExactRational:
        return ExactRational(-self.numerator, self.denominator)

    @property
    def is_zero(self) -> bool:
        return self.numerator == 0

    def __lt__(self, other: ExactRational) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.numerator * other.denominator < other.numerator * self.denominator

    def __le__(self, other: ExactRational) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.numerator * other.denominator <= other.numerator * self.denominator

    def __gt__(self, other: ExactRational) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.numerator * other.denominator > other.numerator * self.denominator

    def __ge__(self, other: ExactRational) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.numerator * other.denominator >= other.numerator * self.denominator

    def abs(self) -> ExactRational:
        """Return absolute value under canonical sign normalization."""
        return ExactRational(abs(self.numerator), self.denominator)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.numerator == other.numerator
            and self.denominator == other.denominator
        )

    def __hash__(self) -> int:
        return hash((type(self), self.numerator, self.denominator))


def _require_nonnegative_dimension(value: object, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_exact_matrix(
    matrix: tuple[tuple[ExactRational, ...], ...],
    *,
    rows: int,
    row_dim: str,
    cols: int,
    col_dim: str,
    name: str,
) -> None:
    if len(matrix) != rows:
        raise ValueError(f"{name} row count {len(matrix)} != {row_dim} {rows}")
    for row in matrix:
        if len(row) != cols:
            raise ValueError(f"{name} column count {len(row)} != {col_dim} {cols}")
        _require_rational_entries(name, row)


def _require_rational_entries(name: str, row: tuple[ExactRational, ...]) -> None:
    for entry in row:
        if type(entry) is not ExactRational:
            raise TypeError(f"{name} entries must be ExactRational, got {type(entry).__name__}")


def _composition_entry(
    d1_row: tuple[ExactRational, ...],
    d0: tuple[tuple[ExactRational, ...], ...],
    column: int,
    middle: int,
) -> ExactRational:
    comp_entry = ExactRational(0, 1)
    for index in range(middle):
        comp_entry = comp_entry + (d1_row[index] * d0[index][column])
    return comp_entry


def _require_chain_law(cochain: CochainComplex) -> None:
    for row_index, d1_row in enumerate(cochain.d1):
        for column in range(cochain.c0_dim):
            comp_entry = _composition_entry(d1_row, cochain.d0, column, cochain.c1_dim)
            if not comp_entry.is_zero:
                raise ValueError(
                    f"Cochain chain law d1*d0=0 violated at row {row_index}, col {column}"
                )


@dataclass(frozen=True)
class CochainComplex:
    """Exact rational cochain complex with verified chain law d1 * d0 = 0."""

    c0_dim: int
    c1_dim: int
    c2_dim: int
    d0: tuple[tuple[ExactRational, ...], ...]
    d1: tuple[tuple[ExactRational, ...], ...]

    def __post_init__(self) -> None:
        emit_witness_port_deprecation_warning("CochainComplex")
        _require_nonnegative_dimension(self.c0_dim, "c0_dim")
        _require_nonnegative_dimension(self.c1_dim, "c1_dim")
        _require_nonnegative_dimension(self.c2_dim, "c2_dim")
        _require_exact_matrix(
            self.d0,
            rows=self.c1_dim,
            row_dim="c1_dim",
            cols=self.c0_dim,
            col_dim="c0_dim",
            name="d0",
        )
        _require_exact_matrix(
            self.d1,
            rows=self.c2_dim,
            row_dim="c2_dim",
            cols=self.c1_dim,
            col_dim="c1_dim",
            name="d1",
        )
        _require_chain_law(self)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.c0_dim == other.c0_dim
            and self.c1_dim == other.c1_dim
            and self.c2_dim == other.c2_dim
            and self.d0 == other.d0
            and self.d1 == other.d1
        )

    def __hash__(self) -> int:
        return hash((type(self), self.c0_dim, self.c1_dim, self.c2_dim, self.d0, self.d1))


def _require_boundary_cochains(boundary: object) -> None:
    if not isinstance(boundary, Mapping):
        raise TypeError("boundary_cochains must be a mapping")
    for key, value in boundary.items():
        _require_boundary_entry(key, value)


def _require_boundary_entry(key: object, value: object) -> None:
    if type(key) is not str:
        raise TypeError("boundary_cochains keys must be str")
    if isinstance(value, float):
        raise FloatForbiddenError(f"Floating-point value {value} forbidden in boundary_cochains")
    if type(value) is not ExactRational:
        raise TypeError(
            f"boundary_cochains values must be ExactRational, got {type(value).__name__}"
        )


def _require_degree_k(degree_k: object) -> None:
    if degree_k is None:
        return
    if type(degree_k) is float:
        raise FloatForbiddenError("Floating-point value forbidden in degree_k")
    if type(degree_k) not in (int, ExactRational):
        raise TypeError(f"degree_k must be int or ExactRational, got {type(degree_k).__name__}")


@dataclass(frozen=True)
class WitnessVerificationRequest:
    """Request Value Object for exact rational witness verification."""

    boundary_cochains: Mapping[str, ExactRational]
    carrier_hash: str
    complex: CochainComplex | None = None
    degree_k: int | ExactRational | None = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _require_boundary_cochains(self.boundary_cochains)
        if type(self.carrier_hash) is not str or not self.carrier_hash:
            raise ValueError("carrier_hash must be a non-empty string")
        _require_degree_k(self.degree_k)
        if self.authority_effect != "None":
            raise ValueError("authority_effect must strictly be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.boundary_cochains == other.boundary_cochains
            and self.carrier_hash == other.carrier_hash
            and self.complex == other.complex
            and self.degree_k == other.degree_k
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        sorted_items = tuple(
            sorted((k, v.to_string()) for k, v in self.boundary_cochains.items())
        )
        return hash((
            type(self),
            sorted_items,
            self.carrier_hash,
            self.complex,
            self.degree_k,
            self.authority_effect,
        ))


@dataclass(frozen=True)
class WitnessVerificationResult:
    """Result Value Object representing certified rational witness evidence."""

    is_valid: bool
    residual_digest: str
    details: Mapping[str, Any]
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.is_valid) is not bool:
            raise TypeError("is_valid must be an exact bool")
        if type(self.residual_digest) is not str:
            raise TypeError("residual_digest must be an exact str")
        if not isinstance(self.details, Mapping):
            raise TypeError("details must be a mapping")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must strictly be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.is_valid == other.is_valid
            and self.residual_digest == other.residual_digest
            and dict(self.details) == dict(other.details)
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.is_valid,
            self.residual_digest,
            tuple(sorted((k, str(v)) for k, v in self.details.items())),
            self.authority_effect,
        ))


class IWitnessVerificationPort(Protocol):
    """Clean Architecture Domain Port for witness evaluation."""

    def verify_witness(
        self,
        request: WitnessVerificationRequest,
    ) -> Result[WitnessVerificationResult, Refusal]:
        """Evaluate an exact rational witness under railway return semantics."""
        ...
