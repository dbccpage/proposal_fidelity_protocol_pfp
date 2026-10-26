# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Measured comparison counts of two pinned procedures: each run names a
procedure and reads an input; its stated count must be the number of
comparisons the procedure makes on that input, its log digest the digest of
the procedure's comparison log, the environment must name this
implementation and its counter, and a ratio between two runs must rest on
the measured basis and be the ratio of their recounted counts on one input.

The procedures are pinned here, supplied and restated exactly: a stepwise
insertion order and a halving merge order over lists of naturals, each
counting element comparisons and logging the index pair of every
comparison.  A log's digest is the SHA-256 of its canonical JSON (a list of
index pairs).  Nothing is timed: the counter is exact, and the environment
is this implementation, named by the pinned tag ``TAG`` and the counter
name ``COUNTER``.

The claim: one tag and one counter (each carrying a text), procedures (each
carrying its pinned name as a text), runs (each carrying its stated count),
logs (each carrying a digest, an exact 32-byte value), entries (each
carrying a natural: the pool of input entries, in declared order) and one
ratio (carrying the stated ratio); ``performs(r, p)``, ``logged(r, l)``,
``reads(r, x)`` (a run's input is the entries it reads, in declared order),
``baseline(q, r)``, ``candidate(q, r)``, and the basis: ``measured(q)`` or
``estimated(q)``.

Relational clauses, carried by derivability over the hosted claim:
``procedure_given``, ``one_procedure``, ``log_given``, ``one_log``,
``reads_entries``, ``ends_given``, ``one_baseline``, ``one_candidate``,
``basis_measured`` (the refused case: a ratio on the estimated basis) and
``one_basis``.

Decoded clauses, decided outside the grammar, over the reruns:
``well_formed``, ``environment_pinned``, ``counts_exact``, ``logs_exact``
and ``ratio_exact``.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.digest import digest_of
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..lists import nat
from ..shared import rows

CHALLENGE_ID = "counted_runs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("well_formed", "environment_pinned", "counts_exact", "logs_exact", "ratio_exact")
TAG = "procedures-v1"
COUNTER = "comparisons"
MAX_INPUT = 64
Log = list[list[int]]


def insertion_sort(items: list[int]) -> tuple[list[int], Log]:
    items, log = list(items), Log()
    for i in range(1, len(items)):
        j = i
        while j > 0:
            log.append([j - 1, j])
            if items[j - 1] <= items[j]:
                break
            items[j - 1], items[j] = items[j], items[j - 1]
            j -= 1
    return items, log


def merge_sort(items: list[int]) -> tuple[list[int], Log]:
    log: Log = []

    def order(low: int, high: int, values: list[int]) -> list[int]:
        if high - low <= 1:
            return values[low:high]
        middle = (low + high) // 2
        left, right = order(low, middle, values), order(middle, high, values)
        out: list[int] = []
        i, j = 0, 0
        while i < len(left) and j < len(right):
            log.append([low + i, middle + j])
            if left[i] <= right[j]:
                out.append(left[i])
                i += 1
            else:
                out.append(right[j])
                j += 1
        return out + left[i:] + right[j:]

    return order(0, len(items), list(items)), log


PROCEDURES: dict[str, Callable[[list[int]], tuple[list[int], Log]]] = {
    "insertion_sort": insertion_sort, "merge_sort": merge_sort}


def _one(rel: list[tuple[int, ...]], a: int) -> int | None:
    got = [b for x, b in rel if x == a]
    return got[0] if len(got) == 1 else None


def procedure_of(fs: FiniteStructure, r: int) -> str | None:
    p = _one(rows(fs, "performs"), r)
    return None if p is None else fs.text(p)


def input_of(fs: FiniteStructure, r: int) -> list[int]:
    mine = {x for rr, x in rows(fs, "reads") if rr == r}
    return [nat(fs, x) for x in fs.elements("entry") if x in mine]


def rerun(fs: FiniteStructure, r: int) -> tuple[int, bytes] | None:
    """The run's recount and the digest of its recomputed log."""
    name, items = procedure_of(fs, r), input_of(fs, r)
    if name not in PROCEDURES or -1 in items:
        return None
    _, log = PROCEDURES[name](items)
    return len(log), digest_of(log)


def ends(fs: FiniteStructure) -> tuple[int, int, int] | None:
    qs = fs.elements("ratio")
    if len(qs) != 1:
        return None
    b, c = _one(rows(fs, "baseline"), qs[0]), _one(rows(fs, "candidate"), qs[0])
    return None if b is None or c is None else (qs[0], b, c)


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    tags, counters, e = fs.elements("tag"), fs.elements("counter"), ends(fs)
    return (len(tags) == 1 and len(counters) == 1 and fs.text(tags[0]) is not None
            and fs.text(counters[0]) is not None
            and all(fs.text(p) in PROCEDURES for p in fs.elements("procedure"))
            and all(nat(fs, r) >= 0 and len(input_of(fs, r)) <= MAX_INPUT for r in fs.elements("run"))
            and all(fs.digest(lg) is not None for lg in fs.elements("log"))
            and all(nat(fs, x) >= 0 for x in fs.elements("entry"))
            and e is not None and e[1] != e[2] and fs.value(e[0]) is not None)


def environment_pinned(fs: FiniteStructure, _o: Oracle) -> bool:
    tags, counters = fs.elements("tag"), fs.elements("counter")
    return [fs.text(t) for t in tags] == [TAG] and [fs.text(c) for c in counters] == [COUNTER]


def counts_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    for r in fs.elements("run"):
        got = rerun(fs, r)
        if got is None or nat(fs, r) != got[0]:
            return False
    return True


def logs_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    for r in fs.elements("run"):
        got, lg = rerun(fs, r), _one(rows(fs, "logged"), r)
        if got is None or lg is None or fs.digest(lg) != got[1]:
            return False
    return True


def ratio_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    e = ends(fs)
    if e is None:
        return False
    q, b, c = e
    got_b, got_c = rerun(fs, b), rerun(fs, c)
    return (got_b is not None and got_c is not None and input_of(fs, b) == input_of(fs, c) and got_c[0] > 0
            and fs.value(q) == Q.of(got_b[0], got_c[0]))


def describe(fs: FiniteStructure) -> dict[str, object]:
    got = [rerun(fs, r) for r in fs.elements("run")]
    return {"counts": [None if g is None else g[0] for g in got],
            "logs": [None if g is None else "sha256:" + g[1].hex() for g in got]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    run, log, entry, ratio = e.form("run"), e.form("log"), e.form("entry"), e.form("ratio")
    performs, logged, reads = e.form("performs"), e.form("logged"), e.form("reads")
    baseline, candidate = e.form("baseline"), e.form("candidate")
    measured, estimated = e.form("measured"), e.form("estimated")
    return Compiled(
        (
            Total("procedure_given", ((run, ("r",)),), ((performs, ("r", "p")),)),
            Functional("one_procedure", performs, 1),
            Total("log_given", ((run, ("r",)),), ((logged, ("r", "l")),)),
            Functional("one_log", logged, 1),
            Closure("reads_entries", ((reads, ("r", "x")),), ((run, ("r",)), (entry, ("x",)))),
            Total("ends_given", ((ratio, ("q",)),), ((baseline, ("q", "b")), (candidate, ("q", "c")))),
            Functional("one_baseline", baseline, 1),
            Functional("one_candidate", candidate, 1),
            Closure("basis_measured", ((ratio, ("q",)),), ((measured, ("q",)),)),
            Forbid("one_basis", ((measured, ("q",)), (estimated, ("q",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("environment_pinned", environment_pinned),
            ("counts_exact", counts_exact), ("logs_exact", logs_exact), ("ratio_exact", ratio_exact))),
    )
