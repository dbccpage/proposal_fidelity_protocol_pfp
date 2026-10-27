# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Words of length two over a hosted table of allowed steps are grouped into
rings: each ring holds exactly the turns of its lead, the lead is the least
of them, and the ring's declared span is the least number of turns that
returns the lead.

A word is read cyclically: its two steps are first-to-second and
second-to-first, and turning it once exchanges its two letters.  Letters are
ordered as declared, words by their letters.

Relational clauses, carried by derivability over the hosted claim:
``steps_typed``, ``first_given``, ``one_first``, ``second_given``,
``one_second``, ``spelled`` (every pair of letters spells a word),
``lies_typed``, ``one_ring``, ``steps_allowed`` (every word in a ring takes
only allowed steps, the wrap-around included), ``turn_closed`` (a ring holds
the turn of each of its words), ``lead_given``, ``one_lead``, ``lead_lies``,
``covered`` (every word whose steps are allowed lies in a ring),
``span_given`` and ``one_span``.

Decoded clauses, decided over the hosted structure outside the grammar:
``one_class`` (a ring holds nothing but the turns of its lead),
``span_least`` (the declared span, an exact natural, is the least number of
turns that returns the lead: a constant word returns after one) and
``lead_least`` (the lead is the least of its turns).  Their Lean
certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import Q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "cycle_words"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)


def _rows(fs: FiniteStructure, name: str) -> list[tuple[int, ...]]:
    return [a for n, a in fs.tuples if n == name]


def spelling(fs: FiniteStructure) -> dict[int, tuple[int, int]]:
    """Each word's letters as positions in the declared order of letters;
    a word with a missing or repeated letter is left out."""
    letters = fs.elements("letter")
    firsts: dict[int, list[int]] = {}
    seconds: dict[int, list[int]] = {}
    for w, a in _rows(fs, "first"):
        firsts.setdefault(w, []).append(a)
    for w, a in _rows(fs, "second"):
        seconds.setdefault(w, []).append(a)
    out = {}
    for w in fs.elements("word"):
        f, s = firsts.get(w, []), seconds.get(w, [])
        if len(f) == 1 and len(s) == 1 and f[0] in letters and s[0] in letters:
            out[w] = (letters.index(f[0]), letters.index(s[0]))
    return out


def turns(word: tuple[int, int]) -> set[tuple[int, int]]:
    return {word, (word[1], word[0])}


def least_span(word: tuple[int, int]) -> int:
    """The least number of turns that returns the word (1 or 2 at length two)."""
    return 1 if word[0] == word[1] else 2


@dataclass(frozen=True)
class Ring:
    words: frozenset[tuple[int, int]]
    lead: tuple[int, int] | None
    span: Q | None


def rings(fs: FiniteStructure) -> dict[int, Ring]:
    """Per ring: its words spelled, its lead spelled, its declared span."""
    sp = spelling(fs)
    out: dict[int, Ring] = {}
    for r in fs.elements("ring"):
        words = frozenset(sp[w] for w, rr in _rows(fs, "lies_in") if rr == r and w in sp)
        leads = [sp[w] for rr, w in _rows(fs, "lead") if rr == r and w in sp]
        spans = [fs.value(c) for rr, c in _rows(fs, "span") if rr == r]
        out[r] = Ring(words, leads[0] if len(leads) == 1 else None, spans[0] if len(spans) == 1 else None)
    return out


