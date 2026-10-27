"""Domain Invariants for the Grammar Bounded Context."""

from __future__ import annotations

from fractions import Fraction

from pfp.domain.mssn_research.grammar.quantification import (
    BoundedAlternationBlock,
    ExactPhi4Certificate,
)
from pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal, Result
from pfp.domain.mssn_research.shared_kernel.value_objects import (
    Rational,
)

from ..packets.value_objects import RefusalCode
from .errors import (
    AlternationBudgetError,
    BianchiNilpotenceError,
    DualCavityGapError,
    GrammarDomainError,
    UnboundedQuantifierError,
)


def check_bounded_quantifier_block(block: BoundedAlternationBlock) -> Result[bool, GrammarDomainError]:
    """Invariant 18 (Level 14): Bounded Quantifier Hierarchy Constraints.

    1. Alternation count <= 12 (FW-BUDGET).
    2. Every variable has explicit finite bound_limit <= step_budget (FW-UNBOUNDED).
    """
    if block.alternation_count > 12:
        return Refusal(AlternationBudgetError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=f"FW-BUDGET: Alternation count {block.alternation_count} exceeds maximum bound 12"
        ))
    if len(block.bounded_vars) == 0:
        return Refusal(UnboundedQuantifierError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="FW-UNBOUNDED: Predicate formula requires at least one bounded variable declaration"
        ))
    for v in block.bounded_vars:
        if v.bound_limit > block.step_budget:
            return Refusal(UnboundedQuantifierError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message=(
                    f"FW-UNBOUNDED: Variable '{v.var_id}' bound limit {v.bound_limit} "
                    f"exceeds step budget {block.step_budget}"
                )
            ))
    return Ok(True)


def check_phi4_dual_certificate(cert: ExactPhi4Certificate) -> Result[bool, GrammarDomainError]:
    """Invariant 19 (Level 14): Exact Degree-4 LP Weak Duality & Bianchi Nilpotence.

    Mirrors engine/crates_rs/core_functional/src/phi4.rs.
    1. Checks discrete Bianchi coboundary nilpotence: d_3 ∘ d_2 = 0.
    2. Checks dual cycle condition: d_3^T * v = 0.
    3. Checks dual capacity bounds: |v_sigma| <= mu_sigma for all 4-cells.
    4. Checks primal residual: r = G - d_3 * C.
    5. Checks zero duality gap over Q: ||r||_{1, mu} == <G, v> == reported_value.
    """
    if not cert.complex.check_bianchi_nilpotence():
        return Refusal(BianchiNilpotenceError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="Discrete Bianchi nilpotence failure: d_3 ∘ d_2 != 0"
        ))

    checks = (
        _check_phi4_dimensions(cert),
        _check_dual_cycle(cert),
        _check_dual_capacity(cert),
        _check_primal_residual(cert),
    )
    failed = next((result for result in checks if result.is_err()), None)
    if failed is not None:
        return failed
    primal_val = sum((abs(_fraction(residual)) * _fraction(weight)
                      for residual, weight in zip(cert.primal_residual, cert.weights)), Fraction(0))
    dual_val = sum((_fraction(flux) * _fraction(witness)
                    for flux, witness in zip(cert.flux_g, cert.dual_witness)), Fraction(0))
    reported = _fraction(cert.reported_value)
    if primal_val != dual_val or primal_val != reported:
        return Refusal(DualCavityGapError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=(
                f"Non-zero duality gap over Q: primal={primal_val}, dual={dual_val}, "
                f"reported={reported} (duality gap {primal_val - dual_val})"
            )
        ))

    return Ok(True)


def _fraction(value: Rational) -> Fraction:
    return Fraction(value.numerator, value.denominator)


def _check_phi4_dimensions(cert: ExactPhi4Certificate) -> Result[bool, GrammarDomainError]:
    d3 = cert.complex.d3
    checks = (
        (d3.rows == len(cert.flux_g), f"d3 rows ({d3.rows}) != flux_g length ({len(cert.flux_g)})"),
        (d3.cols == len(cert.potential_c), f"d3 cols ({d3.cols}) != potential_c length ({len(cert.potential_c)})"),
        (len(cert.weights) == len(cert.flux_g), "weights dimension mismatch with flux_g"),
        (len(cert.dual_witness) == len(cert.flux_g), "dual_witness dimension mismatch with flux_g"),
    )
    invalid = next((message for valid, message in checks if not valid), None)
    if invalid is not None:
        return Refusal(DualCavityGapError(code=RefusalCode.WRONG_ARITY, message=invalid))
    return Ok(True)


def _check_dual_cycle(cert: ExactPhi4Certificate) -> Result[bool, GrammarDomainError]:
    transpose = cert.complex.d3.transpose()
    for row in range(transpose.rows):
        cycle_sum = sum((_fraction(transpose.get(row, column)) * _fraction(cert.dual_witness[column])
                         for column in range(transpose.cols)), Fraction(0))
        if cycle_sum != 0:
            return Refusal(DualCavityGapError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message=f"Dual witness v is not a closed 4-cycle: (d_3^T * v)[{row}] = {cycle_sum} != 0",
            ))
    return Ok(True)


def _check_dual_capacity(cert: ExactPhi4Certificate) -> Result[bool, GrammarDomainError]:
    invalid = next(((index, abs(_fraction(witness)), _fraction(weight))
                    for index, (witness, weight) in enumerate(zip(cert.dual_witness, cert.weights))
                    if abs(_fraction(witness)) > _fraction(weight)), None)
    if invalid is None:
        return Ok(True)
    index, witness, weight = invalid
    return Refusal(DualCavityGapError(
        code=RefusalCode.HOST_VERIFICATION_REQUIRED,
        message=f"Dual witness at index {index} violates capacity: |{witness}| > {weight}",
    ))


def _check_primal_residual(cert: ExactPhi4Certificate) -> Result[bool, GrammarDomainError]:
    d3 = cert.complex.d3
    computed = tuple(Rational(value.numerator, value.denominator) for value in (
        _fraction(cert.flux_g[row]) - sum(
            (_fraction(d3.get(row, column)) * _fraction(cert.potential_c[column])
             for column in range(d3.cols)),
            Fraction(0),
        )
        for row in range(d3.rows)
    ))
    if computed != cert.primal_residual:
        return Refusal(DualCavityGapError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="Primal residual mismatch: r != G - d_3 * C",
        ))
    return Ok(True)
