"""EIS exclusions as hypotheses: every "don't do X" carries the cheapest test that would show it wrong.

AuthorityEffect: None. An exclusion only decides where test effort goes; a host
check still decides every result.

Models share training data, so their mistakes are correlated. A confident wrong
"branch B is dead" from several seats of one model family is one opinion, not
several, and it can hide the real answer. This module applies four rules:

1. **No exclusion without a falsifier.** ``ExclusionHypothesisV1`` refuses an
   empty falsifier (``EXCLUSION_WITHOUT_FALSIFIER``) and records its cost.
2. **Agreement is counted by model family.** Seats of one family collapse to one
   vote. ``classify`` returns:

   * ``FRONTIER``: families disagree, or one family's seats split. Test here first.
   * ``UNCORROBORATED``: only one family supports the exclusion.
   * ``PROBABLY_DEAD``: at least ``min_families`` families agree and none dissents.

3. **Cheap dead branches still get tested.** ``plan_retests`` orders falsifiers
   frontier first, then uncorroborated, then probably-dead ones whose cost is at
   most ``dead_floor``, cheapest first within each tier, under one budget.
4. **A falsifier result is final for its run.** ``settle`` marks a hypothesis
   ``REFUTED`` (its branch reopens) or ``SURVIVED_TEST``. Untested ones keep
   their classification, which is a statement about votes, never a fact.

``headstone_exclusion`` applies the same rule to the PCIV cemetery: a candidate
killed by a host check stays buried (the check is deterministic), while one
killed by a model seat becomes an exclusion hypothesis that can be retested.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from . import immune_host

AUTHORITY_NONE = 'None'

FRONTIER = 'FRONTIER'
UNCORROBORATED = 'UNCORROBORATED'
PROBABLY_DEAD = 'PROBABLY_DEAD'
REFUTED = 'REFUTED'
SURVIVED_TEST = 'SURVIVED_TEST'
CLASSIFICATIONS = (FRONTIER, UNCORROBORATED, PROBABLY_DEAD)
_TIER = {FRONTIER: 0, UNCORROBORATED: 1, PROBABLY_DEAD: 2}

DEAD_ABOVE_FLOOR = 'DEAD_ABOVE_FLOOR'
OVER_BUDGET = 'OVER_BUDGET'


class ExclusionError(ValueError):
    """A malformed exclusion. The message starts with a stable code."""


def _refuse(code: str, detail: str) -> ExclusionError:
    return ExclusionError(f'{code}: {detail}')


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _refuse('EXCLUSION_FIELD_EMPTY', f'{name} must be a nonempty string')
    return value


@dataclass(frozen=True)
class ExclusionVoteV1:
    """One seat's position on one exclusion. ``model_family`` is the correlation key."""
    seat_id: str
    model_family: str
    excludes: bool

    def __post_init__(self) -> None:
        _text(self.seat_id, 'seat_id')
        _text(self.model_family, 'model_family')
        if type(self.excludes) is not bool:
            raise _refuse('EXCLUSION_FIELD_EMPTY', 'excludes must be a bool')


