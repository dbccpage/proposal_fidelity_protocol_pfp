"""One parametrized suite for every registered workflow family."""
from __future__ import annotations

import json

import pytest

from pfp_core import REPO_ROOT
from pfp_core.workflow_families import base, load
from pfp_core.workflow_families.base import (
    POSITIVE,
    REFUSED,
    FixtureProposer,
    Proposal,
    SealedLeakError,
    Usage,
    WorkflowFamilySpecV1,
    new_budget,
    run_fixture,
)

REGISTRY = load()
TARGET = {f'WF{n}' for n in range(6, 50)} | {'WF51', 'WF55', 'WF56', 'WF57'}
CASES = [(wf_id, name, expected) for wf_id, cls in REGISTRY.items()
         for name, (_bundle, expected) in cls().fixtures().items()]


@pytest.fixture(scope='module')
def audit_nodes():
    audit = json.loads((REPO_ROOT / 'dag' / 'reviews' / 'workflows_audit.json').read_text(encoding='utf-8'))
    return {n['id']: n for n in audit['registry']['family_nodes']}


def test_registry_covers_wf6_to_wf49_wf51_and_wf55_to_wf57_exactly():
    assert set(REGISTRY) == TARGET


@pytest.mark.parametrize('wf_id', sorted(REGISTRY))
def test_spec_matches_the_dag_node(wf_id, audit_nodes):
    spec, node = REGISTRY[wf_id].spec, audit_nodes[wf_id]
    assert (spec.name, spec.layer, list(spec.depends_on), spec.merge_into, spec.folder) == (
        node['name'], node['layer'], node['depends_on'], node['merge_into'], node['path'])
    assert spec.authority_effect == 'None'
    assert (REPO_ROOT / spec.folder).is_dir()


@pytest.mark.parametrize('wf_id', sorted(REGISTRY))
def test_every_family_has_a_positive_and_an_adversarial_fixture(wf_id):
    expected = [e for _b, e in REGISTRY[wf_id]().fixtures().values()]
    assert any(e in POSITIVE for e in expected)
    assert REFUSED in expected


@pytest.mark.parametrize(('wf_id', 'name', 'expected'), CASES)
def test_fixture_verdict(wf_id, name, expected):
    family = REGISTRY[wf_id]()
    first = run_fixture(family, name)
    again = run_fixture(family, name)
    assert first.verdict == expected, (first.code, first.detail, first.host)
    assert first.receipt_sha256 == again.receipt_sha256
    assert first.budget['spent_microusd'] == 0
    assert first.authority_effect == 'None'
    if expected in POSITIVE and first.host['certified_predicates']:
        assert not [k for k, v in first.host['certified_predicates'].items() if not v]


def test_authority_escalation_is_refused():
    with pytest.raises(ValueError, match='AUTHORITY_ESCALATION'):
        WorkflowFamilySpecV1('WF7', 'x', 1, (), None, 'c', 'workflows/wf07_typed_refusal', authority_effect='Host')


def test_a_prompt_carrying_a_sealed_literal_never_dispatches():
    family = REGISTRY['WF7']()
    bundle = {'task': {'statement': 'secret 98765', 'A': [[1]], 'b': [1]}, 'sealed': {'expected': 98765},
              'replies': [{'answer': [1]}]}
    budget = new_budget('leak', bundle['task'])
    with pytest.raises(SealedLeakError):
        family.execute(bundle, budget=budget)
    assert budget.summary()['calls'] == 0


def test_a_priced_reply_is_refused_by_the_zero_spend_budget():
    family = REGISTRY['WF7']()
    bundle, _ = family.fixtures()['solvable_answered']
    priced = FixtureProposer([Proposal({'answer': [2, 1]}, Usage(quote_microusd=50, actual_microusd=40))])
    out = family.execute(bundle, budget=new_budget('priced', bundle['task']), proposer=priced)
    assert out.verdict == REFUSED and out.budget['spent_microusd'] == 0
    assert out.transcript[-1]['reply'] == 'BUDGET_REFUSED'


def test_canonical_rejects_floats_as_fractions():
    with pytest.raises(base.MalformedCandidateError):
        base.as_fraction('0.5', 'x')
    assert base.as_fraction('1/2', 'x') == base.Fraction(1, 2)


