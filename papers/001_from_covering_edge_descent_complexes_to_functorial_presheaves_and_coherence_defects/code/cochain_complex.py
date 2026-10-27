"""Graded cochain sequence C^0, C^1, C^2 and operators d_0, d_1 for PO-001.

On a non-flat restriction system, d_1 composed with d_0 equals the curvature
action rather than zero, so the sequence is not asserted to be a complex.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from exact import (
    ExactInput,
    as_rational,
    exact_equal,
    exact_matrix_from_matrix,
    l1_norm,
)
from exactsym import Basic, Matrix, simplify

from covering_edge_poset import ComparablePair, FinitePoset, NodeId
from restriction_system import RestrictionSystem


@dataclass(frozen=True)
class Section0Cochain:
    """A 0-cochain assigning a column vector in F(x) to each poset element x."""

    poset: FinitePoset
    values: Mapping[NodeId, Matrix]

    def __post_init__(self) -> None:
        clean_values = {}
        for elem in self.poset.elements:
            if elem not in self.values:
                raise ValueError(f"missing 0-cochain value for node {elem}")
            clean_values[elem] = exact_matrix_from_matrix(self.values[elem])
        object.__setattr__(self, "values", clean_values)

    def __call__(self, node: NodeId) -> Matrix:
        return self.values[node]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Section0Cochain):
            return False
        if self.poset.elements != other.poset.elements:
            return False
        return all(exact_equal(self.values[n], other.values[n]) for n in self.poset.elements)


@dataclass(frozen=True)
class Cochain1:
    """A 1-cochain assigning a vector in F(a) to each comparable pair a <= b."""

    poset: FinitePoset
    values: Mapping[tuple[NodeId, NodeId], Matrix]

    def __post_init__(self) -> None:
        clean_values = {}
        for pair in self.poset.comparable_pairs():
            key = (pair.lower, pair.upper)
            if key not in self.values:
                raise ValueError(f"missing 1-cochain value for pair {key}")
            clean_values[key] = exact_matrix_from_matrix(self.values[key])
        object.__setattr__(self, "values", clean_values)

    def __call__(self, lower: NodeId, upper: NodeId) -> Matrix:
        return self.values[(lower, upper)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cochain1):
            return False
        return all(exact_equal(self.values[k], other.values[k]) for k in self.values)


@dataclass(frozen=True)
class Cochain2:
    """A 2-cochain assigning a vector in F(a) to each comparable triple a <= b <= c."""

    poset: FinitePoset
    values: Mapping[tuple[NodeId, NodeId, NodeId], Matrix]

    def __post_init__(self) -> None:
        clean_values = {}
        for a, b, c in self.values:
            clean_values[(a, b, c)] = exact_matrix_from_matrix(self.values[(a, b, c)])
        object.__setattr__(self, "values", clean_values)

    def __call__(self, a: NodeId, b: NodeId, c: NodeId) -> Matrix:
        return self.values[(a, b, c)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cochain2):
            return False
        if set(self.values.keys()) != set(other.values.keys()):
            return False
        return all(exact_equal(self.values[k], other.values[k]) for k in self.values)


def coboundary_d0(system: RestrictionSystem, s: Section0Cochain) -> Cochain1:
    """Compute 1-cochain (d_0 s)(a, b) = r_{b, a}(s(b)) - s(a) for all a <= b."""
    values: dict[tuple[NodeId, NodeId], Matrix] = {}
    for pair in system.poset.comparable_pairs():
        a, b = pair.lower, pair.upper
        r = system.get_restriction(target=a, source=b)
        val = r(s(b)) - s(a)
        values[(a, b)] = val
    return Cochain1(poset=system.poset, values=values)


def coboundary_d1(system: RestrictionSystem, g: Cochain1) -> Cochain2:
    """Compute 2-cochain (d_1 g)(a, b, c) = r_{b, a}(g(b, c)) - g(a, c) + g(a, b) for all a <= b <= c."""
    values: dict[tuple[NodeId, NodeId, NodeId], Matrix] = {}
    poset = system.poset

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                r_ba = system.get_restriction(target=a, source=b)
                term1 = r_ba(g(b, c))
                term2 = g(a, c)
                term3 = g(a, b)
                values[(a, b, c)] = term1 - term2 + term3

    return Cochain2(poset=poset, values=values)
