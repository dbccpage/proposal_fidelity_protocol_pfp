"""A trace of events by several agents is accepted only when its parent links
form no cycle, every parent is an event of the trace, every event with no
parent carries evidence, every evidence link names a witness, and every
witness's stamp is the digest of its content.

Acyclicity is decided over the hosted claim, by derivability: the claim
hosts an order ``descends(e, a)`` (``a`` is an ancestor of ``e``), which
must hold of every parent link and be closed under composition, and no
event may descend from itself.  A trace whose parent links contain a cycle
has no such order, whatever order is claimed: the composition closure then
forces some ``descends(e, e)``.  A trace without a cycle has one, its
parent links' own composition closure.

A witness's stamp is the SHA-256 of its content's bytes: a declared
convention.

The claim: events (in declared order), agents (each carrying its name, a
text), witnesses (each carrying its content, a text) and stamps (each
carrying a digest, an exact 32-byte value); ``by(e, a)``, ``parent(e, p)``,
``descends(e, a)``, ``cites(e, w)`` (an evidence link) and
``stamped(w, s)``.

Relational clauses, carried by derivability over the hosted claim:
``acyclic`` (the refused case: a circular dependency), ``parents_known``,
``descends_from_parents``, ``descends_composed``, ``evidence_resolves``,
``agent_given``, ``one_agent``, ``by_typed``, ``stamp_given``,
``one_stamp`` and ``stamped_typed``.

Decoded clauses, decided outside the grammar: ``roots_grounded`` (every
event with no parent cites a witness) and ``stamps_recomputed``.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.exact.digest import sha256
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import rows

CHALLENGE_ID = "grounded_traces"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.digest",)
CLAUSES = ("roots_grounded", "stamps_recomputed")


def roots_grounded(fs: FiniteStructure, _o: Oracle) -> bool:
    children = {e for e, _ in rows(fs, "parent")}
    cited = {e for e, _ in rows(fs, "cites")}
    return all(e in children or e in cited for e in fs.elements("event"))


def stamps_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    stamp = {w: s for w, s in rows(fs, "stamped")}
    for w in fs.elements("witness"):
        text = fs.text(w)
        if w not in stamp or text is None or fs.digest(stamp[w]) != sha256(text.encode("ascii")):
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"stamps": ["sha256:" + sha256(t.encode("ascii")).hex() if (t := fs.text(w)) is not None else None
                       for w in fs.elements("witness")]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    event, agent, witness, stamp = e.form("event"), e.form("agent"), e.form("witness"), e.form("stamp")
    by, parent, descends, cites, stamped = (e.form("by"), e.form("parent"), e.form("descends"), e.form("cites"),
                                            e.form("stamped"))
    return Compiled(
        (
            Forbid("acyclic", ((descends, ("e", "e")),)),
            Closure("parents_known", ((parent, ("e", "p")),), ((event, ("e",)), (event, ("p",)))),
            Closure("descends_from_parents", ((parent, ("e", "p")),), ((descends, ("e", "p")),)),
            Closure("descends_composed", ((descends, ("e", "f")), (descends, ("f", "g"))), ((descends, ("e", "g")),)),
            Closure("evidence_resolves", ((cites, ("e", "w")),), ((event, ("e",)), (witness, ("w",)))),
            Total("agent_given", ((event, ("e",)),), ((by, ("e", "a")),)),
            Functional("one_agent", by, 1),
            Closure("by_typed", ((by, ("e", "a")),), ((agent, ("a",)),)),
            Total("stamp_given", ((witness, ("w",)),), ((stamped, ("w", "s")),)),
            Functional("one_stamp", stamped, 1),
            Closure("stamped_typed", ((stamped, ("w", "s")),), ((stamp, ("s",)),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("roots_grounded", roots_grounded), ("stamps_recomputed", stamps_recomputed))),
    )
