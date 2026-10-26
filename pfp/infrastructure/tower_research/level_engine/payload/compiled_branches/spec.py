# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A loop-free source expression over one natural input, a compiled program
for a small stack machine, declared inputs, a fuel and a claimed table of
results.  The source is evaluated here on every declared input, and the
program is run here on every declared input within the fuel; the inputs
must take both arms of every choice in the source, every run must stay on
its stack and halt within the fuel, every halted run must give the
source's result, and the table must be the source's results on exactly the
declared inputs.  The refused case: a compiled branch that changes the
result.

The source: nodes, one ``root(e)``; ``reads_input(e)`` (the input),
``constant(e)`` (the node's own value, a natural), ``plus(e, a, b)``,
``minus(e, a, b)`` and ``if_less(e, a, b, t, f)`` (``t`` when ``a < b``,
else ``f``).  A node may be shared; the expression is its unfolding from
the root, and each place of a choice in the unfolding is its own choice.

The program: instructions in declared order (the first is the start), each
one of ``push(i)`` (pushes the instruction's own value, a natural),
``load(i)`` (pushes the input), ``add(i)`` and ``sub(i)`` (pop ``b``, pop
``a``, push ``a + b`` or ``a - b``), ``jump_if_less(i, t)`` (pop ``b``, pop
``a``, go to ``t`` when ``a < b``), ``jump(i, t)`` and ``halt(i)`` (the
result is the top of the stack).  Integers are exact and unbounded.  With
fuel ``k`` a run executes at most ``k + 1`` instructions, the last of which
may be the halt.

The claim: numbers (exact integers, pairwise distinct), ``input(k)``,
``table_row(k, r)`` (the claimed result for input ``k`` is ``r``) and
``fuel(k)``.

Relational clauses, carried by derivability over the hosted claim:
``root_typed``, ``one_root``, ``plus_typed``, ``minus_typed``, ``if_typed``,
``jumps_land`` and ``plain_jumps_land`` (a jump names an instruction),
``one_target``, ``one_plain_target``, ``inputs_numbers``, ``rows_typed``,
``one_row``, ``rows_given``, ``fuel_typed`` and ``one_fuel``.

Decoded clauses, decided outside the grammar: ``well_formed`` (every node
and instruction read one way, the unfolding finite and reaching every node,
naturals where naturals are due, one fuel of at most 100000),
``never_stuck`` (no run pops too few entries, halts on an empty stack
or passes the last instruction),
``arms_covered`` (the declared inputs take both arms of every choice),
``halts`` (no run runs out of fuel), ``branch_kept`` (every halted run
gives the source's result: the refused case) and ``table_exact``.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "compiled_branches"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "never_stuck", "arms_covered", "halts", "branch_kept", "table_exact")
MAX_FUEL = 100000
MAX_DEPTH = 64
KINDS = ("reads_input", "constant", "plus", "minus", "if_less")
OPS = ("push", "load", "add", "sub", "jump_if_less", "jump", "halt")

# An unfolded expression: ("input",), ("constant", k), ("plus", a, b),
# ("minus", a, b) or ("if_less", a, b, t, f).
Expr = tuple[object, ...]
# An instruction by positions: ("push", k), ("load",), ("add",), ("sub",),
# ("jump_if_less", t), ("jump", t) or ("halt",).
Op = tuple[object, ...]


def _int(fs: FiniteStructure, e: int) -> int | None:
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 else None


def _nat(fs: FiniteStructure, e: int) -> int | None:
    v = _int(fs, e)
    return v if v is not None and v >= 0 else None


def _unfold(fs: FiniteStructure, e: int, above: tuple[int, ...], met: set[int]) -> Expr | None:
    if e in above or len(above) > MAX_DEPTH or e not in fs.elements("node"):
        return None
    met.add(e)
    got: list[tuple[str, tuple[int, ...]]] = [(k, a[1:]) for k in KINDS for a in rows(fs, k) if a[0] == e]
    if len(got) != 1:
        return None
    kind, kids = got[0]
    if kind == "reads_input":
        return ("input",)
    if kind == "constant":
        k = _nat(fs, e)
        return None if k is None else ("constant", k)
    if fs.value(e) is not None:
        return None
    parts = [_unfold(fs, c, above + (e,), met) for c in kids]
    return None if any(p is None for p in parts) else (kind,) + tuple(parts)


def source(fs: FiniteStructure) -> Expr | None:
    roots = rows(fs, "root")
    met: set[int] = set()
    out = _unfold(fs, roots[0][0], (), met) if len(roots) == 1 else None
    return out if out is not None and met == set(fs.elements("node")) else None


def program(fs: FiniteStructure) -> list[Op] | None:
    instrs = fs.elements("instr")
    out: list[Op] = []
    for i in instrs:
        got = [(k, a[1:]) for k in OPS for a in rows(fs, k) if a[0] == i]
        if len(got) != 1:
            return None
        kind, rest = got[0]
        if kind == "push":
            k = _nat(fs, i)
            if k is None:
                return None
            out.append(("push", k))
            continue
        if fs.value(i) is not None:
            return None
        if kind in ("jump_if_less", "jump"):
            if rest[0] not in instrs:
                return None
            out.append((kind, instrs.index(rest[0])))
        else:
            out.append((kind,))
    return out or None


class Claim:
    """A well-formed claim: the unfolded source, the program, the declared
    inputs, the fuel and the claimed table."""

    def __init__(self, expr: Expr, prog: list[Op], inputs: list[int], fuel: int, table: dict[int, int]) -> None:
        self.expr = expr
        self.prog = prog
        self.inputs = inputs
        self.fuel = fuel
        self.table = table


def claim(fs: FiniteStructure) -> Claim | None:
    expr, prog = source(fs), program(fs)
    if expr is None or prog is None:
        return None
    numbers = [_int(fs, k) for k in fs.elements("number")]
    if any(v is None for v in numbers) or len(set(numbers)) != len(numbers):
        return None
    inputs = [n for (k,) in rows(fs, "input") for n in (_nat(fs, k),) if n is not None]
    fuels = [n for (k,) in rows(fs, "fuel") for n in (_nat(fs, k),) if n is not None]
    table = {n: r for k, rr in rows(fs, "table_row") for n, r in ((_nat(fs, k), _int(fs, rr)),)
             if n is not None and r is not None}
    if not inputs or len(inputs) != len(rows(fs, "input")) or len(table) != len(rows(fs, "table_row")):
        return None
    if len(fuels) != 1 or len(rows(fs, "fuel")) != 1 or fuels[0] > MAX_FUEL:
        return None
    return Claim(expr, prog, sorted(inputs), fuels[0], table)


def result_of(expr: Expr, n: int, taken: set[tuple[str, int]], place: str = "") -> int:
    """The source's result on input ``n``; ``taken`` collects each choice's
    place in the unfolding with the arm taken (3 then, 4 else)."""
    kind = expr[0]
    if kind == "input":
        return n
    if kind == "constant":
        return int(str(expr[1]))
    parts = [p for p in expr[1:] if isinstance(p, tuple)]
    if kind == "plus":
        return result_of(parts[0], n, taken, place + "a") + result_of(parts[1], n, taken, place + "b")
    if kind == "minus":
        return result_of(parts[0], n, taken, place + "a") - result_of(parts[1], n, taken, place + "b")
    arm = 3 if result_of(parts[0], n, taken, place + "a") < result_of(parts[1], n, taken, place + "b") else 4
    taken.add((place, arm))
    return result_of(parts[arm - 1], n, taken, place + str(arm))


def choices(expr: Expr, place: str = "") -> set[tuple[str, int]]:
    """Both arms of every choice in the unfolding, by place."""
    kind = expr[0]
    if kind in ("input", "constant"):
        return set()
    parts = [p for p in expr[1:] if isinstance(p, tuple)]
    out = choices(parts[0], place + "a") | choices(parts[1], place + "b")
    if kind == "if_less":
        out |= {(place, 3), (place, 4)} | choices(parts[2], place + "3") | choices(parts[3], place + "4")
    return out


def run(prog: list[Op], n: int, fuel: int) -> tuple[str, int | None]:
    """("HALT", result), ("FUEL", None) when the fuel runs out first, or
    ("STUCK", None) when a pop finds too few entries, a halt finds none, or
    the run passes the last instruction."""
    stack: list[int] = []
    at = 0
    for _ in range(fuel + 1):
        if at >= len(prog):
            return ("STUCK", None)
        op = prog[at]
        kind = op[0]
        if kind == "halt":
            return ("HALT", stack[-1]) if stack else ("STUCK", None)
        at += 1
        if kind == "push":
            stack.append(int(str(op[1])))
        elif kind == "load":
            stack.append(n)
        elif kind == "jump":
            at = int(str(op[1]))
        else:
            if len(stack) < 2:
                return ("STUCK", None)
            b = stack.pop()
            a = stack.pop()
            if kind == "add":
                stack.append(a + b)
            elif kind == "sub":
                stack.append(a - b)
            elif a < b:
                at = int(str(op[1]))
    return ("FUEL", None)


_SEEN: dict[FiniteStructure, tuple[Claim, dict[int, int], set[tuple[str, int]], dict[int, tuple[str, int | None]]]
            | None] = {}


def replay(fs: FiniteStructure) -> tuple[Claim, dict[int, int], set[tuple[str, int]],
                                          dict[int, tuple[str, int | None]]] | None:
    """The claim, the source's result on each declared input, the arms the
    inputs take, and each input's run; ``None`` when not well formed."""
    if fs in _SEEN:
        return _SEEN[fs]
    c = claim(fs)
    out = None
    if c is not None:
        taken: set[tuple[str, int]] = set()
        results = {n: result_of(c.expr, n, taken) for n in c.inputs}
        out = (c, results, taken, {n: run(c.prog, n, c.fuel) for n in c.inputs})
    _SEEN[fs] = out
    return out


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    return claim(fs) is not None


def never_stuck(fs: FiniteStructure, _o: Oracle) -> bool:
    got = replay(fs)
    return got is not None and all(kind != "STUCK" for kind, _ in got[3].values())


def arms_covered(fs: FiniteStructure, _o: Oracle) -> bool:
    got = replay(fs)
    return got is not None and choices(got[0].expr) <= got[2]


def halts(fs: FiniteStructure, _o: Oracle) -> bool:
    got = replay(fs)
    return got is not None and all(kind != "FUEL" for kind, _ in got[3].values())


def branch_kept(fs: FiniteStructure, _o: Oracle) -> bool:
    got = replay(fs)
    return got is not None and all(v == got[1][n] for n, (kind, v) in got[3].items() if kind == "HALT")


def table_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    got = replay(fs)
    return got is not None and got[0].table == got[1]


def describe(fs: FiniteStructure) -> dict[str, object]:
    got = replay(fs)
    if got is None:
        return {"runs": None}
    return {"runs": [[n, got[1][n], got[3][n][0], got[3][n][1]] for n in got[0].inputs]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    node, number, instr = e.form("node"), e.form("number"), e.form("instr")
    root, plus, minus, if_less = e.form("root"), e.form("plus"), e.form("minus"), e.form("if_less")
    jump_if_less, jump = e.form("jump_if_less"), e.form("jump")
    input_, table_row, fuel = e.form("input"), e.form("table_row"), e.form("fuel")
    return Compiled(
        (
            Closure("root_typed", ((root, ("e",)),), ((node, ("e",)),)),
            Functional("one_root", root, 0),
            Closure("plus_typed", ((plus, ("e", "a", "b")),), ((node, ("e",)), (node, ("a",)), (node, ("b",)))),
            Closure("minus_typed", ((minus, ("e", "a", "b")),), ((node, ("e",)), (node, ("a",)), (node, ("b",)))),
            Closure("if_typed", ((if_less, ("e", "a", "b", "t", "f")),),
                    ((node, ("e",)), (node, ("a",)), (node, ("b",)), (node, ("t",)), (node, ("f",)))),
            Closure("jumps_land", ((jump_if_less, ("i", "t")),), ((instr, ("i",)), (instr, ("t",)))),
            Closure("plain_jumps_land", ((jump, ("i", "t")),), ((instr, ("i",)), (instr, ("t",)))),
            Functional("one_target", jump_if_less, 1),
            Functional("one_plain_target", jump, 1),
            Closure("inputs_numbers", ((input_, ("k",)),), ((number, ("k",)),)),
            Closure("rows_typed", ((table_row, ("k", "r")),), ((number, ("k",)), (number, ("r",)))),
            Functional("one_row", table_row, 1),
            Total("rows_given", ((input_, ("k",)),), ((table_row, ("k", "r")),)),
            Closure("fuel_typed", ((fuel, ("k",)),), ((number, ("k",)),)),
            Functional("one_fuel", fuel, 0),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("never_stuck", never_stuck), ("arms_covered", arms_covered),
            ("halts", halts), ("branch_kept", branch_kept), ("table_exact", table_exact))),
    )
