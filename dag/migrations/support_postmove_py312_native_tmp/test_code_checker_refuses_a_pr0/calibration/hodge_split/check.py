"""Independent exact checker for the discrete Hodge split task. AuthorityEffect: None.

The checker recomputes the unique decomposition f = d0 p + d1^T q + h with exact
rationals and compares every required field. Exit 0 on a full match, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from fractions import Fraction
from pathlib import Path

VERTEX_COUNT = 6
EDGES = ((0, 1), (1, 2), (0, 2), (2, 3), (3, 4), (2, 4), (4, 5), (3, 5), (1, 5))
TRIANGLES = ((0, 1, 2), (2, 3, 4))
FLOW = (3, -1, 2, 0, 4, 1, -2, 5, 1)
FIELDS = ("b0", "b1", "euler_characteristic", "potential", "gradient", "curl", "harmonic",
          "harmonic_norm_squared")
RATIONAL = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")


def d0() -> list[list[Fraction]]:
    rows = []
    for u, v in EDGES:
        row = [Fraction(0)] * VERTEX_COUNT
        row[u], row[v] = Fraction(-1), Fraction(1)
        rows.append(row)
    return rows


def d1() -> list[list[Fraction]]:
    index = {edge: i for i, edge in enumerate(EDGES)}
    rows = []
    for a, b, c in TRIANGLES:
        row = [Fraction(0)] * len(EDGES)
        row[index[(a, b)]] += 1
        row[index[(b, c)]] += 1
        row[index[(a, c)]] -= 1
        rows.append(row)
    return rows


def transpose(m):
    return [list(col) for col in zip(*m)]


def matmul(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def matvec(m, v):
    return [sum(x * y for x, y in zip(row, v)) for row in m]


def solve(a, b):
    """Gauss-Jordan over Fractions for a square nonsingular system."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next(r for r in range(col, n) if m[r][col] != 0)
        m[col], m[pivot] = m[pivot], m[col]
        m[col] = [x / m[col][col] for x in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                factor = m[r][col]
                m[r] = [x - factor * y for x, y in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


def rank(m) -> int:
    m = [row[:] for row in m]
    r = 0
    for col in range(len(m[0]) if m else 0):
        pivot = next((i for i in range(r, len(m)) if m[i][col] != 0), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        for i in range(len(m)):
            if i != r and m[i][col] != 0:
                factor = m[i][col] / m[r][col]
                m[i] = [x - factor * y for x, y in zip(m[i], m[r])]
        r += 1
    return r


def text(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def reference() -> dict:
    f = [Fraction(x) for x in FLOW]
    D0, D1 = d0(), d1()
    D0t = transpose(D0)
    laplacian0 = matmul(D0t, D0)
    rhs0 = matvec(D0t, f)
    # Ground vertex 0: drop its row and column, the graph being connected.
    reduced = [row[1:] for row in laplacian0[1:]]
    p = [Fraction(0)] + solve(reduced, rhs0[1:])
    gradient = matvec(D0, p)
    laplacian2 = matmul(D1, transpose(D1))
    q = solve(laplacian2, matvec(D1, f))
    curl = matvec(transpose(D1), q)
    harmonic = [x - g - c for x, g, c in zip(f, gradient, curl)]
    r0, r1 = rank(D0), rank(D1)
    b0 = VERTEX_COUNT - r0
    b1 = len(EDGES) - r0 - r1
    return {"b0": b0, "b1": b1,
            "euler_characteristic": VERTEX_COUNT - len(EDGES) + len(TRIANGLES),
            "potential": [text(x) for x in p], "gradient": [text(x) for x in gradient],
            "curl": [text(x) for x in curl], "harmonic": [text(x) for x in harmonic],
            "harmonic_norm_squared": text(sum(x * x for x in harmonic))}


def canonical(value):
    """Reduce a rational string to lowest terms; refuse anything that is not one."""
    if type(value) is not str or RATIONAL.fullmatch(value) is None:
        return None
    return text(Fraction(value))


def check(raw: str) -> dict:
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"pass": False, "problems": [f"not a JSON object: {exc.msg}"]}
    if type(answer) is not dict:
        return {"pass": False, "problems": ["top level must be a JSON object"]}
    expected = reference()
    problems = [f"missing field {name}" for name in FIELDS if name not in answer]
    problems += [f"unexpected field {name}" for name in answer if name not in FIELDS]
    for name in ("b0", "b1", "euler_characteristic"):
        if name in answer and (type(answer[name]) is not int or answer[name] != expected[name]):
            problems.append(f"{name} is wrong")
    for name in ("potential", "gradient", "curl", "harmonic"):
        if name not in answer:
            continue
        given = answer[name]
        if type(given) is not list or len(given) != len(expected[name]):
            problems.append(f"{name} must be a list of {len(expected[name])} rational strings")
            continue
        wrong = [i for i, (g, e) in enumerate(zip(given, expected[name])) if canonical(g) != e]
        if wrong:
            problems.append(f"{name} is wrong at positions {wrong}")
    if "harmonic_norm_squared" in answer and canonical(answer["harmonic_norm_squared"]) != expected["harmonic_norm_squared"]:
        problems.append("harmonic_norm_squared is wrong")
    return {"pass": not problems, "problems": problems,
            "answer": {key: answer.get(key) for key in FIELDS}}


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import review_common

    fragments = [f"| {i} | ({u},{v}) |" for i, (u, v) in enumerate(EDGES)]
    fragments.append("f = [" + ", ".join(str(x) for x in FLOW) + "]")
    return review_common.run(argv, check=check, reference=reference,
        prompt=Path(__file__).resolve().parent / "prompt.md", fragments=fragments)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
