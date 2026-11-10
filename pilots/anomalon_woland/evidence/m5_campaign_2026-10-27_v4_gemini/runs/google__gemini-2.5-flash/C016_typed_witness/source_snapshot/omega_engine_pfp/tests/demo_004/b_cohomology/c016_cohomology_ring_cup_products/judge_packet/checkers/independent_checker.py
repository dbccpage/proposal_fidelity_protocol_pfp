"""Independent Cup Product Checker (Checker 2) for C016.

Self-contained: no reference-solver or checker-1 imports. It closes the simplicial
complexes, computes rational Betti numbers, chooses its own cocycle
representatives for H^p and H^q, forms Alexander-Whitney products, and measures
the rank of the cup-product image in H^{p+q} as

    rank = dim(span{alpha_i cup beta_j} + B^{p+q}) - dim B^{p+q},

which needs no homology cycles (the reference evaluates on a cycle basis instead;
both equal the image dimension because the Kronecker pairing is perfect over Q).
Ranks must be canonical non-negative integers (decimal string or plain int);
floats and Booleans are rejected. The answer's own certificate is checked here
too, with this module's coboundaries and cup: every basis cochain is a cocycle
on simplices of the complex, every nonzero witness is a closed cycle on which
the stated product takes the stated nonzero value (at least as many witnesses as
the claimed rank), and every primitive gamma has coboundary equal to its product. An UNKNOWN is accepted only with INVALID_DEGREES
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


def _chain(raw: Any) -> dict[Simplex, Fraction]:
    """A serialized chain {"[0, 1]": "1/2", ...}; orientation is the sorted vertex order."""
    if not isinstance(raw, dict):
        raise ValueError("serialized chain must be a mapping")
    chain: dict[Simplex, Fraction] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ValueError("serialized simplex key must be a string")
        body = key.strip().strip("[]()").replace(" ", "")
        if not body:
            continue
        simplex = tuple(sorted(int(v) for v in body.split(",")))
        coefficient = Fraction(str(value))
        if coefficient != 0:
            chain[simplex] = coefficient
    return chain


def _index(value: Any, size: int) -> int:
    if type(value) not in (int, str):
        raise ValueError("basis index must be an integer or integer string")
    index = int(value)
    if not 0 <= index < size:
        raise ValueError(f"basis index {index} outside basis of size {size}")
    return index


def _coboundary(chain: dict[Simplex, Fraction], levels: dict[int, list[Simplex]], k: int):
    """delta(chain) on each (k+1)-simplex: sum over faces of (-1)^i chain(face_i)."""
    if k + 1 > 4:
        return {}
    return {
        sigma: sum(
            (
                Fraction(-1 if i % 2 else 1) * chain.get(sigma[:i] + sigma[i + 1 :], Fraction(0))
                for i in range(len(sigma))
            ),
            Fraction(0),
        )
        for sigma in levels[k + 1]
    }


def _product(alpha, beta, levels, p, q) -> dict[Simplex, Fraction]:
    return {
        s: alpha.get(s[: p + 1], Fraction(0)) * beta.get(s[p:], Fraction(0)) for s in levels[p + q]
    }


def _certificate_error(
    side: dict[str, Any], levels: dict[int, list[Simplex]], p: int, q: int, rank: int
) -> str | None:
    try:
        bases = []
        for degree, field in ((p, "basis_p"), (q, "basis_q")):
            raw = side.get(field, [])
            if not isinstance(raw, list):
                return f"{field} must be a list of serialized cochains"
            basis = [_chain(c) for c in raw]
            allowed = set(levels[degree])
            for idx, cochain in enumerate(basis):
                if any(s not in allowed for s in cochain):
                    return f"{field}[{idx}] uses a simplex outside C^{degree}"
                if any(_coboundary(cochain, levels, degree).values()):
                    return f"{field}[{idx}] is not a cocycle"
            bases.append(basis)
        basis_p, basis_q = bases
        target, below = set(levels[p + q]), set(levels[p + q - 1]) if p + q > 0 else set()
        witnesses = side.get("nonzero", [])
        if not isinstance(witnesses, list):
            return "nonzero witnesses must be a list"
        if len(witnesses) < rank:
            return f"{len(witnesses)} nonzero witnesses for claimed rank {rank}"
        for witness in witnesses:
            if not isinstance(witness, dict):
                return "nonzero witness must be a mapping"
            i, j = _index(witness["i"], len(basis_p)), _index(witness["j"], len(basis_q))
            cycle, value = _chain(witness["cycle"]), Fraction(str(witness["value"]))
            if any(s not in target for s in cycle):
                return f"witness cycle uses a simplex outside C_{p + q}"
            if value == 0:
                return "nonzero witness reports zero"
            if p + q > 0:
                boundary: dict[Simplex, Fraction] = {}
                for s, c in cycle.items():
                    for k in range(len(s)):
                        face = s[:k] + s[k + 1 :]
                        boundary[face] = boundary.get(face, Fraction(0)) + (-c if k % 2 else c)
                if any(boundary.values()):
                    return "witness cycle is not closed"
            product = _product(basis_p[i], basis_q[j], levels, p, q)
            if sum((product[s] * c for s, c in cycle.items()), Fraction(0)) != value:
                return f"product of basis_p[{i}] and basis_q[{j}] on the cycle is not {value}"
        primitives = side.get("primitives", [])
        if not isinstance(primitives, list):
            return "primitive witnesses must be a list"
        for witness in primitives:
            if not isinstance(witness, dict):
                return "primitive witness must be a mapping"
            i, j = _index(witness["i"], len(basis_p)), _index(witness["j"], len(basis_q))
            gamma = _chain(witness["gamma"])
            if any(s not in below for s in gamma):
                return f"primitive gamma uses a simplex outside C^{p + q - 1}"
            if p + q > 0:
                product = _product(basis_p[i], basis_q[j], levels, p, q)
                if _coboundary(gamma, levels, p + q - 1) != product:
                    return f"delta(gamma) is not the product of basis_p[{i}] and basis_q[{j}]"
    except (KeyError, ValueError, TypeError, ZeroDivisionError) as exc:
        return f"malformed certificate: {exc}"
    return None


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
    for name, levels in (("X", X), ("Y", Y)):
        error = _certificate_error(result[name], levels, p, q, _natural(result[name]["rank"]))
        if error is not None:
            return False, f"Independent checker: {name} certificate: {error}"
    return True, "Independent cup product rank, verdict and certificates verified"
