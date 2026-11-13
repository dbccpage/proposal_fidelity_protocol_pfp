"""Exclusions as hypotheses: falsifier required, family-counted agreement, retest planning."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from pfp_core.exclusions import (
    DEAD_ABOVE_FLOOR,
    FRONTIER,
    OVER_BUDGET,
    PROBABLY_DEAD,
    REFUTED,
    SURVIVED_TEST,
    UNCORROBORATED,
    ExclusionError,
    ExclusionHypothesisV1,
    ExclusionVoteV1,
    HeadstoneExclusionPolicyV1,
    headstone_exclusion,
    plan_retests,
    run_plan,
    settle,
)


def vote(seat: str, family: str, excludes: bool = True) -> ExclusionVoteV1:
    return ExclusionVoteV1(seat, family, excludes)


def hyp(eid: str, votes, cost: int = 1, falsifier: str = 'evaluate one witness') -> ExclusionHypothesisV1:
    return ExclusionHypothesisV1(eid, f'branch_{eid}', f'{eid} is dead', falsifier, cost, tuple(votes))


def test_an_exclusion_without_a_falsifier_is_refused():
    with pytest.raises(ExclusionError, match='EXCLUSION_WITHOUT_FALSIFIER'):
        hyp('a', [vote('s1', 'f1')], falsifier='  ')


def test_an_exclusion_nobody_proposes_is_refused():
    with pytest.raises(ExclusionError, match='EXCLUSION_WITHOUT_SUPPORT'):
        hyp('a', [vote('s1', 'f1', False)])


@pytest.mark.parametrize('cost', [-1, 1.0, True])
def test_falsifier_cost_must_be_a_nonnegative_int(cost):
    with pytest.raises(ExclusionError, match='FALSIFIER_COST_INVALID'):
        hyp('a', [vote('s1', 'f1')], cost=cost)


def test_authority_is_refused():
    with pytest.raises(ExclusionError, match='AUTHORITY_ESCALATION'):
        ExclusionHypothesisV1('a', 'b', 'c', 'd', 0, (vote('s', 'f'),), authority_effect='Host')


def test_seats_of_one_family_count_as_one_vote():
    h = hyp('a', [vote('s1', 'f1'), vote('s2', 'f1'), vote('s3', 'f1')])
    assert h.supporting_families() == ('f1',)
    assert h.classify(min_families=2) == UNCORROBORATED


def test_agreement_across_families_is_probably_dead():
    assert hyp('a', [vote('s1', 'f1'), vote('s2', 'f2')]).classify() == PROBABLY_DEAD


def test_cross_family_disagreement_is_frontier():
    assert hyp('a', [vote('s1', 'f1'), vote('s2', 'f2', False)]).classify() == FRONTIER


def test_a_family_that_splits_is_frontier_even_if_others_agree():
    votes = [vote('s1', 'f1'), vote('s2', 'f1', False), vote('s3', 'f2'), vote('s4', 'f3')]
    assert hyp('a', votes).classify() == FRONTIER


def test_min_families_must_be_positive():
    with pytest.raises(ExclusionError, match='MIN_FAMILIES_INVALID'):
        hyp('a', [vote('s1', 'f1')]).classify(0)


def test_plan_orders_frontier_then_uncorroborated_then_cheap_dead():
    dead = hyp('dead', [vote('s1', 'f1'), vote('s2', 'f2')], cost=1)
    lone = hyp('lone', [vote('s1', 'f1')], cost=1)
    front = hyp('front', [vote('s1', 'f1'), vote('s2', 'f2', False)], cost=3)
    plan = plan_retests([dead, lone, front], budget=10, dead_floor=2)
    assert plan.order == ('front', 'lone', 'dead')
    assert plan.cost == 5
    assert plan.classification == {'dead': PROBABLY_DEAD, 'lone': UNCORROBORATED, 'front': FRONTIER}


def test_dead_above_floor_is_skipped_but_cheap_dead_is_tested():
    cheap = hyp('cheap', [vote('s1', 'f1'), vote('s2', 'f2')], cost=2)
    dear = hyp('dear', [vote('s1', 'f1'), vote('s2', 'f2')], cost=3)
    plan = plan_retests([cheap, dear], budget=100, dead_floor=2)
    assert plan.order == ('cheap',)
    assert plan.skipped == {'dear': DEAD_ABOVE_FLOOR}


def test_budget_skips_what_does_not_fit_and_keeps_cheaper_later_items():
    a = hyp('a', [vote('s1', 'f1'), vote('s2', 'f2', False)], cost=2)
    b = hyp('b', [vote('s1', 'f1'), vote('s2', 'f2', False)], cost=5)
    c = hyp('c', [vote('s1', 'f1')], cost=1)
    plan = plan_retests([a, b, c], budget=3, dead_floor=0)
    assert plan.order == ('a', 'c')
    assert plan.skipped == {'b': OVER_BUDGET}
    assert plan.to_dict()['cost'] == 3


@pytest.mark.parametrize(('budget', 'floor'), [(-1, 0), (0, -1), (1.5, 0)])
def test_plan_refuses_a_bad_budget(budget, floor):
    with pytest.raises(ExclusionError, match='RETEST_BUDGET_INVALID'):
        plan_retests([], budget=budget, dead_floor=floor)


def test_duplicate_ids_are_refused():
    h = hyp('a', [vote('s1', 'f1')])
    with pytest.raises(ExclusionError, match='EXCLUSION_ID_DUPLICATE'):
        plan_retests([h, h], budget=5, dead_floor=5)


def test_settle_marks_refuted_and_survived_and_keeps_untested_classification():
    a = hyp('a', [vote('s1', 'f1')])
    b = hyp('b', [vote('s1', 'f1'), vote('s2', 'f2')])
    c = hyp('c', [vote('s1', 'f1'), vote('s2', 'f2')], cost=9)
    plan = plan_retests([a, b, c], budget=10, dead_floor=1)
    assert settle(plan, {'a': True, 'b': False}) == {'a': REFUTED, 'b': SURVIVED_TEST, 'c': PROBABLY_DEAD}


@pytest.mark.parametrize('results', [{}, {'a': True, 'x': False}, {'a': 1}])
def test_settle_requires_exactly_the_planned_results(results):
    plan = plan_retests([hyp('a', [vote('s1', 'f1')])], budget=1, dead_floor=0)
    with pytest.raises(ExclusionError, match='RETEST_RESULTS_MISMATCH'):
        settle(plan, results)


def test_run_plan_calls_the_falsifier_in_plan_order():
    seen = []
    hs = [hyp('a', [vote('s1', 'f1')], cost=2), hyp('b', [vote('s1', 'f1'), vote('s2', 'f2', False)], cost=2)]
    plan = plan_retests(hs, budget=4, dead_floor=0)

    def falsify(h):
        seen.append(h.exclusion_id)
        return h.exclusion_id == 'a'
    assert run_plan(plan, hs, falsify) == {'a': REFUTED, 'b': SURVIVED_TEST}
    assert seen == ['b', 'a']


def test_run_plan_refuses_a_non_bool_falsifier_result():
    hs = [hyp('a', [vote('s1', 'f1')])]
    plan = plan_retests(hs, budget=1, dead_floor=0)
    with pytest.raises(ExclusionError, match='FALSIFIER_RESULT_INVALID'):
        run_plan(plan, hs, lambda _h: 'yes')


def headstone(seat: str):
    return SimpleNamespace(headstone_id='hs1', candidate_id='cand1', cause_of_death='critic said wrong',
                           killing_seat_id=seat)


POLICY = HeadstoneExclusionPolicyV1(frozenset({'host_check'}), {'critic_a': 'family_a'})


def test_a_host_kill_stays_buried():
    assert headstone_exclusion(headstone('host_check'), POLICY, falsifier='rerun', falsifier_cost=1) is None


def test_a_model_kill_becomes_a_retestable_hypothesis():
    h = headstone_exclusion(headstone('critic_a'), POLICY, falsifier='rerun host check', falsifier_cost=1)
    assert (h.exclusion_id, h.branch, h.supporting_families()) == ('hs1', 'cand1', ('family_a',))
    assert h.classify() == UNCORROBORATED
    assert plan_retests([h], budget=1, dead_floor=0).order == ('hs1',)


def test_a_model_seat_without_a_family_is_refused():
    with pytest.raises(ExclusionError, match='SEAT_FAMILY_UNKNOWN'):
        headstone_exclusion(headstone('critic_z'), POLICY, falsifier='rerun', falsifier_cost=1)


@pytest.mark.parametrize(('seat', 'family'), [('', 'f'), ('s', ' ')])
def test_vote_fields_are_required(seat, family):
    with pytest.raises(ExclusionError, match='EXCLUSION_FIELD_EMPTY'):
        ExclusionVoteV1(seat, family, True)


def test_vote_excludes_must_be_bool():
    with pytest.raises(ExclusionError, match='EXCLUSION_FIELD_EMPTY'):
        ExclusionVoteV1('s', 'f', 1)