@dataclass(frozen=True)
class ExclusionHypothesisV1:
    """A claim that a branch is not worth searching, with the cheapest test that would refute it."""
    exclusion_id: str
    branch: str
    claim: str
    falsifier: str
    falsifier_cost: int
    votes: tuple[ExclusionVoteV1, ...]
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _text(self.exclusion_id, 'exclusion_id')
        _text(self.branch, 'branch')
        _text(self.claim, 'claim')
        if not isinstance(self.falsifier, str) or not self.falsifier.strip():
            raise _refuse('EXCLUSION_WITHOUT_FALSIFIER', f'{self.exclusion_id} names no test that could refute it')
        if type(self.falsifier_cost) is not int or self.falsifier_cost < 0:
            raise _refuse('FALSIFIER_COST_INVALID', 'falsifier_cost must be a nonnegative int')
        object.__setattr__(self, 'votes', tuple(self.votes))
        if any(type(v) is not ExclusionVoteV1 for v in self.votes):
            raise _refuse('EXCLUSION_FIELD_EMPTY', 'votes must be ExclusionVoteV1')
        if not any(v.excludes for v in self.votes):
            raise _refuse('EXCLUSION_WITHOUT_SUPPORT', f'no seat proposes {self.exclusion_id}')
        if self.authority_effect != AUTHORITY_NONE:
            raise _refuse('AUTHORITY_ESCALATION', 'an exclusion never holds authority')

    def family_positions(self) -> dict[str, frozenset[bool]]:
        """Each family's set of positions; a set of two means the family split."""
        out: dict[str, set[bool]] = {}
        for vote in self.votes:
            out.setdefault(vote.model_family, set()).add(vote.excludes)
        return {k: frozenset(v) for k, v in sorted(out.items())}

    def supporting_families(self) -> tuple[str, ...]:
        return tuple(f for f, pos in self.family_positions().items() if pos == {True})

    def classify(self, min_families: int = 2) -> str:
        """Classify consensus: FRONTIER, PROBABLY_DEAD, or UNCORROBORATED.

        Invokes Rust host binary pfp_immune exclusion when available, retaining
        deterministic Python fallback for offline execution.
        """
        if type(min_families) is not int or min_families < 1:
            raise _refuse('MIN_FAMILIES_INVALID', 'min_families must be a positive int')
        if min_families == 2 and immune_host.is_available():
            try:
                positions = self.family_positions()
                votes = {}
                for fam, pos in positions.items():
                    votes[fam] = "EXCLUDE" if pos == {True} else "INCLUDE"
                res = immune_host.exclusion(votes, [self.exclusion_id])
                return res["consensus"]
            except (immune_host.ImmuneHostError, OSError, KeyError):
                pass  # noqa: S110
        positions = self.family_positions()
        if any(pos != {True} for pos in positions.values()):
            return FRONTIER
        return PROBABLY_DEAD if len(positions) >= min_families else UNCORROBORATED


@dataclass(frozen=True)
class RetestPlanV1:
    """Falsifiers to run, in order, and why the rest were not run."""
    order: tuple[str, ...]
    skipped: Mapping[str, str]
    classification: Mapping[str, str]
    cost: int
    budget: int
    authority_effect: str = AUTHORITY_NONE

    def to_dict(self) -> dict[str, Any]:
        return {'order': list(self.order), 'skipped': dict(self.skipped),
                'classification': dict(self.classification), 'cost': self.cost, 'budget': self.budget}


def _unique(hypotheses: Iterable[ExclusionHypothesisV1]) -> tuple[ExclusionHypothesisV1, ...]:
    out = tuple(hypotheses)
    ids = [h.exclusion_id for h in out]
    if len(ids) != len(set(ids)):
        raise _refuse('EXCLUSION_ID_DUPLICATE', 'exclusion ids must be unique')
    return out


def plan_retests(hypotheses: Iterable[ExclusionHypothesisV1], *, budget: int, dead_floor: int,
                 min_families: int = 2) -> RetestPlanV1:
    """Order falsifiers: frontier, then uncorroborated, then cheap probably-dead; cheapest first in a tier.

    A probably-dead exclusion costing more than ``dead_floor`` is skipped as
    ``DEAD_ABOVE_FLOOR``. Anything that no longer fits the budget is skipped as
    ``OVER_BUDGET``; a cheaper later item may still fit.
    """
    for name, value in (('budget', budget), ('dead_floor', dead_floor)):
        if type(value) is not int or value < 0:
            raise _refuse('RETEST_BUDGET_INVALID', f'{name} must be a nonnegative int')
    items = _unique(hypotheses)
    status = {h.exclusion_id: h.classify(min_families) for h in items}
    skipped: dict[str, str] = {}
    ranked = []
    for h in items:
        if status[h.exclusion_id] == PROBABLY_DEAD and h.falsifier_cost > dead_floor:
            skipped[h.exclusion_id] = DEAD_ABOVE_FLOOR
        else:
            ranked.append(h)
    ranked.sort(key=lambda h: (_TIER[status[h.exclusion_id]], h.falsifier_cost, h.exclusion_id))
    order: list[str] = []
    spent = 0
    for h in ranked:
        if spent + h.falsifier_cost > budget:
            skipped[h.exclusion_id] = OVER_BUDGET
            continue
        order.append(h.exclusion_id)
        spent += h.falsifier_cost
    return RetestPlanV1(tuple(order), dict(sorted(skipped.items())), status, spent, budget)


