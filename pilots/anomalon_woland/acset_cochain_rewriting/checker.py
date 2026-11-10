"""Independent edgewise gradient judge, separate from the rewrite executor."""

import re
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction

from omega_engine_pfp.domain.rewriting.finite_dpo import FiniteACSet

_RATIONAL = re.compile(r"-?(?:0|[1-9][0-9]{0,63})/[1-9][0-9]{0,63}\Z")


def rational(text: str) -> Fraction:
    """Require bounded canonical rational strings; no floating-point conversion."""
    if type(text) is not str or _RATIONAL.fullmatch(text) is None:
        raise ValueError("NONCANONICAL_RATIONAL")
    value = Fraction(text)
    if text != f"{value.numerator}/{value.denominator}":
        raise ValueError("NONCANONICAL_RATIONAL")
    return value


@dataclass(frozen=True)
class GradientCheck:
    accepted: bool
    reason: str
    residuals: tuple[tuple[str, Fraction], ...] = ()


def _read(state: FiniteACSet) -> dict[str, Fraction]:
    if type(state) is not FiniteACSet or not state.parts or not state.links:
        raise ValueError("EMPTY_COCHAIN")
    potentials = {}
    for part in state.parts:
        if part.kind != "vertex" or tuple(key for key, _ in part.attrs) != ("potential",):
            raise ValueError("COCHAIN_SCHEMA")
        potentials[part.id] = rational(dict(part.attrs)["potential"])
    for link in state.links:
        if link.kind != "edge" or tuple(key for key, _ in link.attrs) != ("cochain",):
            raise ValueError("COCHAIN_SCHEMA")
        rational(dict(link.attrs)["cochain"])
    return potentials


def check_gradient(source: FiniteACSet, candidate: FiniteACSet) -> GradientCheck:
    """Preserve vertices/potentials and oriented multiplicities, then check each edge.

    Edge IDs may change during delete/recreate DPO operations. No quotient-norm
    minimization, unspecified potentials or physical interpretation is claimed.
    """
    try:
        _read(source)
        potentials = _read(candidate)
        if source.parts != candidate.parts:
            return GradientCheck(False, "PROTECTED_POTENTIAL_CHANGED")
        def topology(state: FiniteACSet) -> Counter:
            return Counter((link.kind, link.source, link.target) for link in state.links)
        if topology(source) != topology(candidate):
            return GradientCheck(False, "ORIENTED_TOPOLOGY_CHANGED")
        residuals = tuple((link.id, rational(dict(link.attrs)["cochain"])
            - (potentials[link.target] - potentials[link.source])) for link in candidate.links)
        if any(residual != 0 for _, residual in residuals):
            return GradientCheck(False, "NONZERO_EDGE_RESIDUAL", residuals)
        return GradientCheck(True, "EXACT_EDGEWISE_GRADIENT", residuals)
    except (KeyError, ValueError, TypeError) as exc:
        return GradientCheck(False, str(exc))
