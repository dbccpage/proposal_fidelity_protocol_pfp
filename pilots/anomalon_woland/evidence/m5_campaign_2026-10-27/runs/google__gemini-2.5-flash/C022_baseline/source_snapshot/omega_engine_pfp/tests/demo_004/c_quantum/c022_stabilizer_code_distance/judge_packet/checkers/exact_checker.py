"""Exact algebraic certificate checker for C022.

Self-contained: no reference-solver imports and no comparison with reference
output. Pauli operators are symplectic bit masks (x, z) over n qubits.

- OUT_OF_SCOPE is accepted only for a case whose generators anticommute, are
  linearly dependent over F2, or generate -I, and only with a witness that
  exhibits that defect (any valid witness is accepted, not only the reference's);
  or, witness {"kind": "full_rank"}, for a valid group with m = n generators,
  where k = 0 and no logical operator exists.
- SOLVED needs an int distance d >= 1, a logical operator of weight d that
  commutes with every generator and lies outside the stabilizer group, and
  `lower_bound: null`. The lower bound is certified here by enumerating every
  Pauli operator of weight 1..d-1 and confirming none is a nontrivial logical.
  Supported bound: the enumeration runs when sum_{w=1}^{d-1} C(n, w) 3^w <=
  ENUMERATION_LIMIT (all n <= 20 with d <= 5); larger claims are refused.
"""

from __future__ import annotations

import itertools
from math import comb
from typing import Any

from .schema_guard import validate_certificate

ENUMERATION_LIMIT = 1_000_000
_BITS = {"I": (0, 0), "X": (1, 0), "Z": (0, 1), "Y": (1, 1)}


class CaseError(ValueError):
    """The judge case is not a parseable list of generators."""


def _fail(reason: str) -> dict[str, Any]:
    return {"verdict": "FAIL", "reason": reason}


def _word_to_mask(word: str) -> tuple[int, int]:
    x = z = 0
    for q, ch in enumerate(word):
        if ch not in _BITS:
            raise ValueError(f"invalid Pauli character {ch!r}")
        bx, bz = _BITS[ch]
        x |= bx << q
        z |= bz << q
    return x, z


def _parse_case(case: dict[str, Any]) -> tuple[int, list[int], list[tuple[int, int]], list[str]]:
    n = case.get("num_qubits")
    gens = case.get("generators")
    if type(n) is not int or not 1 <= n <= 20 or not isinstance(gens, list):
        raise CaseError("num_qubits must be an int in [1, 20] and generators a list")
    signs, masks, words = [], [], []
    for g in gens:
        if type(g) is not str:
            raise CaseError(f"generator {g!r} is not a string")
        sign = -1 if g.startswith("-") else 1
        word = g[1:] if g[:1] in ("+", "-") else g
        if len(word) != n:
            raise CaseError(f"generator {g!r} has length != {n}")
        try:
            masks.append(_word_to_mask(word))
        except ValueError as exc:
            raise CaseError(str(exc)) from exc
        signs.append(sign)
        words.append(word)
    return n, signs, masks, words


