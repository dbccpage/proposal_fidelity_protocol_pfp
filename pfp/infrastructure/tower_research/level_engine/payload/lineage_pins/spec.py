# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Every derived value points to immutable inputs: each derived record names
its inputs, each a source or a record listed earlier, together with the
digest the input had when it was used; its value is its operation (sum or
product) of its inputs' values; every record's digest hashes its content;
and every pinned digest is still its input's digest.

A record's content is the canonical JSON object ``{"id": name, "value":
value}`` (a record is named ``r<k>`` by its place; the value is written as
a canonical rational), and its digest is the SHA-256 of that text: a
declared convention.

The claim: records (sources and derived records, in declared order, each
carrying its value), seals and pins (each carrying a digest, an exact
32-byte value); ``source(r)``, ``sums(r)``, ``multiplies(r)``, ``sealed(r,
s)`` (record ``r``'s digest is seal ``s``) and ``reads(r, i, p)`` (derived
record ``r`` reads input ``i``, pinned at digest ``p``).

Relational clauses, carried by derivability over the hosted claim:
``inputs_are_records`` (the refused case: an input that is no record, a
missing source), ``sealed_given``, ``one_seal``, ``derived_read``,
``sources_read_nothing`` and ``one_operation``.

Decoded clauses, decided outside the grammar: ``inputs_earlier`` (an input
is a source or a record listed before its reader), ``values_exact``,
``digests_exact`` (each record's seal is the digest of its content) and
``pins_hold`` (each pinned digest is its input's seal).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.digest import digest_of
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, fmt_q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import position, rows

CHALLENGE_ID = "lineage_pins"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("inputs_earlier", "values_exact", "digests_exact", "pins_hold")


def _p(fs: FiniteStructure, e: int) -> int:
    k = position(fs, "record", e)
    return -1 if k is None else k


def inputs_earlier(fs: FiniteStructure, _o: Oracle) -> bool:
    sources = {r for (r,) in rows(fs, "source")}
    return all(i in sources or 0 <= _p(fs, i) < _p(fs, r) for r, i, _ in rows(fs, "reads"))


def values_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    sums = {r for (r,) in rows(fs, "sums")}
    prods = {r for (r,) in rows(fs, "multiplies")}
    for r in sums | prods:
        vals = [fs.value(i) for rr, i, _ in rows(fs, "reads") if rr == r]
        if any(v is None for v in vals) or fs.value(r) is None:
            return False
        acc = ZERO if r in sums else ONE
        for v in vals:
            assert v is not None
            acc = acc + v if r in sums else acc * v
        if fs.value(r) != acc:
            return False
    return True


def content_digest(fs: FiniteStructure, r: int) -> bytes | None:
    v = fs.value(r)
    return None if v is None else digest_of({"id": f"r{_p(fs, r)}", "value": fmt_q(v)})


def digests_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    seal = {r: s for r, s in rows(fs, "sealed")}
    return all(r in seal and fs.digest(seal[r]) == content_digest(fs, r) for r in fs.elements("record"))


def pins_hold(fs: FiniteStructure, _o: Oracle) -> bool:
    seal = {r: s for r, s in rows(fs, "sealed")}
    return all(i in seal and fs.digest(p) == fs.digest(seal[i]) for _, i, p in rows(fs, "reads"))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"digests": [None if (d := content_digest(fs, r)) is None else "sha256:" + d.hex()
                        for r in fs.elements("record")]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    record, seal, pin = e.form("record"), e.form("seal"), e.form("pin")
    source, sums, mult, sealed, reads = (e.form("source"), e.form("sums"), e.form("multiplies"), e.form("sealed"),
                                         e.form("reads"))
    return Compiled(
        (
            Closure("inputs_are_records", ((reads, ("r", "i", "p")),), ((record, ("i",)), (pin, ("p",)))),
            Total("sealed_given", ((record, ("r",)),), ((sealed, ("r", "s")),)),
            Functional("one_seal", sealed, 1),
            Total("derived_read", ((sums, ("r",)),), ((reads, ("r", "i", "p")),)),
            Forbid("sources_read_nothing", ((source, ("r",)), (reads, ("r", "i", "p")))),
            Forbid("one_operation", ((sums, ("r",)), (mult, ("r",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("inputs_earlier", inputs_earlier), ("values_exact", values_exact), ("digests_exact", digests_exact),
            ("pins_hold", pins_hold))),
    )