def one_class(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(g.lead is not None and g.words == turns(g.lead) for g in rings(fs).values())


def span_least(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(g.lead is not None and g.span is not None and g.span == Q(least_span(g.lead))
               for g in rings(fs).values())


def lead_least(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(g.lead is not None and g.lead == min(turns(g.lead)) for g in rings(fs).values())


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"rings": {str(r): {"least_span": None if g.lead is None else least_span(g.lead),
                               "words": sorted("".join(map(str, w)) for w in g.words)}
                      for r, g in rings(fs).items()}}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    letter, word, ring = e.form("letter"), e.form("word"), e.form("ring")
    step, first, second = e.form("step"), e.form("first"), e.form("second")
    lies_in, lead, span = e.form("lies_in"), e.form("lead"), e.form("span")
    spelled_w = ((first, ("w", "a")), (second, ("w", "b")))
    return Compiled(
        (
            Closure("steps_typed", ((step, ("a", "b")),), ((letter, ("a",)), (letter, ("b",)))),
            Total("first_given", ((word, ("w",)),), ((first, ("w", "a")),)),
            Functional("one_first", first, 1),
            Total("second_given", ((word, ("w",)),), ((second, ("w", "a")),)),
            Functional("one_second", second, 1),
            Total("spelled", ((letter, ("a",)), (letter, ("b",))), spelled_w),
            Closure("lies_typed", ((lies_in, ("w", "r")),), ((word, ("w",)), (ring, ("r",)))),
            Functional("one_ring", lies_in, 1),
            Closure("steps_allowed", ((lies_in, ("w", "r")),) + spelled_w,
                    ((step, ("a", "b")), (step, ("b", "a")))),
            Closure("turn_closed", ((lies_in, ("w", "r")),) + spelled_w + ((first, ("v", "b")), (second, ("v", "a"))),
                    ((lies_in, ("v", "r")),)),
            Total("lead_given", ((ring, ("r",)),), ((lead, ("r", "w")),)),
            Functional("one_lead", lead, 1),
            Closure("lead_lies", ((lead, ("r", "w")),), ((lies_in, ("w", "r")),)),
            Total("covered", ((word, ("w",)),) + spelled_w + ((step, ("a", "b")), (step, ("b", "a"))),
                  ((lies_in, ("w", "r")),)),
            Total("span_given", ((ring, ("r",)),), ((span, ("r", "c")),)),
            Functional("one_span", span, 1),
        ),
        decoded=(
            DecodedClause("one_class", one_class, EXACT),
            DecodedClause("span_least", span_least, EXACT),
            DecodedClause("lead_least", lead_least, EXACT),
        ),
    )


LEAN_MODULE = "CycleWords"
CLAUSES = ("one_class", "span_least", "lead_least")
LEAN_DEFS = (
    "/-- A word of length two, as the positions of its two letters. -/",
    "abbrev Word := Prod Nat Nat",
    "",
    "/-- Turning a word once exchanges its letters. -/",
    "def turn (w : Word) : Word := (w.2, w.1)",
    "",
    "/-- The turns of a word. -/",
    "def turns (w : Word) : List Word := if w.1 = w.2 then [w] else [w, turn w]",
    "",
    "/-- A ring: its words, its lead and its declared span, when given. -/",
    "structure Ring where",
    "  words : List Word",
    "  lead : Option Word",
    "  span : Option Nat",
    "",
    "def sameSet (a b : List Word) : Bool := a.all (fun x => b.contains x) && b.all (fun x => a.contains x)",
    "",
    "/-- Each ring holds exactly the turns of its lead. -/",
    "def oneClass (rs : List Ring) : Bool :=",
    "  rs.all fun r => match r.lead with",
    "    | some l => sameSet r.words (turns l)",
    "    | none => false",
    "",
    "/-- The least number of turns that returns a word of length two. -/",
    "def leastSpan (w : Word) : Nat := if w.1 = w.2 then 1 else 2",
    "",
    "/-- Each ring's declared span is the least span of its lead. -/",
    "def spanLeast (rs : List Ring) : Bool :=",
    "  rs.all fun r => match r.lead, r.span with",
    "    | some l, some s => s == leastSpan l",
    "    | _, _ => false",
    "",
    "def lexLe (a b : Word) : Bool := a.1 < b.1 || (a.1 == b.1 && a.2 <= b.2)",
    "",
    "/-- Each ring's lead is the least of its turns. -/",
    "def leadLeast (rs : List Ring) : Bool :=",
    "  rs.all fun r => match r.lead with",
    "    | some l => lexLe l (turn l)",
    "    | none => false",
    "",
)
LEAN_CALLS = {"one_class": "oneClass", "span_least": "spanLeast", "lead_least": "leadLeast"}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    """(declaration, fixture, clause) for every fixture whose decoded clauses
    were evaluated."""
    out = []
    for v in verdicts:
        if dict(v.decoded).get("one_class") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def _lean_ring(g: Ring) -> str:
    words = ", ".join(f"({a}, {b})" for a, b in sorted(g.words))
    lead = "none" if g.lead is None else f"some ({g.lead[0]}, {g.lead[1]})"
    span = "none" if g.span is None or g.span.den != 1 or g.span.num < 0 else f"some {g.span.num}"
    return f"{{ words := [{words}], lead := {lead}, span := {span} }}"


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One list of rings per evaluated fixture; the kernel re-decides each
    decoded clause."""
    from operations.use_cases.level_engine.research_engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The decoded clauses of `cycle_words`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        rs = [g for _, g in sorted(rings(by[fid].structure).items())]
        lines += [f"def rings_{fid} : List Ring :=", "  [" + ",\n   ".join(_lean_ring(g) for g in rs) + "]", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause]} rings_{fid} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
