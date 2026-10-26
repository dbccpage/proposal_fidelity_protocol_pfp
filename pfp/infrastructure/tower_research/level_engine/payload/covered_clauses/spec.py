# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A record of a source text's coverage, for audit: every clause the declared
splitter finds in the source is recorded once by its span, each record's
digest is the digest of its span's text, and each record is either linked
to a formal object or carries a stated exception (``OPEN`` is one), never
both and never neither.  A clause holding a quantifier word is never
dropped: it stays in the record, if only as an open exception.

Declared conventions, supplied and classified in the restatement:

- the splitter: a clause is a maximal run of the source between the
  separators ``;`` and ``.``, each followed by white space or the end of
  the text, with white space trimmed at both ends; an empty run is no
  clause;
- the quantifier words: ``all``, ``any``, ``each``, ``every``, ``exists``,
  ``no``, ``none``, ``only``, ``some``; a clause is quantified when one of
  them is a whole word of it (a maximal run of letters), in any case;
- a span ``[start, end)`` is read in the source's characters; its digest is
  the SHA-256 of its text's bytes.

This is not language understanding: a clause the splitter does not separate
is one clause, and a quantifier word outside the list is not seen.

The claim: one source (a text), records (each carrying its digest, in
declared order), offsets (each carrying a natural), links (each carrying a
formal object's name, a text) and exceptions (each carrying a stated
exception, a text); ``begins(r, o)``, ``ends(r, o)`` and ``tagged(r, t)``
(the record's link or exception).

Relational clauses, carried by derivability over the hosted claim:
``source_given``, ``one_source``, ``begins_given``, ``one_begin``,
``ends_given``, ``one_end``, ``begins_typed``, ``ends_typed``,
``accounted`` (a record with neither link nor exception), ``one_account``
(a record with both), ``tag_not_source``, ``tag_not_record`` and
``tag_not_offset`` (a tag is a link or an exception).

Decoded clauses, decided outside the grammar: ``spans_are_clauses`` (every
recorded span is a clause of the splitter, recorded once),
``span_digests``, ``quantified_recorded`` (the refused case: a quantified
clause missing from the record) and ``clauses_recorded`` (every clause
without a quantifier is recorded too).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.digest import sha256
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..lists import nat
from ..shared import rows

CHALLENGE_ID = "covered_clauses"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("spans_are_clauses", "span_digests", "quantified_recorded", "clauses_recorded")

SEPARATORS = ";."
QUANTIFIER_WORDS = ("all", "any", "each", "every", "exists", "no", "none", "only", "some")


def split(text: str) -> list[tuple[int, int]]:
    """The declared splitter: the trimmed clauses' spans, in order."""
    runs, start = [], 0
    for i, ch in enumerate(text):
        if ch in SEPARATORS and (i + 1 == len(text) or text[i + 1].isspace()):
            runs.append((start, i))
            start = i + 1
    runs.append((start, len(text)))
    out = []
    for lo, hi in runs:
        while lo < hi and text[lo].isspace():
            lo += 1
        while hi > lo and text[hi - 1].isspace():
            hi -= 1
        if lo < hi:
            out.append((lo, hi))
    return out


def quantified(clause: str) -> bool:
    words, cur = [], ""
    for ch in clause + " ":
        if ch.isascii() and ch.isalpha():
            cur += ch
        else:
            if cur:
                words.append(cur.lower())
            cur = ""
    return any(w in QUANTIFIER_WORDS for w in words)


def source(fs: FiniteStructure) -> str:
    got = [fs.text(s) for s in fs.elements("source")]
    return got[0] if len(got) == 1 and got[0] is not None else ""


def spans(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    """(record, start, end) in declared order."""
    begin = {r: o for r, o in rows(fs, "begins")}
    end = {r: o for r, o in rows(fs, "ends")}
    return [(r, nat(fs, begin[r]) if r in begin else -1, nat(fs, end[r]) if r in end else -1)
            for r in fs.elements("record")]


def spans_are_clauses(fs: FiniteStructure, _o: Oracle) -> bool:
    got = [(lo, hi) for _, lo, hi in spans(fs)]
    return set(got) <= set(split(source(fs))) and len(set(got)) == len(got)


def span_digests(fs: FiniteStructure, _o: Oracle) -> bool:
    text = source(fs)
    return all(0 <= lo <= hi <= len(text) and fs.digest(r) == sha256(text[lo:hi].encode("ascii"))
               for r, lo, hi in spans(fs))


def quantified_recorded(fs: FiniteStructure, _o: Oracle) -> bool:
    text = source(fs)
    got = {(lo, hi) for _, lo, hi in spans(fs)}
    return all(c in got for c in split(text) if quantified(text[c[0]:c[1]]))


def clauses_recorded(fs: FiniteStructure, _o: Oracle) -> bool:
    text = source(fs)
    got = {(lo, hi) for _, lo, hi in spans(fs)}
    return all(c in got for c in split(text) if not quantified(text[c[0]:c[1]]))


def describe(fs: FiniteStructure) -> dict[str, object]:
    text = source(fs)
    return {"clauses": [[lo, hi, quantified(text[lo:hi])] for lo, hi in split(text)]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    src, record, offset = e.form("source"), e.form("record"), e.form("offset")
    begins, ends, tagged = e.form("begins"), e.form("ends"), e.form("tagged")
    return Compiled(
        (
            Total("source_given", (), ((src, ("s",)),)),
            Functional("one_source", src, 0),
            Total("begins_given", ((record, ("r",)),), ((begins, ("r", "o")),)),
            Functional("one_begin", begins, 1),
            Total("ends_given", ((record, ("r",)),), ((ends, ("r", "o")),)),
            Functional("one_end", ends, 1),
            Closure("begins_typed", ((begins, ("r", "o")),), ((record, ("r",)), (offset, ("o",)))),
            Closure("ends_typed", ((ends, ("r", "o")),), ((record, ("r",)), (offset, ("o",)))),
            Total("accounted", ((record, ("r",)),), ((tagged, ("r", "t")),)),
            Functional("one_account", tagged, 1),
            Forbid("tag_not_source", ((tagged, ("r", "t")), (src, ("t",)))),
            Forbid("tag_not_record", ((tagged, ("r", "t")), (record, ("t",)))),
            Forbid("tag_not_offset", ((tagged, ("r", "t")), (offset, ("t",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("spans_are_clauses", spans_are_clauses), ("span_digests", span_digests),
            ("quantified_recorded", quantified_recorded), ("clauses_recorded", clauses_recorded))),
    )