def test_wiki_pages_and_dag_records_are_current():
    from pfp_core.workflow_families import docs
    assert docs.build(check=True) == []


def test_a_private_name_in_a_source_field_is_refused(audit_nodes):
    from pfp_core.workflow_families import docs
    private = 'run it on the ' + 'om' + 'ega' + '_engine host'
    node = {**audit_nodes['WF7'], 'process': ['Freeze the task', private]}
    with pytest.raises(ValueError, match=r"WF7: field 'process'"):
        docs.render(REGISTRY['WF7'], node, [])
    with pytest.raises(ValueError, match='readme'):
        docs.guard('WF7', 'readme block', 'see the ' + 'wo' + 'land gate')
    # The Greek letter as a math symbol is not a name.
    sym = 'om' + 'ega'
    math = f'\\{sym}_1 and {sym}_2 and {sym}1'
    assert docs.guard('WF7', 'math', math) == math


def test_a_readme_without_the_generated_markers_is_refused():
    from pfp_core.workflow_families import docs
    block = docs.render_readme_block(REGISTRY['WF7'])
    with pytest.raises(ValueError, match='WF7: README lacks'):
        docs.splice_readme('WF7', '# WF7: Typed refusal\n\nhand-written\n', block)
    spliced = docs.splice_readme('WF7', f'# WF7\n\n{docs.README_BEGIN}\nold\n{docs.README_END}\n\nkept\n', block)
    assert spliced == f'# WF7\n\n{block}\n\nkept\n'


def test_every_generated_readme_block_is_current_and_says_runnable_offline():
    from pfp_core.workflow_families import docs
    for wf_id in sorted(docs.README_BLOCK_IDS):
        cls = REGISTRY[wf_id]
        text = (REPO_ROOT / cls.spec.folder / 'README.md').read_text(encoding='utf-8')
        assert docs.render_readme_block(cls) in text.replace('\r\n', '\n'), wf_id
        assert 'no runner and no run yet' not in text, wf_id


def test_drift_in_the_index_or_the_dag_status_is_reported():
    from pfp_core.workflow_families import docs
    reg = {'WF7': REGISTRY['WF7']}
    index = '| WF | Workflow | Status |\n| --- | --- | --- |\n| 7 | [Typed refusal](x) | runnable offline |\n'
    dag = {'nodes': [{'id': 'WF7', 'status': docs.DAG_STATUS}]}
    assert docs.drift(reg, index, dag) == []
    assert docs.drift(reg, index.replace('runnable offline', 'proposal'), dag) == [
        "workflows/README.md#WF7: status 'proposal', expected 'runnable offline'"]
    assert docs.drift(reg, index, {'nodes': [{'id': 'WF7', 'status': 'proposal'}]}) == [
        "workflows/dag/workflow_dag.json#WF7: status 'proposal', expected 'implemented_offline'"]


def test_an_unaffordable_call_is_never_dispatched():
    from pfp_core.workflow_families.base import CallableProposer
    calls = []

    def fn(prompt):
        calls.append(prompt)
        return {'answer': [2, 1]}, Usage(actual_microusd=900)
    family = REGISTRY['WF7']()
    bundle, _ = family.fixtures()['solvable_answered']
    out = family.execute(bundle, budget=new_budget('dear', bundle['task']),
                         proposer=CallableProposer(fn, quote_microusd=1_000_000))
    assert calls == [] and out.verdict == REFUSED and out.budget['spent_microusd'] == 0


def test_a_short_sealed_answer_is_caught_as_a_whole_token():
    family = REGISTRY['WF7']()
    bundle = {'task': {'statement': 'the answer is 42', 'A': [[1]], 'b': [1]}, 'sealed': {'answer': 42},
              'replies': [{'answer': [1]}]}
    with pytest.raises(SealedLeakError):
        family.execute(bundle, budget=new_budget('short', bundle['task']))
    bundle['task']['statement'] = 'the answer is 421'
    assert family.execute(bundle, budget=new_budget('ok', bundle['task'])).verdict == 'HOST_CERTIFIED'


