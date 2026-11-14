"""WF56: what the workflow hands to the Rust host and reports back. Needs the ``pfp_operad`` binary."""
from __future__ import annotations

import json

from pfp.infrastructure import operad_host
from pfp_core import REPO_ROOT
from pfp_core.workflow_families.base import FixtureProposer, new_budget, prompt_leaks, run_fixture
from pfp_core.workflow_families.candidates import ANSWER_REJECTED, FOLDER, HostRunOperadCandidates

FAMILY = HostRunOperadCandidates()
EXAMPLE = REPO_ROOT / 'workflows' / FOLDER / 'examples' / 'product_by_coincidence.json'


def rows(out):
    return [(row['id'], row['disposition'], row.get('code')) for row in out.detail['candidates']['candidates']]


def test_the_verdict_and_every_disposition_are_the_hosts():
    out = run_fixture(FAMILY, 'an_unverified_extra_does_not_block')
    assert (out.verdict, out.code) == ('HOST_CERTIFIED', 'CANDIDATE_VERIFIED')
    assert rows(out) == [('add-the-list', 'HOST_VERIFIED', None), ('explain', 'UNVERIFIED_CANDIDATE', 'NO_BODY')]
    assert out.detail['candidates']['verified'] == ['add-the-list']
    assert out.host['certified_predicates'] == {
        'candidate_run_against_host_judge': True, 'answer_accepted_by_host_judge': True}


def test_a_probe_refuses_an_operation_that_agrees_on_the_task_case():
    out = run_fixture(FAMILY, 'product_agrees_only_on_the_task_case')
    assert (out.verdict, out.code) == ('REFUSED', 'CANDIDATE_REFUSED')
    assert rows(out) == [('multiply', 'REFUSED', 'RESULT_DIFFERS')]
    assert out.detail['candidates']['candidates'][0]['message'].startswith('case 1:')
    assert out.host['certified_predicates'] == {'candidate_run_against_host_judge': False}


def test_refusals_carry_the_hosts_code():
    codes = {name: run_fixture(FAMILY, name).code for name, (_bundle, expected) in FAMILY.fixtures().items()
             if expected == 'REFUSED'}
    assert codes == {
        'product_agrees_only_on_the_task_case': 'CANDIDATE_REFUSED',
        'signature_without_a_body': 'NO_VERIFIED_CANDIDATE',
        'colour_outside_the_task_colours': 'CANDIDATE_REFUSED',
        'verified_operation_with_a_wrong_answer': ANSWER_REJECTED,
        'body_outside_the_closed_list': 'BAD_REQUEST',
        'reply_that_marks_itself_verified': 'BAD_REQUEST',
        'reply_without_candidates': 'BAD_REQUEST',
    }


def test_a_wrong_answer_is_refused_after_its_candidate_was_verified():
    out = run_fixture(FAMILY, 'verified_operation_with_a_wrong_answer')
    assert rows(out) == [('add-the-list', 'HOST_VERIFIED', None)]
    assert out.host['certified_predicates'] == {
        'candidate_run_against_host_judge': True, 'answer_accepted_by_host_judge': False}


def test_the_prompt_carries_the_task_case_and_never_a_probe():
    bundle, _expected = FAMILY.fixtures()['list_sum_is_verified']
    prompt = FAMILY.prompt(bundle['task'])
    assert '"case":{"values":[1,2,3]}' in prompt and '"bodies"' in prompt and '"colours"' in prompt
    assert 'probes' not in prompt and '[4,-1,6]' not in prompt and 'checker' not in prompt
    assert not prompt_leaks(prompt, bundle['sealed'])


def test_no_reply_and_a_reply_that_is_not_an_object_are_refused():
    bundle, _expected = FAMILY.fixtures()['list_sum_is_verified']

    def run(replies):
        budget = new_budget('WF56:replies', bundle['task'])
        try:
            return FAMILY.execute(bundle, budget=budget, proposer=FixtureProposer(replies))
        finally:
            budget.close()
    assert run([]).code == 'NO_ADMISSIBLE_REPLY'
    assert run(['add them']).code == 'BAD_REQUEST'


def test_the_shipped_example_is_the_fixture_request_and_the_host_refuses_it():
    request = json.loads(EXAMPLE.read_text(encoding='utf-8'))
    bundle, _expected = FAMILY.fixtures()['product_agrees_only_on_the_task_case']
    assert request['cases'] == [bundle['task']['case'], *bundle['sealed']['probes']]
    outcome = operad_host.outcome('run', request)
    assert (outcome['status'], outcome['result']['verdict']) == ('FAIL', 'CANDIDATE_REFUSED')
    assert outcome['result']['verified'] == ['add-the-list']
