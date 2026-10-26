"""A reading on the points of a fine scale, two coarsening steps (each point
to a block; the coarse reading is the block average), each step with a
claimed error bound, and two jumps across scales with their own maps and
bounds.

The claim: points, first blocks and second blocks (in declared order),
values, ``reads(p, v)``, ``first(p, b)`` and ``second(b, c)`` (the steps'
maps), ``first_bound(v)`` and ``second_bound(v)``, ``near_jump(p, b)`` with
``near_jump_bound(v)`` (a jump from the points to the first blocks) and
``far_jump(p, c)`` with ``far_jump_bound(v)`` (a jump from the points to
the second blocks).  The error of a map is the largest distance between a
reading and the coarse reading of its image.

Relational clauses, carried by derivability over the hosted claim:
``reads_given``, ``one_read``, ``first_given``, ``one_first``,
``second_given``, ``one_second``, ``near_jump_given``, ``one_near_jump``,
``far_jump_given``, ``one_far_jump``, ``step_bounds_given`` and
``jumps_bounded`` (a jump with no loss bound is refused).

Decoded clauses, decided over exact values outside the grammar:
``composite_maps`` (each jump's map is the composite of the steps between
its scales), ``bounds_hold`` (no step or jump bound is below its recomputed
error) and ``bounds_composed`` (a jump's bound does not exceed the sum of
the bounds of the steps it composes).  Their Lean certificates are
re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.q import ZERO, Q, fmt_q
from engine.kinds import Functional, Oracle, Req, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, lean_q, position, render, rows

CHALLENGE_ID = "scale_steps"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ScaleSteps"
EXACT = ("py.exact.q",)
CLAUSES = ("composite_maps", "bounds_hold", "bounds_composed")


def _map(fs: FiniteStructure, name: str, source: str, target: str) -> list[int]:
    got = {s: position(fs, target, t) for s, t in rows(fs, name)}
    return [v if (v := got.get(s)) is not None else -1 for s in fs.elements(source)]


def _one(fs: FiniteStructure, name: str) -> Q | None:
    got = rows(fs, name)
    return fs.value(got[0][0]) if len(got) == 1 else None


def reading(fs: FiniteStructure) -> list[Q]:
    got = {p: fs.value(v) for p, v in rows(fs, "reads")}
    return [x if (x := got.get(p)) is not None else ZERO for p in fs.elements("point")]


def coarse(fine: list[Q], m: list[int], blocks: int) -> list[Q]:
    out = []
    for b in range(blocks):
        members = [x for x, k in zip(fine, m) if k == b]
        out.append(sum(members, ZERO) / Q(len(members)) if members else ZERO)
    return out


def error(fine: list[Q], coarser: list[Q], m: list[int]) -> Q:
    return max((abs_q(x - coarser[k]) if 0 <= k < len(coarser) else Q(10 ** 9) for x, k in zip(fine, m)), default=ZERO)


def abs_q(x: Q) -> Q:
    return -x if x.sign() < 0 else x


def scales(fs: FiniteStructure) -> tuple[list[Q], list[Q], list[Q], list[int], list[int]]:
    r0 = reading(fs)
    m1 = _map(fs, "first", "point", "first_block")
    m2 = _map(fs, "second", "first_block", "second_block")
    r1 = coarse(r0, m1, len(fs.elements("first_block")))
    r2 = coarse(r1, m2, len(fs.elements("second_block")))
    return r0, r1, r2, m1, m2


def composite_maps(fs: FiniteStructure, _o: Oracle) -> bool:
    _, _, _, m1, m2 = scales(fs)
    far = [m2[b] if 0 <= b < len(m2) else -1 for b in m1]
    return _map(fs, "near_jump", "point", "first_block") == m1 and _map(fs, "far_jump", "point", "second_block") == far


def bounds_hold(fs: FiniteStructure, _o: Oracle) -> bool:
    r0, r1, r2, m1, m2 = scales(fs)
    checks = [("first_bound", error(r0, r1, m1)), ("second_bound", error(r1, r2, m2)),
              ("near_jump_bound", error(r0, r1, _map(fs, "near_jump", "point", "first_block"))),
              ("far_jump_bound", error(r0, r2, _map(fs, "far_jump", "point", "second_block")))]
    return all((b := _one(fs, name)) is not None and b >= e for name, e in checks)


def bounds_composed(fs: FiniteStructure, _o: Oracle) -> bool:
    b1, b2 = _one(fs, "first_bound"), _one(fs, "second_bound")
    near, far = _one(fs, "near_jump_bound"), _one(fs, "far_jump_bound")
    if b1 is None or b2 is None or near is None or far is None:
        return False
    return near <= b1 and far <= b1 + b2


def describe(fs: FiniteStructure) -> dict[str, object]:
    r0, r1, r2, m1, m2 = scales(fs)
    return {"coarse": [[fmt_q(x) for x in r1], [fmt_q(x) for x in r2]],
            "errors": [fmt_q(error(r0, r1, m1)), fmt_q(error(r1, r2, m2))]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "bounds_hold")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    point, first_block = e.form("point"), e.form("first_block")
    reqs: list[Req] = [Total("reads_given", ((point, ("p",)),), ((e.form("reads"), ("p", "v")),)),
            Functional("one_read", e.form("reads"), 1)]
    for name, source in (("first", point), ("second", first_block), ("near_jump", point), ("far_jump", point)):
        reqs += [Total(f"{name}_given", ((source, ("x",)),), ((e.form(name), ("x", "y")),)),
                 Functional(f"one_{name}", e.form(name), 1)]
    reqs += [Total("step_bounds_given", (), ((e.form("first_bound"), ("a",)), (e.form("second_bound"), ("b",)))),
             Total("jumps_bounded", (), ((e.form("near_jump_bound"), ("a",)), (e.form("far_jump_bound"), ("b",))))]
    return Compiled(tuple(reqs), decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
        ("composite_maps", composite_maps), ("bounds_hold", bounds_hold), ("bounds_composed", bounds_composed))))


LEAN_DEFS = (
    "def qabs (x : QN) : QN := if QN.pos (-x) then -x else x",
    "",
    "def le (x y : QN) : Bool := !QN.pos (x - y)",
    "",
    "/-- The block averages of a reading under a map onto `n` blocks. -/",
    "def coarse (r : List QN) (m : List Nat) (n : Nat) : List QN :=",
    "  (List.range n).map fun b =>",
    "    let xs := (List.zip r m).filter (fun p => p.2 == b)",
    "    (xs.foldl (fun acc p => acc + p.1) 0) / QN.ofInt (Int.ofNat xs.length)",
    "",
    "/-- The largest distance between a reading and the coarse reading of its image. -/",
    "def err (r c : List QN) (m : List Nat) : QN :=",
    "  (List.zip r m).foldl (fun acc p => let d := qabs (p.1 - c.getD p.2 0); if le d acc then acc else d) 0",
    "",
    "def compositeMaps (m1 m2 near far : List Nat) : Bool := decide (near = m1) && decide (far = m1.map fun b => m2.getD b 0)",
    "",
    "def boundsHold (r : List QN) (m1 m2 near far : List Nat) (n1 n2 : Nat) (b1 b2 bn bf : QN) : Bool :=",
    "  let c1 := coarse r m1 n1; let c2 := coarse c1 m2 n2",
    "  le (err r c1 m1) b1 && le (err c1 c2 m2) b2 && le (err r c1 near) bn && le (err r c2 far) bf",
    "",
    "def boundsComposed (b1 b2 bn bf : QN) : Bool := le bn b1 && le bf (b1 + b2)",
    "",
)
LEAN_CALLS = {"composite_maps": "compositeMaps m1_{f} m2_{f} near_{f} far_{f}",
              "bounds_hold": "boundsHold r_{f} m1_{f} m2_{f} near_{f} far_{f} n1_{f} n2_{f} b1_{f} b2_{f} bn_{f} bf_{f}",
              "bounds_composed": "boundsComposed b1_{f} b2_{f} bn_{f} bf_{f}"}


def _nats(xs: Sequence[int]) -> str:
    assert all(x >= 0 for x in xs)
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    r0, _, _, m1, m2 = scales(fs)
    bs = [_one(fs, n) for n in ("first_bound", "second_bound", "near_jump_bound", "far_jump_bound")]
    assert all(b is not None for b in bs)
    b1, b2, bn, bf = (lean_q(b) for b in bs if b is not None)
    return [("r", "List QN", lean_list([lean_q(x) for x in r0])), ("m1", "List Nat", _nats(m1)),
            ("m2", "List Nat", _nats(m2)), ("near", "List Nat", _nats(_map(fs, "near_jump", "point", "first_block"))),
            ("far", "List Nat", _nats(_map(fs, "far_jump", "point", "second_block"))),
            ("n1", "Nat", str(len(fs.elements("first_block")))), ("n2", "Nat", str(len(fs.elements("second_block")))),
            ("b1", "QN", b1), ("b2", "QN", b2), ("bn", "QN", bn), ("bf", "QN", bf)]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `scale_steps`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