HOSTED = {wf_id: cls for wf_id, cls in REGISTRY.items() if issubclass(cls, base.HostedFamily)}


def test_the_rust_host_lists_every_hosted_family_under_the_registry_s_names():
    from pfp.infrastructure import operad_host
    listed = operad_host.result(operad_host.call(('family', 'list')))['families']
    assert listed == [{'workflow': wf_id, 'name': cls.spec.name, 'host_check': cls.spec.host_check_id}
                      for wf_id, cls in HOSTED.items()]
    assert set(HOSTED) == {'WF7', 'WF9', 'WF10', 'WF11', 'WF13', 'WF20', 'WF24', 'WF25', 'WF26', 'WF27', 'WF30',
                           'WF31', 'WF32', 'WF33', 'WF38', 'WF40', 'WF45', 'WF46', 'WF47'}


@pytest.mark.parametrize('wf_id', sorted(HOSTED))
def test_a_hosted_family_holds_no_check_of_its_own(wf_id):
    cls = HOSTED[wf_id]
    for name in ('validate', 'check', 'run', 'prompt', 'execute', '_host', '_verdict'):
        assert name not in vars(cls), f'{wf_id} overrides {name}'
    assert set(vars(cls)) - {'__module__', '__doc__', '__qualname__', '__firstlineno__', '__static_attributes__',
                             '__annotations__'} <= {'spec', 'fixtures'}


def test_a_hosted_family_refuses_a_malformed_task_before_any_proposal():
    from pfp_core.workflow_families.base import CallableProposer
    calls = []

    def fn(prompt):
        calls.append(prompt)
        return {'answer': [1]}, Usage()
    family = REGISTRY['WF7']()
    bundle = {'task': {'A': [[1, 2], [3]], 'b': [1, 2]}}
    budget = new_budget('WF7:ragged', bundle['task'])
    with pytest.raises(base.MalformedCandidateError, match='rectangular'):
        family.execute(bundle, budget=budget, proposer=CallableProposer(fn, quote_microusd=0))
    assert calls == [] and budget.summary()['calls'] == 0


def test_a_hosted_family_asks_exactly_what_the_host_wrote():
    from pfp_core.workflow_families.base import CallableProposer
    prompts = []

    def fn(prompt):
        prompts.append(prompt)
        return {'coefficients': [1, 0, 2]}, Usage()
    family = REGISTRY['WF31']()
    bundle, _ = family.fixtures()['held_out_winner']
    out = family.execute(bundle, budget=new_budget('WF31:host', bundle['task']),
                         proposer=CallableProposer(fn, quote_microusd=0))
    assert out.verdict == 'HOST_CERTIFIED' and out.code == 'WINNER_SELECTED'
    assert [t['stage'] for t in out.transcript] == ['proposer:0', 'proposer:1', 'proposer:2']
    assert len(set(prompts)) == 1 and prompts[0].startswith('WF31 Multi-agent tournament')
    assert 'held_out' not in prompts[0]
    assert {t['request_sha256'] for t in out.transcript} == {base.sha256_hex(prompts[0])}
    assert out.host['certified_predicates'] == {'splits_disjoint': True, 'winner_beats_baseline': True}
    assert out.host['final_output_certified'] is True


def test_what_the_host_leaves_unchecked_keeps_the_run_from_being_fully_certified():
    family = REGISTRY['WF32']()
    scoped = run_fixture(family, 'checked_claims_admitted_rest_open')
    assert (scoped.verdict, scoped.code) == ('HOST_CERTIFIED', 'CLAIM_SCOPED')
    assert scoped.host['uncertified_obligations'] == ['c3', 'c4']
    assert scoped.host['final_output_certified'] is False
    full = run_fixture(family, 'every_claim_checked')
    assert (full.verdict, full.code) == ('HOST_CERTIFIED', 'ALL_CLAIMS_ADMITTED')
    assert full.host['uncertified_obligations'] == [] and full.host['final_output_certified'] is True


