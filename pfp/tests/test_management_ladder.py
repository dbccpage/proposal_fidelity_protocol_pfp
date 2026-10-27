import json
from pathlib import Path
from dataclasses import replace

import pytest

from pfp.domain.pilots.management_ladder import item_bank,grade_answer,canonical_answer,control_answers
from pfp.infrastructure.management_ladder import check_composition,p0,host_trial,analyze,registration,stage_summary,quote_scope,STAGE_CAPS,PLANNED_MAX_CALLS
from operations.domain.rop.result import Ok
from pfp.infrastructure.pfp_operad import PfpTurnExecutor


def test_each_family_exact_controls_and_compact_expansion():
    result=p0()
    assert result['status']=='PASS'
    assert result['checks']==result['passed']


def test_host_controls_use_actual_public_inputs_and_gate(tmp_path):
    for item in item_bank():
        if item.family=='composition': continue
        receipt=host_trial(item,tmp_path)
        assert receipt.completed,receipt.refusal
        assert receipt.output['accepted'],(item.item_id,receipt.output)
        corrupted=replace(item,expected={'counterfeit':True})
        if item.family!='linear_algebra':
            other=host_trial(corrupted,tmp_path)
            assert not other.output['accepted']


def test_scalar_without_witness_and_forged_composition_refuse():
    linear=next(item for item in item_bank() if item.family=='linear_algebra')
    assert not grade_answer(linear,canonical_answer({'answer':linear.expected['answer']}))['accepted']
    item=next(item for item in item_bank() if item.family=='composition')
    assert not grade_answer(item,canonical_answer({**item.expected,'op_count':99}),composition_checker=check_composition)['accepted']


def test_inputs_never_contain_expected_response_and_training_split_is_fixed():
    bank=item_bank()
    assert len({item.item_id for item in bank})==len(bank)==24
    for item in bank:
        assert json.dumps(item.expected,sort_keys=True,separators=(',',':')) not in item.prompt
    record=registration()
    assert record['campaign_cap_microusd']==sum(record['stage_caps'].values())==2_000_000
    assert record['provider_seed']=='UNSUPPORTED'


def test_actual_pfp_executor_checks_binding_and_keeps_accounting():
    def complete(turn):
        payload={key:value for key,value in turn.binding.items() if key!='checker_id'}
        payload['answer']='checked proposal'
        return dict(checked=turn.check_completion(json.dumps(payload)),model='actual-model',generation_id='actual-generation',
            usage=dict(input_tokens=2,output_tokens=3),cost_microusd=7,cost_basis='METERED_ESTIMATE')
    executor=PfpTurnExecutor('test.op','bare_metal_anchor','v4','task','attempt',complete,lineage=('parent',),local_experiment_seed=12015)
    result=executor({'public':'input'})
    assert result.value=='checked proposal' and result.cost_micro_usd==7
    assert result.context['operation_id']=='test.op' and result.context['lineage']==['parent']
    assert result.context['generation_id']=='actual-generation'
    assert result.context['local_experiment_seed']==12015 and result.context['provider_seed']=='UNSUPPORTED'
    assert result.verdict=='UNVERIFIED'
    def wrong(turn):
        return dict(checked=turn.check_completion('{"answer":"forged"}'))
    executor.complete=wrong
    with pytest.raises(ValueError): executor('public')
    def stale(turn):
        result=complete(turn)
        result['checked']['binding']['input_sha256']='wrong-candidate'
        return result
    executor.complete=stale
    with pytest.raises(ValueError,match='BINDING_MISMATCH'): executor('public')
    def counterfeit(turn):
        result=complete(turn)
        result['checked']['answer']='counterfeit cached answer'
        return result
    executor.complete=counterfeit
    assert executor('public').value=='checked proposal'


def test_analysis_keeps_failed_unknown_accounting_rows():
    rows=[dict(policy='M0',stage='P2',item_id='x',model='m',stratum='composition',accepted=False,cost_microusd=None,scored=True),
        dict(policy='M5',stage='P2',item_id='x',model='m',stratum='composition',accepted=True,cost_microusd=10,scored=True),
        dict(policy='M0',stage='P2',item_id='y',model='m',stratum='composition',accepted=False,cost_microusd=None,scored=False)]
    result=analyze(rows)['composition']
    assert result['arms']['M0']['n']==1 and result['arms']['M0']['accepted']==0
    assert result['arms']['M0']['planned']==2 and result['arms']['M0']['censored']==1
    assert result['paired']['M5']['paired_cost_differences']==[None]
    assert result['paired']['M5']['exact_sign_p']==1


def test_prereg_quotes_count_staged_calls_and_cannot_dispatch(tmp_path):
    class Quotes:
        def send(self,request,**options):
            assert options['quote_only'] and options['ceiling_microusd']==0
            return Ok(dict(quote_microusd=50000,input_token_bound=3000))
    record=quote_scope(registration(),Quotes(),tmp_path)
    assert record['stage_call_limits']==dict(P0=0,P1=4,P2=12,P3=16,P4=8)
    assert PLANNED_MAX_CALLS['P3']==43


def test_missing_provider_is_prerequisite_failure_not_completed():
    rows=[dict(reason='HOST_BINARY_NOT_FOUND',calls=[],accepted=False,host_solved=False)]
    snapshot=dict(attempts={},stage_spent={stage:0 for stage in STAGE_CAPS})
    assert stage_summary(rows,'P1',snapshot)['status']=='PREREQUISITE_FAILED'
    rows[0]['reason']='UNRECONCILED_ATTEMPT'
    assert stage_summary(rows,'P1',snapshot)['status']=='ACCOUNTING_HALTED'
    rows[0]['reason']='BUDGET_CENSORED'
    assert stage_summary(rows,'P1',snapshot)['status']=='BUDGET_CENSORED'


def test_native_managed_pilot_records_actual_generation_and_stage_parent():
    from pfp.infrastructure.management_ladder import _prepared,_op_run,VERSION,SEED
    item=next(item for item in item_bank() if item.item_id=='train-composition-2')
    attempt='P3:train-composition-2:M6:fixture-model:1'
    turn=_prepared(item,'M6',attempt)
    def complete(prepared):
        payload={key:value for key,value in prepared.binding.items() if key!='checker_id'}
        payload['answer']=canonical_answer(item.expected)
        text=json.dumps(payload)
        return dict(checked=prepared.check_completion(text),model='fixture-model',
            outcome=dict(response=dict(id='fixture-generation',text=text)),
            usage=dict(input_tokens=3,output_tokens=4),cost_microusd=5,cost_basis='FIXTURE')
    receipt,_=_op_run(item,'M6',turn,complete)
    assert receipt.completed and receipt.output['accepted']
    execution=receipt.steps[0].execution
    assert execution['context']['generation_id']=='fixture-generation'
    assert execution['context']['local_experiment_seed']==SEED
    assert execution['context']['lineage']==[VERSION,item.item_id,'M6','P3',attempt[:-1]+'0']
    assert turn.task.case['context']['lineage']==execution['context']['lineage']
