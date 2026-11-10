"""Synthetic transport tests only; this module never opens a network connection."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile

import pytest

from budget_ledger import BudgetError
from campaign_ledger import CampaignAdmission, CampaignLedger, validate_manifest
from openrouter_provider import OpenRouterProvider, ProviderError, NoRedirect, parse_json, price_ceiling
from reference_runner import HERE, PLANS, canonical, run, sha

MODEL = 'synthetic/model'
SLUG = 'synthetic/region'


def metadata():
    return {'data': {'id': MODEL, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']},
            'endpoints': [{'tag': SLUG, 'model_id': MODEL, 'status': 0, 'provider_name': 'Synthetic',
                           'context_length': 32000, 'max_prompt_tokens': 32000, 'max_completion_tokens': 8000,
                           'supported_parameters': ['max_tokens'],
                           'pricing': {'prompt': '0.0000001', 'completion': '0.0000004', 'request': '0',
                                       'input_cache_read': '0.00000005'}}]}}


def response():
    return {'model': MODEL, 'provider': 'Synthetic', 'id': 'synthetic-request',
            'choices': [{'message': {'content': 'Synthetic candidate, not a QM solution.'}, 'finish_reason': 'stop'}],
            'usage': {'cost': '0.000041', 'prompt_tokens': 100, 'completion_tokens': 50,
                      'completion_tokens_details': {'reasoning_tokens': 10}}}


class Transport:
    def __init__(self, meta=None, reply=None):
        self.meta = meta if meta is not None else metadata()
        self.reply = reply if reply is not None else response()
        self.posts = []; self.gets = []

    def request(self, method, path, body=None):
        if method == 'GET':
            self.gets.append(path)
            return canonical(self.meta), deepcopy(self.meta)
        self.posts.append(body)
        if isinstance(self.reply, Exception):
            raise self.reply
        return canonical(self.reply), deepcopy(self.reply)


def request():
    return {'messages': [{'role': 'user', 'content': 'synthetic fixture'}],
            'max_output_tokens': 4000, 'tools': [], 'retries': 0}


def test_configured_output_allowance_is_bound_and_sent(location):
    from live_campaign import prepare
    manifest = prepare('larger-output-fixture', MODEL, SLUG, ['direct'], 1, 100000, 7,
                       max_output_tokens=6000)
    ledger = CampaignLedger(location/'campaign.sqlite3')
    transport = Transport()
    try:
        ledger.create(manifest)
        receipt = run('direct', OpenRouterProvider(MODEL, SLUG, transport), location/'run',
                      manifest['runs'][0]['run_id'], max_output_tokens=6000,
                      live_admission=CampaignAdmission(ledger))
        assert manifest['runs'][0]['max_output_tokens'] == 6000
        assert transport.posts[0]['max_tokens'] == 6000
        assert receipt['calls'][0]['quote_microusd'] == 5600
        assert receipt['budget']['cap_microusd'] == 100000
    finally:
        ledger.close()


@pytest.mark.parametrize('limit', [0, -1, True, 1.5])
def test_invalid_output_allowance_refused_during_preparation(limit):
    from live_campaign import prepare
    with pytest.raises(ValueError, match='output-token'):
        prepare('invalid-output-fixture', MODEL, SLUG, ['direct'], 1, 100000, 7,
                max_output_tokens=limit)


def manifest():
    commitment = json.loads((HERE / 'commitment.json').read_text())
    return {'schema_version': '1.0', 'campaign_id': 'synthetic', 'seed_sha256': commitment['seed_sha256'],
            'cap_microusd': 200000,
            'runs': [{'run_id': f'synthetic-{i}', 'plan': 'self_critique',
                      'plan_sha256': sha(canonical(PLANS['self_critique'])),
                      'provider_identity': {'adapter': 'openrouter-context-bound-v1', 'model': MODEL, 'endpoint_slug': SLUG},
                      'max_output_tokens': 4000, 'cap_microusd': 100000} for i in range(2)]}


@pytest.fixture
def location():
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        yield Path(directory)


def test_full_context_quote_and_single_dispatch_not_character_estimate():
    transport = Transport(); provider = OpenRouterProvider(MODEL, SLUG, transport)
    req = request()
    assert provider.upper_quote(req) == 4800
    assert provider.request_evidence()['input_token_bound'] == 32000
    reply = provider.complete(req)
    assert reply.actual_microusd == 41 and reply.accounting_error is None
    wire = transport.posts[0]
    assert wire['max_tokens'] == 4000 and wire['provider']['allow_fallbacks'] is False
    assert wire['provider']['require_parameters'] is True
    assert wire['provider']['only'] == [SLUG]
    assert 'tools' not in wire and 'plugins' not in wire and 'models' not in wire
    with pytest.raises(ProviderError):
        provider.complete(req)
    assert len(transport.posts) == 1


def test_observed_public_endpoint_schema_quotes_without_any_network_or_key():
    raw = (HERE / 'openrouter_endpoint_observation.json').read_bytes()
    data = parse_json(raw)
    transport = Transport(meta=data)
    provider = OpenRouterProvider(data['data']['id'], 'siliconflow/fp8', transport)
    assert provider.upper_quote(request()) == 24793
    assert transport.posts == []
    assert provider.request_evidence()['input_token_bound'] == 262144


def test_mutating_public_evidence_cannot_mutate_reserved_wire():
    transport = Transport(); provider = OpenRouterProvider(MODEL, SLUG, transport)
    req = request(); provider.upper_quote(req)
    evidence = provider.request_evidence()
    evidence['wire_request']['max_tokens'] = 100000
    evidence['wire_request']['provider']['allow_fallbacks'] = True
    evidence['wire_request']['model'] = 'different/model'
    provider.complete(req)
    assert transport.posts[0]['max_tokens'] == 4000
    assert transport.posts[0]['provider']['allow_fallbacks'] is False
    assert transport.posts[0]['model'] == MODEL


def test_changed_internal_wire_fails_integrity_check_before_dispatch():
    transport = Transport(); provider = OpenRouterProvider(MODEL, SLUG, transport)
    req = request(); provider.upper_quote(req)
    provider._prepared.wire['max_tokens'] = 100000
    with pytest.raises(ProviderError, match='wire changed'):
        provider.complete(req)
    assert transport.posts == []


@pytest.mark.parametrize('change', ['override', 'fee', 'cache_write', 'unknown_tariff', 'no_limit', 'ambiguous_slug'])
def test_unsupported_billing_or_routing_refused_before_dispatch(change):
    data = metadata(); endpoint = data['data']['endpoints'][0]
    if change == 'override': endpoint['pricing']['overrides'] = [{'min_prompt_tokens': 1, 'prompt': '0.5'}]
    if change == 'fee': endpoint['pricing']['request'] = '0.0001'
    if change == 'cache_write': endpoint['pricing']['input_cache_write'] = '0.0000001'
    if change == 'unknown_tariff': endpoint['pricing']['new_fee'] = '0'
    if change == 'no_limit': endpoint['supported_parameters'] = []
    if change == 'ambiguous_slug':
        sibling = deepcopy(endpoint); sibling['tag'] += '/turbo'; data['data']['endpoints'].append(sibling)
    transport = Transport(data); provider = OpenRouterProvider(MODEL, SLUG, transport)
    with pytest.raises((ProviderError, BudgetError)):
        provider.upper_quote(request())
    assert transport.posts == []


def test_metadata_refreshed_each_call_and_changed_request_cannot_dispatch():
    transport = Transport(); provider = OpenRouterProvider(MODEL, SLUG, transport)
    req = request(); provider.upper_quote(req); provider.complete(req)
    transport.meta['data']['endpoints'][0]['pricing']['prompt'] = '0.0000002'
    assert provider.upper_quote(req) == 8000
    changed = deepcopy(req); changed['messages'][0]['content'] += ' changed'
    with pytest.raises(ProviderError, match='matching'):
        provider.complete(changed)
    assert len(transport.gets) == 2 and len(transport.posts) == 1


def test_json_decimals_duplicate_keys_and_numeric_price_bounds():
    assert parse_json(b'{"cost":0.0000001}')['cost'] == '0.0000001'
    for raw in (b'{"cost":0,"cost":1}', b'{"cost":NaN}'):
        with pytest.raises(ProviderError): parse_json(raw)
    for price in ['0.1', '0.123456789012345678901', '1e-15']:
        assert Decimal(str(price_ceiling(Decimal(price)))) <= Decimal(price)
    with pytest.raises(ProviderError):
        NoRedirect().redirect_request(None, None, 302, '', {}, 'https://untrusted.invalid')


def test_campaign_freezes_membership_and_cannot_reset(location):
    ledger = CampaignLedger(location / 'campaign.sqlite3'); ledger.create(manifest())
    with pytest.raises(BudgetError): ledger.create(manifest())
    later = manifest()['runs'][1]
    with pytest.raises(BudgetError, match='order'):
        ledger.admit(later['run_id'], later['plan'], later['provider_identity'], manifest()['seed_sha256'], 4000)
    p = manifest()['runs'][0]
    with pytest.raises(BudgetError):
        ledger.admit(p['run_id'], p['plan'], p['provider_identity'], manifest()['seed_sha256'], 4001)
    ledger.admit(p['run_id'], p['plan'], p['provider_identity'], manifest()['seed_sha256'], 4000)
    with pytest.raises(BudgetError):
        ledger.admit(p['run_id'], p['plan'], p['provider_identity'], manifest()['seed_sha256'], 4000)
    ledger.close()
    reopened = CampaignLedger(location / 'campaign.sqlite3')
    assert reopened.summary()['held_microusd'] == 100000
    later = manifest()['runs'][1]
    with pytest.raises(BudgetError, match='unfinished'):
        reopened.admit(later['run_id'], later['plan'], later['provider_identity'], manifest()['seed_sha256'], 4000)
    reopened.close()
    bad = manifest(); bad['cap_microusd'] = 199999
    with pytest.raises(BudgetError): validate_manifest(bad)


def test_prepare_is_finite_reproducible_and_has_no_transport():
    from live_campaign import prepare
    first = prepare('example', MODEL, SLUG, ['direct', 'self_critique'], 2, 400000, 70719)
    assert first == prepare('example', MODEL, SLUG, ['direct', 'self_critique'], 2, 400000, 70719)
    assert len(first['runs']) == 4 and sum(r['cap_microusd'] for r in first['runs']) == 400000
    with pytest.raises(BudgetError):
        prepare('example', MODEL, SLUG, ['direct', 'self_critique'], 2, 399999, 70719)
    bad = manifest(); bad['runs'][0]['plan_sha256'] = '0' * 64
    with pytest.raises(BudgetError): validate_manifest(bad)


def test_guarded_synthetic_run_settles_campaign_and_freezes_wire(location):
    ledger = CampaignLedger(location / 'campaign.sqlite3'); ledger.create(manifest())
    transport = Transport()
    receipt = run('self_critique', OpenRouterProvider(MODEL, SLUG, transport), location / 'run', 'synthetic-0',
                  live_admission=CampaignAdmission(ledger))
    assert receipt['status'] == 'completed' and not receipt['offline']
    assert ledger.summary()['spent_microusd'] == 82 and ledger.summary()['held_microusd'] == 0
    assert len(transport.posts) == 2
    seed = (HERE / 'seed_prompt.txt').read_bytes()
    for wire in transport.posts:
        assert wire['messages'][1]['content'].encode() == seed
    assert (location / 'run' / 'calls' / '000.request.json').exists()
    assert receipt['accuracy_score'] is None
    ledger.close()


@pytest.mark.parametrize('fault', ['timeout', 'missing_cost', 'wrong_provider', 'overrun', 'token_overrun'])
def test_uncertain_or_invalid_provider_blocks_run_and_campaign(location, fault):
    reply = response()
    if fault == 'timeout': reply = TimeoutError('synthetic timeout')
    if fault == 'missing_cost': del reply['usage']['cost']
    if fault == 'wrong_provider': reply['provider'] = 'Unadmitted'
    if fault == 'overrun': reply['usage']['cost'] = '0.11'
    if fault == 'token_overrun': reply['usage']['completion_tokens'] = 5000
    ledger = CampaignLedger(location / 'campaign.sqlite3'); ledger.create(manifest())
    transport = Transport(reply=reply)
    receipt = run('self_critique', OpenRouterProvider(MODEL, SLUG, transport), location / 'run', 'synthetic-0',
                  live_admission=CampaignAdmission(ledger))
    assert len(transport.posts) == 1 and receipt['budget']['blocked'] and ledger.summary()['blocked']
    assert receipt['answer_text'] is None
    p = manifest()['runs'][1]
    with pytest.raises(BudgetError):
        ledger.admit(p['run_id'], p['plan'], p['provider_identity'], manifest()['seed_sha256'], 4000)
    if fault == 'overrun':
        assert ledger.summary()['spent_microusd'] == 110000
        assert receipt['budget']['spent_microusd'] == 110000
    ledger.close()


def test_high_context_price_refused_before_paid_post(location):
    data = metadata(); data['data']['endpoints'][0]['pricing']['prompt'] = '0.001'
    ledger = CampaignLedger(location / 'campaign.sqlite3'); ledger.create(manifest())
    transport = Transport(meta=data)
    receipt = run('self_critique', OpenRouterProvider(MODEL, SLUG, transport), location / 'run', 'synthetic-0',
                  live_admission=CampaignAdmission(ledger))
    assert not transport.posts and receipt['status'] == 'admission_failure'
    assert ledger.summary()['spent_microusd'] == 0 and ledger.summary()['held_microusd'] == 0
    ledger.close()


@pytest.mark.parametrize('fault', ['invalid_usage', 'malformed_choice', 'response_write_failure'])
def test_known_charge_survives_later_validation_or_persistence_failure(location, monkeypatch, fault):
    import reference_runner
    reply = response()
    if fault == 'invalid_usage': reply['usage']['prompt_tokens'] = True
    if fault == 'malformed_choice': reply['choices'] = [{'message': 17}]
    if fault == 'response_write_failure':
        original = reference_runner.freeze_json
        def fail_response(path, value):
            if path.name.endswith('.response.json'):
                raise OSError('synthetic artifact failure')
            return original(path, value)
        monkeypatch.setattr(reference_runner, 'freeze_json', fail_response)
    ledger = CampaignLedger(location / 'campaign.sqlite3'); ledger.create(manifest())
    transport = Transport(reply=reply)
    receipt = run('self_critique', OpenRouterProvider(MODEL, SLUG, transport), location / 'run', 'synthetic-0',
                  live_admission=CampaignAdmission(ledger))
    assert len(transport.posts) == 1 and receipt['budget']['blocked'] and ledger.summary()['blocked']
    assert receipt['budget']['spent_microusd'] == 41 and ledger.summary()['spent_microusd'] == 41
    assert receipt['answer_text'] is None
    ledger.close()


def test_overrun_is_retained_even_when_other_usage_fields_are_malformed(location):
    reply = response(); reply['usage'].update(cost='0.11', prompt_tokens=True)
    ledger = CampaignLedger(location / 'campaign.sqlite3'); ledger.create(manifest())
    # The frozen campaign specifies self_critique; no parameter substitutions.
    receipt = run('self_critique', OpenRouterProvider(MODEL, SLUG, Transport(reply=reply)), location / 'run', 'synthetic-0',
                  live_admission=CampaignAdmission(ledger))
    assert receipt['budget']['spent_microusd'] == 110000
    assert ledger.summary()['spent_microusd'] == 110000 and ledger.summary()['blocked']
    ledger.close()
