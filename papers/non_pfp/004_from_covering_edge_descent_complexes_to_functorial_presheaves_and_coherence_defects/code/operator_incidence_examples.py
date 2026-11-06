"""Deterministic exact inputs shared by the paper's independently scoped controls."""
from operator_incidence_dga import Cochain, OperatorCarrier
from sympy import ImmutableMatrix, Rational


def chain_carrier(dims=(2, 1, 3, 2, 1, 2, 3, 2)):
    return OperatorCarrier(tuple(dims), frozenset((i, j) for i in range(len(dims)) for j in range(i + 1, len(dims))))


def fixture(c, degree, seed=7):
    def matrix(chain):
        tag = sum((i + 1) * (x + 2) for i, x in enumerate(chain))
        return ImmutableMatrix(c.dimensions[chain[0]], c.dimensions[chain[-1]],
                               lambda i, j: Rational(seed + tag * (i + 1) - (j + 3)**2, 2 + (tag + i + j) % 3))
    return Cochain(c, degree, {chain: matrix(chain) for chain in c.chains(degree)})
