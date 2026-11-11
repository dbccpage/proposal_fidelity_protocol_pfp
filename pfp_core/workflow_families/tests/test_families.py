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
TARGET = {f'WF{n}' for n in range(6, 50)}
CASES = [(wf_id, name, expected) for wf_id, cls in REGISTRY.items()
         for name, (_bundle, expected) in cls().fixtures().items()]


@pytest.fixture(scope='module')
def audit_nodes():
    audit = json.loads((REPO_ROOT / 'dag' / 'reviews' / 'workflows_audit.json').read_text(encoding='utf-8'))
    return {n['id']: n for n in audit['registry']['family_nodes']}


def test_registry_covers_wf6_to_wf49_exactly():
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
