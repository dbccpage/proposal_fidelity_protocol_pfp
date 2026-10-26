# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 095: the engine's runs, logs, environment and ratio
written as the target checker's runs, environment and speedup.  Runs are in
declared order; a run's input is the entries it reads, in declared order;
counts, digests and the ratio are written as hosted, never recomputed here.
The procedure names travel as hosted; the counter name travels as hosted;
the implementation tag is written under the checker's level prefix (the
engine's pinned tag ``procedures-v1`` is the checker's
``mss095-procedures-v1``).  A ratio marked measured, and not estimated, is
written on the measured basis; any other is written estimated.  Written
against the registered stage-95 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_095"
CLAUSES = (("C1", "R095_ESTIMATED_SPEEDUP"), ("C2", "R095_ENVIRONMENT"), ("C3", "R095_COUNTER_MISMATCH"),
           ("C4", "R095_LOG_MISMATCH"), ("C5", "R095_SPEEDUP_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "naturals, exact rationals, SHA-256 digests and texts",
                      "target": "naturals, exact rationals, SHA-256 digests and texts"}
SORTS = (("tag", "environment implementation"), ("counter", "environment counter"), ("procedure", "procedure name"),
         ("run", "run"), ("log", "run log digest"), ("ratio", "speedup"), ("entry", "input entry"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
PREFIX = "mss095-"
LOSS_ROWS = (
    ("target.environment.implementation", "the pinned tag procedures-v1", "the tag under the level prefix mss095-",
     "PRESERVED"),
    ("target.basis", "measured(q) or estimated(q)", "the strings measured and estimated", "PRESERVED"),
    ("target.inputs", "a run's input as the pooled entries it reads, at most 18 elements in all",
     "a list of at most 64 naturals per run", "WEAKENED"),
    ("target.wall_time", "not measured", "not measured", "PRESERVED"),
)
NEAR = (("own_neg", "R095_ESTIMATED_SPEEDUP"), ("near_counter", "R095_ENVIRONMENT"),
        ("near_inputs", "R095_SPEEDUP_MISMATCH"))
MUTATIONS = (("C1", "R095_ESTIMATED_SPEEDUP", "mut", "mut"),
             ("C2", "R095_ENVIRONMENT", "tag_changed", "near_tag"),
             ("C3", "R095_COUNTER_MISMATCH", "count_changed", "near_count"),
             ("C4", "R095_LOG_MISMATCH", "log_changed", "near_log"),
             ("C5", "R095_SPEEDUP_MISMATCH", "ratio_inverted", "near_ratio"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    digest = {int(e): str(d) for e, d in structure["digests"]}
    text = {int(e): str(t) for e, t in structure["texts"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    runs, entries = _sort(structure, "run"), _sort(structure, "entry")
    (tag,), (counter,), (ratio,) = _sort(structure, "tag"), _sort(structure, "counter"), _sort(structure, "ratio")
    procedure = {a[0]: text[a[1]] for n, a in rel if n == "performs"}
    log = {a[0]: digest[a[1]] for n, a in rel if n == "logged"}
    ends = {n: runs.index(a[1]) for n, a in rel if n in ("baseline", "candidate") and a[0] == ratio}
    marks = {n for n, a in rel if n in ("measured", "estimated") and a == [ratio]}

    def reads(r: int) -> list[int]:
        mine = {a[1] for n, a in rel if n == "reads" and a[0] == r}
        return [int(Fraction(value[x])) for x in entries if x in mine]

    return {"environment": {"counter": text[counter], "implementation": PREFIX + text[tag]},
            "runs": [[procedure[r], reads(r), int(Fraction(value[r])), log[r]] for r in runs],
            "speedup": {"basis": "measured" if marks == {"measured"} else "estimated",
                        "baseline": ends["baseline"], "candidate": ends["candidate"], "ratio": value[ratio]}}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return ([["tag:0", "environment.implementation"], ["counter:0", "environment.counter"]]
            + [[f"run:{k}", f"runs:{k}"] for k in range(len(positive["runs"]))] + [["ratio:0", "speedup"]])
