"""Public synthetic algebra only; no seed solutions, secrets, network or graders."""
from copy import deepcopy
import json

import pytest

from rational_panel import (ArtifactError, CONTRACT_SHA256, LIMITS, VARIABLES,
                            WorkBudget, candidate, check_panel, fixed_panel, rational)


SEED = 'a' * 64


def q(value): return {'op': 'q', 'value': f'{value}/1'}
def var(name='J'): return {'op': 'var', 'name': name}
def binary(op, left, right): return {'op': op, 'left': left, 'right': right}


def envelope(**fields):
    return {'schema_version': '1.0', 'seed_sha256': SEED, 'contract_sha256': CONTRACT_SHA256, **fields}


def claim(lhs=None, rhs=None, guards=None):
    return {'id': 'identity', 'obligation_id': '5', 'kind': 'forall_real_equality',
            'guards': [] if guards is None else guards, 'lhs': var() if lhs is None else lhs,
            'rhs': var() if rhs is None else rhs}


def proposal(claims=None):
    return envelope(answer_text='Synthetic algebra fixture; not a solution to the seed.',
                    claims=[claim()] if claims is None else claims)


def challenge(value=2, **values):
    assignment = {name: '0/1' for name in VARIABLES}
    assignment['J'] = f'{value}/1'; assignment.update(values)
    return envelope(challenges=[{'id': 'probe', 'obligation_id': '5', 'assignment': assignment}])


def check(proposed, challenged=None):
    return check_panel(json.dumps(proposed), json.dumps(challenged or challenge()), SEED)[0]


def test_exact_counterexample_and_finite_pass_have_different_meanings():
    wrong = proposal([claim(binary('mul', var(), var()), var())])
    failed = check(wrong)
    assert failed['checks'][0]['status'] == 'REFUTED_ENCODED_EQUALITY'
    assert (failed['checks'][0]['lhs'], failed['checks'][0]['rhs']) == ('4/1', '2/1')
    passed = check(wrong, challenge(1))
    assert passed['claims'][0]['status'] == 'FINITE_CHECKS_PASSED_NOT_PROVED'
    assert passed['claims'][0]['semantic_alignment'] == 'OPEN'
    assert passed['all_requested_obligations_remain_uncertified']
    assert passed['accuracy_status'] == 'UNSCORED'


def test_exact_fraction_arithmetic_without_binary_float():
    third = {'op': 'q', 'value': '1/3'}
    expression = binary('mul', third, q(3))
    assert check(proposal([claim(expression, q(1))]))['checks'][0]['lhs'] == '1/1'


def test_guarded_division_and_sufficient_antecedent_false_are_not_refuted():
    guard = {'left': var(), 'relation': 'ne', 'right': q(0)}
    proposed = proposal([claim(binary('div', var(), var()), q(1), [guard])])
    assert check(proposed, challenge(0))['checks'][0]['status'] == 'GUARD_FALSE_NOT_A_COUNTEREXAMPLE'
    assert check(proposed, challenge(2))['checks'][0]['status'] == 'EXACT_POINT_PASS_NOT_PROOF'


def test_undefined_claim_and_guard_remain_distinct():
    quotient = binary('div', var(), var())
    report = check(proposal([claim(quotient, q(1))]), challenge(0))
    assert report['checks'][0]['status'] == 'UNDEFINED_AT_ADMISSIBLE_POINT'
    guard = {'left': quotient, 'relation': 'eq', 'right': q(1)}
    report = check(proposal([claim(q(0), q(1), [guard])]), challenge(0))
    assert report['checks'][0]['status'] == 'UNKNOWN_GUARD_UNDEFINED'


@pytest.mark.parametrize('coordinate', ['t', 'beta'])
def test_out_of_public_domain_witness_is_inapplicable(coordinate):
    report = check(proposal([claim(q(0), q(1))]), challenge(**{coordinate: '-1/1'}))
    assert report['checks'][0]['status'] == 'OUTSIDE_PUBLIC_DOMAIN'
    assert report['claims'][0]['status'] == 'OPEN_UNSUPPORTED_OR_UNTESTED'


def test_partial_base_is_checked_under_zero_power():
    expr = {'op': 'pow', 'base': binary('div', q(1), q(0)), 'exponent': 0}
    assert check(proposal([claim(expr, q(1))]))['checks'][0]['status'] == 'UNDEFINED_AT_ADMISSIBLE_POINT'


@pytest.mark.parametrize('value', [True, 1, 0.5, '1', '1/0', '2/2', '-0/1', '01/1', '1/-2', ' 1/2', '1e3/1', f'{2**128}/1'])
def test_rational_wire_rejects_ambiguous_or_oversized_values(value):
    with pytest.raises(ArtifactError): rational(value)


@pytest.mark.parametrize('raw', [
    '{"schema_version":"1.0","schema_version":"1.0"}',
    '{"unused":NaN}', '{"unused":1.5}', '```json\n{}\n```',
    '[' * 2000 + ']' * 2000,
])
def test_malformed_json_never_becomes_empty_accepted_evidence(raw):
    receipt, answer = check_panel(raw, json.dumps(challenge()), SEED)
    assert receipt['artifact_errors']['candidate']
    assert receipt['claims'] == [] and answer == raw
    assert receipt['missing_obligation_ids'] == ['1', '2', '3', '4', '5']


