import hashlib
import json
from pathlib import Path
import tempfile

import pytest

from reference_runner import HERE, OfflineTape, Reply, PLANS, run, canonical, sha
from rational_panel import CONTRACT_SHA256
from rational_workflows import EXPERIMENTS
from live_campaign import prepare
from test_rational_panel import proposal, challenge


def artifacts():
    seed = json.loads((HERE / 'commitment.json').read_text())['seed_sha256']
    obj = proposal(); obj['seed_sha256'] = seed
    obj['answer_text'] = 'PRIVATE_TO_SOLVER_CANDIDATE_731. Synthetic fixture only.'
    probes = challenge(); probes['seed_sha256'] = seed
    return json.dumps(obj), json.dumps(probes)


@pytest.fixture
def folder():
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        yield Path(directory) / 'run'


@pytest.mark.parametrize('plan,visible,calls', [
    ('rational_blind_panel_v1', False, 2), ('rational_visible_panel_v1', True, 2),
    ('rational_fixed_panel_v1', False, 1),
    ('rational_fixed_panel_v2', False, 1),
])
def test_visibility_exact_seed_caps_and_original_answer_retention(folder, plan, visible, calls):
    answer, panel = artifacts(); provider = OfflineTape([answer, panel])
    receipt = run(plan, provider, folder, 'synthetic')
    assert len(provider.requests) == calls
    for request in provider.requests:
        assert request['messages'][1]['content'].encode() == (HERE / 'seed_prompt.txt').read_bytes()
        assert request['tools'] == [] and request['retries'] == 0
    assert provider.requests[0]['max_output_tokens'] == 3000
    if calls == 2:
        assert provider.requests[1]['max_output_tokens'] == 1500
        transmitted = json.dumps(provider.requests[1])
        assert ('PRIVATE_TO_SOLVER_CANDIDATE_731' in transmitted) is visible
        assert bool(receipt['calls'][1]['visible_artifact_sha256s']) is visible
    assert receipt['answer_text'] == json.loads(answer)['answer_text']
    assert receipt['answer_text'] != panel
    assert receipt['host_checks']['all_requested_obligations_remain_uncertified']
    assert receipt['host_checks']['contract_sha256'] == CONTRACT_SHA256
    assert receipt['accuracy_score'] is None
    assert hashlib.sha256((folder / 'run.json').read_bytes()).hexdigest() == (folder / 'run.sha256').read_text().strip()
    assert json.loads((folder / 'host_checks.json').read_text()) == receipt['host_checks']


def test_blind_challenger_request_is_invariant_under_changed_candidate(folder):
    a, panel = artifacts()
    first = OfflineTape([a, panel]); second = OfflineTape(['entirely different and invalid candidate', panel])
    run('rational_blind_panel_v1', first, folder, 'first')
    run('rational_blind_panel_v1', second, folder.parent / 'other', 'second')
    assert first.requests[1] == second.requests[1]


def test_invalid_solver_is_recorded_and_critic_never_replaces_it(folder):
    _, panel = artifacts(); provider = OfflineTape(['not JSON', panel])
    receipt = run('rational_blind_panel_v1', provider, folder, 'invalid')
    assert receipt['answer_text'] == 'not JSON'
    assert receipt['host_checks']['artifact_errors']['candidate'] == 'INVALID_JSON'
    assert receipt['host_checks']['claims'] == []
    assert receipt['status'] == 'artifact_validation_failure'


@pytest.mark.parametrize('actual,expected_calls', [(60000, 1), (None, 1)])
def test_both_branches_share_cap_and_unknown_charge_stops_dispatch(folder, actual, expected_calls):
    answer, panel = artifacts()
    class Priced(OfflineTape):
        def upper_quote(self, request): return 60000
        def complete(self, request):
            self.requests.append(request)
            return Reply(next(self.responses), actual, 100, 100)
    provider = Priced([answer, panel])
    receipt = run('rational_blind_panel_v1', provider, folder, 'priced')
    assert len(provider.requests) == expected_calls
    if actual is None:
        assert receipt['budget']['held_microusd'] == 60000 and receipt['budget']['blocked']
    else:
        assert receipt['budget']['spent_microusd'] == 60000
    assert receipt['host_checks']['artifact_errors']['panel'] == 'MISSING_ARTIFACT'


def test_experiment_plan_hash_binds_schemas_visibility_checker_bytes():
    hashes = {sha(canonical(PLANS[name])) for name in EXPERIMENTS}
    assert len(hashes) == len(EXPERIMENTS)
    for value in EXPERIMENTS.values():
        for name, digest in value['source_pins'].items():
            assert sha((HERE / name).read_bytes()) == digest


def test_campaign_can_pin_new_plans_without_dispatch():
    manifest = prepare('public-synthetic', 'synthetic/model', 'synthetic/endpoint',
                       list(EXPERIMENTS), 1, 100000 * len(EXPERIMENTS), 7)
    assert len(manifest['runs']) == len(EXPERIMENTS)
    assert {item['plan'] for item in manifest['runs']} == set(EXPERIMENTS)
    for item in manifest['runs']:
        assert item['plan_sha256'] == sha(canonical(PLANS[item['plan']]))


