"""Independent exact paper model of the strict-chain operator algebra.

Reusable implementation: omega_homology::restriction_dga. This model uses subset
enumeration and SymPy rational matrices, independently of the Rust chain walker.
It accepts a full strict order, not unclosed cover data. Computational bounds:
1..8 vertices, dimensions 1..4. No physical gauge availability is inferred.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from types import MappingProxyType

from sympy import ImmutableMatrix, eye, zeros

Chain = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class OperatorCarrier:
    dimensions: tuple[int, ...]
    strict_order: frozenset[tuple[int, int]]
    by_degree: tuple[tuple[Chain, ...], ...] = field(init=False)

    def __post_init__(self) -> None:
        dims = tuple(self.dimensions)
        order = frozenset(self.strict_order)
        n = len(dims)
        if not 1 <= n <= 8 or any(type(d) is not int or not 1 <= d <= 4 for d in dims):
            raise ValueError("carrier profile requires 1..8 vertices and dimensions 1..4")
        if any(type(x) is not int or type(y) is not int or not 0 <= x < n or not 0 <= y < n or x == y for x, y in order):
            raise ValueError("invalid strict relation")
        if any((y, x) in order for x, y in order):
            raise ValueError("cyclic order")
        if any((x, z) not in order for x, y in order for a, z in order if y == a):
            raise ValueError("strict order must already be transitive")
        degrees = []
        for size in range(1, n + 1):
            chains = []
            for subset in combinations(range(n), size):
                chain = tuple(sorted(subset, key=lambda x: sum((y, x) in order for y in subset)))
                if all((x, y) in order for x, y in zip(chain, chain[1:])):
                    chains.append(chain)
            degrees.append(tuple(sorted(chains)))
        object.__setattr__(self, "dimensions", dims)
        object.__setattr__(self, "strict_order", order)
        object.__setattr__(self, "by_degree", tuple(degrees))

    def chains(self, degree: int) -> tuple[Chain, ...]:
        if type(degree) is not int or degree < 0:
            raise ValueError("degree must be a nonnegative integer")
        return self.by_degree[degree] if degree < len(self.by_degree) else ()

    def matrix(self, chain: Chain, value: object) -> ImmutableMatrix:
        matrix = ImmutableMatrix(value)
        if matrix.shape != (self.dimensions[chain[0]], self.dimensions[chain[-1]]):
            raise ValueError("endpoint matrix shape mismatch")
        if any(entry.is_Rational is not True for entry in matrix):
            raise ValueError("entries must be exact rational numbers")
        return matrix

    def covers(self) -> frozenset[tuple[int, int]]:
        return frozenset((x, y) for x, y in self.strict_order if not any(
            (x, z) in self.strict_order and (z, y) in self.strict_order for z in range(len(self.dimensions))
        ))


@dataclass(frozen=True, slots=True)
class Cochain:
    carrier: OperatorCarrier
    degree: int
    values: Mapping[Chain, ImmutableMatrix]

    def __post_init__(self) -> None:
        expected = set(self.carrier.chains(self.degree))
        if set(self.values) != expected or any(type(x) is not int for key in self.values for x in key):
            raise ValueError("complete cochain coverage required")
        values = {chain: self.carrier.matrix(chain, self.values[chain]) for chain in expected}
        object.__setattr__(self, "values", MappingProxyType(values))

    @classmethod
    def zero(cls, carrier: OperatorCarrier, degree: int) -> Cochain:
        return cls(carrier, degree, {chain: zeros(carrier.dimensions[chain[0]], carrier.dimensions[chain[-1]])
                                     for chain in carrier.chains(degree)})

    @classmethod
    def unit(cls, carrier: OperatorCarrier) -> Cochain:
        return cls(carrier, 0, {(x,): eye(d) for x, d in enumerate(carrier.dimensions)})

    def same_carrier(self, other: Cochain) -> None:
        if self.carrier != other.carrier:
            raise ValueError("carrier mismatch")

    def add(self, other: Cochain, sign: int = 1) -> Cochain:
        self.same_carrier(other)
        if self.degree != other.degree or type(sign) is not int or sign not in (-1, 1):
            raise ValueError("degree/sign mismatch")
        return Cochain(self.carrier, self.degree, {chain: value + sign * other.values[chain]
                                                  for chain, value in self.values.items()})

    def cup(self, other: Cochain) -> Cochain:
        self.same_carrier(other)
        p = self.degree
        degree = p + other.degree
        return Cochain(self.carrier, degree, {chain: self.values[chain[:p + 1]] * other.values[chain[p:]]
                                              for chain in self.carrier.chains(degree)})

    def b(self) -> Cochain:
        values = {}
        for chain in self.carrier.chains(self.degree + 1):
            value = zeros(self.carrier.dimensions[chain[0]], self.carrier.dimensions[chain[-1]])
            for i in range(1, self.degree + 1):
                value += (-1)**i * self.values[chain[:i] + chain[i + 1:]]
            values[chain] = value
        return Cochain(self.carrier, self.degree + 1, values)

    def bracket(self, other: Cochain) -> Cochain:
        return self.cup(other).add(other.cup(self), -(-1)**(self.degree * other.degree))

    def d(self, connection: Cochain) -> Cochain:
        self.same_carrier(connection)
        if connection.degree != 1:
            raise ValueError("connection must have degree one")
        return self.b().add(connection.cup(self)).add(self.cup(connection), -(-1)**self.degree)

    def curvature(self) -> Cochain:
        if self.degree != 1:
            raise ValueError("connection must have degree one")
        return self.b().add(self.cup(self))

    def is_zero(self) -> bool:
        return all(all(entry == 0 for entry in matrix) for matrix in self.values.values())

    def gauge(self, g: Sequence[ImmutableMatrix], inverse: Sequence[ImmutableMatrix]) -> Cochain:
        if len(g) != len(self.carrier.dimensions) or len(inverse) != len(g):
            raise ValueError("one gauge and inverse per vertex required")
        gs, hs = [], []
        for x, dim in enumerate(self.carrier.dimensions):
            gx, hx = self.carrier.matrix((x,), g[x]), self.carrier.matrix((x,), inverse[x])
            if gx * hx != eye(dim) or hx * gx != eye(dim):
                raise ValueError("gauge matrices must be mutual inverses")
            gs.append(gx)
            hs.append(hx)
        return Cochain(self.carrier, self.degree, {chain: gs[chain[0]] * value * hs[chain[-1]]
                                                  for chain, value in self.values.items()})


class PathDependent(ValueError):
    """Exact obstruction carrying the endpoints and two disagreeing paths."""

    def __init__(self, endpoints: tuple[int, int], paths: tuple[Chain, Chain]) -> None:
        self.endpoints, self.paths = endpoints, paths
        super().__init__(f"saturated path products disagree: {endpoints}, {paths}")


def flat_cover_extension(carrier: OperatorCarrier, maps: Mapping[tuple[int, int], ImmutableMatrix]) -> Cochain:
    covers = carrier.covers()
    if set(maps) != set(covers) or any(type(x) is not int for edge in maps for x in edge):
        raise ValueError("complete and exact cover coverage required")
    checked = {edge: carrier.matrix(edge, matrix) for edge, matrix in maps.items()}
    products = {}
    for chains in carrier.by_degree[1:]:
        for chain in chains:
            if any(edge not in covers for edge in zip(chain, chain[1:])):
                continue
            value = eye(carrier.dimensions[chain[0]])
            for edge in zip(chain, chain[1:]):
                value *= checked[edge]
            endpoints = (chain[0], chain[-1])
            if endpoints in products and products[endpoints][1] != value:
                raise PathDependent(endpoints, (products[endpoints][0], chain))
            products[endpoints] = (chain, value)
    return Cochain(carrier, 1, {edge: products[edge][1] for edge in carrier.chains(1)})
