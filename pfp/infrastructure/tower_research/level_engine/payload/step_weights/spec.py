# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A hosted table of step weights between states: every weight is exact and
nonnegative, and the weights leaving each state sum to exactly one.

The claim: states, exact values, and ``weight(s, t, v)`` (the weight of a step
from ``s`` to ``t`` is the value ``v``).  Rows and columns follow the declared
order of states.

Relational clauses, carried by derivability over the hosted claim:
``complete`` (every ordered pair of states has a weight), ``one_weight`` and
``typed``.

Decoded clauses, decided over exact values outside the grammar:
``nonnegative`` (no weight is negative) and ``rows_sum_to_one`` (each state's
outgoing weights sum to one).  Their Lean certificates are re-decided by the
kernel with the exact-rational library.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "step_weights"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "StepWeights"
EXACT = ("py.exact.q",)
CLAUSES = ("nonnegative", "rows_sum_to_one")


def table(fs: FiniteStructure) -> list[list[Q]] | None:
    """The weights in the declared order of states; ``None`` when a weight is
    missing, repeated or undecodable."""
    states = fs.elements("state")
    got: dict[tuple[int, int], Q] = {}
    for name, args in fs.tuples:
        if name != "weight":
            continue
        s, t, v = args
        val = fs.value(v)
        if val is None or (s, t) in got:
            return None
        got[(s, t)] = val
    if any((s, t) not in got for s in states for t in states):
        return None
    return [[got[(s, t)] for t in states] for s in states]


def nonnegative(fs: FiniteStructure, _o: Oracle) -> bool:
    k = table(fs)
    return k is not None and all(x.sign() >= 0 for r in k for x in r)


def rows_sum_to_one(fs: FiniteStructure, _o: Oracle) -> bool:
    k = table(fs)
    return k is not None and all(sum(r, ZERO) == ONE for r in k)


def describe(fs: FiniteStructure) -> dict[str, object]:
    k = table(fs)
    return {"row_sums": None if k is None else [fmt_q(sum(r, ZERO)) for r in k]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    out = []
    for v in verdicts:
        if dict(v.decoded).get("rows_sum_to_one") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    state, val, weight = e.form("state"), e.form("val"), e.form("weight")
    return Compiled(
        (
            Total("complete", ((state, ("s",)), (state, ("t",))), ((weight, ("s", "t", "v")),)),
            Functional("one_weight", weight, 2),
            Closure("typed", ((weight, ("s", "t", "v")),), ((state, ("s",)), (state, ("t",)), (val, ("v",)))),
        ),
        decoded=(
            DecodedClause("nonnegative", nonnegative, EXACT),
            DecodedClause("rows_sum_to_one", rows_sum_to_one, EXACT),
        ),
    )


LEAN_DEFS = (
    "/-- The sum of a row. -/",
    "def total (xs : List QN) : QN := xs.foldl (fun acc x => acc + x) 0",
    "",
    "/-- No weight is negative. -/",
    "def nonnegative (k : Mat) : Bool := k.all fun r => r.all fun x => !QN.pos (-x)",
    "",
    "/-- Each row sums to exactly one. -/",
    "def rowsSumToOne (k : Mat) : Bool := k.all fun r => decide (total r = 1)",
    "",
)
LEAN_CALLS = {"nonnegative": "nonnegative", "rows_sum_to_one": "rowsSumToOne"}


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One table per evaluated fixture; the kernel re-decides each value clause."""
    from operations.use_cases.level_engine.research_engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The value clauses of `step_weights`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        k = table(by[fid].structure)
        assert k is not None
        lines += [f"def table_{fid} : Mat :=", f"  {T.mat(k)}", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause]} table_{fid} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
