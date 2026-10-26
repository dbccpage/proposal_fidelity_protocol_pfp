"""A map from the instances of one question to the instances of another that
must keep every answer, up to a declared bound; offered counts are never a
map.

The questions are "is a multiple of the modulus", for a declared source
modulus and target modulus (two or three).  The claim: numbers (values that
are naturals), ``instance(x)`` (the source instances, which must be exactly
``0`` to the bound), ``sends(x, y)`` (the map), ``source_mod(m)``,
``target_mod(m)`` and ``offered(v)`` (a count offered in support).

Relational clauses, carried by derivability over the hosted claim:
``map_given`` (every source instance has an image: with no map there is
nothing to check), ``one_image``, ``map_typed``, ``no_surrogate`` (no
count is offered: counts, keys and labels are never evidence of a map),
``source_given``, ``one_source``, ``target_given`` and ``one_target``.

Decoded clauses, decided outside the grammar: ``moduli_declared`` (both
moduli are two or three), ``instances_counted`` (the instances are exactly
``0`` to their largest) and ``answers_kept`` (each instance and its image
get the same answer).  A pass says only that the map keeps the answers up
to the bound; nothing is claimed about how hard either question is.  Their
Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, render, rows

CHALLENGE_ID = "answer_keeping"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "AnswerKeeping"
EXACT = ("py.exact.q",)
CLAUSES = ("moduli_declared", "instances_counted", "answers_kept")
MODULI = (2, 3)


def _nat(fs: FiniteStructure, e: int) -> int | None:
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 and v.num >= 0 else None


def moduli(fs: FiniteStructure) -> tuple[int | None, int | None]:
    s, t = rows(fs, "source_mod"), rows(fs, "target_mod")
    return (_nat(fs, s[0][0]) if len(s) == 1 else None, _nat(fs, t[0][0]) if len(t) == 1 else None)


def instances(fs: FiniteStructure) -> list[int | None]:
    return sorted((_nat(fs, x) for (x,) in rows(fs, "instance")), key=lambda n: -1 if n is None else n)


def mapped(fs: FiniteStructure) -> list[tuple[int | None, int | None]]:
    return sorted(((_nat(fs, x), _nat(fs, y)) for x, y in rows(fs, "sends")), key=str)


def moduli_declared(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(m in MODULI for m in moduli(fs))


def instances_counted(fs: FiniteStructure, _o: Oracle) -> bool:
    xs = instances(fs)
    return xs == list(range(len(xs))) and len(xs) <= 10001


def answers_kept(fs: FiniteStructure, _o: Oracle) -> bool:
    sm, tm = moduli(fs)
    if sm is None or tm is None or sm == 0 or tm == 0:
        return False
    return all(x is not None and y is not None and (y % tm == 0) == (x % sm == 0) for x, y in mapped(fs))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"moduli": list(moduli(fs)), "map": [list(p) for p in mapped(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "answers_kept")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    num, instance, sends = e.form("num"), e.form("instance"), e.form("sends")
    source, target, offered = e.form("source_mod"), e.form("target_mod"), e.form("offered")
    return Compiled(
        (
            Total("map_given", ((instance, ("x",)),), ((sends, ("x", "y")),)),
            Functional("one_image", sends, 1),
            Closure("map_typed", ((sends, ("x", "y")),), ((instance, ("x",)), (num, ("y",)))),
            Forbid("no_surrogate", ((offered, ("v",)),)),
            Total("source_given", (), ((source, ("m",)),)),
            Functional("one_source", source, 0),
            Total("target_given", (), ((target, ("m",)),)),
            Functional("one_target", target, 0),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("moduli_declared", moduli_declared), ("instances_counted", instances_counted),
            ("answers_kept", answers_kept))),
    )


LEAN_DEFS = (
    "/-- Both moduli are two or three. -/",
    "def moduliDeclared (sm tm : Nat) : Bool := (sm == 2 || sm == 3) && (tm == 2 || tm == 3)",
    "",
    "/-- The instances are exactly zero to their largest. -/",
    "def instancesCounted (xs : List Nat) : Bool := decide (xs = List.range xs.length)",
    "",
    "/-- Each instance and its image get the same answer. -/",
    "def answersKept (sm tm : Nat) (m : List (Prod Nat Nat)) : Bool :=",
    "  m.all fun p => (p.2 % tm == 0) == (p.1 % sm == 0)",
    "",
)
LEAN_CALLS = {"moduli_declared": "moduliDeclared sm_{f} tm_{f}", "instances_counted": "instancesCounted insts_{f}",
              "answers_kept": "answersKept sm_{f} tm_{f} map_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    sm, tm = moduli(fs)
    xs, m = instances(fs), mapped(fs)
    assert sm is not None and tm is not None and None not in xs and all(None not in p for p in m)
    return [("sm", "Nat", str(sm)), ("tm", "Nat", str(tm)), ("insts", "List Nat", lean_list([str(x) for x in xs])),
            ("map", "List (Prod Nat Nat)", lean_list([f"({x}, {y})" for x, y in m]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `answer_keeping`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