def test_a_battery_asks_one_capsule_at_a_time_and_counts_a_missing_reply():
    family = REGISTRY['WF13']()
    out = run_fixture(family, 'dropped_capsule_keeps_denominator')
    assert [t['stage'] for t in out.transcript] == ['capsule:stab5', 'capsule:stab3', 'capsule:anom', 'capsule:comm',
                                                    'capsule:refuse']
    assert out.verdict == 'REFUSED' and out.detail['denominator'] == 5
    assert out.host['certified_predicates']['capsule:refuse'] is False


def test_a_sealed_value_in_a_hosted_task_is_refused_by_the_host_and_never_dispatched():
    family = REGISTRY['WF31']()
    bundle, _ = family.fixtures()['held_out_winner']
    leaky = {**bundle, 'task': {**bundle['task'], 'statement': 'One held-out value is 51.'},
             'sealed': {'held_out': bundle['sealed']['held_out'], 'answer': 51}}
    budget = new_budget('WF31:leak', leaky['task'])
    with pytest.raises(SealedLeakError, match='proposer:0'):
        family.execute(leaky, budget=budget)
    assert budget.summary()['calls'] == 0


def test_the_python_guard_of_the_unported_families_reads_a_closing_mark_as_the_host_does():
    assert base.prompt_leaks('The total is 42.', {'answer': 42})
    assert base.prompt_leaks('Is it 42?', {'answer': 42})
    assert not base.prompt_leaks('p = .42 and 42.5', {'answer': 42})
    assert not base.prompt_leaks('The total is 42.', {'note': 42})
    assert base.prompt_leaks('choose a.?', {'answer': 'a.'})
    assert not base.prompt_leaks('choose a', {'answer': 'a.'})


XOR_FAMILIES = ['WF9', 'WF20', 'WF27', 'WF33']


@pytest.mark.parametrize('wf_id', XOR_FAMILIES)
@pytest.mark.parametrize('label', [0.9, 0.0, 1.0, '0', '1', True, False, 2, -1, None])
def test_a_non_binary_edge_label_is_refused_before_any_proposal(wf_id, label):
    # Regression: int(x) % 2 read 0.9 as 0 and certified the empty repair of a different task.
    from pfp_core.workflow_families.base import CallableProposer
    calls = []

    def fn(prompt):
        calls.append(prompt)
        return {'flip': []}, Usage()
    family = REGISTRY[wf_id]()
    bundle = {'task': {'statement': 'Flip the fewest labels.', 'edges': [[0, 1], [1, 2], [2, 0]],
                       'labels': [label, 0, 0], 'fuel': 9}, 'replies': [{'flip': []}]}
    budget = new_budget(f'{wf_id}:label', bundle['task'])
    with pytest.raises(base.MalformedCandidateError, match='exact integer 0 or 1'):
        family.execute(bundle, budget=budget, proposer=CallableProposer(fn, quote_microusd=0))
    assert calls == [] and budget.summary()['calls'] == 0


@pytest.mark.parametrize('label', [float('nan'), float('inf')])
def test_a_label_that_is_not_json_never_reaches_the_host(label):
    family = REGISTRY['WF9']()
    bundle = {'task': {'edges': [[0, 1], [1, 2], [2, 0]], 'labels': [label, 0, 0]}, 'replies': [{'flip': []}]}
    budget = new_budget('WF9:nan', bundle['task'])
    with pytest.raises(ValueError, match='not JSON compliant'):
        family.execute(bundle, budget=budget)
    assert budget.summary()['calls'] == 0


@pytest.mark.parametrize('edges', [[[0, 1], [1, 2], [2, 0, 5]], [[0, 1], [1, 2], 'ab']])
def test_a_malformed_edge_is_refused_before_any_proposal(edges):
    family = REGISTRY['WF9']()
    bundle = {'task': {'edges': edges, 'labels': [1, 0, 0]}, 'replies': [{'flip': []}]}
    with pytest.raises(base.MalformedCandidateError, match='each edge is a pair'):
        family.execute(bundle, budget=new_budget('WF9:edge', bundle['task']))


@pytest.mark.parametrize('wf_id', XOR_FAMILIES)
def test_exact_binary_labels_are_still_admitted(wf_id):
    family = REGISTRY[wf_id]()
    task = {'edges': [[0, 1], [1, 2], [2, 0]], 'labels': [1, 0, 0], 'fuel': 9}
    assert family.validate(task) is task
