"""Strict finite QDDC wire contracts; mathematical validation belongs to Rust.

An operator-valued cochain is not a collection of density states. These models
validate syntax and shape; native constructors check Hermiticity, chain laws,
positivity, and trace. AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Annotated, Protocol, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

MAX_OUTPUT_RATIONAL_BITS = 8192
MAX_OUTPUT_RATIONAL_TEXT_BYTES = 6000


def _rational(value: str) -> str:
    if len(value) > MAX_OUTPUT_RATIONAL_TEXT_BYTES:
        raise ValueError("rational text exceeds output bound")
    try:
        number = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("expected a canonical rational string") from error
    if str(number) != value:
        raise ValueError("expected a canonical rational string")
    if (
        max(number.numerator.bit_length(), number.denominator.bit_length())
        > MAX_OUTPUT_RATIONAL_BITS
    ):
        raise ValueError("rational exceeds output bit bound")
    return value


RationalText = Annotated[str, Field(strict=True), AfterValidator(_rational)]
Dimension = Annotated[int, Field(strict=True, ge=0, le=32)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RationalMatrix(Contract):
    rows: Dimension
    cols: Dimension
    data: tuple[tuple[RationalText, ...], ...]

    @model_validator(mode="after")
    def shaped(self) -> Self:
        if len(self.data) != self.rows or any(len(row) != self.cols for row in self.data):
            raise ValueError("matrix data must match declared shape")
        return self


class Operator(Contract):
    real: RationalMatrix
    imag: RationalMatrix

    @model_validator(mode="after")
    def square(self) -> Self:
        n = self.real.rows
        if not 1 <= n <= 8 or (self.real.cols, self.imag.rows, self.imag.cols) != (n, n, n):
            raise ValueError("operator must have matching square parts of dimension 1..8")
        return self


class QddcState(Contract):
    d_prev: RationalMatrix
    d_next: RationalMatrix
    operator_dim: Annotated[int, Field(strict=True, ge=1, le=8)]
    cochain: tuple[Operator, ...] = Field(max_length=32)

    @model_validator(mode="after")
    def shaped(self) -> Self:
        if self.d_prev.rows != len(self.cochain) or self.d_next.cols != len(self.cochain):
            raise ValueError("cochain length must match both differentials")
        if any(op.real.rows != self.operator_dim for op in self.cochain):
            raise ValueError("cochain operator dimensions must match")
        return self


class HodgeResult(Contract):
    alpha: tuple[Operator, ...] = Field(max_length=32)
    beta: tuple[Operator, ...] = Field(max_length=32)
    exact: tuple[Operator, ...] = Field(max_length=32)
    coexact: tuple[Operator, ...] = Field(max_length=32)
    harmonic: tuple[Operator, ...] = Field(max_length=32)
    scalar_ops: Annotated[int, Field(strict=True, ge=0, le=4_000_000)]


class LindbladRequest(Contract):
    rho: Operator
    hamiltonian: Operator
    jumps: tuple[Operator, ...] = Field(max_length=16)


class LindbladResult(Contract):
    derivative: Operator


class RepairProjectorResult(Contract):
    projector: Operator


class RetractionRequest(Contract):
    rho: Operator
    projector: Operator
    eta: RationalText


class RetractionResult(Contract):
    rho: Operator
    outside_before: RationalText
    outside_after: RationalText


class ProbeRequest(Contract):
    rho: Operator
    projector: Operator


class ProbeResult(Contract):
    probability: RationalText
    conditional: Operator | None


class DeformationRequest(Contract):
    state: QddcState
    alpha: tuple[Operator, ...] = Field(max_length=32)
    unitary: Operator


class DeformationResult(Contract):
    cochain: tuple[Operator, ...] = Field(max_length=32)


class DensityRequest(Contract):
    rho: Operator


class DensityResult(Contract):
    purity: RationalText
    is_pure: bool


class QddcPort(Protocol):
    def hodge(self, state: QddcState) -> HodgeResult: ...
    def repair_projector(self, state: QddcState) -> RepairProjectorResult: ...
    def lindblad(self, request: LindbladRequest) -> LindbladResult: ...
    def retract(self, request: RetractionRequest) -> RetractionResult: ...
    def probe(self, request: ProbeRequest) -> ProbeResult: ...
    def deform(self, request: DeformationRequest) -> DeformationResult: ...
    def density(self, request: DensityRequest) -> DensityResult: ...
