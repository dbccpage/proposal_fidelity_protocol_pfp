# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of sealed evidence: the stages of the sealed possession reading's
genesis history, each a presentation (its admitted data, no equation), and
the maps between them, checked on generators and on every source equation.

The sealed history (``derivation.engine.GENESIS_F``, replayed with the sealed
``replay`` from the pinned clone) admits one datum at a time.  A stage is the
regime replayed up to one admission: its generators are the admitted data,
named by their presentation tokens, and it states no equation between them
(the sealed grammar never identifies two data).  Each map sends a datum of
an earlier stage to the same datum of a later one; a later replay keeps every
earlier datum (sealed ``Derivation.historyF_replays``;
``PresentationDescent.faithful_descent_iff_round_trip_coherent`` is the
sealed theorem this kind of check rests on).

The positive is computed, not written: the replayed stages, the consecutive
maps, and the direct map from the first stage to the last.

Clauses, each decided on the replayed sealed stages:

* ``stages_replayed``: the stages are exactly the replayed ones;
* ``maps_total``: every map is defined on every generator of its source and
  lands on a generator of its target, and every consecutive map is present;
* ``keeps_equations``: every map sends each source equation to a consequence
  of the target's equations;
* ``keeps_apart``: no map sends two generators the source keeps apart to one
  class of the target (the target's equations included);
* ``coherent``: a direct map agrees with the composite through every
  intermediate stage.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.canon import load_path
from omega_engine_operations.use_cases.level_engine.research_engine.components import ROOT
from omega_engine_operations.use_cases.level_engine.research_engine.level import FixtureVerdict, LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.sealed import AdmitDatum, replay
from omega_engine_operations.use_cases.level_engine.research_engine.sealed_evidence import lean_citation
from derivation.engine import GENESIS_F

CHALLENGE_ID = "stage_chain"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Derivation.historyF_replays", "PresentationDescent.faithful_descent_iff_round_trip_coherent",
        "PresentationDescent.faithful_descent_to_coherent")
SOURCES = ("code/derivation/engine.py", "code/derivation/model.py")
CLAUSES = ("stages_replayed", "maps_total", "keeps_equations", "keeps_apart", "coherent")


def replayed_stages() -> list[dict[str, object]]:
    """One stage per admission event of the sealed history."""
    out: list[dict[str, object]] = []
    for k, e in enumerate(GENESIS_F):
        if isinstance(e, AdmitDatum):
            out.append({"generators": list(replay(GENESIS_F[:k + 1]).data), "relations": []})
    return out


def chain() -> dict[str, object]:
    stages = replayed_stages()
    last = len(stages) - 1

    def inclusion(i: int, j: int) -> dict[str, object]:
        gens = stages[i]["generators"]
        assert isinstance(gens, list)
        return {"on_generators": [[g, g] for g in gens], "source": i, "target": j}

    return {"maps": [inclusion(i, i + 1) for i in range(last)] + [inclusion(0, last)], "stages": stages}


def packets() -> list[tuple[str, str, dict[str, object], str | None]]:
    d = ROOT / "payload" / CHALLENGE_ID
    pos = chain()
    inst = load_path(d / "instance.json")
    assert isinstance(inst, dict) and isinstance(inst["fixtures"], list)
    out: list[tuple[str, str, dict[str, object], str | None]] = [("pos", "positive", pos, None)]
    for f in inst["fixtures"]:
        out.append((str(f["id"]), str(f["role"]), {**pos, **f["set"]}, f.get("violates")))
    m = load_path(d / "mutation.json")
    assert isinstance(m, dict)
    out.append((str(m["id"]), "mutation", {**pos, **m["set"]}, str(m["violates"])))
    return out


def _classes(stage: dict[str, object]) -> dict[str, str]:
    gens = [str(g) for g in stage["generators"]]  # type: ignore[attr-defined]
    parent = {g: g for g in gens}

    def root(x: str) -> str:
        while parent[x] != x:
            x = parent[x]
        return x

    for a, b in stage["relations"]:  # type: ignore[attr-defined]
        ra, rb = root(str(a)), root(str(b))
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {g: root(g) for g in gens}


def decide(pk: dict[str, object]) -> tuple[str, ...]:
    stages = pk["stages"]
    maps = pk["maps"]
    assert isinstance(stages, list) and isinstance(maps, list)
    failed: list[str] = []
    if stages != replayed_stages():
        failed.append("stages_replayed")
    classes = [_classes(s) for s in stages]
    tables: dict[tuple[int, int], dict[str, str]] = {}
    total = True
    for m in maps:
        i, j = int(m["source"]), int(m["target"])
        table = {str(a): str(b) for a, b in m["on_generators"]}
        tables[(i, j)] = table
        if set(table) != set(classes[i]) or not set(table.values()) <= set(classes[j]):
            total = False
    if not total or any((i, i + 1) not in tables for i in range(len(stages) - 1)):
        failed.append("maps_total")
    elif any(classes[j][table[str(a)]] != classes[j][table[str(b)]]
             for (i, j), table in tables.items() for a, b in stages[i]["relations"]):
        failed.append("keeps_equations")
    elif any(classes[j][table[x]] == classes[j][table[y]] and classes[i][x] != classes[i][y]
             for (i, j), table in tables.items() for x in table for y in table if x < y):
        failed.append("keeps_apart")
    elif any(tables[(k, j)][tables[(i, k)][x]] != direct[x]
             for (i, j), direct in tables.items() for k in range(i + 1, j)
             if (i, k) in tables and (k, j) in tables for x in direct):
        failed.append("coherent")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    verdicts = []
    for fid, role, pk, _ in packets():
        failed = decide(pk)
        verdicts.append(FixtureVerdict(fid, role, True, not failed,
                                       "ACCEPT" if not failed else "FAILS:" + ",".join(sorted(failed)), failed))
    census = tuple((c, "decoded", ()) for c in CLAUSES)
    claims = tuple({"id": n.split(".")[-1], "lean": [lean_citation(n)], "status": "PROVED_THEOREM"} for n in LEAN)
    return LevelResult(CHALLENGE_ID, ANSWER_TYPE, tuple(verdicts), census, None, (), {"chain": chain()},
                       "repo_content", claims, SOURCES)
