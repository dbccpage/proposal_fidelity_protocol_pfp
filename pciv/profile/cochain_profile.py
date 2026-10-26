"""One prompt profile whose checker is ``verify_cochain_complex``.

``omega_ooutwire_primitives::alpha_projection_obstruction::cochain_presentation::verify_cochain_complex``
is Rust-only. This module is the pure-Python admission check for that
function: ``d1 ∘ d0 = 0`` on exact integer or rational matrices, and a
refusal otherwise. Phi1 is the exact ℓ¹ mass of that composition residual.
An AST defect count is not phi1.

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

PROFILE_NAME = "prompt_cochain_complex_v1"
CHECKER_NAME = "verify_cochain_complex"

_HIGHER_DIFFERENTIAL_UNAVAILABLE = (
    "PO-000 native covering-edge data supplies no C2 or d1"
)
_DIMENSIONS_DO_NOT_COMPOSE = "d1 and d0 dimensions do not compose"
_COMPLEX_CONDITION_FAILED = "d1*d0=0 complex condition failed"
_NON_EXACT_ENTRY = (
    "d1*d0=0 complex condition failed: entry is not an exact integer or rational"
)


class CochainRefusal(Exception):
    """Refusal from the prompt cochain checker. AuthorityEffect: None."""


class HigherDifferentialUnavailable(CochainRefusal):
    """``d1`` was not supplied, matching the Rust refusal of that name."""


class ComplexConditionFailed(CochainRefusal):
    """Shapes do not compose, entries are not exact, or ``d1 ∘ d0 ≠ 0``."""


@dataclass(frozen=True, slots=True)
class ExactMatrix:
    """Row-major exact matrix. Well-formed means ``rows * cols == len(data)``."""

    rows: int
    cols: int
    data: tuple[Fraction, ...]

    def is_well_formed(self) -> bool:
        return self.rows >= 0 and self.cols >= 0 and self.rows * self.cols == len(self.data)

    def is_zero(self) -> bool:
        return all(entry == 0 for entry in self.data)

    def l1_norm(self) -> Fraction:
        total = Fraction(0, 1)
        for entry in self.data:
            total += abs(entry)
        return total

    def rows_tuple(self) -> tuple[tuple[Fraction, ...], ...]:
        width = self.cols
        return tuple(
            self.data[index * width : (index + 1) * width] for index in range(self.rows)
        )


@dataclass(frozen=True, slots=True)
class AdmittedComplexV1:
    """Complex admitted by ``verify_cochain_complex``, with its composition residual."""

    d0: ExactMatrix
    d1: ExactMatrix
    residual: ExactMatrix
    phi1: Fraction


def _exact_entry(value: object) -> Fraction:
    if type(value) is int:
        return Fraction(value, 1)
    if type(value) is Fraction:
        return Fraction(value.numerator, value.denominator)
    raise ComplexConditionFailed(_NON_EXACT_ENTRY)


def _parse_matrix(value: object) -> ExactMatrix:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ComplexConditionFailed(_DIMENSIONS_DO_NOT_COMPOSE)
    rows = list(value)
    if not rows:
        matrix = ExactMatrix(rows=0, cols=0, data=())
    else:
        parsed_rows: list[tuple[Fraction, ...]] = []
        width: int | None = None
        for row in rows:
            if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
                raise ComplexConditionFailed(_DIMENSIONS_DO_NOT_COMPOSE)
            entries = tuple(_exact_entry(entry) for entry in row)
            if width is None:
                width = len(entries)
            elif len(entries) != width:
                raise ComplexConditionFailed(_DIMENSIONS_DO_NOT_COMPOSE)
            parsed_rows.append(entries)
        matrix = ExactMatrix(
            rows=len(parsed_rows),
            cols=width or 0,
            data=tuple(entry for row in parsed_rows for entry in row),
        )
    if not matrix.is_well_formed():
        raise ComplexConditionFailed(_DIMENSIONS_DO_NOT_COMPOSE)
    return matrix


def _matmul(left: ExactMatrix, right: ExactMatrix) -> ExactMatrix:
    if left.cols != right.rows:
        raise ComplexConditionFailed(_DIMENSIONS_DO_NOT_COMPOSE)
    data: list[Fraction] = []
    for row_index in range(left.rows):
        for col_index in range(right.cols):
            total = Fraction(0, 1)
            for shared in range(left.cols):
                total += left.data[row_index * left.cols + shared] * right.data[
                    shared * right.cols + col_index
                ]
            data.append(total)
    return ExactMatrix(rows=left.rows, cols=right.cols, data=tuple(data))


def verify_cochain_complex(d0: object, d1: object = None) -> AdmittedComplexV1:
    """Admit ``d1 ∘ d0 = 0`` exactly, or refuse.

    Matches the admitted condition of the Rust ``verify_cochain_complex``:
    missing ``d1`` is refused, non-exact or non-composing matrices are
    refused, and a non-zero composition is refused. The admitted residual
    is that composition; its exact ℓ¹ mass is phi1.
    """
    if d1 is None:
        raise HigherDifferentialUnavailable(_HIGHER_DIFFERENTIAL_UNAVAILABLE)
    parsed_d0 = _parse_matrix(d0)
    parsed_d1 = _parse_matrix(d1)
    if (
        not parsed_d0.is_well_formed()
        or not parsed_d1.is_well_formed()
        or parsed_d1.cols != parsed_d0.rows
    ):
        raise ComplexConditionFailed(_DIMENSIONS_DO_NOT_COMPOSE)
    residual = _matmul(parsed_d1, parsed_d0)
    if not residual.is_zero():
        raise ComplexConditionFailed(_COMPLEX_CONDITION_FAILED)
    return AdmittedComplexV1(
        d0=parsed_d0,
        d1=parsed_d1,
        residual=residual,
        phi1=residual.l1_norm(),
    )


@dataclass(frozen=True, slots=True)
class PromptCochainProfile:
    """The one prompt profile bound to ``verify_cochain_complex``."""

    name: str
    checker_name: str

    def admit(self, d0: object, d1: object = None) -> AdmittedComplexV1:
        """Run this profile's named checker and return its admitted residual."""
        checker = globals()[self.checker_name]
        if checker is not verify_cochain_complex:
            raise ComplexConditionFailed(
                "profile checker is not verify_cochain_complex"
            )
        return checker(d0, d1)


PROMPT_COCHAIN_COMPLEX_PROFILE = PromptCochainProfile(
    name=PROFILE_NAME,
    checker_name=CHECKER_NAME,
)


__all__ = [
    "CHECKER_NAME",
    "PROMPT_COCHAIN_COMPLEX_PROFILE",
    "PROFILE_NAME",
    "AdmittedComplexV1",
    "CochainRefusal",
    "ComplexConditionFailed",
    "ExactMatrix",
    "HigherDifferentialUnavailable",
    "PromptCochainProfile",
    "verify_cochain_complex",
]
