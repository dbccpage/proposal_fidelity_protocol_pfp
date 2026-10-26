"""Append-only campaign recovery controls; synthetic transport, zero sockets."""
from hashlib import sha256
import json

import pytest

from omega_engine_operations.domain.rop.result import Ok
from omega_engine_pfp.infrastructure.estimated_gateway import NativeAnthropicCampaign


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


class Transport:
    def __init__(self, *, unknown=False):
        self.unknown, self.calls = unknown, []

    def send(self, request, **options):
        if options.get('quote_only'):
            return Ok(dict(quote_microusd=100))
        self.calls.append(request)
        if self.unknown:
            return Ok(dict(dispatch='OUTCOME_UNKNOWN', refusal=dict(code='TRANSPORT_ERROR')))
        return Ok(dict(dispatch='REPLIED', response=dict(model=request['model']), metered_cost_microusd=40))


def owner(tmp_path, transport, registration=None, **kwargs):
    return NativeAnthropicCampaign(transport=transport, accounting_path=tmp_path/'ledger.sqlite3',
        run_id='continuing', registration=registration or dict(version=1), sleep=lambda _: None, **kwargs)


def uncertain(tmp_path):
    campaign = owner(tmp_path, Transport(unknown=True))
    request = dict(model='m')
    original = campaign.send(request, stage='P1', attempt_id='old', raw_dir=tmp_path)
    return campaign, request, original


def test_conservative_charge_keeps_unknown_outcome_and_never_retries_it(tmp_path):
    campaign, request, original = uncertain(tmp_path)
    before = campaign.snapshot()
    event = campaign.reconcile_ambiguous('old', authorization_reference='human:explicit-decision',
        expected_snapshot_sha256=digest(before), expected_request_sha256=digest(request))
    after = campaign.snapshot()
    assert after['spent'] == after['stage_spent']['P1'] == 100
    assert after['attempts']['old']['actual_microusd'] is None
    assert after['attempts']['old']['outcome'] == original
    assert event['basis'] == 'CONSERVATIVE_RESERVED_CHARGE'
    restarted_transport = Transport()
    restarted = owner(tmp_path, restarted_transport)
    assert restarted.send(request, stage='P1', attempt_id='old', raw_dir=tmp_path) == original
    restarted.send(request, stage='P2', attempt_id='next', raw_dir=tmp_path)
    assert len(restarted_transport.calls) == 1
    assert restarted.snapshot()['spent'] == 140
    assert restarted.snapshot()['stage_spent']['P1'] == 100


def test_reconciliation_requires_exact_human_decision_and_snapshot(tmp_path):
    campaign, request, _ = uncertain(tmp_path)
    before = campaign.snapshot()
    for authorization, state_hash, request_hash in [('', digest(before), digest(request)),
            ('human:yes', '0'*64, digest(request)), ('human:yes', digest(before), '0'*64)]:
        with pytest.raises(ValueError):
            campaign.reconcile_ambiguous('old', authorization_reference=authorization,
                expected_snapshot_sha256=state_hash, expected_request_sha256=request_hash)
        assert campaign.snapshot() == before


def test_reviewed_registration_amendment_carries_history_not_a_second_budget(tmp_path):
    campaign, request, original = uncertain(tmp_path)
    before = campaign.snapshot()
    revised = dict(version=2)
    amendment = dict(schema='pfp.native-anthropic-amendment.v1',
        predecessor_registration_sha256=digest(dict(version=1)), successor_registration_sha256=digest(revised),
        accounting_sha256=digest(before), authorization_reference='human:reviewed-continuation',
        reason='Reviewed current-source continuation; preserve original experiment.', source_changes={})
    transport = Transport()
    updated = owner(tmp_path, transport, revised, registration_amendment=amendment)
    snapshot = updated.snapshot()
    assert snapshot['attempts'] == before['attempts']
    assert snapshot['spent'] == 100
    assert snapshot['campaign_scope'] == before['campaign_scope']
    assert snapshot['registration_amendments'] == [amendment]
    assert snapshot['campaign_registration_sha256'] == digest(revised)
    with pytest.raises(ValueError, match='UNRECONCILED_ATTEMPT'):
        updated.send(dict(model='m'), stage='P2', attempt_id='next', raw_dir=tmp_path)
    assert not transport.calls
    assert owner(tmp_path, Transport(), revised, registration_amendment=amendment).snapshot() == snapshot
    assert snapshot['attempts']['old']['outcome'] == original


