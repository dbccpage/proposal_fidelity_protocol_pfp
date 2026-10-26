"""Evaluation: sealed minima, ephemeral quotient, declared base untouched.

AuthorityEffect: None.

Imports sealed ``min_responses``, ``apply_delta``, ``canonical``,
``Impose``, and ``replay``.  Quotient children are discarded after their
keys.  The declared base is not mutated.  Evaluation never admits, never
persists ``delta_events``, and never returns Tie / UniqueClass /
UniqueDelta / None.
"""

from __future__ import annotations

from derivation.candidates import Bounds, Delta, apply_delta, min_responses
from derivation.iso import CanonKey, canonical
from derivation.model import Event, Impose, Pair, Regime, replay

from harness import (
    EvalResult,
    EvaluationPersistedEventError,
    RetainedClass,
)


def evaluate(
    base: Regime,
    target: Pair,
    measure: str,
    bounds: Bounds,
) -> EvalResult:
    """Retain every iso class of the sealed minimum responses.

    Ephemeral children used for keys are discarded.  ``base`` is not
    written.  The return is always an ``EvalResult``.
    """
    minima = min_responses(base, target, measure, bounds)
    if minima is None:
        return EvalResult(
            measure=measure,
            cost=None,
            raw_minima=(),
            retained=(),
            found=False,
            max_items=bounds.max_items,
            max_arity=bounds.max_arity,
        )
    grouped: dict[CanonKey, list[Delta]] = {}
    for delta in minima.deltas:
        imposed = replay((Impose(target[0], target[1]),), base)
        child = apply_delta(imposed, delta)
        key = canonical(child)
        grouped.setdefault(key, []).append(delta)
        del child
        del imposed
    retained = tuple(
        RetainedClass(key, tuple(members))
        for key, members in sorted(grouped.items())
    )
    return EvalResult(
        measure=minima.measure,
        cost=minima.cost,
        raw_minima=minima.deltas,
        retained=retained,
        found=True,
        max_items=bounds.max_items,
        max_arity=bounds.max_arity,
    )


def fresh_retained_keys(
    base: Regime,
    target: Pair,
    measure: str,
    bounds: Bounds,
) -> frozenset[CanonKey]:
    """Sealed min_responses / canonical keys, recomputed, not a stored EvalResult."""
    return frozenset(
        item.key for item in evaluate(base, target, measure, bounds).retained
    )


def persist_eval_events_on_base(
    base: Regime,
    result: EvalResult,
    events: tuple[Event, ...],
) -> Regime:
    """Named refusal: evaluation does not persist Events onto the declared base."""
    del base, result, events
    raise EvaluationPersistedEventError(
        "evaluation does not persist Events onto the declared base"
    )


def declared_base_mutated(
    before: Regime,
    after: Regime,
    history: tuple[Event, ...],
) -> bool:
    """Comparison, not a literal: whether the declared base moved."""
    return after != before or replay(history) != after