def _anticommute(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return bin((a[0] & b[1]) ^ (a[1] & b[0])).count("1") % 2 == 1


def _reduced_basis(masks: list[tuple[int, int]], n: int) -> list[int]:
    basis: list[int] = []
    for x, z in masks:
        v = x | (z << n)
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
            basis.sort(reverse=True)
    return basis


def _in_span(basis: list[int], x: int, z: int, n: int) -> bool:
    v = x | (z << n)
    for b in basis:
        v = min(v, v ^ b)
    return v == 0


def _product_phase(
    words: list[str], signs: list[int], subset: list[int], n: int
) -> tuple[int, str]:
    """Return (phase exponent k with phase i^k, word) of the ordered product of the subset."""
    k = 0
    acc = ["I"] * n
    table = {
        ("X", "Y"): ("Z", 1),
        ("Y", "Z"): ("X", 1),
        ("Z", "X"): ("Y", 1),
        ("Y", "X"): ("Z", 3),
        ("Z", "Y"): ("X", 3),
        ("X", "Z"): ("Y", 3),
    }
    for idx in subset:
        if signs[idx] == -1:
            k += 2
        for q, ch in enumerate(words[idx]):
            a = acc[q]
            if ch == "I":
                continue
            if a == "I":
                acc[q] = ch
            elif a == ch:
                acc[q] = "I"
            else:
                acc[q], extra = table[(a, ch)]
                k += extra
    return k % 4, "".join(acc)


def _defects(n: int, signs: list[int], masks: list[tuple[int, int]]) -> set[str]:
    found: set[str] = set()
    if not masks:
        found.add("empty_generators")
    if any(
        _anticommute(masks[i], masks[j])
        for i in range(len(masks))
        for j in range(i + 1, len(masks))
    ):
        found.add("anticommuting")
    if len(_reduced_basis(masks, n)) < len(masks):
        found.add("dependent")
        found.add("minus_identity")  # only possible with a dependency; checked per witness
    if not found and len(masks) == n:
        found.add("full_rank")  # k = 0: every commuting operator lies in S, so no logical exists
    return found


def _check_witness(
    witness: Any, n: int, signs: list[int], masks: list[tuple[int, int]], words: list[str]
) -> str | None:
    m = len(masks)
    if not isinstance(witness, dict):
        return "witness must be an object"
    kind = witness.get("kind")
    if kind == "empty_generators":
        return (
            None
            if m == 0 and set(witness) == {"kind"}
            else "empty_generators witness on a nonempty case"
        )
    if kind == "full_rank":
        if set(witness) != {"kind"}:
            return "full_rank witness takes no fields besides kind"
        if m != n:
            return f"full_rank needs exactly n = {n} generators, got {m}"
        if any(_anticommute(masks[i], masks[j]) for i in range(m) for j in range(i + 1, m)):
            return "generators anticommute; full_rank does not apply"
        if len(_reduced_basis(masks, n)) < m:
            return "generators are dependent; full_rank does not apply"
        return None
    if kind == "anticommuting":
        pair = witness.get("pair")
        if not (
            isinstance(pair, list)
            and len(pair) == 2
            and all(type(i) is int and 0 <= i < m for i in pair)
        ):
            return "anticommuting witness needs a pair of generator indices"
        i, j = pair
        if i == j or not _anticommute(masks[i], masks[j]):
            return f"generators {i} and {j} commute"
        return None
    if kind == "dependent":
        comb_vec = witness.get("linear_combination")
        if not (
            isinstance(comb_vec, list)
            and len(comb_vec) == m
            and all(type(c) is int and c in (0, 1) for c in comb_vec)
        ):
            return "dependent witness needs a 0/1 integer vector of length m"
        if not any(comb_vec):
            return "dependent witness is the zero combination"
        x = z = 0
        for c, (gx, gz) in zip(comb_vec, masks):
            if c:
                x ^= gx
                z ^= gz
        return None if x == 0 and z == 0 else "linear combination is not zero over F2"
    if kind == "minus_identity":
        subset = witness.get("subset")
        if not (
            isinstance(subset, list)
            and subset
            and all(type(i) is int and 0 <= i < m for i in subset)
        ):
            return "minus_identity witness needs a nonempty list of generator indices"
        if len(set(subset)) != len(subset):
            return "minus_identity subset repeats a generator"
        k, word = _product_phase(words, signs, subset, n)
        return None if word == "I" * n and k == 2 else "subset product is not -I"
    return f"unknown witness kind {kind!r}"


def _lighter_logical(
    n: int, masks: list[tuple[int, int]], basis: list[int], max_weight: int
) -> str | None:
    for w in range(1, max_weight + 1):
        for support in itertools.combinations(range(n), w):
            for choice in itertools.product(((1, 0), (0, 1), (1, 1)), repeat=w):
                x = z = 0
                for q, (bx, bz) in zip(support, choice):
                    x |= bx << q
                    z |= bz << q
                if any(_anticommute((x, z), g) for g in masks):
                    continue
                if not _in_span(basis, x, z, n):
                    return "".join("IXZY"[((x >> q) & 1) | (((z >> q) & 1) << 1)] for q in range(n))
    return None


def check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    schema_error = validate_certificate(case, cert)
    if schema_error:
        return _fail(schema_error)
    try:
        n, signs, masks, words = _parse_case(case)
    except CaseError as exc:
        return _fail(f"judge case is malformed: {exc}")
    defects = _defects(n, signs, masks)
    status = cert.get("status")

    if status == "OUT_OF_SCOPE":
        if not defects:
            return _fail("generators form a valid stabilizer group; OUT_OF_SCOPE is not admissible")
        problem = _check_witness(cert.get("witness"), n, signs, masks, words)
        if problem:
            return _fail(f"invalid OUT_OF_SCOPE witness: {problem}")
        return {"verdict": "PASS", "details": "Out of scope witness verified"}

    if status != "SOLVED":
        return _fail(f"Unsupported status: {status}")
    if defects:
        return _fail(f"case is out of scope ({sorted(defects)}); SOLVED is not admissible")

    dist = cert.get("distance")
    if type(dist) is not int or dist < 1:
        return _fail(f"distance must be an int >= 1, got {dist!r}")
    if cert.get("lower_bound") is not None:
        return _fail("lower_bound must be null: the judge certifies the lower bound by enumeration")
    log_word = cert.get("logical")
    if type(log_word) is not str or len(log_word) != n:
        return _fail(f"logical must be a Pauli string of length {n}")
    try:
        lx, lz = _word_to_mask(log_word)
    except ValueError as exc:
        return _fail(f"Invalid logical operator format: {exc}")
    weight = bin(lx | lz).count("1")
    if weight != dist:
        return _fail(f"Logical weight {weight} != reported distance {dist}")
    for idx, g in enumerate(masks):
        if _anticommute((lx, lz), g):
            return _fail(f"Logical operator does not commute with generator {idx}")
    basis = _reduced_basis(masks, n)
    if _in_span(basis, lx, lz, n):
        return _fail("Degenerate defect: logical operator lies in the stabilizer group S")

    work = sum(comb(n, w) * 3**w for w in range(1, dist))
    if work > ENUMERATION_LIMIT:
        return _fail(
            f"distance claim needs {work} enumerations, above the judge limit {ENUMERATION_LIMIT}"
        )
    lighter = _lighter_logical(n, masks, basis, dist - 1)
    if lighter is not None:
        return _fail(f"Found lighter logical operator {lighter} of weight < {dist}")
    return {
        "verdict": "PASS",
        "details": "Logical operator verified; no lighter logical exists (exhaustive)",
    }
