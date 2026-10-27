"""Held-out adversarial mutant families for the detector adequacy battery.

Each family takes a clean trace (``traces.clean_trace``) and a seeded ``random.Random``
and returns a new, defective trace that keeps the schema and reads as plausible. The
families were written without reading the detectors or the battery, and they model
ways a tool-using or LLM-written trace goes wrong while staying internally tidy. Every
returned trace is defective by the independent judge: the answer is wrong, some step
replays as defective, or the trace is malformed as stated in the family docstring.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import random
from fractions import Fraction
from typing import Callable, Dict, List

from pfp.use_cases.detector_adequacy.traces import Trace, _step, cramer, det, q


def _xs(trace: Trace) -> List[Fraction]:
    return [Fraction(v) for v in _step(trace, "s2")["output"]["x"]]


def _slip(xs: List[Fraction], rng: random.Random) -> List[Fraction]:
    """A realistic slip: a dropped minus sign, or two coordinates traded; else an off-by-one."""
    out = list(xs)
    nonzero = [i for i, v in enumerate(out) if v != 0]
    pairs = [(i, j) for i in range(len(out)) for j in range(i + 1, len(out)) if out[i] != out[j]]
    choice = rng.choice(("sign", "swap"))
    if choice == "sign" and nonzero:
        i = rng.choice(nonzero)
        out[i] = -out[i]
    elif pairs:
        i, j = rng.choice(pairs)
        out[i], out[j] = out[j], out[i]
    else:
        i = rng.randrange(len(out))
        out[i] += 1
    return out


def _rebuild(t: Trace, a: List[List[Fraction]], b: List[Fraction]) -> None:
    """Make s0..s4 a self-consistent solution of the system (a, b); ``posed`` is untouched."""
    x = cramer(a, b)
    n = len(x)
    _step(t, "s0")["output"] = {"A": [[q(v) for v in row] for row in a], "b": [q(v) for v in b]}
    _step(t, "s1")["output"]["R"] = [[q(int(i == j)) for j in range(n)] + [q(x[i])] for i in range(n)]
    _step(t, "s2")["output"]["x"] = [q(v) for v in x]
    _step(t, "s3")["output"]["r"] = [q(0)] * n
    _step(t, "s4")["output"]["x"] = [q(v) for v in x]


def h1_drifted_given_copy(trace: Trace, rng: random.Random) -> Trace:
    """The trace's own copy of the system (s0) drifts from what was posed.

    Models a transcription error when the solver restates the problem: one entry
    changed, two rows of A swapped without b, A transposed, or a sign lost in b. Every
    later step is a correct solution of the drifted copy, so the chain is internally
    consistent. Defective: s0 differs from ``posed`` (the given step replays defective),
    and the answer usually fails the posed system.
    """
    t = copy.deepcopy(trace)
    a = [[Fraction(v) for v in row] for row in trace["posed"]["A"]]
    b = [Fraction(v) for v in trace["posed"]["b"]]
    n = len(a)
    variant = rng.choice(("entry", "row_swap", "transpose", "b_sign"))
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if b[i] != b[j]]
    transposed = [list(col) for col in zip(*a)]
    if variant == "row_swap" and pairs:
        i, j = rng.choice(pairs)
        a[i], a[j] = a[j], a[i]
    elif variant == "transpose" and transposed != a:
        a = transposed
    elif variant == "b_sign" and any(b):
        i = rng.choice([k for k, v in enumerate(b) if v != 0])
        b[i] = -b[i]
    else:
        variant = "entry"
        while True:
            i, j = rng.randrange(n), rng.randrange(n)
            trial = [row[:] for row in a]
            trial[i][j] += rng.choice((-2, -1, 1, 2))
            if det(trial) != 0:
                a = trial
                break
    _rebuild(t, a, b)
    t["mutation_variant"] = variant
    return t


def h2_conflicting_answers(trace: Trace, rng: random.Random) -> Trace:
    """Two answer steps with different values; one is a 'final' restatement.

    Models a self-correction that goes the wrong way, or a correct revision appended
    after a wrong first answer. A reader that keeps only the first, or only the last,
    answer sees a clean trace. Defective: the wrong answer step disagrees with the
    claim it cites (replays defective); when it comes first the answer is also wrong.
    """
    t = copy.deepcopy(trace)
    wrong = [q(v) for v in _slip(_xs(t), rng)]
    extra = copy.deepcopy(_step(t, "s4"))
    extra["id"] = "s5"
    extra["text"] = "Final answer, restated after re-checking the arithmetic."
    if rng.random() < 0.5:
        extra["output"]["x"] = wrong
        t["mutation_variant"] = "wrong_last"
    else:
        _step(t, "s4")["output"]["x"] = wrong
        t["mutation_variant"] = "wrong_first"
    t["steps"].append(extra)
    return t


def h3_overriding_claim(trace: Trace, rng: random.Random) -> Trace:
    """A second read-out claim 'corrects' the first, and the answer follows the second.

    The residual tool still checks the original, correct claim and honestly reports
    zero, and the answer cites that zero residual. Defective: the inserted claim does
    not match the reduced matrix it cites (replays defective) and the answer is wrong.
    """
    t = copy.deepcopy(trace)
    wrong = [q(v) for v in _slip(_xs(t), rng)]
    k = rng.randrange(len(wrong)) + 1
    extra = {"id": "s2b", "kind": "claim", "claim": "read_solution", "cites": ["s1"],
             "output": {"x": wrong},
             "text": f"On re-reading row {k} of the reduced matrix, the values are as listed."}
    pos = next(i for i, s in enumerate(t["steps"]) if s["id"] == "s2") + 1
    t["steps"].insert(pos, extra)
    _step(t, "s4")["cites"] = ["s2b", "s3"]
    _step(t, "s4")["output"]["x"] = list(wrong)
    return t


def _decimal(v: Fraction, digits: int) -> str:
    n = round(v * 10 ** digits)
    whole, frac = divmod(abs(n), 10 ** digits)
    return f"{'-' if n < 0 else ''}{whole}.{frac:0{digits}d}"


def h4_decimal_rounding(trace: Trace, rng: random.Random) -> Trace:
    """Claim and answer written as rounded decimals; the residual is reported as zero.

    Models a solver that converts exact fractions to 2-4 decimal places and a check
    that rounds its residual. The decimals look equal to the exact values, but as
    rationals they are not. When every coordinate terminates at that precision, a sign
    or ordering slip is used instead. Defective: the claim differs from the reduced
    matrix, the residual step misreports, and the answer is wrong.
    """
    t = copy.deepcopy(trace)
    digits = rng.choice((2, 3, 4))
    xs = _xs(t)
    shown = [_decimal(v, digits) for v in xs]
    if all(Fraction(s) == v for s, v in zip(shown, xs)):
        shown = [_decimal(v, digits) for v in _slip(xs, rng)]
        t["mutation_variant"] = "slip"
    else:
        t["mutation_variant"] = "rounded"
    _step(t, "s2")["output"]["x"] = shown
    _step(t, "s4")["output"]["x"] = list(shown)
    _step(t, "s3")["output"]["r"] = [_decimal(Fraction(0), digits)] * len(xs)
    _step(t, "s3")["text"] = f"Residual A x - b, rounded to {digits} places."
    return t


def h5_unreduced_reading(trace: Trace, rng: random.Random) -> Trace:
    """The tool returns a row-equivalent but not reduced matrix, read off naively.

    Either two rows of [I | x] come back swapped, or one pivot row is left scaled by a
    constant. The matrix is still row-equivalent to [A | b], and the claim faithfully
    reads its last column top to bottom, but that column is not the solution. The
    residual is reported as zero. Defective: the rref step is not the reduced form,
    the residual step misreports, and the answer is wrong.
    """
    t = copy.deepcopy(trace)
    xs = _xs(t)
    n = len(xs)
    rows = [[Fraction(int(i == j)) for j in range(n)] + [xs[i]] for i in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if xs[i] != xs[j]]
    nonzero = [i for i, v in enumerate(xs) if v != 0] or list(range(n))
    if pairs and rng.random() < 0.5:
        i, j = rng.choice(pairs)
        rows[i], rows[j] = rows[j], rows[i]
        t["mutation_variant"] = "rows_swapped"
    else:
        i = rng.choice(nonzero)
        k = rng.choice((-2, -1, 2, 3))
        rows[i] = [k * v for v in rows[i]]
        t["mutation_variant"] = "pivot_unscaled"
    _step(t, "s1")["output"]["R"] = [[q(v) for v in row] for row in rows]
    read = [q(row[-1]) for row in rows]
    _step(t, "s2")["output"]["x"] = read
    _step(t, "s4")["output"]["x"] = list(read)
    return t


def h6_length_mismatch(trace: Trace, rng: random.Random) -> Trace:
    """Claim and answer carry one coordinate too many or too few.

    Models an extra 'free variable' appended, or a dropped last unknown. A checker that
    pairs lists with a truncating zip sees every listed value agree. Defective and
    malformed: the solution vector's length differs from the system's dimension, so
    the claim does not match the reduced matrix and the answer is not a solution.
    """
    t = copy.deepcopy(trace)
    xs = list(_step(t, "s2")["output"]["x"])
    if rng.random() < 0.5:
        xs.append(q(rng.randint(-3, 3)))
        t["mutation_variant"] = "padded"
    else:
        xs.pop(rng.randrange(len(xs)))
        t["mutation_variant"] = "dropped"
    _step(t, "s2")["output"]["x"] = xs
    _step(t, "s4")["output"]["x"] = list(xs)
    return t


HELDOUT_FAMILIES: Dict[str, Callable[[Trace, random.Random], Trace]] = {
    "H1_drifted_given_copy": h1_drifted_given_copy,
    "H2_conflicting_answers": h2_conflicting_answers,
    "H3_overriding_claim": h3_overriding_claim,
    "H4_decimal_rounding": h4_decimal_rounding,
    "H5_unreduced_reading": h5_unreduced_reading,
    "H6_length_mismatch": h6_length_mismatch,
}
