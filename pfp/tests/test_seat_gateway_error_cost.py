"""Native transport accounting controls; synthetic outcomes, no sockets."""
import pytest
import json
from hashlib import sha256
from operations.domain.rop.result import Ok
from pfp.infrastructure.estimated_gateway import NativeAnthropicCampaign


class Transport:
    def __init__(self, outcome=None):
        self.calls = []
        self.outcome = outcome or dict(dispatch="REPLIED", response=dict(model="m"), metered_cost_microusd=40)
    def send(self, request, **kwargs):
        if kwargs.get("quote_only"):
            return Ok(dict(dispatch="NOT_SENT", quote_microusd=100))
        self.calls.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return Ok(self.outcome)


def campaign(tmp_path, transport, **kwargs):
    return NativeAnthropicCampaign(transport=transport, accounting_path=tmp_path / 'budget.sqlite3',
        run_id='fixture', registration=dict(version=2), sleep=lambda _: None, **kwargs)


def test_reservation_survives_exception_restart_and_no_fallback(tmp_path):
    transport=Transport(TimeoutError('synthetic'))
    owner=campaign(tmp_path,transport)
    with pytest.raises(TimeoutError):
        owner.send(dict(model='m'),stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert owner.snapshot()['spent']==100
    later=Transport(); reopened=campaign(tmp_path,later)
    with pytest.raises(ValueError,match='UNRECONCILED_ATTEMPT'):
        reopened.send(dict(model='other'),stage='P2',attempt_id='b',raw_dir=tmp_path)
    assert not later.calls


def test_missing_usage_retains_hold_instead_of_zero(tmp_path):
    owner=campaign(tmp_path,Transport(dict(dispatch='REPLIED',response=dict(model='m'),metered_cost_microusd=None)))
    owner.send(dict(model='m'),stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert owner.snapshot()['spent']==100
    assert owner.snapshot()['attempts']['a']['actual_microusd'] is None


def test_settlement_and_replay_do_not_resend(tmp_path):
    raw=json.dumps(dict(type='message',id='message-1',model='m',content=[dict(type='text',text='candidate')],
        usage=dict(input_tokens=1,output_tokens=1),stop_reason='end_turn')).encode()
    path=tmp_path/'reply.json'; path.write_bytes(raw)
    response=dict(id='message-1',model='m',text='candidate',usage=dict(input_tokens=1,output_tokens=1),
        stop_reason='end_turn',assistant_message=dict(role='assistant',content=[dict(type='text',text='candidate')]),container_id=None)
    transport=Transport(dict(dispatch='REPLIED',response=response,metered_cost_microusd=40,
        raw=dict(path=str(path),sha256=sha256(raw).hexdigest(),bytes=len(raw))))
    owner=campaign(tmp_path,transport)
    request=dict(model='m')
    owner.send(request,stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert owner.snapshot()['spent']==40
    owner.send(request,stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert len(transport.calls)==1
    with pytest.raises(ValueError,match='ATTEMPT_BINDING'):
        owner.send(dict(model='changed'),stage='P1',attempt_id='a',raw_dir=tmp_path)
    with owner.ledger.transaction(owner.limit) as state:
        state['attempts']['a']['outcome']['response']['text']='counterfeit cached answer'
    with pytest.raises(ValueError,match='REPLAY_RESPONSE_MISMATCH'):
        owner.send(request,stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert len(transport.calls)==1


def test_stage_allowance_cannot_consume_later_stage_budget(tmp_path):
    owner=campaign(tmp_path,Transport(),limit_microusd=200,
        stage_caps=dict(P0=0,P1=50,P2=50,P3=50,P4=50))
    result=owner.send(dict(model='m'),stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert result['refusal']['code']=='BUDGET_CENSORED'
    assert owner.snapshot()['spent']==0


def test_registration_cannot_change_on_restart(tmp_path):
    campaign(tmp_path,Transport())
    with pytest.raises(ValueError,match='CAMPAIGN_SCOPE'):
        NativeAnthropicCampaign(transport=Transport(),accounting_path=tmp_path/'budget.sqlite3',
            run_id='fixture',registration=dict(version=3))


def test_frozen_shape_quote_and_call_count_refuse_before_send(tmp_path):
    transport=Transport()
    owner=NativeAnthropicCampaign(transport=transport,accounting_path=tmp_path/'scope.sqlite3',
        run_id='scope',registration=dict(quote_bounds={'P1:m:0':dict(quote_microusd=99)},
            stage_call_limits=dict(P0=0,P1=1,P2=1,P3=1,P4=1)))
    result=owner.send(dict(model='m'),stage='P1',attempt_id='a',raw_dir=tmp_path)
    assert result['refusal']['code']=='QUOTE_SCOPE_EXCEEDED'
    assert not transport.calls and owner.snapshot()['spent']==0
