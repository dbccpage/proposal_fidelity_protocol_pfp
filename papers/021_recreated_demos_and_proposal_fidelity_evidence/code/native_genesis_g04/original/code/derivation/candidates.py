"""Candidate one-step augmentations (deltas), cost measures, and minimum
valid responses to a separation requirement.

Classification: metatheory apparatus.  The *candidate space* and the *cost
measures* are declared bounds of the derivation, recorded in the paper.

A delta is a finite multiset of items, kept as a canonically sorted tuple:

* ``NewDatum``            -- admit one fresh datum;
* ``NewForm(arity)``      -- admit one judgment form (1 <= arity <= bound);
* ``NewInst(form, args)`` -- admit one judgment instance; ``form`` may index
                             a form added by the same delta;
* ``NewRuleAll(form)``    -- admit the uniform all-tuples rule for a form.

Cost measures (both declared):

* ``mu1(delta)`` = number of items;
* ``mu2(delta)`` = (number of items, sum of arities of new forms), ordered
  lexicographically.

A delta is a *valid response* to requirement ``(i, j)`` on a base regime when
the augmented regime satisfies every previously imposed requirement together
with the new one.

Pruning of the cost-2 enumeration is justified by four lemmas (each with a
negative cross-check test against the unpruned space, and formalized where
noted in the claim ledger):

* rule-removal: a delta containing ``NewRuleAll`` is never a minimum valid
  response (uniform additions preserve profile equality, so dropping the rule
  item preserves every separation);
* datum-irrelevance: a ``NewDatum`` not referenced by any ``NewInst`` of the
  same delta changes no profile of previously admitted data;
* form-irrelevance: a ``NewForm`` without an instance in the same delta
  contributes no derivable context;
* mention lemma: an instance-only delta changes the profile of datum ``d``
  only if some added instance mentions ``d``.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import Iterator, Optional, Union

from .model import (
    AdmissionError,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Args,
    Event,
    Impose,
    Pair,
    Regime,
    replay,
)
from .observe import Context, contexts, profiles


@dataclass(frozen=True)
class NewDatum:
    pass


@dataclass(frozen=True)
class NewForm:
    arity: int


@dataclass(frozen=True)
class NewInst:
    form: int
    args: Args


@dataclass(frozen=True)
class NewRuleAll:
    form: int


Item = Union[NewDatum, NewForm, NewInst, NewRuleAll]
Delta = tuple[Item, ...]


def item_key(it: Item) -> tuple[int, int, Args]:
    """Deterministic sort key giving the canonical item order:
    data, forms, rules, instances."""
    if isinstance(it, NewDatum):
        return (0, 0, ())
    if isinstance(it, NewForm):
        return (1, it.arity, ())
    if isinstance(it, NewRuleAll):
        return (2, it.form, ())
    return (3, it.form, it.args)


def canonical_delta(items: tuple[Item, ...]) -> Delta:
    return tuple(sorted(items, key=item_key))


def mu1(delta: Delta) -> int:
    return len(delta)


def mu2(delta: Delta) -> tuple[int, int]:
    return (
        len(delta),
        sum(it.arity for it in delta if isinstance(it, NewForm)),
    )


def delta_events(base: Regime, delta: Delta) -> tuple[Event, ...]:
    """Translate a canonical delta into admission events.

    Fresh data receive tokens ``w<index>`` where the index is the datum's
    admission position; indices increase strictly along any history, so the
    tokens are unique."""
    events: list[Event] = []
    n = base.n_data()
    for it in delta:
        if isinstance(it, NewDatum):
            events.append(AdmitDatum(f"w{n}"))
            n += 1
        elif isinstance(it, NewForm):
            events.append(AdmitForm(it.arity))
        elif isinstance(it, NewRuleAll):
            events.append(AdmitRuleAll(it.form))
        else:
            events.append(AdmitInst(it.form, it.args))
    return tuple(events)


def apply_delta(base: Regime, delta: Delta) -> Regime:
    """Apply a delta; raises ``AdmissionError`` when ill-formed."""
    return replay(delta_events(base, delta), base)


@dataclass(frozen=True)
class Bounds:
    """Declared finite bounds of the candidate space."""

    max_items: int = 2
    max_arity: int = 2


# ---------------------------------------------------------------------------
# Fast validity check (cross-validated against the naive check in tests and
# on every accepted delta by the engine).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NodeView:
    """Precomputed observation data for one base regime."""

    base: Regime
    ctxs: tuple[Context, ...]
    profs: tuple[frozenset[Context], ...]

    @staticmethod
    def of(base: Regime) -> "NodeView":
        if base.rules:
            raise ValueError(
                "fast path requires a rule-free base regime "
                "(engine invariant; use the naive check otherwise)"
            )
        return NodeView(base, contexts(base), profiles(base))


def _nonempty_subsets(positions: tuple[int, ...]) -> Iterator[tuple[int, ...]]:
    for k in range(1, len(positions) + 1):
        yield from combinations(positions, k)


def profile_additions(
    view: NodeView, delta: Delta
) -> tuple[dict[int, set[Context]], int]:
    """Profile additions per datum index caused by ``delta``.

    Returns ``(additions, n_total)``.  Correctness relies on the base regime
    having no uniform rules (enforced by ``NodeView.of``): every context that
    mentions a datum or form introduced by the delta is derivable only via
    instances or rules of the delta itself.
    """
    base = view.base
    n0 = base.n_data()
    n_total = n0 + sum(1 for it in delta if isinstance(it, NewDatum))
    arities: list[int] = list(base.forms)
    for it in delta:
        if isinstance(it, NewForm):
            arities.append(it.arity)
    adds: dict[int, set[Context]] = {}

    def _add(d: int, c: Context) -> None:
        adds.setdefault(d, set()).add(c)

    for it in delta:
        if isinstance(it, NewRuleAll):
            arity = arities[it.form]
            options: list[Optional[int]] = [None] + list(range(n_total))
            for slots in product(options, repeat=arity):
                if any(s is None for s in slots):
                    for d in range(n_total):
                        _add(d, (it.form, slots))
        elif isinstance(it, NewInst):
            for d in set(it.args):
                positions = tuple(
                    k for k, v in enumerate(it.args) if v == d
                )
                for sub in _nonempty_subsets(positions):
                    slots = tuple(
                        None if k in sub else v
                        for k, v in enumerate(it.args)
                    )
                    _add(d, (it.form, slots))
    return adds, n_total


_EMPTY_ADD: frozenset[Context] = frozenset()


def response_valid_fast(
    view: NodeView, target: Pair, delta: Delta
) -> bool:
    """Fast check: does the delta separate the target while preserving every
    previously imposed requirement?"""
    adds, _ = profile_additions(view, delta)
    base = view.base

    def prof(d: int) -> frozenset[Context]:
        base_p = view.profs[d] if d < base.n_data() else _EMPTY_ADD
        extra = adds.get(d)
        if not extra:
            return base_p
        return base_p | extra

    for (p, q) in sorted(base.reqs | {target}):
        if prof(p) == prof(q):
            return False
    return True


def response_valid_naive(base: Regime, target: Pair, delta: Delta) -> bool:
    """Reference check: full recomputation via replay.  Raises on
    ill-formed deltas."""
    from .model import step
    from .observe import satisfies

    augmented = step(apply_delta(base, delta), Impose(target[0], target[1]))
    return satisfies(augmented)


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------


def iter_cost1_items(base: Regime, bounds: Bounds) -> Iterator[Item]:
    """All single items over the base regime, in deterministic order."""
    yield NewDatum()
    for arity in range(1, bounds.max_arity + 1):
        yield NewForm(arity)
    for f in sorted(set(range(len(base.forms))) - set(base.rules)):
        yield NewRuleAll(f)
    for f, arity in enumerate(base.forms):
        for args in product(range(base.n_data()), repeat=arity):
            yield NewInst(f, tuple(args))


def _mentions(it: NewInst, ds: frozenset[int]) -> bool:
    return any(a in ds for a in it.args)


def iter_cost2_deltas(
    base: Regime, bounds: Bounds, target: Pair
) -> Iterator[Delta]:
    """Pruned two-item deltas (see module docstring for the lemmas).

    Shapes: (NewForm, NewInst on the new form), (NewDatum, NewInst mentioning
    the new datum), and (NewInst, NewInst) where at least one instance
    mentions a member of the target pair."""
    n0 = base.n_data()
    new_form_index = len(base.forms)
    # (a) fresh form + one instance on it, over previously admitted data
    for arity in range(1, bounds.max_arity + 1):
        for args in product(range(n0), repeat=arity):
            yield canonical_delta(
                (NewForm(arity), NewInst(new_form_index, tuple(args)))
            )
    # (b) fresh datum + one instance on an existing form mentioning it
    for f, arity in enumerate(base.forms):
        for args in product(range(n0 + 1), repeat=arity):
            if n0 in args:
                yield canonical_delta(
                    (NewDatum(), NewInst(f, tuple(args)))
                )
    # (c) two instances on existing forms, at least one mentioning the target
    tgt = frozenset(target)
    all_insts: list[NewInst] = [
        NewInst(f, tuple(args))
        for f, arity in enumerate(base.forms)
        for args in product(range(n0), repeat=arity)
    ]
    mentioning = [it for it in all_insts if _mentions(it, tgt)]
    for a in mentioning:
        ka = item_key(a)
        for b in all_insts:
            if (a.form, a.args) == (b.form, b.args):
                continue
            if _mentions(b, tgt) and item_key(b) < ka:
                continue  # unordered pair already emitted with roles swapped
            yield canonical_delta((a, b))


def iter_full_deltas(base: Regime, cost: int, bounds: Bounds) -> Iterator[Delta]:
    """Unpruned enumeration of every well-formed delta of the given item
    count (0, 1, or 2).  Used by cross-check tests to certify the pruned
    enumeration; deliberately brute force."""
    if cost == 0:
        yield ()
        return
    if cost == 1:
        yield from (
            (it,) for it in iter_cost1_items(base, bounds)
        )
        return
    if cost != 2:
        raise ValueError("full enumeration is declared only for cost <= 2")
    n0 = base.n_data()
    universe: list[Item] = [NewDatum()]
    for arity in range(1, bounds.max_arity + 1):
        universe.append(NewForm(arity))
    max_form = len(base.forms) + 1  # at most one new form in a 2-item delta
    max_arity_any = max(
        [bounds.max_arity] + list(base.forms)
    )
    for f in range(max_form):
        universe.append(NewRuleAll(f))
        for arity in range(1, max_arity_any + 1):
            for args in product(range(n0 + 1), repeat=arity):
                universe.append(NewInst(f, tuple(args)))
    seen: set[Delta] = set()
    for a in universe:
        for b in universe:
            delta = canonical_delta((a, b))
            if delta in seen:
                continue
            seen.add(delta)
            try:
                apply_delta(base, delta)
            except AdmissionError:
                continue
            yield delta


@dataclass(frozen=True)
class MinResponses:
    """All minimum valid responses under a measure, before the isomorphism
    quotient.  ``cost`` is the measure value attained; ``complete_within``
    records the declared bound."""

    measure: str
    cost: tuple[int, int]
    deltas: tuple[Delta, ...]
    complete_within: Bounds


def min_responses(
    base: Regime,
    target: Pair,
    measure: str,
    bounds: Bounds,
) -> Optional[MinResponses]:
    """Minimum valid responses to ``Separate(target)`` within the declared
    bounds, or ``None`` when no valid delta of at most ``max_items`` items
    exists.

    ``measure`` is ``"mu1"`` or ``"mu2"``.  Iteration is by item count; for
    ``mu2`` the valid deltas at the first successful item count are refined
    by new-form arity sum (lexicographic order makes this exact)."""
    if measure not in ("mu1", "mu2"):
        raise ValueError(f"unknown measure: {measure}")
    view = NodeView.of(base)
    for cost in range(0, bounds.max_items + 1):
        if cost == 0:
            valid: list[Delta] = [()] if response_valid_fast(
                view, target, ()
            ) else []
        elif cost == 1:
            valid = [
                (it,)
                for it in iter_cost1_items(base, bounds)
                if response_valid_fast(view, target, (it,))
            ]
        elif cost == 2:
            valid = []
            seen: set[Delta] = set()
            for delta in iter_cost2_deltas(base, bounds, target):
                if delta in seen:
                    continue
                seen.add(delta)
                if response_valid_fast(view, target, delta):
                    valid.append(delta)
        else:  # pragma: no cover - bounds.max_items is 2 in this derivation
            raise ValueError(
                "enumeration beyond two items is outside the declared bounds"
            )
        if not valid:
            continue
        if measure == "mu1":
            return MinResponses(
                "mu1", (cost, -1), tuple(sorted(valid, key=_delta_key)), bounds
            )
        best = min(mu2(d) for d in valid)
        chosen = tuple(
            sorted((d for d in valid if mu2(d) == best), key=_delta_key)
        )
        return MinResponses("mu2", best, chosen, bounds)
    return None


def _delta_key(delta: Delta) -> tuple[tuple[int, int, Args], ...]:
    return tuple(item_key(it) for it in delta)