def test_changed_or_unreviewed_registration_cannot_launder_accounting(tmp_path):
    campaign, _, _ = uncertain(tmp_path)
    before = campaign.snapshot()
    revised = dict(version=2)
    with pytest.raises(ValueError, match='CAMPAIGN_SCOPE_MISMATCH'):
        owner(tmp_path, Transport(), revised)
    amendment = dict(schema='pfp.native-anthropic-amendment.v1',
        predecessor_registration_sha256=digest(dict(version=1)), successor_registration_sha256=digest(revised),
        accounting_sha256='0'*64, authorization_reference='human:yes', reason='reviewed', source_changes={})
    with pytest.raises(ValueError, match='AMENDMENT'):
        owner(tmp_path, Transport(), revised, registration_amendment=amendment)
    assert campaign.snapshot() == before


def test_conservative_settlement_cannot_hide_liability_above_reserve(tmp_path):
    campaign, request, _ = uncertain(tmp_path)
    with campaign.ledger.transaction(campaign.limit) as state:
        state['attempts']['old']['actual_microusd'] = 101
    before = campaign.snapshot()
    with pytest.raises(ValueError, match='RESERVE_INSUFFICIENT'):
        campaign.reconcile_ambiguous('old', authorization_reference='human:yes',
            expected_snapshot_sha256=digest(before), expected_request_sha256=digest(request))
    assert campaign.snapshot() == before


def test_historical_ambiguous_trial_is_retained_without_preparing_or_resending(tmp_path):
    from omega_engine_pfp.domain.pilots.management_ladder import item_bank
    from omega_engine_pfp.infrastructure.management_ladder import trial, stage_summary
    item = item_bank()[0]
    attempt = f'P1:{item.item_id}:M0:m:0'
    campaign = owner(tmp_path, Transport(unknown=True))
    request = dict(model='m')
    campaign.send(request, stage='P1', attempt_id=attempt, raw_dir=tmp_path)
    campaign.reconcile_ambiguous(attempt, authorization_reference='human:yes',
        expected_snapshot_sha256=digest(campaign.snapshot()), expected_request_sha256=digest(request))
    campaign.transport = Transport()
    result = trial(campaign, item, 'M0', 'P1', tmp_path, model='m')
    assert result['reason'] == 'HISTORICAL_AMBIGUOUS_CHARGED'
    assert result['cost_microusd'] is result['usage'] is None
    assert not result['scored'] and not result['accepted'] and not campaign.transport.calls
    summary = stage_summary([result], 'P1', campaign.snapshot())
    assert summary['status'] == 'COMPLETED_WITH_RETAINED_FAILURE'
    assert summary['charged_microusd'] == 100 and summary['accepted'] == 0


def test_reconciled_charge_still_consumes_stage_and_global_allowance(tmp_path):
    campaign, request, _ = uncertain(tmp_path)
    campaign.reconcile_ambiguous('old', authorization_reference='human:yes',
        expected_snapshot_sha256=digest(campaign.snapshot()), expected_request_sha256=digest(request))
    with campaign.ledger.transaction(campaign.limit) as state:
        state['stage_spent']['P1'] = campaign.stage_caps['P1']
        state['spent'] = campaign.limit
    campaign.transport = Transport()
    result = campaign.send(request, stage='P2', attempt_id='next', raw_dir=tmp_path)
    assert result['refusal']['code'] == 'BUDGET_CENSORED'
    assert not campaign.transport.calls


def test_preparation_binds_live_history_and_preserves_frozen_packet(tmp_path, monkeypatch):
    from omega_engine_pfp.infrastructure import management_ladder as ladder
    predecessor = tmp_path/'frozen'; predecessor.mkdir()
    old = dict(source_sha256={'owner.py':'a'*64}, native_host_sha256='b'*64)
    old_raw = json.dumps(old, indent=2).encode()
    (predecessor/'registration.json').write_bytes(old_raw)
    live = tmp_path/'live.sqlite3'
    campaign = NativeAnthropicCampaign(transport=Transport(unknown=True), accounting_path=live,
        run_id=ladder.VERSION, registration=old, sleep=lambda _: None)
    campaign.send(dict(model='m'), stage='P1', attempt_id='old', raw_dir=tmp_path)
    frozen_ledger = predecessor/'accounting.sqlite3'
    frozen_ledger.write_bytes(live.read_bytes())
    ledger_bytes, state = live.read_bytes(), campaign.snapshot()
    current = dict(source_sha256={'owner.py':'c'*64}, native_host_sha256='d'*64,
        observation_sha256={'prices':'e'*64})
    output = tmp_path/'continuation'; output.mkdir()
    monkeypatch.setattr(ladder, 'freeze', lambda *args, **kwargs: current)
    amendment = ladder.continuation_amendment(predecessor, output, live,
        authorization_reference='human:fixture-explicit-yes')
    assert amendment['accounting_sha256'] == digest(state)
    assert amendment['source_changes'] == {'owner.py':dict(before='a'*64, after='c'*64)}
    assert amendment['ambiguous_attempts'][0]['reserved_microusd'] == 100
    assert live.read_bytes() == ledger_bytes == frozen_ledger.read_bytes()
    assert (predecessor/'registration.json').read_bytes() == old_raw
    assert json.loads((output/'continuation_amendment.json').read_bytes()) == amendment
    with pytest.raises(ValueError, match='LIVE_LEDGER'):
        ladder.continuation_amendment(predecessor, output, frozen_ledger,
            authorization_reference='human:fixture-explicit-yes')


