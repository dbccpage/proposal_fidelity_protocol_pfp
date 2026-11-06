"""The finite cross-check for rung three: the first-demand index.

Classification (assumption discipline):

* Everything here is metatheory apparatus layered on the sealed kernel and
  on the sibling ``research/second_nofirst/nofirst.py``, both imported
  read-only through their public functions and pinned by blob in
  ``SOURCE_MANIFEST.json``.  No sibling source is copied.
* A ``Stake`` is DECLARED METATHEORY, and the seven stakes this rung reads
  are exactly the seven the sibling declares.  Nothing here declares an
  eighth.
* The FIRST COUNT of a base, a history and a stake is DERIVED: the least
  count of events whose prefix reaches a regime carrying a demand.  It is
  read off the history and the stake and off nothing else; it is not a
  state of the object language, and nothing in the object language emits
  it.
* The enumeration is a FINITE COMPUTATION over a declared rectangle, run
  without any sealed pruning lemma.
* Nothing here is a theorem.  The theorems of this rung are in ``lean/``;
  this file checks their content by exhaustion on a rectangle and records
  the numbers the theorems do not give.

The vocabulary matches the Lean of this rung: ``stateAt`` is the regime a
prefix reaches, ``HasDemand`` is carrying a demand, ``IsFirstDemand`` is
being a first count.  Here the first count is computed, because over the
rectangle every regime is concrete and its profiles are finite; in Lean it
is a proposition, because the sealed separability is stated over a context
type this rung does not enumerate.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
for _p in (
    str(REPO / "code"),
    str(REPO / "research" / "identification_dual"),
    str(REPO / "research" / "two_sided_commitment"),
    str(REPO / "research" / "second_nofirst"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# This tree goes back to the front.  The sibling trees carry modules of
# their own named `verify_pins`, `check_coverage` and `test_forbidden`;
# putting those trees on the path ahead of this one would silently
# substitute a sibling's module for this rung's.  A sibling consumed
# read-only must not be able to shadow a module of the consumer.  The
# defect was found live in the sibling rung and is recorded there.
if str(HERE) in sys.path:
    sys.path.remove(str(HERE))
sys.path.insert(0, str(HERE))

from derivation.model import (  # noqa: E402
    EMPTY,
    AdmissionError,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Event,
    Impose,
    Regime,
    Supply,
    replay,
    step,
)
from derivation.engine import READINGS  # noqa: E402
from nofirst import (  # noqa: E402
    ALPHABET,
    Alphabet,
    Node,
    Stake,
    declared_stakes,
    demands,
    dishonoured_labelled_pairs,
    enumerate_by_levels,
    enumerate_rectangle,
    event_kind,
)

# FOUND LIVE, not hypothetical, and deeper than the note above.  The
# sibling module `nofirst` runs the same protection for ITSELF when it is
# imported, putting `research/second_nofirst` at the front of the path.
# Doing it before that import therefore does not last: under
# `unittest discover` the loader then imported the SIBLING's `test_pins`
# instead of this rung's, and refused with an import error naming the
# wrong directory.  So this tree goes back to the front once more, after
# the sibling import rather than before it.
if str(HERE) in sys.path:
    sys.path.remove(str(HERE))
sys.path.insert(0, str(HERE))

# The three declared bases.  EMPTY is the regime with nothing admitted --
# the Lean `genesis`.  L and F are the sealed engine's two genesis
# readings, consumed through its public `READINGS` and never rewritten.
EMPTY_BASE = "EMPTY"
BASE_NAMES: tuple[str, ...] = (EMPTY_BASE,) + tuple(r.name for r in READINGS)

# The three event kinds the sibling rung proved demand-inert, by the class
# names of the sealed event types.  Named here so that the rectangle can
# check the theorem of this rung without restating its proof.
INERT_KINDS: frozenset[str] = frozenset({"Supply", "Impose", "AdmitForm"})

CROSSCHECK_DEPTH = 3


def base_genesis(name: str) -> tuple[Event, ...]:
    """The genesis history of a declared base.  The empty base has the
    empty history; the two sealed readings have theirs."""
    if name == EMPTY_BASE:
        return ()
    for reading in READINGS:
        if reading.name == name:
            return tuple(reading.genesis)
    raise KeyError(name)


def base_regime(name: str) -> Regime:
    """The regime a declared base names, replayed from the sealed empty
    regime.  Never constructed by hand."""
    return replay(base_genesis(name), EMPTY)


# ---------------------------------------------------------------------------
# Carrying a demand, cached by regime
# ---------------------------------------------------------------------------


class Observations:
    """Demand sets over the rectangle, memoized by stake name and regime.

    Two classifiers are kept apart and neither is derived from the other:
    ``carries`` reads the sibling's ``demands``; ``dishonoured`` reads the
    sibling's independently written ``dishonoured_labelled_pairs``.  The
    second procedure below uses only the second classifier, so agreement
    between the two procedures is a check and not a tautology.
    """

    def __init__(self) -> None:
        self._demands: dict[tuple[str, Regime], bool] = {}
        self._dishonoured: dict[tuple[str, Regime], bool] = {}

    def carries(self, stake: Stake, regime: Regime) -> bool:
        key = (stake.name, regime)
        found = self._demands.get(key)
        if found is None:
            found = bool(demands(stake, regime))
            self._demands[key] = found
        return found

    def dishonoured(self, stake: Stake, regime: Regime) -> bool:
        key = (stake.name, regime)
        found = self._dishonoured.get(key)
        if found is None:
            found = bool(dishonoured_labelled_pairs(stake, regime))
            self._dishonoured[key] = found
        return found

    def sizes(self) -> tuple[int, int]:
        return len(self._demands), len(self._dishonoured)


# ---------------------------------------------------------------------------
# The two procedures
# ---------------------------------------------------------------------------


def first_index_forward(
    base: Regime, history: Sequence[Event], stake: Stake, seen: Observations
) -> Optional[int]:
    """PROCEDURE ONE.  Walk the history forward from the base, stepping one
    event at a time and stopping at the first prefix whose regime carries a
    demand.  Returns the count of events that prefix consumes, or ``None``
    when no prefix of the history carries one.
    """
    regime = base
    if seen.carries(stake, regime):
        return 0
    for count, event in enumerate(history, start=1):
        regime = step(regime, event)
        if seen.carries(stake, regime):
            return count
    return None


def first_index_scan(
    base: Regime, history: Sequence[Event], stake: Stake, seen: Observations
) -> Optional[int]:
    """PROCEDURE TWO, written independently of procedure one.

    Three differences, each deliberate: every prefix is replayed from the
    base in its own right rather than folded incrementally; the classifier
    is the sibling's dishonoured-labelled-pair test rather than its demand
    list; and the scan runs from the longest prefix down to the shortest,
    with no early stop, so the value returned is the last one written
    rather than the first one found.
    """
    found: Optional[int] = None
    for count in range(len(history), -1, -1):
        regime = replay(tuple(history[:count]), base)
        if seen.dishonoured(stake, regime):
            found = count
    return found


def event_descriptor(event: Event) -> str:
    """A deterministic one-line reading of an event, for the receipt's
    exhibited witnesses.  Presentation tokens appear here because a
    witness must be replayable by hand; they are never compared."""
    kind = event_kind(event)
    if isinstance(event, Supply):
        return f"{kind}({event.token})"
    if isinstance(event, AdmitDatum):
        return f"{kind}({event.token})"
    if isinstance(event, AdmitForm):
        return f"{kind}({event.arity})"
    if isinstance(event, AdmitInst):
        return f"{kind}({event.form},{list(event.args)})"
    if isinstance(event, AdmitRuleAll):
        return f"{kind}({event.form})"
    if isinstance(event, Impose):
        return f"{kind}({event.i},{event.j})"
    raise TypeError(f"unknown event type {type(event).__name__}")


def history_descriptor(history: Sequence[Event]) -> tuple[str, ...]:
    return tuple(event_descriptor(e) for e in history)


def regime_shape(regime: Regime) -> dict[str, int]:
    """The counted shape of a regime: no token, no order, no environment."""
    return {
        "data": regime.n_data(),
        "forms": len(regime.forms),
        "insts": len(regime.insts),
        "rules": len(regime.rules),
        "reqs": len(regime.reqs),
    }


# ---------------------------------------------------------------------------
# The rectangle, and what is measured on it
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rectangle:
    """One base's rectangle: its nodes, and the two stop counts the
    enumerator reports.  The nodes include the root, whose history is
    empty."""

    base: str
    regime: Regime
    nodes: tuple[Node, ...]
    bound_stops: int
    grammar_refusals: int

    def by_history(self) -> dict[tuple[Event, ...], Regime]:
        return {node.history: node.regime for node in self.nodes}


def build_rectangle(base: str, alphabet: Alphabet) -> Rectangle:
    genesis = base_genesis(base)
    nodes, bound_stops, refusals = enumerate_rectangle(genesis, alphabet)
    return Rectangle(base, base_regime(base), nodes, bound_stops, refusals)


def replay_check(rect: Rectangle) -> int:
    """Every node replays from its base to the regime recorded for it.
    Returns the count of mismatches, which the caller requires to be
    zero.  Replay is from the SEALED empty regime through the base's own
    genesis history, so no node is trusted to its enumerator."""
    genesis = base_genesis(rect.base)
    mismatches = 0
    for node in rect.nodes:
        if replay(genesis + node.history, EMPTY) != node.regime:
            mismatches += 1
    return mismatches


@dataclass(frozen=True)
class StakeReport:
    """What one stake shows over one base's rectangle."""

    earliest: Optional[int]
    counts_with_an_index: int
    index_distribution: dict[str, int]
    first_event_kinds: dict[str, int]
    procedure_disagreements: int
    inert_last_event_violations: int
    cessation_kinds: dict[str, int]
    colliding_regimes: int
    collision_witness: Optional[dict[str, object]]


