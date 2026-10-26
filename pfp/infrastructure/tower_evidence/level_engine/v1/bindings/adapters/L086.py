"""Adapter for level 086: the engine's events and witnesses written as the
target checker's events and witnesses, in declared order.  Events are
named ``e<k>`` and witnesses ``w<k>`` by place; a parent or evidence link
to an element that is no event (no witness) is written ``x<element>``.  An
event's parents and evidence are listed in declared order, its agent is
its agent's name as hosted, and a witness's content and stamp are written
as hosted, never recomputed here.  The claimed order ``descends`` is the
engine's certificate for acyclicity; the checker decides acyclicity by
itself and is not shown it.  Written against the registered stage-86
checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_086"
CLAUSES = (("C1", "R086_UNKNOWN_PARENT"), ("C2", "R086_CIRCULAR"), ("C3", "R086_UNGROUNDED_ROOT"),
           ("C4", "R086_UNRESOLVED_EVIDENCE"), ("C5", "R086_WITNESS_DIGEST"))
COEFFICIENT_DOMAIN = {"source": "finite traces, ASCII texts and SHA-256 digests",
                      "target": "finite traces, ASCII texts and SHA-256 digests"}
SORTS = (("event", "event"), ("agent", "agent"), ("witness", "witness content"), ("stamp", "witness digest"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.names", "events and witnesses by place", "strings e<k> and w<k>; x<element> for a non-member",
     "PRESERVED"),
    ("target.descends", "the claimed order descends, checked natively", "not presented: the checker peels roots itself",
     "DROPPED"),
)
NEAR = (("own_neg", "R086_CIRCULAR"), ("near_grounded", "R086_CIRCULAR"))
MUTATIONS = (("C1", "R086_UNKNOWN_PARENT", "parent_unknown", "near_parent"),
             ("C2", "R086_CIRCULAR", "back_edge", "near_cycle"),
             ("C3", "R086_UNGROUNDED_ROOT", "root_ungrounded", "near_root"),
             ("C4", "R086_UNRESOLVED_EVIDENCE", "evidence_unresolved", "near_evidence"),
             ("C5", "R086_WITNESS_DIGEST", "content_changed", "near_stamp"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    digest = {int(e): str(d) for e, d in structure["digests"]}
    text = {int(e): str(t) for e, t in structure["texts"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    events, witnesses = _sort(structure, "event"), _sort(structure, "witness")

    def ev(x: int) -> str:
        return f"e{events.index(x)}" if x in events else f"x{x}"

    def wt(x: int) -> str:
        return f"w{witnesses.index(x)}" if x in witnesses else f"x{x}"

    def seconds(name: str, first: int) -> list[int]:
        return sorted(a[1] for n, a in rel if n == name and a[0] == first)

    return {"events": [[ev(e), text[seconds("by", e)[0]], [ev(p) for p in seconds("parent", e)],
                        [wt(w) for w in seconds("cites", e)]] for e in events],
            "witnesses": [[wt(w), text[w], digest[seconds("stamped", w)[0]]] for w in witnesses]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"event:{k}", f"event:{e[0]}"] for k, e in enumerate(positive["events"])] + [
        [f"witness:{k}", f"witness:{w[0]}"] for k, w in enumerate(positive["witnesses"])]