def test_repeated_reconciliation_is_idempotent_but_changed_decision_refuses(tmp_path):
    campaign, request, _ = uncertain(tmp_path)
    event = campaign.reconcile_ambiguous('old', authorization_reference='human:one',
        expected_snapshot_sha256=digest(campaign.snapshot()), expected_request_sha256=digest(request))
    after = campaign.snapshot()
    repeated = campaign.reconcile_ambiguous('old', authorization_reference='human:one',
        expected_snapshot_sha256=digest(campaign.snapshot()), expected_request_sha256=digest(request))
    assert repeated == event and campaign.snapshot() == after
    with pytest.raises(ValueError, match='BINDING_MISMATCH'):
        campaign.reconcile_ambiguous('old', authorization_reference='human:different',
            expected_snapshot_sha256=digest(after), expected_request_sha256=digest(request))
    assert campaign.snapshot() == after


def test_retained_reply_settlement_binds_raw_request_and_existing_reservation(tmp_path):
    raw = json.dumps(dict(type='message', id='public-usage-control', model='m', stop_reason='end_turn',
        content=[dict(type='text', text='public fixture answer')], usage=dict(input_tokens=856, output_tokens=407,
        cache_creation_input_tokens=0, cache_read_input_tokens=0, speed='standard'))).encode()
    path=tmp_path/'retained.json'; path.write_bytes(raw)
    retained=dict(dispatch='REPLIED',status=200,raw=dict(path=str(path),sha256=digest(json.loads(raw)),bytes=len(raw)),
        response=dict(model='m'),metered_cost_microusd=None)
    retained['raw']['sha256']=sha256(raw).hexdigest()
    transport=Transport(); transport.send=lambda request, **options: Ok(dict(quote_microusd=100)) if options.get('quote_only') else Ok(retained)
    campaign=owner(tmp_path,transport)
    request=dict(model='m')
    campaign.send(request,stage='P1',attempt_id='answered',raw_dir=tmp_path)
    assert campaign.snapshot()['spent']==100
    class ReplayOnly:
        def replay(self, observed_request, **options):
            assert observed_request==request and options['raw']==retained['raw'] and options['status']==200
            return Ok({**retained,'metered_cost_microusd':40})
        def send(self,*args,**kwargs):
            raise AssertionError('settlement cannot dispatch')
    campaign.transport=ReplayOnly()
    event=campaign.settle_retained_reply('answered',request=request,expected_snapshot_sha256=digest(campaign.snapshot()))
    state=campaign.snapshot()
    assert state['spent']==state['stage_spent']['P1']==40
    assert state['attempts']['answered']['state']=='settled'
    assert state['attempts']['answered']['actual_microusd']==40
    assert event['original_outcome']==retained
    assert path.read_bytes()==raw
    assert campaign.settle_retained_reply('answered',request=request,expected_snapshot_sha256=digest(state))==event
    assert campaign.snapshot()==state
    with pytest.raises(ValueError,match='BINDING'):
        campaign.settle_retained_reply('answered',request=dict(model='wrong'),expected_snapshot_sha256=digest(state))


def test_active_registration_is_a_valid_multi_hop_predecessor(tmp_path,monkeypatch):
    from omega_engine_pfp.infrastructure import management_ladder as ladder
    old=dict(source_sha256={'owner.py':'a'*64},native_host_sha256='b'*64)
    active=dict(source_sha256={'owner.py':'c'*64},native_host_sha256='d'*64)
    live=tmp_path/'live.sqlite3'
    first=NativeAnthropicCampaign(transport=Transport(),accounting_path=live,run_id=ladder.VERSION,registration=old)
    amendment=dict(schema='pfp.native-anthropic-amendment.v1',predecessor_registration_sha256=digest(old),
        successor_registration_sha256=digest(active),accounting_sha256=digest(first.snapshot()),
        authorization_reference='human:yes',reason='first reviewed source change',source_changes={})
    NativeAnthropicCampaign(transport=Transport(),accounting_path=live,run_id=ladder.VERSION,
        registration=active,registration_amendment=amendment)
    predecessor=tmp_path/'active'; predecessor.mkdir()
    (predecessor/'registration.json').write_bytes(json.dumps(active).encode())
    next_record=dict(source_sha256={'owner.py':'e'*64},native_host_sha256='f'*64,observation_sha256={})
    output=tmp_path/'next'; output.mkdir()
    monkeypatch.setattr(ladder,'freeze',lambda *args,**kwargs:next_record)
    next_amendment=ladder.continuation_amendment(predecessor,output,live,authorization_reference='human:yes')
    assert next_amendment['predecessor_registration_sha256']==digest(active)
    third=NativeAnthropicCampaign(transport=Transport(),accounting_path=live,run_id=ladder.VERSION,
        registration=next_record,registration_amendment=next_amendment)
    state=third.snapshot()
    assert state['campaign_scope']['registration_sha256']==digest(old)
    assert len(state['registration_amendments'])==2 and state['spent']==0


