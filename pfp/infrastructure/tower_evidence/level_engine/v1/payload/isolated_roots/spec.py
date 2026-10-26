"""A rational polynomial and a rational interval that isolates exactly one of
its roots, certified by the sign changes of its remainder chain at the two
ends, with the claimed end values evaluated exactly.

The chain: the polynomial, its derivative, then each negated remainder of
the two before it, until a remainder is zero.  Its last member is constant
exactly when the polynomial has no repeated root; the drop in sign changes
from the lower end to the upper end then counts the distinct roots inside.

The claim: coefficients (in declared order: the constant first), two ends
(lower first) and two claimed values, each carrying an exact value, and
``at(e, c)`` (the claimed value at end ``e`` is ``c``).

Relational clauses, carried by derivability over the hosted claim:
``claim_given``, ``one_claim`` and ``at_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (degree 1 to
12 with a nonzero leading coefficient, and the lower end below the upper),
``squarefree`` (the chain's last member is constant), ``ends_not_roots``
(the polynomial does not vanish at either end), ``isolating`` (the drop in
sign changes is exactly one: the refused case is an interval holding two
roots) and ``values_exact`` (each claimed value is the exact value at its
end).  The chain is a finite family: the kernel recomputes it and re-decides
the last four clauses over ExactRat.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine import lean_text as T
from engine.encoding import Encoding
from engine.exact.q import ZERO, Q, fmt_q
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, render, rows

CHALLENGE_ID = "isolated_roots"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "IsolatedRoots"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "squarefree", "ends_not_roots", "isolating", "values_exact")
LEAN_CLAUSES = CLAUSES[1:]
Poly = list[Q]


def poly(fs: FiniteStructure) -> Poly:
    return [v if (v := fs.value(c)) is not None else ZERO for c in fs.elements("coef")]


def ends(fs: FiniteStructure) -> list[Q]:
    return [v if (v := fs.value(e)) is not None else ZERO for e in fs.elements("end")]


def trim(p: Poly) -> Poly:
    p = list(p)
    while p and p[-1].is_zero():
        p.pop()
    return p


def value_at(p: Poly, x: Q) -> Q:
    out = ZERO
    for c in reversed(p):
        out = out * x + c
    return out


def remainder(num: Poly, den: Poly) -> Poly:
    num = trim(num)
    while den and len(num) >= len(den) and num:
        factor = num[-1] / den[-1]
        shift = len(num) - len(den)
        for i, c in enumerate(den):
            num[shift + i] = num[shift + i] - factor * c
        num = trim(num)
    return num


def chain(p: Poly) -> list[Poly]:
    p = trim(p)
    out = [p, trim([Q(i) * c for i, c in enumerate(p)][1:])]
    while out[-1] and len(out) <= len(p) + 1:
        out.append([-c for c in remainder(out[-2], out[-1])])
    return [q for q in out if q]


def changes(ch: list[Poly], x: Q) -> int:
    signs = [s for q in ch if (s := value_at(q, x).sign()) != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    p, e = poly(fs), ends(fs)
    return 2 <= len(p) <= 13 and not p[-1].is_zero() and len(e) == 2 and e[0] < e[1]


def squarefree(fs: FiniteStructure, _o: Oracle) -> bool:
    ch = chain(poly(fs))
    return len(ch[-1]) == 1


def ends_not_roots(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(not value_at(poly(fs), x).is_zero() for x in ends(fs))


def isolating(fs: FiniteStructure, _o: Oracle) -> bool:
    ch, e = chain(poly(fs)), ends(fs)
    return len(e) == 2 and changes(ch, e[0]) - changes(ch, e[1]) == 1


def claimed(fs: FiniteStructure) -> list[Q | None]:
    got = {e: fs.value(c) for e, c in rows(fs, "at")}
    return [got.get(e) for e in fs.elements("end")]


def values_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return claimed(fs) == [value_at(poly(fs), x) for x in ends(fs)]


def describe(fs: FiniteStructure) -> dict[str, object]:
    ch, e = chain(poly(fs)), ends(fs)
    return {"chain_length": len(ch), "changes": [changes(ch, x) for x in e],
            "end_values": [fmt_q(value_at(poly(fs), x)) for x in e]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "isolating")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    end, cl, at = e.form("end"), e.form("claimed"), e.form("at")
    return Compiled(
        (
            Total("claim_given", ((end, ("e",)),), ((at, ("e", "c")),)),
            Functional("one_claim", at, 1),
            Closure("at_typed", ((at, ("e", "c")),), ((end, ("e",)), (cl, ("c",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("squarefree", squarefree), ("ends_not_roots", ends_not_roots),
            ("isolating", isolating), ("values_exact", values_exact))),
    )


LEAN_DEFS = (
    "abbrev P := List QN",
    "",
    "def evalP (p : P) (x : QN) : QN := p.foldr (fun c acc => c + x * acc) 0",
    "",
    "/-- Drop zero coefficients from the top. -/",
    "def trim (p : P) : P := (p.reverse.dropWhile fun c => decide (c = 0)).reverse",
    "",
    "def deriv (p : P) : P := trim (((List.range p.length).map fun (i : Nat) => QN.ofInt (Int.ofNat i) * p.getD i 0).drop 1)",
    "",
    "/-- One step of long division: cancel the top coefficient of `num`. -/",
    "def cancelTop (num den : P) : P :=",
    "  let f := num.getLastD 0 * QN.inv (den.getLastD 1)",
    "  let s := num.length - den.length",
    "  trim ((List.range num.length).map fun i => num.getD i 0 - (if s <= i then f * den.getD (i - s) 0 else 0))",
    "",
    "def remF (den : P) : Nat -> P -> P",
    "  | 0, num => num",
    "  | fuel + 1, num => if den.isEmpty || num.length < den.length || num.isEmpty then num",
    "      else remF den fuel (cancelTop num den)",
    "",
    "/-- The chain: `p`, `p'`, then negated remainders, with fuel bounding its length. -/",
    "def chainF : Nat -> P -> P -> List P",
    "  | 0, a, b => [a, b]",
    "  | fuel + 1, a, b => if b.isEmpty then [a] else",
    "      a :: chainF fuel b ((remF b (a.length + 1) a).map fun c => -c)",
    "",
    "def chain (p : P) : List P := (chainF (p.length + 2) (trim p) (deriv p)).filter fun q => !q.isEmpty",
    "",
    "def sgn (x : QN) : Int := if 0 < x then 1 else if x = 0 then 0 else -1",
    "",
    "def changes (ch : List P) (x : QN) : Nat :=",
    "  let s := (ch.map fun q => sgn (evalP q x)).filter fun v => v != 0",
    "  ((List.range (s.length - 1)).filter fun i => s.getD i 0 != s.getD (i + 1) 0).length",
    "",
    "def squarefree (p : P) : Bool := ((chain p).getLastD []).length == 1",
    "",
    "def endsNotRoots (p : P) (a b : QN) : Bool := !decide (evalP p a = 0) && !decide (evalP p b = 0)",
    "",
    "def isolating (p : P) (a b : QN) : Bool := changes (chain p) a == changes (chain p) b + 1",
    "",
    "def valuesExact (p : P) (a b va vb : QN) : Bool := decide (evalP p a = va) && decide (evalP p b = vb)",
    "",
)
LEAN_CALLS = {"squarefree": "squarefree poly_{f}", "ends_not_roots": "endsNotRoots poly_{f} lo_{f} hi_{f}",
              "isolating": "isolating poly_{f} lo_{f} hi_{f}",
              "values_exact": "valuesExact poly_{f} lo_{f} hi_{f} atLo_{f} atHi_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    e, c = ends(fs), claimed(fs)
    assert len(e) == 2 and c[0] is not None and c[1] is not None
    return [("poly", "P", T.row(poly(fs))), ("lo", "QN", T.q(e[0])), ("hi", "QN", T.q(e[1])),
            ("atLo", "QN", T.q(c[0])), ("atHi", "QN", T.q(c[1]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `isolated_roots`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
