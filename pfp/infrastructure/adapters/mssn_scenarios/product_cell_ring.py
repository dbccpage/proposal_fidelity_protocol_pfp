"""Exact product-ring teaching fixture with declared generator relations."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import product

BASIS = ("1", "a", "b", "w")
DEGREES = (0, 2, 2, 4)


class RingRefusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise RingRefusal(code)


def unit(index):
    return tuple(Fraction(int(i == index)) for i in range(4))


def declared_table():
    zero = tuple(Fraction(0) for _ in BASIS)
    table = {(x, y): zero for x in BASIS for y in BASIS}
    for i, x in enumerate(BASIS):
        table[("1", x)] = unit(i)
        table[(x, "1")] = unit(i)
    table[("a", "b")] = table[("b", "a")] = unit(3)
    return table


def multiply(left, right, table):
    return tuple(sum(left[i] * right[j] * table[(x, y)][k]
                     for i, x in enumerate(BASIS)
                     for j, y in enumerate(BASIS)) for k in range(4))


def check_product_ring(table):
    require(set(table) == set(product(BASIS, repeat=2)), "REFUSED_INCOMPLETE_PRODUCT_TABLE")
    for key, value in table.items():
        require(len(value) == 4, "REFUSED_PRODUCT_ARITY")
        require(all(type(x) in (int, Fraction) for x in value), "REFUSED_INEXACT_SCALAR")
    vectors = [unit(i) for i in range(4)]
    for i, x in enumerate(BASIS):
        require(table[("1", x)] == vectors[i] == table[(x, "1")], "REFUSED_UNIT_LAW")
        for j, y in enumerate(BASIS):
            require(table[(x, y)] == table[(y, x)], "REFUSED_EVEN_COMMUTATIVITY")
            require(all(c == 0 or DEGREES[k] == DEGREES[i] + DEGREES[j]
                        for k, c in enumerate(table[(x, y)])), "REFUSED_DEGREE_MISMATCH")
    for x, y, z in product(vectors, repeat=3):
        require(multiply(multiply(x, y, table), z, table) ==
                multiply(x, multiply(y, z, table), table), "REFUSED_ASSOCIATIVITY")
    zero = tuple(Fraction(0) for _ in BASIS)
    require(table[("a", "a")] == table[("b", "b")] == zero, "REFUSED_GENERATOR_SQUARE")
    require(table[("a", "b")] == unit(3), "REFUSED_DECLARED_ORIENTATION")
    return {"basis_count": 4, "associativity_triples": 64, "status": "PASS"}


def run_product_cell_ring():
    table = declared_table()
    laws = check_product_ring(table)
    coefficients = (Fraction(-1), Fraction(-1, 2), Fraction(0), Fraction(1, 2), Fraction(1))
    pairs = []
    for p, q in product(coefficients, repeat=2):
        flux = (Fraction(0), p, q, Fraction(0))
        square = multiply(flux, flux, table)
        require(square == (Fraction(0), Fraction(0), Fraction(0), 2 * p * q),
                "REFUSED_SQUARE_PAIRING")
        pairs.append({"p": str(p), "q": str(q), "pairing": str(square[3])})
    negatives = []
    mutations = []
    missing = deepcopy(table)
    del missing[("a", "b")]
    mutations.append(("missing_product", missing, "REFUSED_INCOMPLETE_PRODUCT_TABLE"))
    orientation = deepcopy(table)
    orientation[("a", "b")] = orientation[("b", "a")] = tuple(-x for x in unit(3))
    mutations.append(("orientation_reversal", orientation, "REFUSED_DECLARED_ORIENTATION"))
    square = deepcopy(table)
    square[("a", "a")] = unit(3)
    mutations.append(("nonzero_generator_square", square, "REFUSED_GENERATOR_SQUARE"))
    order = deepcopy(table)
    order[("b", "a")] = tuple(-x for x in unit(3))
    mutations.append(("unequal_even_products", order, "REFUSED_EVEN_COMMUTATIVITY"))
    for name, mutation, expected in mutations:
        try:
            check_product_ring(mutation)
        except RingRefusal as exc:
            require(str(exc) == expected, "REFUSED_WRONG_NEGATIVE_TRIGGER")
            negatives.append({"case": name, "refusal": str(exc)})
        else:
            raise AssertionError("mutated product table admitted")
    return {
        "schema": "mssn.declared_product_cell_ring.v1",
        "status": "PASS",
        "authority_effect": "None",
        "source_kind": "assistant_authored_fixture",
        "provider_calls": 0,
        "api_cost_usd": "0/1",
        "cochain_dimensions": [1, 0, 2, 0, 1],
        "differentials": "zero in each degree",
        "basis": list(BASIS),
        "degrees": list(DEGREES),
        "declared_relations": ["a*a=0", "b*b=0", "a*b=b*a=w", "pair(w)=1"],
        "laws": laws,
        "pairings": pairs,
        "negative_cases": negatives,
        "scope": "Finite rational graded algebra with declared product-cell relations. The manifold interpretation is an input assumption, not inferred from the old Demo9 matrices.",
    }
