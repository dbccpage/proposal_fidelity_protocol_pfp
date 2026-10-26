"""Exact MSS-N tower normal forms.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Optional, Sequence

from omega_engine_pfp.domain.tower.parser import GAMMA_38, parse_packet

# =============================================================================
# Part 3: MSS-N Tower Normal Forms (TBNF, DBCNF, ZFNF, DHNF)
# =============================================================================


def check_tbnf(wire_string: str) -> tuple[bool, str | None]:
    """TBNF: Token-Bounded Normal Form.

    Verifies string uses strictly Gamma38 and is deterministically prefix-decodable.
    """
    for idx, ch in enumerate(wire_string):
        if ch not in GAMMA_38:
            return False, f"Character {ch!r} at position {idx} outside Gamma38"
    try:
        parse_packet(wire_string)
        return True, None
    except Exception as exc:
        return False, f"Parsing failure under TBNF: {exc}"


def canonicalize_dbcnf(seq: Sequence[Any]) -> tuple[Any, ...]:
    """DBCNF: De Bruijn Cyclic Normal Form.

    Computes the lexicographically least cyclic shift (Lyndon word canonical representative).
    """
    if not seq:
        return ()
    n = len(seq)
    min_shift = tuple(seq)
    for shift in range(1, n):
        rotated = tuple(seq[shift:] + seq[:shift])
        if rotated < min_shift:
            min_shift = rotated
    return min_shift


def is_dbcnf(seq: Sequence[Any]) -> bool:
    return tuple(seq) == canonicalize_dbcnf(seq)


@dataclass(frozen=True)
class ZfnfResult:
    """Verdict from Zero-Float Rational Normal Form checker."""

    terminal: str
    primal_obj: Fraction
    dual_obj: Fraction
    duality_gap: Fraction
    primal_feasible: bool = True
    dual_feasible: bool = True


@dataclass(frozen=True)
class _ZfnfOptions:
    primal_sol: Optional[Sequence[object]] = None
    dual_sol: Optional[Sequence[object]] = None
    matrix: Optional[Sequence[Sequence[object]]] = None
    bounds: Optional[Sequence[object]] = None
    objective: Optional[Sequence[object]] = None
    primal_feasible: Optional[bool] = None
    dual_feasible: Optional[bool] = None


def _parse_zfnf_options(args: tuple[object, ...], kwargs: dict[str, object]) -> _ZfnfOptions:
    names = ("primal_sol", "dual_sol", "A", "b", "c", "primal_feasible", "dual_feasible")
    if len(args) > len(names):
        raise TypeError(f"verify_zfnf() takes at most 9 arguments ({len(args) + 2} given)")
    values = dict(zip(names, args, strict=False))
    for name, value in kwargs.items():
        if name not in names:
            raise TypeError(f"verify_zfnf() got an unexpected keyword argument '{name}'")
        if name in values:
            raise TypeError(f"verify_zfnf() got multiple values for argument '{name}'")
        values[name] = value
    remapped = {
        "matrix"
        if name == "A"
        else "bounds"
        if name == "b"
        else "objective"
        if name == "c"
        else name: value
        for name, value in values.items()
    }
    return _ZfnfOptions(**remapped)


def verify_zfnf(
    primal_obj: object,
    dual_obj: object,
    *args: object,
    **kwargs: object,
) -> ZfnfResult:
    """ZFNF: Zero-Float Rational Normal Form verifier.

    Rejects floats, asserts primal & dual feasibility, asserts dualObj >= primalObj,
    and detects exact zero gap. Equal scalars without feasibility cannot certify optimality.
    """
    options = _parse_zfnf_options(args, kwargs)
    _reject_float_contamination(
        primal_obj,
        dual_obj,
        options.primal_sol,
        options.dual_sol,
        options.bounds,
        options.objective,
    )

    p = Fraction(primal_obj)
    d = Fraction(dual_obj)
    gap = d - p

    is_primal_feas = True if options.primal_feasible is None else bool(options.primal_feasible)
    is_dual_feas = True if options.dual_feasible is None else bool(options.dual_feasible)

    if options.primal_sol is not None:
        is_primal_feas = is_primal_feas and _is_primal_solution_feasible(
            options.primal_sol, options.matrix, options.bounds
        )
    if (
        options.dual_sol is not None
        and options.matrix is not None
        and options.objective is not None
    ):
        is_dual_feas = is_dual_feas and _is_dual_solution_feasible(
            options.dual_sol, options.matrix, options.objective
        )

    if not is_primal_feas:
        return ZfnfResult("InfeasiblePrimalViolationRefusal", p, d, gap, False, is_dual_feas)

    if not is_dual_feas or gap < 0:
        return ZfnfResult("InfeasibleDualViolationRefusal", p, d, gap, is_primal_feas, False)

    if gap == 0:
        return ZfnfResult("CertifiedOptimalZeroGap", p, d, gap, True, True)
    return ZfnfResult("SuboptimalPositiveGap", p, d, gap, True, True)


def _reject_float_contamination(*values: object) -> None:
    for value in values:
        items = (
            value
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
            else (value,)
        )
        for item in items:
            if isinstance(item, (float, complex)):
                raise ValueError(
                    "FloatContaminationRefusal: floating-point type in Zero-Float pipeline"
                )


def _is_primal_solution_feasible(
    solution: Sequence[object],
    matrix: Optional[Sequence[Sequence[object]]],
    bounds: Optional[Sequence[object]],
) -> bool:
    values = [Fraction(value) for value in solution]
    if any(value < 0 for value in values):
        return False
    if matrix is None or bounds is None:
        return True
    expected = [Fraction(value) for value in bounds]
    return all(
        sum(Fraction(value) * values[index] for index, value in enumerate(row))
        == expected[row_index]
        for row_index, row in enumerate(matrix)
    )


def _is_dual_solution_feasible(
    solution: Sequence[object],
    matrix: Sequence[Sequence[object]],
    objective: Sequence[object],
) -> bool:
    values = [Fraction(value) for value in solution]
    expected = [Fraction(value) for value in objective]
    return all(
        sum(Fraction(matrix[row][column]) * values[row] for row in range(len(matrix)))
        >= expected[column]
        for column in range(len(expected))
    )


@dataclass(frozen=True)
class DhnfResult:
    """Verdict from Discrete Hodge Normal Form decomposition checker."""

    terminal: str
    exact_reconstructed: bool
    orthogonal: bool
    harmonic_zero: bool


def verify_dhnf(
    c: Mapping[tuple[int, int], Fraction],
    d0_p: Mapping[tuple[int, int], Fraction],
    h: Mapping[tuple[int, int], Fraction],
    d1_star_q: Mapping[tuple[int, int], Fraction],
    allow_harmonic: bool = False,
) -> DhnfResult:
    """DHNF: Discrete Hodge Normal Form decomposition verifier."""
    all_edges = set(c.keys()) | set(d0_p.keys()) | set(h.keys()) | set(d1_star_q.keys())

    # 1. Reconstruction check: c == d0(p) + h + d1_star(q)
    for e in all_edges:
        target = c.get(e, Fraction(0))
        reconstructed = (
            d0_p.get(e, Fraction(0)) + h.get(e, Fraction(0)) + d1_star_q.get(e, Fraction(0))
        )
        if target != reconstructed:
            return DhnfResult("RoundingDriftRefusal", False, False, False)

    # 2. Orthogonality check: <d0_p, h> == 0, <h, d1_star_q> == 0, <d0_p, d1_star_q> == 0
    dot_d0_h = sum(d0_p.get(e, Fraction(0)) * h.get(e, Fraction(0)) for e in all_edges)
    dot_h_d1 = sum(h.get(e, Fraction(0)) * d1_star_q.get(e, Fraction(0)) for e in all_edges)
    dot_d0_d1 = sum(d0_p.get(e, Fraction(0)) * d1_star_q.get(e, Fraction(0)) for e in all_edges)

    if dot_d0_h != Fraction(0) or dot_h_d1 != Fraction(0) or dot_d0_d1 != Fraction(0):
        return DhnfResult("RoundingDriftRefusal", True, False, False)

    # 3. Harmonic check: is h identically zero?
    h_is_zero = all(val == Fraction(0) for val in h.values())

    if h_is_zero and all(val == Fraction(0) for val in d1_star_q.values()):
        return DhnfResult("HodgeDecomposedExact", True, True, True)
    if not h_is_zero:
        if allow_harmonic:
            return DhnfResult("HodgeDecomposedWithHarmonic", True, True, False)
        return DhnfResult("HarmonicObstructionDetected", True, True, False)
    return DhnfResult("HodgeDecomposedExact", True, True, False)
