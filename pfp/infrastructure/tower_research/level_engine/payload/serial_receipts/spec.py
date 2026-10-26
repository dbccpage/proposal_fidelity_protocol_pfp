# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A schedule of reads, writes, commits and aborts, replayed: no operation
touches a key whose last write belongs to another transaction still open,
the conflict graph over the committed transactions is acyclic, and the
receipts list the committed transactions once each in an order every
conflict respects, each bound to the digests of the states before and after
it.

The claim: transactions, keys, tokens, operations (in declared order: the
schedule), receipts (in declared order) and stamps, each stamp carrying a
digest (an exact 32-byte value); ``base(k, v)`` (the base state holds token
``v`` at key ``k``), ``acts(o, t)`` (operation ``o`` belongs to transaction
``t``), ``reads(o, k)``, ``writes(o, k, v)``, ``commits(o)``, ``aborts(o)``,
``receipt_for(r, t)``, ``parent_stamp(r, s)`` and ``state_stamp(r, s)``.

A state is written as the canonical JSON object from key names to token
names (``k<i>`` and ``v<i>`` by position; sorted keys, no white space,
ASCII), and its digest is SHA-256 of that text: a declared convention.

Relational clauses, carried by derivability over the hosted claim:
``acts_given``, ``one_txn``, ``receipt_given``, ``one_receipt_txn``,
``parent_given``, ``one_parent``, ``state_given``, ``one_state`` and
``one_base``.

