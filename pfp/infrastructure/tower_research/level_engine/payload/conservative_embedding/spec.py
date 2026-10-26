# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of sealed evidence: a stage embeds into the stage its sealed minimal
response makes, and the embedding is conservative on what the old stage
protects.

A supplied fixture is hosted by sealed events: three data, one unary form
marking the first, and the requirement that the first two stay apart.  A
new demand asks to separate the second from the third.  The sealed
``min_responses`` answers it, and the sealed ``response_valid_naive`` judges
every candidate of cost one; both are read from the pinned clone.

A stage is presented over data: the old stage over the data its
requirements name, the new stage over all data after the response.  Its
equations are the pairs the stage cannot separate (the sealed
``collapsed_pairs``).  The embedding sends each old datum to itself.  The
sealed grammar states no arrow between data, so no two-cell is presented.

Clauses, each decided on the replayed sealed facts:

* ``old_replayed``: the old stage is the replayed one;
* ``new_is_a_response``: the new stage is the stage after some candidate of
  cost one;
* ``sealed_valid``: that candidate is a valid response (every requirement
  stays separated);
* ``embedding_total``: every old datum has an image among the new data;
* ``keeps_apart``: no two old data the old stage keeps apart are identified
  in the new stage;
* ``keeps_equations``: every old equation holds in the new stage;
* ``no_cells``: no arrow and no two-cell is presented.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result
from derivation.candidates import Bounds, apply_delta, iter_cost1_items, min_responses, response_valid_naive
from derivation.model import AdmitDatum, AdmitForm, AdmitInst, Event, Impose, Regime, Supply, replay
from derivation.observe import collapsed_pairs

CHALLENGE_ID = "conservative_embedding"
ANSWER_TYPE = "M"
BOUND = 1
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Derivation.mark_progress", "Derivation.validResponse_ext", "Derivation.validResponse_dropRules")
SOURCES = ("code/derivation/candidates.py", "code/derivation/model.py", "code/derivation/observe.py")
CLAUSES = ("old_replayed", "new_is_a_response", "sealed_valid", "embedding_total", "keeps_apart",
           "keeps_equations", "no_cells")
TOKENS = ("<x>", "<y>", "<z>")
DEMAND = (1, 2)


def history() -> tuple[Event, ...]:
    out: list[Event] = []
    for t in TOKENS:
        out += [Supply(t), AdmitDatum(t)]
    return tuple(out) + (AdmitForm(1), AdmitInst(0, (0,)), Impose(0, 1))


def old_regime() -> Regime:
    return replay(history())


def stage(r: Regime, over: tuple[int, ...]) -> tuple[list[str], list[list[str]]]:
    """Generators (tokens of the data ``over``) and equations (their
    collapsed pairs)."""
    gens = [r.data[d] for d in over]
    rels = [[r.data[i], r.data[j]] for i, j in collapsed_pairs(r) if i in over and j in over]
    return gens, rels


def old_stage() -> tuple[list[str], list[list[str]]]:
    r = old_regime()
    named = tuple(sorted({d for pair in r.reqs for d in pair}))
    return stage(r, named)


def candidates() -> list[tuple[object, tuple[list[str], list[list[str]]], bool]]:
    """Every candidate of cost one: the new stage it makes, and its sealed validity."""
    r = old_regime()
    out: list[tuple[object, tuple[list[str], list[list[str]]], bool]] = []
    for it in iter_cost1_items(r, Bounds()):
        child = apply_delta(r, (it,))
        out.append((it, stage(child, tuple(range(child.n_data()))), response_valid_naive(r, DEMAND, (it,))))
    return out


def positive() -> Packet:
    r = old_regime()
    found = min_responses(r, DEMAND, "mu1", Bounds())
    assert found is not None and len(found.deltas) == 1
    child = apply_delta(r, found.deltas[0])
    gens, rels = old_stage()
    new_gens, new_rels = stage(child, tuple(range(child.n_data())))
    return {"arrows": [], "cells": [], "embedding": [[g, g] for g in gens], "new_generators": new_gens,
            "new_relations": new_rels, "old_generators": gens, "old_relations": rels}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _classes(gens: list[str], rels: object) -> dict[str, str]:
    parent = {g: g for g in gens}

    def root(x: str) -> str:
        while parent[x] != x:
            x = parent[x]
        return x

    assert isinstance(rels, list)
    for a, b in rels:
        if a in parent and b in parent:
            ra, rb = root(str(a)), root(str(b))
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    return {g: root(g) for g in gens}


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    old_gens, new_gens = pk["old_generators"], pk["new_generators"]
    assert isinstance(old_gens, list) and isinstance(new_gens, list)
    if (old_gens, pk["old_relations"]) != old_stage():
        failed.append("old_replayed")
    match = [valid for _, st, valid in candidates() if st == (new_gens, pk["new_relations"])]
    if not match:
        failed.append("new_is_a_response")
    elif not match[0]:
        failed.append("sealed_valid")
    emb = {str(a): str(b) for a, b in pk["embedding"]}  # type: ignore[attr-defined]
    if set(emb) != set(old_gens) or not set(emb.values()) <= set(new_gens):
        failed.append("embedding_total")
    else:
        old_c, new_c = _classes(old_gens, pk["old_relations"]), _classes(new_gens, pk["new_relations"])
        pairs = [(x, y) for i, x in enumerate(old_gens) for y in old_gens[i + 1:]]
        if any(old_c[x] != old_c[y] and new_c[emb[x]] == new_c[emb[y]] for x, y in pairs):
            failed.append("keeps_apart")
        if any(old_c[x] == old_c[y] and new_c[emb[x]] != new_c[emb[y]] for x, y in pairs):
            failed.append("keeps_equations")
    if pk["arrows"] != [] or pk["cells"] != []:
        failed.append("no_cells")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    rows = packets()
    extra = {"candidates": [{"candidate": repr(it), "new_stage": list(st), "sealed_valid": v}
                            for it, st, v in candidates()], "old_stage": list(old_stage())}
    return result(CHALLENGE_ID, ANSWER_TYPE, rows, decide, CLAUSES, LEAN, SOURCES, extra)