def stake_report(
    rect: Rectangle, stake: Stake, seen: Observations
) -> StakeReport:
    """Measure one stake over one base's rectangle.

    The index of a node is computed by procedure one and checked against
    procedure two at every node.  Nothing is inherited from a parent node:
    each sequence is measured in its own right, so a defect in one node
    cannot be propagated silently to its extensions.
    """
    base = rect.regime
    indices: dict[tuple[Event, ...], Optional[int]] = {}
    distribution: dict[str, int] = {}
    kinds: dict[str, int] = {}
    disagreements = 0
    violations = 0
    with_index = 0
    earliest: Optional[int] = None
    for node in rect.nodes:
        index = first_index_forward(base, node.history, stake, seen)
        if index != first_index_scan(base, node.history, stake, seen):
            disagreements += 1
        indices[node.history] = index
        if index is None:
            continue
        with_index += 1
        distribution[str(index)] = distribution.get(str(index), 0) + 1
        if earliest is None or index < earliest:
            earliest = index
        if index == 0:
            kinds["base"] = kinds.get("base", 0) + 1
            continue
        kind = event_kind(node.history[index - 1])
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind in INERT_KINDS:
            violations += 1

    cessation: dict[str, int] = {}
    by_history = rect.by_history()
    for node in rect.nodes:
        if not node.history:
            continue
        parent = by_history[node.history[:-1]]
        if seen.carries(stake, parent) and not seen.carries(stake, node.regime):
            kind = event_kind(node.history[-1])
            cessation[kind] = cessation.get(kind, 0) + 1

    collisions: dict[Regime, set[int]] = {}
    witnesses: dict[Regime, dict[int, tuple[Event, ...]]] = {}
    for node in rect.nodes:
        index = indices[node.history]
        if index is None:
            continue
        collisions.setdefault(node.regime, set()).add(index)
        witnesses.setdefault(node.regime, {}).setdefault(index, node.history)
    colliding = {r: v for r, v in collisions.items() if len(v) > 1}
    witness: Optional[dict[str, object]] = None
    if colliding:
        chosen = min(
            colliding,
            key=lambda r: (
                sorted(colliding[r]),
                sorted(
                    history_descriptor(witnesses[r][i]) for i in colliding[r]
                ),
            ),
        )
        ordered = sorted(colliding[chosen])
        witness = {
            "regime": regime_shape(chosen),
            "indices": ordered,
            "histories": [
                list(history_descriptor(witnesses[chosen][i])) for i in ordered
            ],
        }
    return StakeReport(
        earliest=earliest,
        counts_with_an_index=with_index,
        index_distribution=distribution,
        first_event_kinds=kinds,
        procedure_disagreements=disagreements,
        inert_last_event_violations=violations,
        cessation_kinds=cessation,
        colliding_regimes=len(colliding),
        collision_witness=witness,
    )