Decoded clauses, decided outside the grammar: ``well_formed`` (each
operation one action; nothing of a transaction after its commit or abort;
every stamp a digest), ``strict_writes`` (no operation touches a key last
written by another transaction that has neither committed nor aborted: the
refused case), ``conflict_acyclic``, ``serial_order`` (the receipts are the
committed transactions, once each, in an order every conflict edge
respects), ``parents_exact`` and ``states_exact`` (each receipt's stamps are
the digests of the states before and after its transaction's writes, applied
along the receipts' order).  Digests stay computed.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.digest import digest_of
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import position, rows

CHALLENGE_ID = "serial_receipts"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.digest",)
CLAUSES = ("well_formed", "strict_writes", "conflict_acyclic", "serial_order", "parents_exact", "states_exact")
# An operation: (txn, kind, key, token) by positions; kind in "r", "w", "c", "a".
Op = tuple[int, str, int, int]


def _p(fs: FiniteStructure, sort: str, e: int) -> int:
    k = position(fs, sort, e)
    return -1 if k is None else k


def ops(fs: FiniteStructure) -> list[Op | None]:
    acts = {o: _p(fs, "txn", t) for o, t in rows(fs, "acts")}
    kinds: dict[int, list[Op]] = {}
    for o, k in rows(fs, "reads"):
        kinds.setdefault(o, []).append((acts.get(o, -1), "r", _p(fs, "key", k), -1))
    for o, k, v in rows(fs, "writes"):
        kinds.setdefault(o, []).append((acts.get(o, -1), "w", _p(fs, "key", k), _p(fs, "token", v)))
    for (o,) in rows(fs, "commits"):
        kinds.setdefault(o, []).append((acts.get(o, -1), "c", -1, -1))
    for (o,) in rows(fs, "aborts"):
        kinds.setdefault(o, []).append((acts.get(o, -1), "a", -1, -1))
    return [kinds[o][0] if len(kinds.get(o, [])) == 1 else None for o in fs.elements("op")]


def _schedule(fs: FiniteStructure) -> list[Op]:
    return [o for o in ops(fs) if o is not None]


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    got = ops(fs)
    if None in got:
        return False
    ended: set[int] = set()
    for op in _schedule(fs):
        if op[0] in ended or op[0] < 0:
            return False
        if op[1] in ("c", "a"):
            ended.add(op[0])
    return all(fs.digest(s) is not None for s in fs.elements("stamp"))


def strict_writes(fs: FiniteStructure, _o: Oracle) -> bool:
    writer: dict[int, int] = {}
    finished: set[int] = set()
    for t, kind, key, _ in _schedule(fs):
        if kind in ("c", "a"):
            finished.add(t)
            continue
        w = writer.get(key)
        if w is not None and w != t and w not in finished:
            return False
        if kind == "w":
            writer[key] = t
    return True


def committed(fs: FiniteStructure) -> list[int]:
    return [t for t, kind, _, _ in _schedule(fs) if kind == "c"]


def edges(fs: FiniteStructure) -> set[tuple[int, int]]:
    live, sched = set(committed(fs)), _schedule(fs)
    out = set()
    for i, (ti, ki, key_i, _) in enumerate(sched):
        if ti not in live or ki not in ("r", "w"):
            continue
        for tj, kj, key_j, _ in sched[i + 1:]:
            if tj != ti and tj in live and kj in ("r", "w") and key_j == key_i and "w" in (ki, kj):
                out.add((ti, tj))
    return out


def conflict_acyclic(fs: FiniteStructure, _o: Oracle) -> bool:
    remaining, es = set(committed(fs)), edges(fs)
    while remaining:
        sources = [t for t in remaining if not any(a in remaining and b == t for a, b in es)]
        if not sources:
            return False
        remaining -= set(sources)
    return True


def receipts(fs: FiniteStructure) -> list[tuple[int, int | None, int | None]]:
    """(txn, parent stamp, state stamp) per receipt, in declared order."""
    txn = {r: _p(fs, "txn", t) for r, t in rows(fs, "receipt_for")}
    par = {r: s for r, s in rows(fs, "parent_stamp")}
    sta = {r: s for r, s in rows(fs, "state_stamp")}
    return [(txn.get(r, -1), par.get(r), sta.get(r)) for r in fs.elements("receipt")]


def serial_order(fs: FiniteStructure, _o: Oracle) -> bool:
    order = [t for t, _, _ in receipts(fs)]
    if sorted(order) != sorted(committed(fs)) or len(set(order)) != len(order):
        return False
    pos = {t: i for i, t in enumerate(order)}
    return all(pos[a] < pos[b] for a, b in edges(fs))


def _states(fs: FiniteStructure) -> tuple[list[bytes], list[bytes]]:
    base = {_p(fs, "key", k): _p(fs, "token", v) for k, v in rows(fs, "base")}
    live = set(committed(fs))
    writes: dict[int, list[tuple[int, int]]] = {t: [] for t in live}
    for t, kind, key, tok in _schedule(fs):
        if kind == "w" and t in live:
            writes[t].append((key, tok))
    state = dict(base)
    before, after = [], []
    for t, _, _ in receipts(fs):
        before.append(digest_of({f"k{k}": f"v{v}" for k, v in state.items()}))
        for key, tok in writes.get(t, []):
            state[key] = tok
        after.append(digest_of({f"k{k}": f"v{v}" for k, v in state.items()}))
    return before, after


def parents_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    before, _ = _states(fs)
    return all(p is not None and fs.digest(p) == want for (_, p, _), want in zip(receipts(fs), before))


def states_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    _, after = _states(fs)
    return all(s is not None and fs.digest(s) == want for (_, _, s), want in zip(receipts(fs), after))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"committed": committed(fs), "edges": sorted(list(e) for e in edges(fs))}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    op, receipt = e.form("op"), e.form("receipt")
    acts, base = e.form("acts"), e.form("base")
    rfor, par, sta = e.form("receipt_for"), e.form("parent_stamp"), e.form("state_stamp")
    return Compiled(
        (
            Total("acts_given", ((op, ("o",)),), ((acts, ("o", "t")),)),
            Functional("one_txn", acts, 1),
            Total("receipt_given", ((receipt, ("r",)),), ((rfor, ("r", "t")),)),
            Functional("one_receipt_txn", rfor, 1),
            Total("parent_given", ((receipt, ("r",)),), ((par, ("r", "s")),)),
            Functional("one_parent", par, 1),
            Total("state_given", ((receipt, ("r",)),), ((sta, ("r", "s")),)),
            Functional("one_state", sta, 1),
            Functional("one_base", base, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("strict_writes", strict_writes), ("conflict_acyclic", conflict_acyclic),
            ("serial_order", serial_order), ("parents_exact", parents_exact), ("states_exact", states_exact))),
    )