def test_changed_contract_refused_before_output_or_dispatch(folder, monkeypatch):
    spec = EXPERIMENTS['rational_blind_panel_v1']
    monkeypatch.setitem(spec, 'contract_sha256', '0' * 64)
    provider = OfflineTape(list(artifacts()))
    with pytest.raises(ValueError, match='contract changed'):
        run('rational_blind_panel_v1', provider, folder, 'changed')
    assert not folder.exists() and provider.requests == []


@pytest.mark.parametrize('surrogate', [False, True])
def test_new_plan_uses_guarded_live_campaign_with_synthetic_transport(folder, surrogate):
    from campaign_ledger import CampaignAdmission, CampaignLedger
    from openrouter_provider import OpenRouterProvider
    from test_live_admission import Transport, MODEL, SLUG, response
    class Sequence(Transport):
        def __init__(self):
            super().__init__()
            solver, panel = artifacts()
            if surrogate:
                obj = json.loads(solver); obj['answer_text'] = '\ud800'; solver = json.dumps(obj)
            self.artifacts = iter((solver, panel))
        def request(self, method, path, body=None):
            if method == 'POST':
                self.reply = response()
                self.reply['choices'][0]['message']['content'] = next(self.artifacts)
            return super().request(method, path, body)
    manifest = prepare('synthetic-adaptation', MODEL, SLUG, ['rational_blind_panel_v1'], 1, 100000, 17)
    ledger = CampaignLedger(folder.parent / 'campaign.sqlite3')
    try:
        ledger.create(manifest); transport = Sequence()
        receipt = run('rational_blind_panel_v1', OpenRouterProvider(MODEL, SLUG, transport), folder,
                      manifest['runs'][0]['run_id'], live_admission=CampaignAdmission(ledger))
        assert len(transport.posts) == 2 and len(transport.gets) == 2
        assert receipt['status'] == ('artifact_validation_failure' if surrogate else 'completed')
        assert receipt['budget']['spent_microusd'] == 82
        assert ledger.summary()['spent_microusd'] == 82 and ledger.summary()['held_microusd'] == 0
        assert 'PRIVATE_TO_SOLVER_CANDIDATE_731' not in json.dumps(transport.posts[1])
        assert receipt['host_checks']['artifact_errors'] == ({'candidate': 'INVALID_UNICODE_TEXT'} if surrogate else {})
        assert (folder / 'run.json').is_file() and (folder / 'run.sha256').is_file()
        assert json.loads((folder / 'run.json').read_text(encoding='utf-8')) == receipt
    finally:
        ledger.close()


@pytest.mark.parametrize('field', ['finish_reason', 'id', 'nested_usage', 'content'])
def test_invalid_provider_unicode_keeps_bill_and_freezes_failure_receipt(folder, field):
    from campaign_ledger import CampaignAdmission, CampaignLedger
    from openrouter_provider import OpenRouterProvider
    from test_live_admission import Transport, MODEL, SLUG, response
    class EscapedResponse(Transport):
        def request(self, method, path, body=None):
            if method == 'GET': return super().request(method, path, body)
            self.posts.append(body)
            result = response()
            if field == 'finish_reason': result['choices'][0]['finish_reason'] = '\ud800'
            elif field == 'id': result['id'] = '\ud800'
            elif field == 'nested_usage': result['usage']['extra'] = {'\ud800': 'bad metadata'}
            else: result['choices'][0]['message']['content'] = '\ud800'
            return json.dumps(result, ensure_ascii=True).encode('ascii'), result
    manifest = prepare('synthetic-unicode', MODEL, SLUG, ['rational_blind_panel_v1'], 1, 100000, 17)
    ledger = CampaignLedger(folder.parent / 'campaign.sqlite3')
    try:
        ledger.create(manifest); transport = EscapedResponse()
        receipt = run('rational_blind_panel_v1', OpenRouterProvider(MODEL, SLUG, transport), folder,
                      manifest['runs'][0]['run_id'], live_admission=CampaignAdmission(ledger))
        assert len(transport.posts) == 1
        assert receipt['status'] == 'provider_or_accounting_failure'
        assert receipt['budget']['spent_microusd'] == 41 and receipt['budget']['blocked']
        assert ledger.summary()['spent_microusd'] == 41 and ledger.summary()['held_microusd'] == 99959
        assert ledger.summary()['blocked']
        assert json.loads((folder / 'run.json').read_text(encoding='utf-8')) == receipt
        assert (folder / 'calls/000.response.json').is_file()
        assert sha((folder / 'run.json').read_bytes()) == (folder / 'run.sha256').read_text().strip()
        evidence = receipt['calls'][0]['provider_evidence']['malformed_response_ascii_json']
        assert '\\ud800' in evidence and evidence.encode('utf-8')
    finally:
        ledger.close()
