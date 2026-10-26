# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A one-function recursion on naturals, run with a declared measure that must
fall strictly at every recursive call, and a result that must be confirmed
by an evaluator whose digest differs from the interpreter's: a
self-certified evaluation is refused.

The program: ``f(n)`` is the base value when ``n`` is a base case, and
``f(n - k) + c`` otherwise; the measure is ``m(n) = a n + b``.

The claim: numbers and evaluators (each in declared order), each number
carrying a natural as its value and each evaluator a digest (an exact
32-byte value), ``base(n, v)``, ``step(k, c)``, ``measure(a, b)``,
``input(n)``, ``output(v)``, ``interpreter(e)`` and ``confirms(e, v)``
(evaluator ``e`` reports the result ``v``).

Relational clauses, carried by derivability over the hosted claim:
``step_given``, ``one_step``, ``measure_given``, ``one_measure``,
``input_given``, ``one_input``, ``output_given``, ``one_output``,
``interpreter_given``, ``one_interpreter``, ``one_base_value`` and
``confirms_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (numbers are
naturals, the input at most 10000, and every evaluator carries a digest),
``decreasing`` (from the input, every recursive call has ``n >= k`` and
lowers the measure strictly, until a base case; the run is checked call by
call before it is made, so no unbounded run is attempted; the refused case
is a call the measure does not lower), ``external`` (some confirmation comes
from an evaluator whose digest is not the interpreter's) and
``output_recomputed`` (the declared output, and every confirmation's
reported result, are the recomputed value).  The last three are re-decided
by the kernel, digests read as naturals.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, render, rows

CHALLENGE_ID = "confirmed_runs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ConfirmedRuns"
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("well_formed", "decreasing", "external", "output_recomputed")
LEAN_CLAUSES = ("decreasing", "external", "output_recomputed")
MAX_INPUT = 10000


def _nat(x: Q | None) -> int:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else -1


def _v(fs: FiniteStructure, e: int) -> int:
    return _nat(fs.value(e))


def _one(fs: FiniteStructure, name: str) -> tuple[int, ...] | None:
    got = rows(fs, name)
    return got[0] if len(got) == 1 else None


def program(fs: FiniteStructure) -> tuple[dict[int, int], int, int, int, int, int] | None:
    """(base, k, c, a, b, input) as naturals, or None when a part is missing."""
    step, meas, inp = _one(fs, "step"), _one(fs, "measure"), _one(fs, "input")
    if step is None or meas is None or inp is None:
        return None
    base = {_v(fs, n): _v(fs, v) for n, v in rows(fs, "base")}
    return base, _v(fs, step[0]), _v(fs, step[1]), _v(fs, meas[0]), _v(fs, meas[1]), _v(fs, inp[0])


def run(fs: FiniteStructure) -> int | None:
    """The recomputed value, or None when a call does not lower the measure
    (checked before the call is made)."""
    p = program(fs)
    if p is None:
        return None
    base, k, c, a, b, n = p
    total, calls = 0, 0
    while n not in base:
        if n < k or not a * (n - k) + b < a * n + b or calls >= MAX_INPUT:
            return None
        calls += 1
        n -= k
        total += c
    return base[n] + total


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    nums = [_v(fs, e) for e in fs.elements("number")]
    p = program(fs)
    return (-1 not in nums and p is not None and 0 <= p[5] <= MAX_INPUT
            and all(fs.digest(e) is not None for e in fs.elements("evaluator")))


def decreasing(fs: FiniteStructure, _o: Oracle) -> bool:
    return run(fs) is not None


def external(fs: FiniteStructure, _o: Oracle) -> bool:
    it = _one(fs, "interpreter")
    if it is None:
        return False
    mine = fs.digest(it[0])
    return any(fs.digest(e) != mine for e, _ in rows(fs, "confirms"))


def output_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    got, out = run(fs), _one(fs, "output")
    return (got is not None and out is not None and _v(fs, out[0]) == got
            and all(_v(fs, v) == got for _, v in rows(fs, "confirms")))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"value": run(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "decreasing")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    num, ev = e.form("number"), e.form("evaluator")
    base, step, meas, inp, out = e.form("base"), e.form("step"), e.form("measure"), e.form("input"), e.form("output")
    interp, conf = e.form("interpreter"), e.form("confirms")
    return Compiled(
        (
            Total("step_given", (), ((step, ("k", "c")),)),
            Functional("one_step", step, 0),
            Total("measure_given", (), ((meas, ("a", "b")),)),
            Functional("one_measure", meas, 0),
            Total("input_given", (), ((inp, ("n",)),)),
            Functional("one_input", inp, 0),
            Total("output_given", (), ((out, ("v",)),)),
            Functional("one_output", out, 0),
            Total("interpreter_given", (), ((interp, ("e",)),)),
            Functional("one_interpreter", interp, 0),
            Functional("one_base_value", base, 1),
            Closure("confirms_typed", ((conf, ("e", "v")),), ((ev, ("e",)), (num, ("v",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("decreasing", decreasing), ("external", external),
            ("output_recomputed", output_recomputed))),
    )


LEAN_DEFS = (
    "/-- The program: base cases, the step `k`, the addend `c`, the measure `a n + b`. -/",
    "structure Prog where",
    "  base : List (Prod Nat Nat)",
    "  k : Nat",
    "  c : Nat",
    "  a : Nat",
    "  b : Nat",
    "",
    "def baseOf (p : Prog) (n : Nat) : Option Nat := (p.base.find? fun r => r.1 == n).map (fun r => r.2)",
    "",
    "/-- Run from `n` with `fuel` calls; each call is checked before it is made. -/",
    "def runF (p : Prog) : Nat -> Nat -> Nat -> Option Nat",
    "  | 0, n, acc => (baseOf p n).map (fun v => v + acc)",
    "  | fuel + 1, n, acc => match baseOf p n with",
    "    | some v => some (v + acc)",
    "    | none => if p.k <= n && p.a * (n - p.k) + p.b < p.a * n + p.b then runF p fuel (n - p.k) (acc + p.c)",
    "        else none",
    "",
    "def decreasing (p : Prog) (n : Nat) : Bool := (runF p 10000 n 0).isSome",
    "",
    "/-- Some confirmer's digest is not the interpreter's. -/",
    "def external (interp : Nat) (confs : List (Prod Nat Nat)) : Bool := confs.any fun r => r.1 != interp",
    "",
    "def outputRecomputed (p : Prog) (n out : Nat) (confs : List (Prod Nat Nat)) : Bool :=",
    "  match runF p 10000 n 0 with",
    "  | some v => out == v && confs.all fun r => r.2 == v",
    "  | none => false",
    "",
)
LEAN_CALLS = {"decreasing": "decreasing prog_{f} input_{f}", "external": "external interp_{f} confs_{f}",
              "output_recomputed": "outputRecomputed prog_{f} input_{f} output_{f} confs_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    p = program(fs)
    out, it = _one(fs, "output"), _one(fs, "interpreter")
    assert p is not None and out is not None and it is not None
    base, k, c, a, b, n = p

    def dig(e: int) -> str:
        d = fs.digest(e)
        assert d is not None
        return str(int.from_bytes(d, "big"))

    prog = (f"{{ base := {lean_list([f'({x}, {y})' for x, y in sorted(base.items())])}, k := {k}, c := {c}, "
            f"a := {a}, b := {b} }}")
    return [("prog", "Prog", prog), ("input", "Nat", str(n)), ("output", "Nat", str(_v(fs, out[0]))),
            ("interp", "Nat", dig(it[0])),
            ("confs", "List (Prod Nat Nat)", lean_list([f"({dig(e)}, {_v(fs, v)})" for e, v in rows(fs, "confirms")]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `confirmed_runs`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
