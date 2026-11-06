"""Independent Cup Product Checker (Checker 2) for C016.

Self-contained: no reference-solver or checker-1 imports. It closes the simplicial
complexes, computes rational Betti numbers, chooses its own cocycle
representatives for H^p and H^q, forms Alexander-Whitney products, and measures
the rank of the cup-product image in H^{p+q} as

    rank = dim(span{alpha_i cup beta_j} + B^{p+q}) - dim B^{p+q},

which needs no homology cycles (the reference evaluates on a cycle basis instead;
both equal the image dimension because the Kronecker pairing is perfect over Q).
Ranks must be canonical non-negative integers (decimal string or plain int);
floats and Booleans are rejected. An UNKNOWN is accepted only with INVALID_DEGREES
or MALFORMED_INPUT when that condition holds for the case.
"""

from __future__ import annotations

import itertools
import re
from fractions import Fraction
from typing import Any

_NATURAL = re.compile(r"0|[1-9][0-9]*")
Simplex = tuple[int, ...]


def _natural(value: Any) -> int | None:
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and _NATURAL.fullmatch(value):
        return int(value)
    return None


def _closure(maximal: Any) -> dict[int, list[Simplex]] | None:
    if not isinstance(maximal, list):
        return None
    levels: dict[int, set[Simplex]] = {d: set() for d in range(5)}
    for simplex in maximal:
        if not isinstance(simplex, list) or not simplex or any(type(v) is not int for v in simplex):
            return None
        verts = tuple(sorted(set(simplex)))
        if len(verts) != len(simplex) or len(verts) > 5:
            return None
        for size in range(1, len(verts) + 1):
            levels[size - 1].update(itertools.combinations(verts, size))
    return {d: sorted(levels[d]) for d in range(5)}


