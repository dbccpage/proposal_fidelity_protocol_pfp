"""Replay of sealed evidence: the sealed observation read as a coarse map,
with its losses recorded and its protected pairs kept apart.

A supplied fixture is hosted by sealed events: three data, one unary form
marking the first, and the requirement that the first two stay apart.  The
demand to separate the second from the third is imposed, and the sealed
``min_responses`` answers it.  After the response, the sealed observation
sends each datum to its class of equal profiles: that is the coarse map.
Every pair it merges is a pair the regime cannot separate (the sealed
``collapsed_pairs``), so the loss ledger is exactly those pairs.  The
protected pairs are the regime's requirements; a valid regime keeps each of
them apart (sealed ``satisfies``), so none is merged.  Identifying a
witnessed pair is an obstruction, never a silent merge (sealed
``collision_of_identifying_witness``).

Clauses, each decided on the replayed sealed facts:

* ``observation_replayed``: the fine and coarse carriers and the block map
  are the sealed observation's quotient of the regime after a candidate of
  cost one;
* ``protected_replayed``: the protected pairs are that regime's requirements;
* ``ledger_complete``: every merged pair is in the ledger;
* ``ledger_exact``: every ledger pair and erasure record is a merged pair;
* ``no_silent_protected_merge``: no protected pair is merged without an
  erasure record.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result
from derivation.candidates import Bounds, apply_delta, iter_cost1_items, min_responses
from derivation.model import AdmitDatum, AdmitForm, AdmitInst, Event, Impose, Regime, Supply, replay, step
from derivation.observe import collapsed_pairs, profiles

CHALLENGE_ID = "observed_blocks"
ANSWER_TYPE = "M"
BOUND = 1
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("PrimDiff.collision_of_identifying_witness", "PrimDiff.obstruction_under_irrefl",
        "Derivation.mark_progress")
SOURCES = ("code/derivation/candidates.py", "code/derivation/model.py", "code/derivation/observe.py")
CLAUSES = ("observation_replayed", "protected_replayed", "ledger_complete", "ledger_exact",
           "no_silent_protected_merge")
TOKENS = ("<x>", "<y>", "<z>")
DEMAND = (1, 2)


def history() -> tuple[Event, ...]:
    out: list[Event] = []
    for t in TOKENS:
        out += [Supply(t), AdmitDatum(t)]
    return tuple(out) + (AdmitForm(1), AdmitInst(0, (0,)), Impose(0, 1))


def after(item: object) -> Regime:
    """The regime after one candidate, with the demand imposed."""
    return step(apply_delta(replay(history()), (item,)), Impose(*DEMAND))  # type: ignore[arg-type]


def reading(r: Regime) -> Packet:
    """The sealed observation's quotient of ``r`` as a block map, with its
    requirements as protected pairs and its collapsed pairs as the ledger."""
    profs = profiles(r)
    reps: list[int] = []
    for d in range(r.n_data()):
        if all(profs[d] != profs[e] for e in reps):
            reps.append(d)
    cls = {d: f"class{next(k for k, e in enumerate(reps) if profs[e] == profs[d])}" for d in range(r.n_data())}
    return {"block_map": [[r.data[d], cls[d]] for d in range(r.n_data())],
            "coarse": [f"class{k}" for k in range(len(reps))], "erasures": [], "fine": list(r.data),
            "ledger": [[r.data[i], r.data[j]] for i, j in collapsed_pairs(r)],
            "protected": [[r.data[i], r.data[j]] for i, j in sorted(r.reqs)]}


def candidates() -> list[Regime]:
    return [after(it) for it in iter_cost1_items(replay(history()), Bounds())]


def positive() -> Packet:
    found = min_responses(replay(history()), DEMAND, "mu1", Bounds())
    assert found is not None and len(found.deltas) == 1
    return reading(after(found.deltas[0][0]))


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _pairs(x: object) -> set[tuple[str, str]]:
    assert isinstance(x, list)
    return {(str(a), str(b)) for a, b in x}


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    keys = ("fine", "coarse", "block_map")
    match = [reading(r) for r in candidates() if all(reading(r)[k] == pk[k] for k in keys)]
    if not match:
        failed.append("observation_replayed")
    elif pk["protected"] != match[0]["protected"]:
        failed.append("protected_replayed")
    block = {str(a): str(b) for a, b in pk["block_map"]}  # type: ignore[attr-defined]
    fine = [str(x) for x in pk["fine"]]  # type: ignore[attr-defined]
    merged = {(x, y) for i, x in enumerate(fine) for y in fine[i + 1:] if x in block and block.get(x) == block.get(y)}
    ledger, erasures, protected = _pairs(pk["ledger"]), _pairs(pk["erasures"]), _pairs(pk["protected"])
    if not merged <= ledger:
        failed.append("ledger_complete")
    if not (ledger <= merged and erasures <= merged):
        failed.append("ledger_exact")
    if (protected & merged) - erasures:
        failed.append("no_silent_protected_merge")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"readings": [reading(r) for r in candidates()]}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
