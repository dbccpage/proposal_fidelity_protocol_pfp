"""Seeded linear-system items, clean solution traces and the pre-lock mutant families.

A trace is a JSON-ready dict: the posed item plus a list of steps. Each step has an
``id``, a ``kind`` (given, tool, claim, answer), the ids it ``cites``, a structured
``output`` and free ``text``. Rationals are written as ``"p/q"`` strings.

The generator's ground truth uses Cramer's rule, not the Gauss-Jordan routine the
detectors use, so a defect in one is not silently shared by the other.
AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import random
from fractions import Fraction
from typing import Any, Callable, Dict, List

Trace = Dict[str, Any]


def q(value: Fraction | int) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def det(m: List[List[Fraction]]) -> Fraction:
    if len(m) == 1:
        return m[0][0]
    total = Fraction(0)
    for j, entry in enumerate(m[0]):
        if entry:
            minor = [row[:j] + row[j + 1:] for row in m[1:]]
            total += (-1) ** j * entry * det(minor)
    return total


def cramer(a: List[List[Fraction]], b: List[Fraction]) -> List[Fraction]:
    d = det(a)
    if d == 0:
        raise ValueError("SINGULAR")
    return [det([row[:j] + [b[i]] + row[j + 1:] for i, row in enumerate(a)]) / d for j in range(len(a))]


def make_item(rng: random.Random, index: int) -> Dict[str, Any]:
    n = rng.choice((3, 4))
    while True:
        a = [[Fraction(rng.randint(-5, 5)) for _ in range(n)] for _ in range(n)]
        if det(a) != 0:
            break
    b = [Fraction(rng.randint(-9, 9)) for _ in range(n)]
    return {"item_id": f"LS-{index:04d}", "A": [[q(v) for v in row] for row in a], "b": [q(v) for v in b]}


def _solution(item: Dict[str, Any]) -> List[Fraction]:
    a = [[Fraction(v) for v in row] for row in item["A"]]
    return cramer(a, [Fraction(v) for v in item["b"]])


def clean_trace(item: Dict[str, Any]) -> Trace:
    x = _solution(item)
    n = len(x)
    r_matrix = [[q(1 if i == j else 0) for j in range(n)] + [q(x[i])] for i in range(n)]
    xs = [q(v) for v in x]
    return {
        "item_id": item["item_id"],
        "posed": {"A": item["A"], "b": item["b"]},
        "steps": [
            {"id": "s0", "kind": "given", "cites": [], "output": {"A": item["A"], "b": item["b"]},
             "text": "The system A x = b as posed."},
            {"id": "s1", "kind": "tool", "tool": "rref", "cites": ["s0"], "output": {"R": r_matrix},
             "text": "Row-reduce the augmented matrix [A | b]."},
            {"id": "s2", "kind": "claim", "claim": "read_solution", "cites": ["s1"], "output": {"x": xs},
             "text": "Read the solution from the last column of the reduced matrix."},
            {"id": "s3", "kind": "tool", "tool": "residual", "cites": ["s0", "s2"],
             "output": {"r": [q(0)] * n}, "text": "Compute the residual A x - b."},
            {"id": "s4", "kind": "answer", "cites": ["s2", "s3"], "output": {"x": xs},
             "text": "The residual is zero, so x solves the system."},
        ],
    }


def _step(trace: Trace, step_id: str) -> Dict[str, Any]:
    return next(s for s in trace["steps"] if s["id"] == step_id)


def _residual(trace: Trace, xs: List[str]) -> List[str]:
    a = trace["posed"]["A"]
    b = trace["posed"]["b"]
    return [q(sum((Fraction(v) * Fraction(w) for v, w in zip(row, xs)), Fraction(0)) - Fraction(bi))
            for row, bi in zip(a, b)]


def _delta(rng: random.Random) -> Fraction:
    while True:
        d = Fraction(rng.choice((-3, -2, -1, 1, 2, 3)), rng.choice((1, 1, 2, 3)))
        if d:
            return d


PARAPHRASES = (
    "Substituting back gives zero in every row, so this is the solution.",
    "Checking each equation, both sides agree; the answer stands.",
    "A quick verification confirms consistency with all equations.",
    "Plugging the values in reproduces b exactly, as required.",
)

# ---- clean controls (expected verdict: green) ---------------------------------


def c0_canonical(trace: Trace, rng: random.Random) -> Trace:
    return copy.deepcopy(trace)


def c1_unreduced_fractions(trace: Trace, rng: random.Random) -> Trace:
    t = copy.deepcopy(trace)
    k = rng.choice((2, 3, 5))

    def scale(s: str) -> str:
        f = Fraction(s)
        return f"{f.numerator * k}/{f.denominator * k}"

    for sid in ("s2", "s4"):
        _step(t, sid)["output"]["x"] = [scale(v) for v in _step(t, sid)["output"]["x"]]
    return t


def c2_paraphrased_text(trace: Trace, rng: random.Random) -> Trace:
    t = copy.deepcopy(trace)
    _step(t, "s4")["text"] = rng.choice(PARAPHRASES)
    _step(t, "s2")["text"] = "Hence each unknown equals the corresponding entry of the reduced column."
    return t


def c3_shuffled_order(trace: Trace, rng: random.Random) -> Trace:
    t = copy.deepcopy(trace)
    rng.shuffle(t["steps"])
    return t


def c4_redundant_check(trace: Trace, rng: random.Random) -> Trace:
    t = copy.deepcopy(trace)
    extra = copy.deepcopy(_step(t, "s3"))
    extra["id"] = "s3b"
    extra["text"] = "Second, independent residual computation."
    t["steps"].insert(4, extra)
    _step(t, "s4")["cites"] = ["s2", "s3", "s3b"]
    return t


CLEAN_FAMILIES: Dict[str, Callable[[Trace, random.Random], Trace]] = {
    "C0_canonical": c0_canonical,
    "C1_unreduced_fractions": c1_unreduced_fractions,
    "C2_paraphrased_text": c2_paraphrased_text,
    "C3_shuffled_order": c3_shuffled_order,
    "C4_redundant_check": c4_redundant_check,
}

# ---- pre-lock mutant families (expected verdict: not green) -------------------


def m1_known_wrong(trace: Trace, rng: random.Random) -> Trace:
    """Wrong solution in the claim and the answer; the residual tool reports honestly."""
    t = copy.deepcopy(trace)
    xs = list(_step(t, "s2")["output"]["x"])
    i = rng.randrange(len(xs))
    xs[i] = q(Fraction(xs[i]) + _delta(rng))
    _step(t, "s2")["output"]["x"] = xs
    _step(t, "s4")["output"]["x"] = list(xs)
    _step(t, "s3")["output"]["r"] = _residual(t, xs)
    return t


def m2_fluent_paraphrase(trace: Trace, rng: random.Random) -> Trace:
    """M1 plus fluent prose asserting verification on every step."""
    t = m1_known_wrong(trace, rng)
    _step(t, "s3")["text"] = "The residual vanishes in every component."
    _step(t, "s4")["text"] = rng.choice(PARAPHRASES)
    return t


def m3_deleted_citation(trace: Trace, rng: random.Random) -> Trace:
    """M1 with the supporting evidence removed: a citation deleted, sometimes with its step."""
    t = m1_known_wrong(trace, rng)
    variant = rng.choice(("drop_residual_step", "uncite_rref", "uncite_given"))
    if variant == "drop_residual_step":
        t["steps"] = [s for s in t["steps"] if s["id"] != "s3"]
        _step(t, "s4")["cites"] = ["s2"]
    elif variant == "uncite_rref":
        _step(t, "s2")["cites"] = []
    else:
        _step(t, "s3")["cites"] = ["s2"]
    t["mutation_variant"] = variant
    return t


def m4_mutated_tool_output(trace: Trace, rng: random.Random) -> Trace:
    """Tool outputs silently changed; every downstream step is consistent with them."""
    t = copy.deepcopy(trace)
    r_matrix = copy.deepcopy(_step(t, "s1")["output"]["R"])
    i = rng.randrange(len(r_matrix))
    r_matrix[i][-1] = q(Fraction(r_matrix[i][-1]) + _delta(rng))
    _step(t, "s1")["output"]["R"] = r_matrix
    xs = [row[-1] for row in r_matrix]
    _step(t, "s2")["output"]["x"] = xs
    _step(t, "s4")["output"]["x"] = list(xs)
    _step(t, "s3")["output"]["r"] = [q(0)] * len(xs)
    return t


MUTANT_FAMILIES: Dict[str, Callable[[Trace, random.Random], Trace]] = {
    "M1_known_wrong": m1_known_wrong,
    "M2_fluent_paraphrase": m2_fluent_paraphrase,
    "M3_deleted_citation": m3_deleted_citation,
    "M4_mutated_tool_output": m4_mutated_tool_output,
}