@pytest.mark.parametrize('mutation', ['seed', 'contract', 'duplicate_id', 'unknown_obligation', 'extra_verdict', 'float', 'bool_exponent', 'unknown_operator', 'unknown_variable'])
def test_candidate_binding_and_language_are_fail_closed(mutation):
    obj = proposal()
    if mutation == 'seed': obj['seed_sha256'] = 'b' * 64
    elif mutation == 'contract': obj['contract_sha256'] = 'b' * 64
    elif mutation == 'duplicate_id': obj['claims'] *= 2
    elif mutation == 'unknown_obligation': obj['claims'][0]['obligation_id'] = '6'
    elif mutation == 'extra_verdict': obj['verdict'] = 'CERTIFIED'
    elif mutation == 'float': obj['claims'][0]['lhs'] = {'op': 'q', 'value': 0.5}
    elif mutation == 'bool_exponent': obj['claims'][0]['lhs'] = {'op': 'pow', 'base': var(), 'exponent': True}
    elif mutation == 'unknown_operator': obj['claims'][0]['lhs'] = {'op': 'eval', 'code': 'arbitrary code'}
    elif mutation == 'unknown_variable': obj['claims'][0]['lhs'] = var('hidden_formula')
    assert check(obj)['artifact_errors']['candidate']


def test_empty_and_unsupported_evidence_leave_obligations_open():
    empty = check(proposal([]))
    assert len(empty['missing_obligation_ids']) == 5 and empty['claims'] == []
    unsupported = check(proposal([{'id': 'analytic', 'obligation_id': '3', 'kind': 'unsupported', 'reason': 'Logarithm outside the language.'}]))
    assert unsupported['claims'][0]['status'] == 'OPEN_UNSUPPORTED_OR_UNTESTED'
    assert unsupported['checks'] == []


def test_wrong_obligation_target_cannot_supply_evidence_for_a_claim():
    probes = challenge(); probes['challenges'][0]['obligation_id'] = '1'
    report = check(proposal([claim(q(0), q(1))]), probes)
    assert report['checks'] == [] and report['claims'][0]['status'] == 'OPEN_UNSUPPORTED_OR_UNTESTED'


@pytest.mark.parametrize('mutation', ['missing_variable', 'extra_variable', 'duplicate_id', 'expected_answer', 'too_many'])
def test_challenge_schema_refuses_incomplete_or_untrusted_extra_data(mutation):
    probes = challenge()
    if mutation == 'missing_variable': probes['challenges'][0]['assignment'].pop('K')
    elif mutation == 'extra_variable': probes['challenges'][0]['assignment']['expected'] = '0/1'
    elif mutation == 'duplicate_id': probes['challenges'] *= 2
    elif mutation == 'expected_answer': probes['challenges'][0]['expected_answer'] = True
    elif mutation == 'too_many': probes['challenges'] *= 13
    report = check(proposal(), probes)
    assert report['artifact_errors']['panel'] and report['checks'] == []


def test_depth_and_work_caps_yield_open_results(monkeypatch):
    expr = var()
    for _ in range(18): expr = {'op': 'pow', 'base': expr, 'exponent': 1}
    assert check(proposal([claim(expr)]))['artifact_errors']['candidate'] == 'EXPRESSION_TOO_LARGE'
    monkeypatch.setitem(LIMITS, 'max_steps', 1)
    report = check(proposal())
    assert report['artifact_errors']['candidate'] == 'HOST_RESOURCE_LIMIT'


def test_intermediate_integer_size_is_bounded():
    expr = q(2)
    for _ in range(5): expr = {'op': 'pow', 'base': expr, 'exponent': 8}
    report = check(proposal([claim(expr, q(0))]))
    assert report['checks'][0]['status'] == 'UNKNOWN_RESOURCE_LIMIT'


def test_fixed_panel_has_twelve_valid_bound_probes_and_no_expected_values():
    probes = fixed_panel(SEED)
    assert len(probes['challenges']) == 12
    assert not check(proposal(), probes)['artifact_errors']
    assert {c['obligation_id'] for c in probes['challenges']} == {'1', '2', '3', '4', '5'}


def test_candidate_source_and_prose_not_modified_by_checking():
    obj = proposal(); before = deepcopy(obj)
    text = json.dumps(obj)
    _, answer = check_panel(text, json.dumps(challenge()), SEED)
    assert obj == before and answer == obj['answer_text']
    assert candidate(text, SEED, WorkBudget()) == obj


@pytest.mark.parametrize('field', ['answer_text', 'reason'])
def test_json_escaped_lone_surrogate_is_rejected_before_answer_extraction(field):
    obj = proposal()
    if field == 'answer_text': obj[field] = '\ud800'
    else: obj['claims'] = [{'id': 'unsupported', 'kind': 'unsupported', 'obligation_id': '3', 'reason': '\udfff'}]
    raw = json.dumps(obj)  # Raw transport bytes are valid ASCII/UTF-8.
    receipt, answer = check_panel(raw, json.dumps(challenge()), SEED)
    assert receipt['artifact_errors']['candidate'] == 'INVALID_UNICODE_TEXT'
    assert answer == raw and answer.encode('utf-8')


@pytest.mark.parametrize('raw', [17, True, {}, [], '\ud800'])
def test_public_checker_rejects_nontext_or_nonencodable_artifact_before_hashing(raw):
    receipt, answer = check_panel(raw, json.dumps(challenge()), SEED)
    assert receipt['artifact_errors']['candidate']
    assert receipt['candidate_sha256'] is None and answer is None
