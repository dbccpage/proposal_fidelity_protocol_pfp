# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A counter-machine program run under declared limits, and a captured exit
state: every jump names an instruction and every instruction a register;
the run is replayed here (halt is a completion; running out of steps is a
timeout; a register above the value bound stops the run at the limit), and
the captured exit kind, registers and step count must be the replayed ones.
Only a halt is a completion.

The claim: instructions (in declared order: the program; the first is the
start), registers (each carrying its initial value), two bounds (steps,
then values), finals (one per register, carrying its captured value) and
one capture (carrying the captured step count); ``inc(i, r, n)``,
``dec(i, r, n, z)`` (on a positive register go to ``n``, on zero to
``z``), ``halt(i)``, ``final_of(f, r)``, and the captured exit kind:
``halted(c)``, ``timed_out(c)`` or ``at_limit(c)``.

Relational clauses, carried by derivability over the hosted claim:
``inc_targets`` and ``dec_targets`` (every jump names an instruction and
every counted register is a register: a bad jump is refused natively),
``one_final`` and ``finals_given``.

Decoded clauses, decided outside the grammar, over the replay:
``well_formed`` (each instruction one kind, one exit kind, naturals
throughout, at most 16 registers and 100000 steps), ``no_false_completion``
(a run that stopped without halting is not captured as halted: the refused
case, a timeout claimed as a completed run), ``exit_exact``,
``state_exact`` and ``steps_exact``.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import position, rows

CHALLENGE_ID = "limited_runs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "no_false_completion", "exit_exact", "state_exact", "steps_exact")
MAX_STEPS = 100000
# An instruction by positions: ("inc", r, n) | ("dec", r, n, z) | ("halt",)
Ins = tuple[object, ...]


def _nat(fs: FiniteStructure, e: int) -> int:
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 and v.num >= 0 else -1


def program(fs: FiniteStructure) -> list[Ins | None]:
    got: dict[int, list[Ins]] = {}

    def ip(e: int) -> int:
        k = position(fs, "instr", e)
        return -1 if k is None else k

    def rp(e: int) -> int:
        k = position(fs, "register", e)
        return -1 if k is None else k

    for i, r, n in rows(fs, "inc"):
        got.setdefault(i, []).append(("inc", rp(r), ip(n)))
    for i, r, n, z in rows(fs, "dec"):
        got.setdefault(i, []).append(("dec", rp(r), ip(n), ip(z)))
    for (i,) in rows(fs, "halt"):
        got.setdefault(i, []).append(("halt",))
    return [got[i][0] if len(got.get(i, [])) == 1 else None for i in fs.elements("instr")]


def exit_kind(fs: FiniteStructure) -> str | None:
    kinds = [k for name, k in (("halted", "HALTED"), ("timed_out", "TIMEOUT"), ("at_limit", "LIMIT"))
             for _ in rows(fs, name)]
    return kinds[0] if len(kinds) == 1 else None


def run(fs: FiniteStructure) -> tuple[str, list[int], int] | None:
    prog = program(fs)
    if None in prog or not prog:
        return None
    regs = [_nat(fs, r) for r in fs.elements("register")]
    bounds = [_nat(fs, b) for b in fs.elements("bound")]
    if -1 in regs or len(bounds) != 2 or -1 in bounds or bounds[0] > MAX_STEPS:
        return None
    max_steps, max_value = bounds
    pc, steps = 0, 0
    while True:
        ins = prog[pc]
        assert ins is not None
        if ins[0] == "halt":
            return "HALTED", regs, steps
        if any(v > max_value for v in regs):
            return "LIMIT", regs, steps
        if steps == max_steps:
            return "TIMEOUT", regs, steps
        r = int(str(ins[1]))
        if not (0 <= r < len(regs)) or any(not 0 <= int(str(t)) < len(prog) for t in ins[2:]):
            return None
        if ins[0] == "inc":
            regs[r] += 1
            pc = int(str(ins[2]))
        elif regs[r] > 0:
            regs[r] -= 1
            pc = int(str(ins[2]))
        else:
            pc = int(str(ins[3]))
        steps += 1


def captured(fs: FiniteStructure) -> tuple[str | None, list[int], int]:
    finals = {r: _nat(fs, f) for f, r in rows(fs, "final_of")}
    caps = fs.elements("capture")
    return (exit_kind(fs), [finals.get(r, -1) for r in fs.elements("register")],
            _nat(fs, caps[0]) if len(caps) == 1 else -1)


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    return run(fs) is not None and exit_kind(fs) is not None and len(fs.elements("register")) <= 16


def no_false_completion(fs: FiniteStructure, _o: Oracle) -> bool:
    got = run(fs)
    return got is not None and (got[0] == "HALTED" or captured(fs)[0] != "HALTED")


def exit_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    got = run(fs)
    return got is not None and got[0] == captured(fs)[0]


def state_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    got = run(fs)
    return got is not None and got[1] == captured(fs)[1]


def steps_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    got = run(fs)
    return got is not None and got[2] == captured(fs)[2]


def describe(fs: FiniteStructure) -> dict[str, object]:
    got = run(fs)
    return {"run": None if got is None else [got[0], got[1], got[2]]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    instr, register = e.form("instr"), e.form("register")
    inc, dec, final_of = e.form("inc"), e.form("dec"), e.form("final_of")
    return Compiled(
        (
            Closure("inc_targets", ((inc, ("i", "r", "n")),), ((instr, ("i",)), (register, ("r",)), (instr, ("n",)))),
            Closure("dec_targets", ((dec, ("i", "r", "n", "z")),),
                    ((instr, ("i",)), (register, ("r",)), (instr, ("n",)), (instr, ("z",)))),
            Functional("one_final", final_of, 1),
            Total("finals_given", ((register, ("r",)),), ((final_of, ("f", "r")),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("no_false_completion", no_false_completion), ("exit_exact", exit_exact),
            ("state_exact", state_exact), ("steps_exact", steps_exact))),
    )
