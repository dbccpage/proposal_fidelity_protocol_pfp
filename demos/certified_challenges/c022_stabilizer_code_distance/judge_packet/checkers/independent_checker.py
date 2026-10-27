"""Independent second checker for C022.

Self-contained: imports neither the reference solver nor checker 1. It works on
0/1 lists (not bit masks), decides stabilizer-group membership by comparing F2
ranks, and verifies the distance claim by enumerating every Pauli operator of
weight below the claimed distance. It verifies OUT_OF_SCOPE witnesses on their
own merits.
"""

from __future__ import annotations

import itertools
from typing import Any

from .schema_guard import validate_certificate

WORK_LIMIT = 1_000_000


def _symplectic(word: str) -> list[int] | None:
    xs, zs = [], []
    for ch in word:
        if ch == "I":
            xs.append(0)
            zs.append(0)
        elif ch == "X":
            xs.append(1)
            zs.append(0)
        elif ch == "Z":
            xs.append(0)
            zs.append(1)
        elif ch == "Y":
            xs.append(1)
            zs.append(1)
        else:
            return None
    return xs + zs


def _form(a: list[int], b: list[int], n: int) -> int:
    return sum(a[i] * b[n + i] + a[n + i] * b[i] for i in range(n)) % 2


def _rank(rows: list[list[int]]) -> int:
    work = [r[:] for r in rows]
    rank = 0
    width = len(work[0]) if work else 0
    for col in range(width):
        pivot = next((i for i in range(rank, len(work)) if work[i][col]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        for i in range(len(work)):
            if i != rank and work[i][col]:
                work[i] = [(p + q) % 2 for p, q in zip(work[i], work[rank])]
        rank += 1
    return rank


def _fail(reason: str) -> dict[str, Any]:
    return {"verdict": "FAIL", "reason": reason}


def _phase_product_is_minus_identity(gens: list[str], subset: list[int], n: int) -> bool:
    # Track each qubit's Pauli and the global phase as a power of i.
    mult = {
        ("X", "Y"): ("Z", 1),
        ("Y", "X"): ("Z", -1),
        ("Y", "Z"): ("X", 1),
        ("Z", "Y"): ("X", -1),
        ("Z", "X"): ("Y", 1),
        ("X", "Z"): ("Y", -1),
    }
    power = 0
    current = ["I"] * n
    for idx in subset:
        g = gens[idx]
        sign, word = (-1 if g[0] == "-" else 1), (g[1:] if g[0] in "+-" else g)
        power += 0 if sign == 1 else 2
        for q in range(n):
            a, b = current[q], word[q]
            if b == "I":
                continue
            if a == "I":
                current[q] = b
            elif a == b:
                current[q] = "I"
            else:
                current[q], p = mult[(a, b)]
                power += p
    return all(c == "I" for c in current) and power % 4 == 2


def independent_check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    schema_error = validate_certificate(case, cert)
    if schema_error:
        return _fail(schema_error)
    n = case.get("num_qubits")
    gens = case.get("generators")
    if (
        type(n) is not int
        or n < 1
        or not isinstance(gens, list)
        or any(type(g) is not str or not g for g in gens)
    ):
        return _fail("judge case is malformed")
    rows = []
    for g in gens:
        word = g[1:] if g[0] in "+-" else g
        vec = _symplectic(word) if len(word) == n else None
        if vec is None:
            return _fail("judge case has a malformed generator")
        rows.append(vec)
    m = len(rows)
    anticommuting = any(_form(rows[i], rows[j], n) for i in range(m) for j in range(i + 1, m))
    dependent = m > 0 and _rank(rows) < m
    in_scope = m > 0 and not anticommuting and not dependent
    no_logical = in_scope and m == n  # a maximal isotropic group: its centralizer is itself

    status = cert.get("status")
    if status == "OUT_OF_SCOPE":
        if no_logical:
            if cert.get("witness") == {"kind": "full_rank"}:
                return {
                    "verdict": "PASS",
                    "details": "m = n independent commuting generators confirmed",
                }
            return _fail("a valid group with m = n needs the witness {'kind': 'full_rank'}")
        if in_scope:
            return _fail("valid stabilizer group reported OUT_OF_SCOPE")
        w = cert.get("witness")
        kind = w.get("kind") if isinstance(w, dict) else None
        if kind == "empty_generators" and m == 0:
            return {"verdict": "PASS", "details": "empty generator list confirmed"}
        if kind == "anticommuting":
            pair = w.get("pair")
            if isinstance(pair, list) and len(pair) == 2 and all(type(i) is int for i in pair):
                i, j = pair
                if 0 <= i < m and 0 <= j < m and _form(rows[i], rows[j], n):
                    return {"verdict": "PASS", "details": "anticommuting pair confirmed"}
            return _fail("anticommuting witness does not name an anticommuting pair")
        if kind == "dependent":
            vec = w.get("linear_combination")
            if (
                isinstance(vec, list)
                and len(vec) == m
                and all(type(c) is int and c in (0, 1) for c in vec)
                and any(vec)
            ):
                total = [sum(rows[k][col] for k in range(m) if vec[k]) % 2 for col in range(2 * n)]
                if not any(total):
                    return {"verdict": "PASS", "details": "F2 dependency confirmed"}
            return _fail("dependent witness is not a nonzero F2 dependency")
        if kind == "minus_identity":
            subset = w.get("subset")
            if (
                isinstance(subset, list)
                and subset
                and all(type(i) is int and 0 <= i < m for i in subset)
                and len(set(subset)) == len(subset)
                and _phase_product_is_minus_identity(gens, subset, n)
            ):
                return {"verdict": "PASS", "details": "-I product confirmed"}
            return _fail("minus_identity witness does not multiply to -I")
        return _fail(f"unknown OUT_OF_SCOPE witness kind {kind!r}")

    if status != "SOLVED":
        return _fail(f"Unexpected status: {status}")
    if not in_scope or no_logical:
        return _fail("case is out of scope (or has no logical qubit); SOLVED is not admissible")
    dist = cert.get("distance")
    if type(dist) is not int or dist < 1:
        return _fail("distance must be an int >= 1")
    if cert.get("lower_bound") is not None:
        return _fail("lower_bound must be null")
    log_word = cert.get("logical")
    logical = _symplectic(log_word) if type(log_word) is str and len(log_word) == n else None
    if logical is None:
        return _fail("Missing or malformed logical operator")
    if sum(1 for ch in log_word if ch != "I") != dist:
        return _fail("Logical weight != reported distance")
    base_rank = _rank(rows)
    if any(_form(logical, r, n) for r in rows):
        return _fail("Logical does not commute with generators")
    if _rank(rows + [logical]) == base_rank:
        return _fail("Logical lies in stabilizer span S")

    budget = 0
    for w in range(1, dist):
        count = 0
        for positions in itertools.combinations(range(n), w):
            count += 3**w
            budget += 3**w
            if budget > WORK_LIMIT:
                return _fail("distance claim is beyond the independent enumeration limit")
            for letters in itertools.product("XYZ", repeat=w):
                chars = ["I"] * n
                for pos, ch in zip(positions, letters):
                    chars[pos] = ch
                cand = _symplectic("".join(chars))
                if any(_form(cand, r, n) for r in rows):
                    continue
                if _rank(rows + [cand]) > base_rank:
                    return _fail(
                        f"Found lighter logical operator {''.join(chars)} of weight {w} < {dist}"
                    )
    return {"verdict": "PASS", "details": "Independent exhaustive distance verification confirmed"}