def _rank(rows: list[list[Fraction]]) -> int:
    work = [r[:] for r in rows if any(r)]
    rank = 0
    width = len(work[0]) if work else 0
    for col in range(width):
        pivot = next((i for i in range(rank, len(work)) if work[i][col] != 0), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        for i in range(rank + 1, len(work)):
            if work[i][col] != 0:
                factor = work[i][col] / work[rank][col]
                work[i] = [a - factor * b for a, b in zip(work[i], work[rank])]
        rank += 1
    return rank


def _coboundary_rows(levels: dict[int, list[Simplex]], k: int) -> list[list[Fraction]]:
    """Rows: delta(e_tau) for each k-simplex tau, as vectors over the (k+1)-simplices."""
    if k < 0 or k >= 4:
        return []
    upper = levels[k + 1]
    position = {s: i for i, s in enumerate(upper)}
    rows = []
    for tau in levels[k]:
        row = [Fraction(0)] * len(upper)
        for sigma in upper:
            if set(tau) <= set(sigma):
                missing = next(i for i, v in enumerate(sigma) if v not in tau)
                row[position[sigma]] = Fraction(-1 if missing % 2 else 1)
        rows.append(row)
    return rows


def _cocycle_representatives(levels: dict[int, list[Simplex]], k: int) -> list[list[Fraction]]:
    n = len(levels[k])
    if n == 0:
        return []
    delta = _coboundary_rows(levels, k)  # n rows, each a vector over (k+1)-simplices
    # Cocycles f satisfy sum_tau f(tau) * delta(e_tau) = 0: the left kernel of `delta`.
    width = len(delta[0]) if delta and delta[0] else 0
    aug = [
        (delta[i] if width else []) + [Fraction(1 if j == i else 0) for j in range(n)]
        for i in range(n)
    ]
    rank = 0
    for col in range(width):
        pivot = next((i for i in range(rank, n) if aug[i][col] != 0), None)
        if pivot is None:
            continue
        aug[rank], aug[pivot] = aug[pivot], aug[rank]
        for i in range(n):
            if i != rank and aug[i][col] != 0:
                factor = aug[i][col] / aug[rank][col]
                aug[i] = [a - factor * b for a, b in zip(aug[i], aug[rank])]
        rank += 1
    cocycles = [row[width:] for row in aug[rank:]]
    exact = _coboundary_rows(levels, k - 1)  # B^k spanned by delta(e_rho), rho a (k-1)-simplex
    reps: list[list[Fraction]] = []
    current = _rank(exact)
    for z in cocycles:
        trial = _rank(exact + reps + [z])
        if trial > current:
            reps.append(z)
            current = trial
    return reps


def _cup(
    alpha: list[Fraction], beta: list[Fraction], levels: dict[int, list[Simplex]], p: int, q: int
) -> list[Fraction]:
    front = {s: i for i, s in enumerate(levels[p])}
    back = {s: i for i, s in enumerate(levels[q])}
    return [alpha[front[s[: p + 1]]] * beta[back[s[p:]]] for s in levels[p + q]]


def _image_rank(levels: dict[int, list[Simplex]], p: int, q: int) -> int:
    if p + q > 4 or not levels[p + q]:
        return 0
    products = [
        _cup(a, b, levels, p, q)
        for a in _cocycle_representatives(levels, p)
        for b in _cocycle_representatives(levels, q)
    ]
    exact = _coboundary_rows(levels, p + q - 1)
    return _rank(exact + products) - _rank(exact)


def _betti(levels: dict[int, list[Simplex]]) -> list[int]:
    ranks = [_rank(_coboundary_rows(levels, k)) for k in range(5)]  # rank delta_k = rank d_{k+1}
    return [len(levels[k]) - ranks[k] - (ranks[k - 1] if k > 0 else 0) for k in range(5)]


def check_independent_cup_products(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    p, q = case.get("deg_p", 1), case.get("deg_q", 1)
    violations = set()
    if type(p) is not int or type(q) is not int or p < 0 or q < 0 or p + q > 4:
        violations.add("INVALID_DEGREES")
    sides = [case.get(name) for name in ("X", "Y")]
    X = _closure(sides[0].get("maximal_simplices")) if isinstance(sides[0], dict) else None
    Y = _closure(sides[1].get("maximal_simplices")) if isinstance(sides[1], dict) else None
    if X is None or Y is None:
        violations.add("MALFORMED_INPUT")
    if status == "UNKNOWN":
        codes = {result.get(k) for k in ("refusal", "refusal_code") if k in result}
        if len(codes) != 1 or next(iter(codes)) not in violations:
            return False, f"Independent checker: refusal {codes!r} does not hold for this case"
        return True, "Independent checker confirms the refusal"
    if violations or X is None or Y is None:
        return False, f"Independent checker: case violates {sorted(violations)}; UNKNOWN expected"

    betti_X, betti_Y = _betti(X), _betti(Y)
    mismatch = next((d for d in range(5) if betti_X[d] != betti_Y[d]), None)
    if mismatch is not None:
        if status != "OUT_OF_SCOPE":
            return False, "Expected OUT_OF_SCOPE from independent Betti analysis"
        witness = result.get("witness")
        expected = {
            "reason": "BETTI_MISMATCH",
            "degree": str(mismatch),
            "betti_X": betti_X[mismatch],
            "betti_Y": betti_Y[mismatch],
        }
        if not isinstance(witness, dict) or any(
            type(witness.get(key)) is not type(value) or witness.get(key) != value
            for key, value in expected.items()
        ):
            return (
                False,
                f"Independent checker rejected incorrect Betti witness: expected {expected}",
            )
        return True, "Independent checker confirms OUT_OF_SCOPE Betti mismatch"

    if status != "SOLVED":
        return False, f"Expected SOLVED, got {status}"

    rank_X, rank_Y = _image_rank(X, p, q), _image_rank(Y, p, q)
    claimed = []
    for name in ("X", "Y"):
        side = result.get(name)
        value = _natural(side.get("rank")) if isinstance(side, dict) else None
        if value is None:
            return (
                False,
                f"Independent checker: {name} rank is not a canonical non-negative integer",
            )
        claimed.append(value)
    if claimed[0] != rank_X:
        return False, f"Independent rank mismatch for X: expected {rank_X}, got {claimed[0]}"
    if claimed[1] != rank_Y:
        return False, f"Independent rank mismatch for Y: expected {rank_Y}, got {claimed[1]}"

    expected_verdict = "DISTINGUISHED" if rank_X != rank_Y else "NOT_DISTINGUISHED_BY_THIS_PRODUCT"
    if result.get("verdict") != expected_verdict:
        return (
            False,
            f"Independent verdict mismatch: expected {expected_verdict}, got {result.get('verdict')}",
        )
    return True, "Independent cup product rank and verdict verified"