def settle(plan: RetestPlanV1, refuted: Mapping[str, bool]) -> dict[str, str]:
    """Final status per exclusion. Every planned falsifier must have a result, and only those."""
    if set(refuted) != set(plan.order):
        raise _refuse('RETEST_RESULTS_MISMATCH', 'results must cover exactly the planned falsifiers')
    if any(type(v) is not bool for v in refuted.values()):
        raise _refuse('RETEST_RESULTS_MISMATCH', 'each result must be a bool')
    out = dict(plan.classification)
    for exclusion_id, was_refuted in refuted.items():
        out[exclusion_id] = REFUTED if was_refuted else SURVIVED_TEST
    return out


def run_plan(plan: RetestPlanV1, hypotheses: Iterable[ExclusionHypothesisV1],
             falsify: Callable[[ExclusionHypothesisV1], bool]) -> dict[str, str]:
    """Run each planned falsifier in order with a host callable (True = refuted) and settle."""
    by_id = {h.exclusion_id: h for h in _unique(hypotheses)}
    results = {}
    for exclusion_id in plan.order:
        outcome = falsify(by_id[exclusion_id])
        if type(outcome) is not bool:
            raise _refuse('FALSIFIER_RESULT_INVALID', f'{exclusion_id} falsifier must return a bool')
        results[exclusion_id] = outcome
    return settle(plan, results)


@dataclass(frozen=True)
class HeadstoneExclusionPolicyV1:
    """Which cemetery kills are facts and which are hypotheses.

    ``host_seat_ids`` are deterministic host checks; their kills stay buried.
    ``family_of`` maps a model seat to its model family; an unknown seat is
    refused rather than guessed, because a wrong family would hide correlation.
    """
    host_seat_ids: frozenset[str]
    family_of: Mapping[str, str] = field(default_factory=dict)
    authority_effect: str = AUTHORITY_NONE


def headstone_exclusion(headstone: Any, policy: HeadstoneExclusionPolicyV1, *, falsifier: str,
                        falsifier_cost: int) -> ExclusionHypothesisV1 | None:
    """None for a host-killed candidate; otherwise an exclusion hypothesis the screen may retest.

    ``headstone`` needs ``headstone_id``, ``candidate_id``, ``cause_of_death``
    and ``killing_seat_id`` (as on ``pciv.domain.models.CemeteryHeadstoneV1``).
    """
    seat = _text(getattr(headstone, 'killing_seat_id', ''), 'killing_seat_id')
    if seat in policy.host_seat_ids:
        return None
    family = policy.family_of.get(seat)
    if family is None:
        raise _refuse('SEAT_FAMILY_UNKNOWN', f'seat {seat!r} has no model family')
    return ExclusionHypothesisV1(
        exclusion_id=_text(getattr(headstone, 'headstone_id', ''), 'headstone_id'),
        branch=_text(getattr(headstone, 'candidate_id', ''), 'candidate_id'),
        claim=_text(getattr(headstone, 'cause_of_death', ''), 'cause_of_death'),
        falsifier=falsifier, falsifier_cost=falsifier_cost,
        votes=(ExclusionVoteV1(seat, family, True),))


__all__ = [
    'CLASSIFICATIONS', 'DEAD_ABOVE_FLOOR', 'ExclusionHypothesisV1', 'ExclusionError', 'ExclusionVoteV1',
    'FRONTIER', 'HeadstoneExclusionPolicyV1', 'OVER_BUDGET', 'PROBABLY_DEAD', 'REFUTED', 'RetestPlanV1',
    'SURVIVED_TEST', 'UNCORROBORATED', 'headstone_exclusion', 'plan_retests', 'run_plan', 'settle',
]