def crosscheck(base: str, alphabet: Alphabet, depth: int) -> dict[str, object]:
    """The sibling's second enumerator, run on the declared cross-check
    family and compared with the first enumerator's reach."""
    genesis = base_genesis(base)
    nodes, _stops, _refusals = enumerate_rectangle(
        genesis,
        Alphabet(
            supply_token=alphabet.supply_token,
            fresh_tokens=alphabet.fresh_tokens,
            arities=alphabet.arities,
            max_data=alphabet.max_data,
            max_forms=alphabet.max_forms,
            max_length=depth,
        ),
    )
    first = frozenset(node.regime for node in nodes)
    second, visits = enumerate_by_levels(genesis, alphabet, depth)
    return {
        "depth": depth,
        "first_enumerator_regimes": len(first),
        "second_enumerator_regimes": len(second),
        "second_enumerator_visits": visits,
        "reach_agrees": first == second,
    }


def cessation_kinds_over(reports: Iterable[Mapping[str, object]]) -> list[str]:
    """Every event kind at which some stake's demand ceased, over every
    base of the run.  Sorted, so the receipt is order-free."""
    found: set[str] = set()
    for report in reports:
        stakes = report.get("stakes")
        if not isinstance(stakes, dict):
            raise TypeError("a base report must carry a stakes object")
        for entry in stakes.values():
            if not isinstance(entry, dict):
                raise TypeError("a stake entry must be an object")
            kinds = entry.get("cessation_kinds")
            if not isinstance(kinds, dict):
                raise TypeError("a stake entry must carry cessation_kinds")
            found.update(kinds)
    return sorted(found)


