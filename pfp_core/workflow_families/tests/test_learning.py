"""WF55: what the workflow carries to and from the Rust host. Needs the ``pfp_operad`` binary."""
from __future__ import annotations

from pfp_core.workflow_families.base import REFUSED, FixtureProposer, new_budget, run_fixture
from pfp_core.workflow_families.learning import EXAMPLE_LEDGER, FailureLedgerTrialGatedRules, lines

FAMILY = FailureLedgerTrialGatedRules()
FIRST = 'rule_admitted_on_a_winning_trial'
LATER = 'later_run_loads_the_admitted_rule'
SIGN_RULE = 'A minus sign belongs to its number. Subtract a negative value; do not add it.'


class Recording(FixtureProposer):
    """Fixture replies, with every request kept."""

    def __init__(self, replies):
        super().__init__(replies)
        self.requests = []

    def propose(self, request):
        self.requests.append(request)
        return super().propose(request)


def recorded(name, replies=None):
    bundle, _expected = FAMILY.fixtures()[name]
    proposer = Recording(bundle['replies'] if replies is None else replies)
    budget = new_budget(f'WF55:{name}', bundle['task'])
    try:
        return FAMILY.execute(bundle, budget=budget, proposer=proposer), proposer.requests
    finally:
        budget.close()


def test_the_shipped_ledger_is_the_one_the_first_run_leaves():
    out = run_fixture(FAMILY, FIRST)
    assert out.detail['ledger'] == lines(EXAMPLE_LEDGER)
    assert [rule['id'] for rule in out.detail['admitted']] == ['keep-the-sign']
    assert out.detail['loaded'] == []


def test_the_outcome_reports_the_hosts_trial_not_a_count_made_here():
    out = run_fixture(FAMILY, FIRST)
    trial = out.detail['trial']
    assert trial['record'] == {'kind': 'trial', 'candidate': 'keep-the-sign', 'held_out': ['h1', 'h2', 'h3'],
                               'baseline_correct': 1, 'treated_correct': 3, 'clean_panel_hits': 0}
    assert [(row['id'], row['baseline'], row['treated']) for row in trial['cases']] == [
        ('h1', False, True), ('h2', False, True), ('h3', True, True)]
    assert list(out.host['certified_predicates']) == [
        'ledger_chain_replayed', 'failure_witnessed:f1', 'failure_recorded:f1', 'failure_witnessed:f2',
        'failure_recorded:f2', 'rule_recorded', 'trial_judged', 'trial_recorded',
        'rule_admitted_on_its_latest_trial']


def test_each_case_is_asked_without_the_proposed_rule_and_then_with_it():
    out, requests = recorded(FIRST)
    assert [request.stage for request in requests] == [
        'propose', 'baseline:h1', 'treated:h1', 'baseline:h2', 'treated:h2', 'baseline:h3', 'treated:h3']
    assert out.budget['calls'] == 7
    propose, baseline, treated = requests[0], requests[1], requests[2]
    assert '"total":11' in propose.prompt and '"id":"f2"' in propose.prompt
    assert baseline.prompt.endswith('{"case":{"values":[8,-3]},"rules":[]}')
    assert treated.prompt.endswith('{"case":{"values":[8,-3]},"rules":["' + SIGN_RULE + '"]}')
    assert baseline.prompt.startswith('WF55 Add the integers in values.')


def test_a_later_run_loads_the_admitted_rule_into_every_prompt():
    out, requests = recorded(LATER)
    solving = [request for request in requests if request.stage != 'propose']
    assert solving and all(SIGN_RULE in request.prompt for request in solving)
    second = 'Read each value with its sign before adding.'
    assert [second in request.prompt for request in solving] == [False, True, False, True]
    assert out.detail['loaded'] == [SIGN_RULE]
    assert [rule['id'] for rule in out.detail['admitted']] == ['check-each-sign', 'keep-the-sign']
    assert out.detail['ledger'][:5] == lines(EXAMPLE_LEDGER)


def test_a_rejected_rule_stays_in_the_ledger_and_is_not_loaded():
    out = run_fixture(FAMILY, 'no_gain_is_not_earned')
    assert (out.verdict, out.code) == (REFUSED, 'NOT_EARNED')
    assert out.detail['admitted'] == []
    assert [line.count('"kind":"trial"') for line in out.detail['ledger']] == [0, 0, 0, 1]
    assert out.host['certified_predicates']['rule_admitted_on_its_latest_trial'] is False
    assert out.detail['trial']['record']['baseline_correct'] == 1


def test_a_missing_reply_is_judged_by_the_host_as_a_wrong_answer():
    bundle, _expected = FAMILY.fixtures()[FIRST]
    out, requests = recorded(FIRST, bundle['replies'][:2])
    assert len(requests) == 7
    assert out.code == 'NOT_EARNED'
    assert out.detail['trial']['record']['treated_correct'] == 0
    none, _requests = recorded(FIRST, [])
    assert (none.verdict, none.code) == (REFUSED, 'NO_ADMISSIBLE_REPLY')
    assert len(none.detail['ledger']) == 2


def test_a_refused_failure_or_ledger_stops_the_run_before_any_model_call():
    for name, code, kept in (('a_correct_answer_is_not_a_failure', 'NOT_A_FAILURE', 0),
                             ('edited_ledger_is_refused', 'CHAIN_BROKEN', 5)):
        out, requests = recorded(name)
        assert (out.verdict, out.code, requests) == (REFUSED, code, [])
        assert len(out.detail['ledger']) == kept
    broken = run_fixture(FAMILY, 'edited_ledger_is_refused')
    assert broken.detail['admitted'] is None
    assert broken.host['certified_predicates'] == {'ledger_chain_replayed': False}


def test_a_proposal_cannot_choose_its_record_kind_or_its_sources():
    kind = run_fixture(FAMILY, 'rule_that_names_its_own_admission')
    assert (kind.code, len(kind.detail['ledger'])) == ('BAD_REQUEST', 2)
    source = run_fixture(FAMILY, 'rule_from_an_unrecorded_failure')
    assert (source.code, len(source.detail['ledger'])) == ('UNKNOWN_FAILURE', 2)
    _out, requests = recorded(FIRST, ['not a rule'])
    assert [request.stage for request in requests] == ['propose']


def test_a_trial_that_reuses_a_source_failure_is_refused_with_its_detail():
    out = run_fixture(FAMILY, 'trial_on_the_failures_the_rule_came_from')
    assert (out.verdict, out.code) == (REFUSED, 'SPLIT_OVERLAP')
    assert out.detail['rule']['id'] == 'keep-the-sign'
    assert out.detail['trial']['record']['held_out'] == ['f1']
    assert len(out.detail['ledger']) == 3
