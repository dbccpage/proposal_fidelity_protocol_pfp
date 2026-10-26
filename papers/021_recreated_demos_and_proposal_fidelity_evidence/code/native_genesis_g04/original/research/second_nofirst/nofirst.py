"""Stage four: the finite cross-check for rung two, track one.

Classification (assumption discipline):

* Everything here is metatheory apparatus layered on the sealed kernel and
  on the sibling ``research/two_sided_commitment/two_sided.py``, both
  imported read-only through their public functions and pinned by blob in
  ``SOURCE_MANIFEST.json``.  No sibling source is copied.
* A ``Stake`` is DECLARED METATHEORY: a label on every ordered pair of
  datum indices taking apart, same, or free, free on the diagonal.  It is
  declared once, reads no state, and emits nothing.
* The demands of a regime under a stake are DERIVED: the labelled held
  pairs the regime does not honour, read off the profiles.  Nothing emits
  them.
* The enumeration is a FINITE COMPUTATION over a declared rectangle, run
  without any sealed pruning lemma.
* Nothing here is a theorem.  The theorems of this rung are in
  ``lean/``; this file checks their content by exhaustion on a rectangle
  and records the numbers the theorems do not give.

The stake vocabulary matches the Lean of this rung: ``APART``, ``SAME``,
``FREE``, ``honour``, ``demands``.  The sealed observation semantics is
the sealed ``profiles``: two data are separable exactly when their
profiles differ.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass
from typing import Callable, Iterator, Optional, Sequence

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
for _p in (
    str(REPO / "code"),
    str(REPO / "research" / "identification_dual"),
    str(REPO / "research" / "two_sided_commitment"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# This tree goes back to the front.  FOUND LIVE, not hypothetical: the
# sibling two-sided tree carries its own `verify_pins` module, and putting
# that tree on the path ahead of this one silently substituted the
# sibling's verifier for this rung's -- every span assertion then failed
# against a module that has no spans.  A sibling consumed read-only must
# not be able to shadow a module of the consumer.
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
    Pair,
    Regime,
    Supply,
    replay,
    step,
)
from derivation.engine import READINGS, Reading  # noqa: E402
from derivation.observe import profiles  # noqa: E402
from two_sided import COMMITMENTS, Commitment, commitment_named  # noqa: E402

APART = "apart"
SAME = "same"
FREE = "free"
LABELS = (APART, SAME, FREE)


# ---------------------------------------------------------------------------
# The stake
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Stake:
    """A label on ordered index pairs, free on the diagonal.  Declared
    once; reads no state; emits nothing.  This is the two-sided reading of
    the Lean ``Stake`` structure of this rung, with the same three values
    and the same diagonal condition."""

    name: str
    rule: Callable[[int, int], str]

    def label(self, i: int, j: int) -> str:
        if i == j:
            return FREE
        lo, hi = (i, j) if i < j else (j, i)
        out = self.rule(lo, hi)
        if out not in LABELS:
            raise ValueError(f"stake {self.name} returned {out!r}")
        return out


def _free(i: int, j: int) -> str:
    return FREE


def stake_of_commitment(c: Commitment) -> Stake:
    """The stake a sibling two-sided commitment induces.  The sibling's
    rule is already three-valued on ``i < j``; the diagonal is forced free
    by ``Stake.label``."""
    return Stake(c.name, c.rule)


def stake_of_one_sided_total() -> Stake:
    """The stake the pinned one-sided TOTAL commitment induces: every
    distinct pair apart, nothing same, because a one-sided commitment
    cannot ask for a collapse.  This mirrors the Lean ``ofCommitment``
    applied to the reconstructed ``total``."""

    def rule(i: int, j: int) -> str:
        return APART if i != j else FREE

    return Stake("one_sided_total", rule)


FREE_STAKE = Stake("free", _free)


def declared_stakes() -> tuple[Stake, ...]:
    """The free stake, the five stakes the sibling declares (consumed
    through the sibling's public tuple, never copied), and the stake the
    pinned one-sided total commitment induces."""
    return (
        (FREE_STAKE,)
        + tuple(stake_of_commitment(c) for c in COMMITMENTS)
        + (stake_of_one_sided_total(),)
    )


# ---------------------------------------------------------------------------
# Honour and demands over the sealed regime
# ---------------------------------------------------------------------------


def honour(r: Regime, label: str, i: int, j: int) -> bool:
    """Apart is honoured by separability, same by collapse, free always.
    Separability is the sealed sense: the profiles differ."""
    if label == FREE:
        return True
    profs = profiles(r)
    equal = profs[i] == profs[j]
    return (not equal) if label == APART else equal


def demands(s: Stake, r: Regime) -> tuple[tuple[str, Pair], ...]:
    """The labelled held pairs the regime does not honour, ordered by
    pair.  Read off the stake and the profiles and off nothing else."""
    n = r.n_data()
    profs = profiles(r)
    out: list[tuple[str, Pair]] = []
    for i in range(n):
        for j in range(i + 1, n):
            label = s.label(i, j)
            if label == FREE:
                continue
            equal = profs[i] == profs[j]
            if (label == APART and equal) or (label == SAME and not equal):
                out.append((label, (i, j)))
    return tuple(out)


def dishonoured_labelled_pairs(s: Stake, r: Regime) -> tuple[Pair, ...]:
    """The held pairs the stake labels that the regime does not honour.
    Computed independently of ``demands`` so that the receipt's totality
    check is not the classifier checking itself."""
    n = r.n_data()
    out: list[Pair] = []
    for i in range(n):
        for j in range(i + 1, n):
            label = s.label(i, j)
            if label == FREE:
                continue
            if not honour(r, label, i, j):
                out.append((i, j))
    return tuple(out)


def empty_profile_data(r: Regime) -> tuple[int, ...]:
    """Held data no well-formed context derives: the empty profile."""
    profs = profiles(r)
    return tuple(d for d in range(r.n_data()) if not profs[d])


# ---------------------------------------------------------------------------
# The declared rectangle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Alphabet:
    """The declared finite event alphabet.  Frozen in PREDICTIONS.md
    before the run."""

    supply_token: str
    fresh_tokens: tuple[str, ...]
    arities: tuple[int, ...]
    max_data: int
    max_forms: int
    max_length: int


ALPHABET = Alphabet(
    supply_token="<z>",
    fresh_tokens=("<n0>", "<n1>", "<n2>", "<n3>", "<n4>"),
    arities=(1, 2),
    max_data=5,
    max_forms=2,
    max_length=4,
)


def _arg_tuples(arity: int, n_data: int) -> Iterator[tuple[int, ...]]:
    if arity == 0:
        yield ()
        return
    for rest in _arg_tuples(arity - 1, n_data):
        for a in range(n_data):
            yield rest + (a,)


def alphabet_at(r: Regime, a: Alphabet, grown: int) -> tuple[Event, ...]:
    """Every event of the declared alphabet available at ``r``.  No
    pruning lemma is used: every syntactically available event within the
    declared bounds is offered, and an event the sealed grammar refuses is
    dropped by the caller when ``step`` raises."""
    out: list[Event] = [Supply(a.supply_token)]
    if r.n_data() < a.max_data and grown < len(a.fresh_tokens):
        out.append(AdmitDatum(a.fresh_tokens[grown]))
    if len(r.forms) < a.max_forms:
        for arity in a.arities:
            out.append(AdmitForm(arity))
    for f, arity in enumerate(r.forms):
        for args in _arg_tuples(arity, r.n_data()):
            out.append(AdmitInst(f, args))
        out.append(AdmitRuleAll(f))
    for i in range(r.n_data()):
        for j in range(i + 1, r.n_data()):
            out.append(Impose(i, j))
    return tuple(out)


def event_kind(e: Event) -> str:
    return type(e).__name__


@dataclass(frozen=True)
class Node:
    """One sequence of the rectangle and the regime it reaches."""

    history: tuple[Event, ...]
    regime: Regime
    grown: int


def enumerate_rectangle(
    genesis: Sequence[Event], a: Alphabet
) -> tuple[tuple[Node, ...], int, int]:
    """Depth-first enumeration of every sequence of at most ``a.max_length``
    declared events after the reading's genesis.  Returns the nodes (the
    root included), the count of extensions the DECLARED BOUNDS withheld,
    and the count the SEALED GRAMMAR refused.

    Unpruned: no sealed lemma is consulted, and no node is merged with
    another.  Two distinct sequences reaching the same regime are two
    nodes.  The two stop counts are kept apart because they mean different
    things: a bound stop is this rung's rectangle ending, and a grammar
    refusal is the sealed model rejecting an ill-formed admission.
    """
    root = Node((), replay(tuple(genesis)), 0)
    nodes: list[Node] = [root]
    bound_stops = 0
    grammar_refusals = 0
    stack: list[Node] = [root]
    while stack:
        node = stack.pop()
        if len(node.history) >= a.max_length:
            continue
        r = node.regime
        if r.n_data() >= a.max_data or node.grown >= len(a.fresh_tokens):
            bound_stops += 1
        if len(r.forms) >= a.max_forms:
            bound_stops += len(a.arities)
        for e in alphabet_at(r, a, node.grown):
            try:
                nxt = step(r, e)
            except AdmissionError:
                grammar_refusals += 1
                continue
            grown = node.grown + (1 if isinstance(e, AdmitDatum) else 0)
            child = Node(node.history + (e,), nxt, grown)
            nodes.append(child)
            stack.append(child)
    return tuple(nodes), bound_stops, grammar_refusals


def enumerate_by_levels(
    genesis: Sequence[Event], a: Alphabet, depth: int
) -> tuple[frozenset[Regime], int]:
    """A SECOND enumerator, written independently of the first: breadth
    first, by levels, accumulating regimes in a set rather than nodes in a
    list, and recomputing the alphabet from scratch at each level.  Used
    only to cross-check the first enumerator's reach on a declared
    cross-check family.
    """
    start = replay(tuple(genesis))
    level: list[tuple[Regime, int]] = [(start, 0)]
    seen: set[Regime] = {start}
    count = 1
    for _ in range(depth):
        nxt: list[tuple[Regime, int]] = []
        for r, grown in level:
            for e in alphabet_at(r, a, grown):
                try:
                    s = step(r, e)
                except AdmissionError:
                    continue
                g = grown + (1 if isinstance(e, AdmitDatum) else 0)
                nxt.append((s, g))
                count += 1
                seen.add(s)
        level = nxt
    return frozenset(seen), count


# ---------------------------------------------------------------------------
# The measurements
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FirstDemand:
    """Where a sequence's first demand appears, and where its first
    dishonoured labelled pair appears.  Computed by two independent
    walks so that agreement is a check and not a tautology."""

    index: Optional[int]
    kind: Optional[str]
    dishonoured_index: Optional[int]


def first_demand(
    genesis: Sequence[Event], history: Sequence[Event], s: Stake
) -> FirstDemand:
    """Walk the sequence from the reading's genesis, recording the first
    event index after which the stake carries a demand, and separately the
    first index after which a labelled held pair is dishonoured."""
    r = replay(tuple(genesis))
    idx: Optional[int] = None
    kind: Optional[str] = None
    dis: Optional[int] = None
    if demands(s, r):
        idx, kind = 0, "genesis"
    if dishonoured_labelled_pairs(s, r):
        dis = 0
    for n, e in enumerate(history, start=1):
        r = step(r, e)
        if idx is None and demands(s, r):
            idx, kind = n, event_kind(e)
        if dis is None and dishonoured_labelled_pairs(s, r):
            dis = n
        if idx is not None and dis is not None:
            break
    return FirstDemand(idx, kind, dis)


def inert_event_kinds(
    base: Regime, nodes: Sequence[Node], stakes: Sequence[Stake]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The event kinds that never change the demand set of any stake at any
    node of the rectangle, and the kinds that were actually exercised.

    A kind is reported inert only if it occurs in the rectangle: a kind
    that never occurs is vacuously unchanging and would be a count below
    the guard, not a count.  The caller checks the two tuples against each
    other.
    """
    changed: set[str] = set()
    seen: set[str] = set()
    for node in nodes:
        if not node.history:
            continue
        kind = event_kind(node.history[-1])
        seen.add(kind)
        if kind in changed:
            continue
        before = replay(node.history[:-1], base)
        for s in stakes:
            if demands(s, before) != demands(s, node.regime):
                changed.add(kind)
                break
    return tuple(sorted(seen - changed)), tuple(sorted(seen))


def kind_occurrences(nodes: Sequence[Node]) -> dict[str, int]:
    out: dict[str, int] = {}
    for node in nodes:
        for e in node.history:
            out[event_kind(e)] = out.get(event_kind(e), 0) + 1
    return out


def grow_once(r: Regime, token: str) -> Regime:
    return step(r, AdmitDatum(token))


def all_apart_stake() -> Stake:
    return stake_of_commitment(commitment_named("total_apart"))


__all__ = [
    "ALPHABET",
    "APART",
    "Alphabet",
    "FREE",
    "FREE_STAKE",
    "FirstDemand",
    "Node",
    "SAME",
    "Stake",
    "all_apart_stake",
    "alphabet_at",
    "commitment_named",
    "declared_stakes",
    "demands",
    "dishonoured_labelled_pairs",
    "empty_profile_data",
    "enumerate_by_levels",
    "enumerate_rectangle",
    "event_kind",
    "first_demand",
    "grow_once",
    "honour",
    "inert_event_kinds",
    "kind_occurrences",
    "stake_of_commitment",
    "stake_of_one_sided_total",
]