def test_native_retained_usage_replay_needs_no_key_or_provider_dispatch(tmp_path):
    from omega_engine_pfp.infrastructure.seat_transport.anthropic_messages import AnthropicMessagesTransport
    from omega_engine_pfp.infrastructure.management_ladder import PRICES
    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
    from omega_engine_operations.domain.rop.result import Err
    import os
    prices=json.loads(PRICES.read_bytes())
    transport=AnthropicMessagesTransport(observations=prices['observations'],at_utc=prices['at_utc'],
        host=RustSymbolGameHost(process_environ={**os.environ,'ANTHROPIC_API_KEY':''}))
    body=dict(type='message',id='public-usage-control',model='claude-haiku-5-5',stop_reason='end_turn',
        content=[dict(type='text',text='public fixture answer')],usage=dict(input_tokens=856,output_tokens=407,
        cache_creation_input_tokens=0,cache_read_input_tokens=0,cache_creation=dict(ephemeral_5m_input_tokens=0,
        ephemeral_1h_input_tokens=0),output_tokens_details=dict(thinking_tokens=229),service_tier='standard',
        inference_geo='global',speed='standard'))
    data=json.dumps(body).encode(); path=tmp_path/'public-usage.json'; path.write_bytes(data)
    raw=dict(path=str(path),sha256=sha256(data).hexdigest(),bytes=len(data))
    request=dict(model=body['model'],max_tokens=768,messages=[dict(role='user',content='Public fixture')])
    result=transport.replay(request,raw=raw,status=200)
    assert not isinstance(result,Err),result
    assert result.value['provider_calls']==0 and result.value['metered_cost_microusd']==290
    assert result.value['response']['usage']==body['usage'] and path.read_bytes()==data
    bad=transport.replay(request,raw={**raw,'sha256':'0'*64},status=200)
    assert isinstance(bad,Err)


@pytest.mark.parametrize('raw,status', [({},200),({'path':None},200),
    ({'path':'missing','bytes':-1,'sha256':'0'*64},200),
    ({'path':'missing','bytes':16777217,'sha256':'0'*64},200),
    ({'path':'missing','bytes':0,'sha256':'0'*64},True)])
def test_malformed_replay_refuses_before_native_call(raw,status):
    from omega_engine_pfp.infrastructure.seat_transport.anthropic_messages import AnthropicMessagesTransport
    from omega_engine_operations.domain.rop.result import Err
    class NoCall:
        def invoke_runtime_with_file(self,*args,**kwargs):
            raise AssertionError('Malformed replay cannot reach native transport')
    result=AnthropicMessagesTransport(observations=[],at_utc='',host=NoCall()).replay(
        {'model':'test'},raw=raw,status=status)
    assert isinstance(result,Err)


@pytest.mark.parametrize('declared_size,actual_size,message',[
    (16777217,0,'reply limit'), (0,16777217,'file size mismatch')])
def test_native_replay_bounds_declared_and_replaced_files_before_read(
    tmp_path,declared_size,actual_size,message
):
    from omega_engine_pfp.infrastructure.management_ladder import PRICES
    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
    prices=json.loads(PRICES.read_bytes())
    path=tmp_path/'bounded-raw'
    with path.open('wb') as handle:
        handle.truncate(actual_size)
    result=RustSymbolGameHost().invoke_runtime_with_file('anthropic_messages',dict(
        request=dict(model='claude-haiku-5-5',max_tokens=768,messages=[dict(role='user',content='Public fixture')]),
        raw_dir=str(tmp_path),raw_name=path.name,ceiling_microusd=0,quote_only=False,
        observations=prices['observations'],at_utc=prices['at_utc'],advisor_pairings=[],
        replay_raw=dict(path=str(path),sha256='0'*64,bytes=declared_size,status=200)),
        file_action='anthropic_messages_file').unwrap()
    assert result['success'] is True
    assert result['result']['refusal']['code']=='ANTHROPIC_HOST_INPUT_INVALID'
    assert message in result['result']['refusal']['message']
