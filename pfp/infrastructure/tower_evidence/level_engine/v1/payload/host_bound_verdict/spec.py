"""Replay of sealed evidence: a terminal claim about a sealed count is
accepted only through the host's own re-run, with the verifier and its scope
bound first.

The claim is a sum: the tied classes the sealed first separation retains in
each admission reading under the item-count measure (the sealed
``partial_decide`` on each reading's genesis, read from the pinned clone),
and their total over both readings.  A proposal carries no authority (sealed
``proposal_confers_no_execution``), and progress needs a licence (sealed
``progress_needs_license``).  So the claimed terminal counts only when the
host's verifier, bound by its scope, re-runs the sum and the output recorded
is that re-run's output.

The packet names its verifier (``host`` or ``candidate``), its scope, the
claimed terminal, and the output it records.

Clauses, each decided on the replayed sealed facts:

* ``claim_replayed``: the items are the sealed class counts per reading and
  the total is the count of classes both readings retain;
* ``verifier_bound``: the verifier is the host's;
* ``scope_bound``: the scope is the host verifier's own (a sum);
* ``terminal_earned``: the terminal is the one the host's re-run gives;
* ``output_bound``: the recorded output is the host's re-run output.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result
import partial_decide
from derivation.candidates import Bounds
from derivation.engine import READINGS
from derivation.model import replay

CHALLENGE_ID = "host_bound_verdict"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Represented.progress_needs_license", "GraphGenesis.proposal_confers_no_execution",
        "Derivation.mu1_minimum_not_unique")
SOURCES = ("code/derivation/engine.py", "research/partial_decide/partial_decide.py")
CLAUSES = ("claim_replayed", "verifier_bound", "scope_bound", "terminal_earned", "output_bound")
SCOPE = "sum"


def class_counts() -> list[int]:
    out = []
    for rd in READINGS:
        g = partial_decide.decide(replay(rd.genesis), rd.target[0], rd.target[1], "mu1", Bounds())
        assert isinstance(g, (partial_decide.Tie, partial_decide.UniqueClass))
        out.append(len(g.quotient.classes))
    return out


def host_run(claim: dict[str, object]) -> dict[str, object]:
    items = claim["items"]
    assert isinstance(items, list)
    return {"sum": sum(int(x) for x in items), "total": claim["total"]}


def positive() -> Packet:
    counts = class_counts()
    claim: dict[str, object] = {"items": counts, "total": sum(counts)}
    out = host_run(claim)
    return {"claim": claim, "claim_value": "GREEN" if out["sum"] == out["total"] else "RED", "output": out,
            "scope": SCOPE, "verifier": "host"}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    claim = pk["claim"]
    assert isinstance(claim, dict)
    counts = class_counts()
    if claim != {"items": counts, "total": sum(counts)}:
        failed.append("claim_replayed")
    if pk["verifier"] != "host":
        failed.append("verifier_bound")
    if pk["scope"] != SCOPE:
        failed.append("scope_bound")
    out = host_run(claim)
    if pk["claim_value"] != ("GREEN" if out["sum"] == out["total"] else "RED"):
        failed.append("terminal_earned")
    if pk["output"] != out:
        failed.append("output_bound")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"class_counts": dict(zip((rd.name for rd in READINGS), class_counts()))}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