def base_report(base: str, alphabet: Alphabet) -> dict[str, object]:
    """Everything this rung measures over one declared base."""
    rect = build_rectangle(base, alphabet)
    seen = Observations()
    stakes: dict[str, object] = {}
    for stake in declared_stakes():
        report = stake_report(rect, stake, seen)
        stakes[stake.name] = {
            "earliest_index": report.earliest,
            "sequences_with_an_index": report.counts_with_an_index,
            "index_distribution": report.index_distribution,
            "first_event_kinds": report.first_event_kinds,
            "procedure_disagreements": report.procedure_disagreements,
            "inert_last_event_violations": report.inert_last_event_violations,
            "cessation_kinds": report.cessation_kinds,
            "colliding_regimes": report.colliding_regimes,
            "collision_witness": report.collision_witness,
        }
    return {
        "base": base,
        "base_regime": regime_shape(rect.regime),
        "genesis_events": len(base_genesis(base)),
        "nodes": len(rect.nodes),
        "distinct_regimes": len({node.regime for node in rect.nodes}),
        "bound_stops": rect.bound_stops,
        "grammar_refusals": rect.grammar_refusals,
        "replay_mismatches": replay_check(rect),
        "crosscheck": crosscheck(base, alphabet, CROSSCHECK_DEPTH),
        "stakes": stakes,
    }


def all_reports(alphabet: Alphabet = ALPHABET) -> list[dict[str, object]]:
    return [base_report(name, alphabet) for name in BASE_NAMES]


def grammar_refuses(regime: Regime, event: Event) -> bool:
    """Whether the sealed grammar refuses an admission at a regime.  Used
    by the tests to exhibit that a refused prefix reaches no regime, which
    is the `none` case the Lean index carries explicitly."""
    try:
        step(regime, event)
    except AdmissionError:
        return True
    return False


__all__ = [
    "ALPHABET",
    "Alphabet",
    "EMPTY",
    "Event",
    "Node",
    "Regime",
    "Stake",
    "all_reports",
    "BASE_NAMES",
    "CROSSCHECK_DEPTH",
    "EMPTY_BASE",
    "INERT_KINDS",
    "Observations",
    "Rectangle",
    "StakeReport",
    "all_reports",
    "base_genesis",
    "base_regime",
    "base_report",
    "build_rectangle",
    "cessation_kinds_over",
    "crosscheck",
    "declared_stakes",
    "event_descriptor",
    "event_kind",
    "first_index_forward",
    "first_index_scan",
    "grammar_refuses",
    "history_descriptor",
    "regime_shape",
    "replay_check",
    "stake_report",
]
