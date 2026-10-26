"""Bounded registered P0-P4 campaign using the existing PFP/native provider ports."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from omega_engine_pfp.domain.pilots.management_ladder import (
    VERSION, SEED, canonical_answer, control_answers, grade_answer, item_bank, select_calibration_items,
)
from omega_engine_pfp.domain.prompts.compression import compress_prompt_tree, prompt_tree_storage_metrics
from omega_engine_pfp.infrastructure.compressed_task_turn import prepare_compressed_turn
from omega_engine_pfp.infrastructure.estimated_gateway import NativeAnthropicCampaign, native_anthropic_request
from omega_engine_operations.domain.rop.result import Err
from omega_engine_pfp.infrastructure.pfp_operad import PfpTurnExecutor
from omega_engine_pfp.infrastructure.seat_transport.anthropic_messages import AnthropicMessagesTransport
from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
from omega_engine_operads.skill_operad.skill_compiler.op_inventory import (
    HostBinding, OpInventory, OpSpec, PfpTurnBinding, SkillDecomposition, Wire,
)
from omega_engine_operads.skill_operad.resolver.resolver import compose, Refusal
from omega_engine_operads.skill_operad.resolver.native_runtime import run_native as run

MODELS=('claude-haiku-5-5','claude-sonnet-5-5','claude-opus-5-5')
STAGE_CAPS=dict(P0=0,P1=200000,P2=600000,P3=800000,P4=400000)
BASE=Path(__file__).resolve().parents[2]
DESIGN=BASE/'omega_engine_woland/tests/pilots/certified_ladder/design_v2.md'
PRICES=BASE/'omega_engine_pfp/fixtures/empirical/anthropic_pricing_20261015.json'
MODEL_ACCESS=BASE/'omega_engine_pfp/fixtures/empirical/anthropic_model_access_20261015.json'
MODELS_RESPONSE=BASE/'omega_engine_pfp/fixtures/empirical/anthropic_models_20261015.json'
POLICIES=('M0','M1','M2','M3_k1','M3_k3','M3_k5','M3_k8','M4','M5','M6')
MAX_PRIOR_BYTES=2048
PLANNED_MAX_CALLS=dict(P0=0,P1=8,P2=12,P3=43,P4=18)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()


def inventory_for(item):
    specs=tuple(OpSpec(**op,summary='finite composition fixture') for op in item.payload['ops'])
    return OpInventory(schema_version='omega.oewas.op_inventory.v3',skills=(SkillDecomposition(
        skill_id='ladder-composition',ops=specs,wiring=Wire.model_validate(item.expected['tree'])),))


def check_composition(item,value):
    if type(value) is not dict or set(value)!={'tree','op_count'} or type(value['op_count']) is not int:
        return False
    try:
        inventory=inventory_for(item)
        proposed=Wire.model_validate(value['tree'])
        minimal=compose(inventory,item.payload['inputs'],item.payload['goal'],max_ops=4)
        if isinstance(minimal,Refusal):
            return False
        # Both minimum and proposed term run through the existing typed/native boundary.
        executors={op.op_id:(lambda data: data) for skill in inventory.skills for op in skill.ops}
        receipt=run(inventory,proposed,['bounded-input'],executors,{})
        root=next(op for skill in inventory.skills for op in skill.ops if op.op_id==proposed.op)
        return receipt.completed and root.output==item.payload['goal'] and value['op_count']==len(receipt.steps)==len(minimal.ops)
    except (ValueError,TypeError,KeyError):
        return False


def p0():
    results=[]
    for item in item_bank():
        results.append(json.dumps(item.expected,sort_keys=True,separators=(',',':')) not in item.prompt)
        for text,expected in control_answers(item):
            answer=grade_answer(item,text,composition_checker=check_composition)
            results.append(answer['accepted']==expected)
    nodes=[dict(node_id=f'n{i}',parent_id=None if i==0 else 'n0',slot=None if i==0 else i-1,
        system='Use exact arithmetic and the canonical answer channel.',user='Public arithmetic task.',
        task_id='compression',attempt_id=f'compression-{i}',answer_schema={'type':'string'},checker_id='ladder-v2')
        for i in range(4)]
    tree=compress_prompt_tree(nodes)
    for node in nodes:
        direct=prepare_task_turn(**{key:value for key,value in node.items() if key not in {'node_id','parent_id','slot'}})
        restored=prepare_compressed_turn(tree,node['node_id'])
        results.append(direct==restored)
    return dict(status='PASS' if all(results) else 'FAIL',checks=len(results),passed=sum(results),
        compression=prompt_tree_storage_metrics(tree),provider_calls=0,
        scope='finite checker controls and byte-identical expanded PFP inputs')


def host_solve(item, output):
    """Read public payload only; the answer key is reserved for the later gate."""
    if item.family=='linear_algebra':
        from fractions import Fraction
        x=Fraction(item.payload['a']+2*item.payload['b'],7)
        y=Fraction(3*item.payload['a']-item.payload['b'],7)
        if x.denominator!=1 or y.denominator!=1:
            raise ValueError('INTEGER_FIXTURE_REQUIRED')
        return dict(answer=int(x+y),witness=dict(x=int(x),y=int(y)))
    if item.family=='seeded_defect':
        from omega_engine_operads.skill_operad.resolver.executors import HOST_EXECUTORS
        directory=output/'host-inputs'; directory.mkdir(exist_ok=True,parents=True)
        path=directory/(item.item_id+'.py'); raw=item.payload['source'].encode()
        if path.exists() and path.read_bytes()!=raw:
            raise ValueError('HOST_INPUT_CHANGED')
        if not path.exists():
            with path.open('xb') as handle: handle.write(raw)
        findings=HOST_EXECUTORS['sfh.scan']([str(path)])
        hit=next(row for row in findings if row['rule_id']=='SFH-PY-001')
        return dict(rule='BARE_EXCEPT',line=hit['line_number'])
    if item.family=='claim_hygiene':
        from omega_engine_pfp.domain.pilots.fail_closed_gate import _HYPE_REGEX
        return dict(matches=[dict(token=match.group(),offset=match.start())
            for match in _HYPE_REGEX.finditer(item.payload['text'])])
    raise ValueError('COMPOSITION_HOST_SOLVING_NOT_ADMITTED')


def host_trial(item,output):
    specs=(OpSpec(op_id='host.solve',summary='existing bounded host solver',inputs=('Task',),output='Candidate',
        binding=HostBinding(target='omega_engine_pfp/infrastructure/management_ladder.py:host_solve')),
        OpSpec(op_id='host.check',summary='exact answer gate',inputs=('Candidate',),output='Audit',
        binding=HostBinding(target='omega_engine_pfp/domain/pilots/management_ladder.py:grade_answer')))
    wire=Wire(op='host.check',args=(Wire(op='host.solve',args=('Task',)),))
    inv=OpInventory(schema_version='omega.oewas.op_inventory.v3',skills=(SkillDecomposition(
        skill_id='ladder-host',ops=specs,wiring=wire),))
    return run(inv,wire,[item.payload],{'host.solve':lambda _:canonical_answer(host_solve(item,output)),
        'host.check':lambda answer:grade_answer(item,answer,composition_checker=check_composition)},{})


def registration(*, prices_path=None, model_access_path=None, models_response_path=None):
    prices_path=Path(prices_path or PRICES)
    model_access_path=Path(model_access_path or MODEL_ACCESS)
    models_response_path=Path(models_response_path or MODELS_RESPONSE)
    prices=json.loads(prices_path.read_text())
    access=json.loads(model_access_path.read_text())
    if access['status']!=200 or access['missing'] or sha256(models_response_path.read_bytes()).hexdigest()!=access['response_sha256']:
        raise ValueError('MODEL_ACCESS_OBSERVATION_INVALID')
    if {row['id'] for row in access['models']} != set(MODELS): raise ValueError('MODEL_ACCESS_SCOPE_INVALID')
    files=[DESIGN,Path(__file__),BASE/'omega_engine_pfp/domain/pilots/management_ladder.py',
        BASE/'omega_engine_pfp/domain/pilots/fail_closed_gate.py',
        BASE/'omega_engine_pfp/infrastructure/estimated_gateway.py',
        BASE/'omega_engine_pfp/infrastructure/pfp_operad.py',
        BASE/'omega_engine_operads/skill_operad/resolver/resolver.py',
        BASE/'omega_engine_pfp/domain/prompts/compression.py',
        BASE/'omega_engine_pfp/infrastructure/compressed_task_turn.py',
        BASE/'omega_engine_pfp/infrastructure/task_turn.py',
        BASE/'omega_engine_pfp/use_cases/pfp_prompt.py',
        BASE/'omega_engine_pfp/use_cases/pfp_proposal.py',
        BASE/'omega_engine_pfp/domain/contracts/pfp_runtime.py',
        BASE/'omega_engine_operads/skill_operad/resolver/native_runtime.py',
        BASE/'omega_engine_operads/skill_operad/resolver/executors.py',
        BASE/'omega_engine_operations/use_cases/verification/silent_failure_hunter.py',
        BASE/'omega_engine_operads/skill_operad/skill_compiler/op_inventory.py',
        BASE/'omega_engine_pfp/infrastructure/seat_transport/anthropic_messages.py',
        BASE/'omega_engine_woland/infrastructure/providers/credential_source.py',
        BASE/'omega_engine/crates_rs/omega_symbol_game/src/anthropic_host.rs',
        BASE/'omega_engine/crates_rs/omega_woland/src/providers/anthropic/request.rs',
        BASE/'omega_engine/crates_rs/omega_woland/src/providers/anthropic/response.rs',
        BASE/'omega_engine/crates_rs/omega_woland/src/providers/anthropic/transport.rs',
        BASE/'omega_engine/crates_rs/omega_operads/src/operad_runtime.rs',
        BASE/'omega_engine/crates_rs/omega_operad_theory/src/foundation/planar_tree.rs']
    return dict(schema=VERSION,authority_effect='None',local_experiment_seed=SEED,
        provider_seed='UNSUPPORTED',decoding='provider-default; no temperature or seed sent',
        campaign_cap_microusd=2_000_000,stage_caps=STAGE_CAPS,models=MODELS,prices=prices,model_access=access,
        max_output_tokens=768,max_tree_ops=4,max_repairs=1,min_call_spacing_seconds=2,
        max_prior_bytes=MAX_PRIOR_BYTES,max_request_bytes=16384,planned_max_calls=PLANNED_MAX_CALLS,
        policies=POLICIES,items=[asdict(item) for item in item_bank()],
        source_sha256={path.relative_to(BASE).as_posix():sha256(path.read_bytes()).hexdigest() for path in files},
        analysis='paired exact sign test; Wilson intervals; training-only halving; descriptive small sample',
        observation_sha256={name:sha256(path.read_bytes()).hexdigest() for name,path in
            (('prices',prices_path),('model_access',model_access_path),('models_response',models_response_path))},
        external_items=dict(mub6='EXTERNAL_OWNER_NOT_ADMITTED'))


def quote_scope(record,transport,output):
    """Freeze conservative request-shape quotes without credentials or sockets."""
    quotes={}
    stage_models=dict(P1=MODELS[:2],P2=MODELS[:2],P3=MODELS[:1],P4=MODELS[2:])
    for stage,models in stage_models.items():
        for model in models:
            for structured in ((False,) if stage=='P1' else (False,True)):
                # Adaptive stages are bounded by retained prior bytes. Extra padding
                # conservatively covers JSON escaping; actual quotes must fit below.
                candidates=[]
                for item in item_bank():
                    prepared=_prepared(item,'M2' if structured else 'M0','quote-'+'x'*154,
                        prior='x'*MAX_PRIOR_BYTES if stage in {'P3','P4'} else '',
                        lesson='Return the actual JSON instance, without fences; answer contains one canonical ANSWER line.')
                    request=native_anthropic_request(prepared,model=model,structured=structured)
                    candidates.append(request)
                request=max(candidates,key=lambda value:len(canonical(value)))
                # Escaped prior text can require twice the plain-byte budget.
                if stage in {'P3','P4'}:
                    request['messages'][0]['content']+='x'*MAX_PRIOR_BYTES
                result=transport.send(request,raw_dir=str(output/'raw'),raw_name='quote-only',
                    ceiling_microusd=0,quote_only=True)
                if isinstance(result,Err): raise ValueError('PREREG_QUOTE_FAILED:'+result.error.code)
                quote=result.value.get('quote_microusd')
                if type(quote) is not int or quote<=0: raise ValueError('PREREG_QUOTE_REQUIRED')
                key=f'{stage}:{model}:{int(structured)}'
                quotes[key]=dict(quote_microusd=quote,request_sha256=sha256(canonical(request)).hexdigest(),
                    request_bytes=len(canonical(request)),input_token_bound=result.value['input_token_bound'])
    limits={'P0':0}
    for stage in stage_models:
        worst=max(row['quote_microusd'] for key,row in quotes.items() if key.startswith(stage+':'))
        limits[stage]=min(PLANNED_MAX_CALLS[stage],STAGE_CAPS[stage]//worst)
    return dict(quote_bounds=quotes,stage_call_limits=limits,
        sample_limit_basis='min(planned maximum calls, stage allowance // largest admitted native quote); actual quote must fit registered shape')


def freeze(output,transport=None,*,observation_paths=None):
    from omega_engine_operating_system.adapters.rust_host.ffi import locate_host_binary
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    record=registration(**(observation_paths or {}))
    located=locate_host_binary()
    if isinstance(located,Err): raise ValueError(located.error.code)
    record['native_host_sha256']=sha256(located.value.binary.read_bytes()).hexdigest()
    selected=transport or AnthropicMessagesTransport(observations=record['prices']['observations'],at_utc=record['prices']['at_utc'])
    record.update(quote_scope(record,selected,output))
    path=output/'registration.json'; raw=canonical(record)
    if path.exists() and path.read_bytes()!=raw:
        raise ValueError('REGISTRATION_CHANGED_NEW_VERSION_REQUIRED')
    if not path.exists():
        with path.open('xb') as handle: handle.write(raw)
    return record


def continuation_amendment(predecessor, output, accounting_path, *, authorization_reference,
                           transport=None, observation_paths=None):
    """Prepare the exact linked amendment for operator review; never send or settle.

    The selected live SQLite file remains the sole ledger. The historical packet
    and its frozen SQLite projection are only read, never copied over live state.
    """
    import sqlite3
    predecessor=Path(predecessor).resolve(); output=Path(output).resolve()
    accounting_path=Path(accounting_path).resolve()
    if (output.is_relative_to(predecessor) or accounting_path.is_relative_to(predecessor)
            or not NativeAnthropicCampaign._authorized_reference(authorization_reference)):
        raise ValueError('CONTINUATION_REQUIRES_LIVE_LEDGER_AND_EXPLICIT_DECISION')
    previous_raw=(predecessor/'registration.json').read_bytes()
    previous=json.loads(previous_raw)
    previous_digest=sha256(canonical(previous)).hexdigest()
    with sqlite3.connect(accounting_path.as_uri()+'?mode=ro',uri=True) as connection:
        row=connection.execute('SELECT state FROM provider_budget WHERE id=?',('native-anthropic:'+VERSION,)).fetchone()
    if row is None: raise ValueError('CONTINUATION_LEDGER_REQUIRED')
    state=json.loads(row[0])
    if (state.get('campaign_registration_sha256',state['campaign_scope']['registration_sha256'])!=previous_digest
            or state['limit']!=2_000_000 or state['campaign_scope']['stage_caps']!=STAGE_CAPS):
        raise ValueError('CONTINUATION_PREDECESSOR_MISMATCH')
    current=freeze(output,transport,observation_paths=observation_paths)
    old_sources=previous['source_sha256']; new_sources=current['source_sha256']
    changes={name:dict(before=old_sources.get(name),after=new_sources.get(name))
        for name in sorted(old_sources.keys()|new_sources.keys()) if old_sources.get(name)!=new_sources.get(name)}
    amendment=dict(schema='pfp.native-anthropic-amendment.v1',
        predecessor_registration_sha256=previous_digest,
        successor_registration_sha256=sha256(canonical(current)).hexdigest(),
        accounting_sha256=sha256(canonical(state)).hexdigest(),
        authorization_reference=authorization_reference,
        reason='Reviewed current-source continuation of the original campaign; no retry of the ambiguous attempt.',
        source_changes=changes,predecessor_registration_file_sha256=sha256(previous_raw).hexdigest(),
        predecessor=str(predecessor),accounting_path=str(accounting_path),run_id=VERSION,
        ambiguous_attempts=[dict(attempt_id=key,request_sha256=value['request_sha256'],
            reserved_microusd=value['reserved_microusd']) for key,value in sorted(state['attempts'].items())
            if value['state'] not in {'settled','not_sent','conservatively_charged'}],
        observations_before=previous.get('observation_sha256'),observations_after=current['observation_sha256'],
        native_host_before=previous['native_host_sha256'],native_host_after=current['native_host_sha256'])
    path=output/'continuation_amendment.json'; raw=canonical(amendment)
    if path.exists() and path.read_bytes()!=raw: raise ValueError('CONTINUATION_AMENDMENT_CHANGED')
    if not path.exists():
        with path.open('xb') as handle: handle.write(raw)
    return amendment


def settle_retained_replies(predecessor,accounting_path,*,transport=None):
    """Reprice only retained HTTP-200 answers under their active original prices."""
    import sqlite3
    predecessor=Path(predecessor).resolve(); accounting_path=Path(accounting_path).resolve()
    if accounting_path.is_relative_to(predecessor): raise ValueError('LIVE_LEDGER_REQUIRED')
    record=json.loads((predecessor/'registration.json').read_bytes())
    with sqlite3.connect(accounting_path.as_uri()+'?mode=ro',uri=True) as connection:
        row=connection.execute('SELECT state FROM provider_budget WHERE id=?',('native-anthropic:'+VERSION,)).fetchone()
    if row is None: raise ValueError('CONTINUATION_LEDGER_REQUIRED')
    state=json.loads(row[0])
    if state.get('campaign_registration_sha256',state['campaign_scope']['registration_sha256'])!=sha256(canonical(record)).hexdigest():
        raise ValueError('CONTINUATION_PREDECESSOR_MISMATCH')
    selected=transport or AnthropicMessagesTransport(observations=record['prices']['observations'],at_utc=record['prices']['at_utc'])
    campaign=NativeAnthropicCampaign(transport=selected,accounting_path=accounting_path,run_id=VERSION,
        registration=record,stage_caps=STAGE_CAPS)
    rows=json.loads((predecessor/'results.json').read_bytes())
    requests={call['binding']['attempt_id']:call['request'] for result in rows for call in result['calls']
        if 'binding' in call and 'request' in call}
    settlements=[]
    for attempt_id,entry in sorted(state['attempts'].items()):
        if entry['state']=='unknown' and (entry.get('outcome') or {}).get('dispatch')=='REPLIED':
            if attempt_id not in requests: raise ValueError('RETAINED_REQUEST_REQUIRED')
            settlements.append(campaign.settle_retained_reply(attempt_id,request=requests[attempt_id],
                expected_snapshot_sha256=sha256(canonical(campaign.snapshot())).hexdigest()))
    return dict(status='RETAINED_REPLIES_SETTLED',provider_calls=0,settlements=settlements,accounting=campaign.snapshot())


def _prepared(item,policy,attempt,prior='',lesson=''):
    if len(attempt)>160: raise ValueError('ATTEMPT_LENGTH_BOUND')
    prior=prior.encode('utf-8')[:MAX_PRIOR_BYTES].decode('utf-8',errors='ignore')
    text=item.prompt+'\nReturn one canonical line ANSWER: <JSON object> with the required witness.'
    system='Solve the public task. Follow the supplied response envelope.'
    if policy!='M0':
        system+=' State the typed input, permitted operation and obligations; verify the final answer against them.'
    if prior:
        text+='\nPrior-stage candidate (untrusted, recheck): '+prior
    if policy=='M4' and lesson:
        text+='\nTraining-derived formatting correction: '+lesson
    stage=attempt.split(':',1)[0]
    lineage=[VERSION,item.item_id,policy,stage]
    tail=attempt.rsplit(':',1)
    if len(tail)==2 and tail[1].isdigit() and int(tail[1])>0:
        lineage.append(tail[0]+':'+str(int(tail[1])-1))
    context=dict(operation_id='ladder.pfp',role_id='ladder-worker',role_version=VERSION,
        lineage=lineage,local_experiment_seed=SEED,provider_seed='UNSUPPORTED')
    args=dict(system=system,user=text,task_id=item.item_id,attempt_id=attempt,context=context,
        answer_schema={'type':'string'},checker_id='management-ladder-exact-v2')
    tree=compress_prompt_tree([dict(node_id='turn',parent_id=None,slot=None,**args)])
    return prepare_compressed_turn(tree,'turn')


def _op_run(item,policy,prepared,complete):
    specs=(OpSpec(op_id='ladder.pfp',summary='execute prepared PFP turn',inputs=('Task',),output='Candidate',
        binding=PfpTurnBinding(role_id='ladder-worker',role_version=VERSION)),
        OpSpec(op_id='ladder.check',summary='exact answer gate',inputs=('Candidate',),output='Audit',
        binding=HostBinding(target='omega_engine_pfp/domain/pilots/management_ladder.py:grade_answer')),
        OpSpec(op_id='ladder.report',summary='retain verdict',inputs=('Audit',),output='Receipt',
        binding=HostBinding(target='omega_engine_pfp/infrastructure/management_ladder.py:_op_run')))
    wire=Wire(op='ladder.report',args=(Wire(op='ladder.check',args=(Wire(op='ladder.pfp',args=('Task',)),)),))
    inv=OpInventory(schema_version='omega.oewas.op_inventory.v3',skills=(SkillDecomposition(
        skill_id='management-ladder',ops=specs,wiring=wire),))
    captured={}
    def capture(turn):
        result=complete(turn); captured['result']=result
        return result
    model_turn=PfpTurnExecutor('ladder.pfp','ladder-worker',VERSION,
        prepared.binding['task_id'],prepared.binding['attempt_id'],capture,
        prepare=lambda _args,_context:prepared,lineage=tuple(prepared.task.case['context']['lineage']),
        local_experiment_seed=SEED)
    receipt=run(inv,wire,[item.prompt],{'ladder.pfp':model_turn,
        'ladder.check':lambda answer:grade_answer(item,answer,composition_checker=check_composition),
        'ladder.report':lambda checked:checked},{})
    return receipt,captured.get('result')


def trial(campaign,item,policy,stage,output,*,model,lesson=''):
    record=dict(stage=stage,item_id=item.item_id,split=item.split,family=item.family,stratum=item.stratum,
        model=model,policy=policy,accepted=False,reason='NOT_RUN',calls=[],cost_microusd=0,
        usage=dict(input_tokens=0,output_tokens=0),host_solved=False,scored=False)
    old_attempt=f'{stage}:{item.item_id}:{policy}:{model}:0'
    previous=campaign.snapshot()['attempts'].get(old_attempt)
    if previous and previous['state']=='conservatively_charged':
        record.update(reason='HISTORICAL_AMBIGUOUS_CHARGED',cost_microusd=None,usage=None,
            historical_ambiguous_charged=True,calls=[dict(outcome=previous.get('outcome') or
                dict(dispatch='OUTCOME_UNKNOWN',refusal=dict(code='HISTORICAL_AMBIGUOUS_CHARGED')),
                usage=None,cost_microusd=None,cost_basis='UNKNOWN')])
        return record
    if policy in {'M5','M6'} and item.family!='composition':
        # Host-solvable controls remain outside the composition headline comparison.
        receipt=host_trial(item,output)
        record['operation_receipts']=[receipt.to_json()]
        if receipt.completed:
            record.update(receipt.output)
            record.update(reason='HOST_SOLVED',host_solved=True,scored=True)
        else:
            record['reason']=receipt.refusal.code
        return record
    stages=int(policy.split('_k')[1]) if policy.startswith('M3_k') else 1
    prior=''
    for index in range(stages+(1 if policy=='M6' else 0)):
        record.update(accepted=False,scored=False)
        attempt=f'{stage}:{item.item_id}:{policy}:{model}:{index}'
        prepared=_prepared(item,policy,attempt,prior,lesson)
        def complete(turn):
            return campaign.complete_prepared(turn,model=model,stage=stage,attempt_id=attempt,
                raw_dir=output/'raw',max_tokens=768,structured=policy not in {'M0','M1'})
        if policy in {'M5','M6'}:
            receipt,result=_op_run(item,policy,prepared,complete)
            record.setdefault('operation_receipts',[]).append(receipt.to_json())
            if result is None:
                record.update(reason=receipt.refusal.code if receipt.refusal else 'OPERATION_UNAVAILABLE')
                break
        else:
            result=complete(prepared)
        outcome=result['outcome']; checked=result['checked'] or {}
        record['calls'].append(result)
        record['scored']=outcome.get('dispatch')=='REPLIED' and 200<=outcome.get('status',0)<300
        cost=result['cost_microusd']
        if cost is None:
            record['cost_microusd']=None
        elif record['cost_microusd'] is not None:
            record['cost_microusd']+=cost
        usage=result.get('usage')
        if usage is None:
            record['usage']=None
        elif record['usage'] is not None:
            for field in ('input_tokens','output_tokens'): record['usage'][field]+=usage[field]
        if outcome.get('dispatch')!='REPLIED':
            record.update(reason=(outcome.get('refusal') or {}).get('code','OUTCOME_UNKNOWN'))
            break
        if not checked.get('schema_valid') or checked.get('failure_class')!='NONE':
            record.update(reason='ENVELOPE_FAILURE')
            prior='Previous response failed envelope validation; produce the required bound JSON.'
        else:
            prior=checked['answer']
            record.update(grade_answer(item,prior,composition_checker=check_composition))
            if policy=='M6' and not record['accepted']:
                prior='Independent checker verdict: '+record['reason']+'. Recheck the public task; no answer key is supplied.\n'+prior
        if policy=='M6' and record['accepted']:
            break
        if index>=stages-1 and policy!='M6':
            break
    return record


def _write(path,value):
    path.write_bytes(canonical(value))


def stage_summary(rows,stage,snapshot):
    attempts=[row for row in snapshot['attempts'].values() if row['stage']==stage]
    outcomes=[call['outcome'] for row in rows for call in row['calls']]
    reasons={row['reason'] for row in rows}
    replied=sum(outcome.get('dispatch')=='REPLIED' for outcome in outcomes)
    if 'UNRECONCILED_ATTEMPT' in reasons or any(row['state'] not in {'settled','not_sent','conservatively_charged'} for row in attempts):
        status='ACCOUNTING_HALTED'
    elif 'BUDGET_CENSORED' in reasons:
        status='BUDGET_CENSORED'
    elif any(not row['calls'] and not row.get('host_solved') for row in rows) or any(outcome.get('dispatch')!='REPLIED'
            for row in rows if not row.get('historical_ambiguous_charged') for outcome in (call['outcome'] for call in row['calls'])):
        status='PREREQUISITE_FAILED'
    else:
        status=('COMPLETED_WITH_RETAINED_FAILURE' if any(row.get('historical_ambiguous_charged') for row in rows)
            else 'COMPLETED') if rows else 'NOT_RUN'
    return dict(status=status,cases=len(rows),calls=len(outcomes),replies=replied,
        dispatched=sum(row['state']!='not_sent' for row in attempts),
        accepted=sum(row['accepted'] and row.get('scored',False) for row in rows),charged_microusd=snapshot['stage_spent'][stage],
        cap_microusd=STAGE_CAPS[stage],reason_counts={reason:sum(row['reason']==reason for row in rows) for reason in sorted(reasons)})


def run_campaign(output, *, execute=False, transport=None, accounting_path=None,
                 reviewed_amendment=None, authorization_reference=None, observation_paths=None):
    output=Path(output).resolve(); registration_record=freeze(output,transport,observation_paths=observation_paths)
    controls=p0(); _write(output/'p0.json',controls)
    host_controls=[host_trial(item,output) for item in item_bank() if item.family!='composition']
    controls['host_runs']=len(host_controls)
    controls['host_passed']=sum(row.completed and row.output.get('accepted',False) for row in host_controls)
    if controls['host_passed']!=len(host_controls): controls['status']='FAIL'
    _write(output/'p0.json',controls)
    summary=dict(schema=VERSION,authority_effect='None',registration_sha256=sha256(canonical(registration_record)).hexdigest(),
        P0=controls,stages={},results=[],external_items=registration_record['external_items'])
    if controls['status']!='PASS' or not execute:
        summary['status']='P0_FAILED' if controls['status']!='PASS' else 'PREPARED_ONLY'
        _write(output/'campaign.json',summary); return summary
    prices=registration_record['prices']
    if transport is None:
        import os
        from omega_engine_woland.infrastructure.providers.credential_source import resolve_credential
        from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
        credential=resolve_credential(('ANTHROPIC_API_KEY',))
        if isinstance(credential,Err): raise ValueError(credential.error.code)
        native=RustSymbolGameHost(process_environ={**os.environ,'ANTHROPIC_API_KEY':credential.value.value})
        selected=AnthropicMessagesTransport(observations=prices['observations'],at_utc=prices['at_utc'],host=native)
    else:
        selected=transport
    amendment=json.loads(Path(reviewed_amendment).read_bytes()) if reviewed_amendment else None
    ledger_path=Path(accounting_path or output/'accounting.sqlite3').resolve()
    if amendment is not None and (not authorization_reference
            or amendment.get('authorization_reference')!=authorization_reference
            or amendment.get('accounting_path')!=str(ledger_path) or amendment.get('run_id')!=VERSION):
        raise ValueError('CONTINUATION_AUTHORIZATION_MISMATCH')
    if amendment is not None:
        predecessor=Path(amendment['predecessor']).resolve()
        if (ledger_path.is_relative_to(predecessor)
                or sha256((predecessor/'registration.json').read_bytes()).hexdigest()!=amendment['predecessor_registration_file_sha256']):
            raise ValueError('CONTINUATION_PREDECESSOR_MISMATCH')
    campaign=NativeAnthropicCampaign(transport=selected,accounting_path=ledger_path,
        run_id=VERSION,registration=registration_record,stage_caps=STAGE_CAPS,registration_amendment=amendment)
    if amendment is not None:
        for attempt in amendment['ambiguous_attempts']:
            state=campaign.snapshot()
            if state['attempts'][attempt['attempt_id']]['reserved_microusd']!=attempt['reserved_microusd']:
                raise ValueError('CONTINUATION_RESERVE_MISMATCH')
            campaign.reconcile_ambiguous(attempt['attempt_id'],authorization_reference=authorization_reference,
                expected_snapshot_sha256=sha256(canonical(state)).hexdigest(),
                expected_request_sha256=attempt['request_sha256'])
        summary['continuation']=dict(amendment_sha256=sha256(canonical(amendment)).hexdigest(),
            predecessor_registration_sha256=amendment['predecessor_registration_sha256'],
            accounting_path=str(ledger_path),historical_usage='UNKNOWN_RETAINED_RESERVE')
    bank=item_bank(); saved=output/'results.json'
    # Rebuild derived verdicts from ledger-bound raw bytes on every invocation.
    # The existing sender replays settled attempts and refuses unknown ones;
    # results.json is a report, never execution/admission state.
    results=[]
    def observe(stage,item,policy,model,lesson=''):
        key=(stage,item.item_id,policy,model)
        old=next((row for row in results if (row['stage'],row['item_id'],row['policy'],row['model'])==key),None)
        if old is not None: return old
        try:
            row=trial(campaign,item,policy,stage,output,model=model,lesson=lesson)
        except (ValueError,TimeoutError,OSError) as exc:
            row=dict(stage=stage,item_id=item.item_id,policy=policy,model=model,family=item.family,
                stratum=item.stratum,split=item.split,accepted=False,reason=str(exc),calls=[],
                cost_microusd=None,usage=None,host_solved=False,scored=False)
        results.append(row); _write(saved,results); return row
    calibration=[item for item in bank if item.split=='train' and item.rung in {1,3} and item.family in {'linear_algebra','composition'}]
    for model in MODELS[:2]:
        for item in calibration: observe('P1',item,'M0',model)
    selected_items=select_calibration_items([row for row in results if row['stage']=='P1'],bank)
    calibration_failures=[row['item_id'] for row in results if row['stage']=='P1'
        and any(call['outcome'].get('dispatch')=='REPLIED' for call in row['calls']) and not row['accepted']]
    summary['calibration_selection']=dict(failure_items=sorted(set(calibration_failures)),
        condition='OBSERVED_FAILURES' if calibration_failures else 'NO_OBSERVED_FAILURES_DIFFICULTY_ORDER_FALLBACK')
    # A composition comparison is always visible even if host-solvable calibration fails.
    composition=next(item for item in bank if item.item_id=='train-composition-3')
    selected_items=tuple({item.item_id:item for item in (*selected_items,composition)}.values())[:3]
    for model in MODELS[:2]:
        for item in selected_items:
            for policy in ('M0','M5'): observe('P2',item,policy,model)
    training=next(item for item in bank if item.item_id=='train-composition-2')
    held=next(item for item in bank if item.item_id=='held_out-composition-2')
    train_failures=[row for row in results if row['split']=='train' and row['reason']=='ENVELOPE_FAILURE']
    lesson=('Return the actual JSON instance, without fences; answer contains one canonical ANSWER line.'
        if train_failures else '')
    summary['training_lesson']=dict(text=lesson,source_attempts=[row['item_id'] for row in train_failures],
        admission='EXPERIMENTAL_PROMPT_GUIDANCE_ONLY')
    for policy in POLICIES: observe('P3',training,policy,MODELS[0],lesson)
    train_rows=[row for row in results if row['stage']=='P3' and row['split']=='train']
    ranked=sorted(train_rows,key=lambda row:(not row['scored'],not row['accepted'],row['cost_microusd'] if row['cost_microusd'] is not None else 2_000_000,row['policy']))
    survivors=[row['policy'] for row in ranked[:5]]
    for policy in survivors: observe('P3',held,policy,MODELS[0],lesson)
    winner=next((policy for policy in survivors if policy!='M0'),'M2')
    for item in (held,next(item for item in bank if item.item_id=='held_out-linalg-3')):
        for policy in ('M0',winner): observe('P4',item,policy,MODELS[2],lesson)
    snapshot=campaign.snapshot()
    for stage in ('P1','P2','P3','P4'):
        rows=[row for row in results if row['stage']==stage]
        summary['stages'][stage]=stage_summary(rows,stage,snapshot)
    states={row['status'] for row in summary['stages'].values()}
    status=('HALTED_ACCOUNTING_UNKNOWN' if 'ACCOUNTING_HALTED' in states else
        'PREREQUISITE_FAILED' if 'PREREQUISITE_FAILED' in states else 'COMPLETED_BOUNDED')
    summary.update(status=status,
        results=results,accounting=snapshot,selected_policies=survivors,selected_frontier_policy=winner,
        analysis=analyze(results),limitations=['Small generated sample; no universal PFP or model ranking claim.',
            'Cost is rated standard usage, not an Anthropic invoice. Missing accounting remains reserved.',
            'Host-solvable rows reported separately; MUB item external.'])
    _write(output/'campaign.json',summary)
    return summary


def analyze(rows):
    from math import sqrt, comb
    report={}
    for stratum in ('composition','host_solvable'):
        planned=[row for row in rows if row['stratum']==stratum]
        group=[row for row in planned if row.get('scored',False)]
        arms={}
        for policy in sorted({row['policy'] for row in planned}):
            sample=[row for row in group if row['policy']==policy]; n=len(sample); wins=sum(row['accepted'] for row in sample)
            total=sum(row['policy']==policy for row in planned)
            if not n:
                arms[policy]=dict(planned=total,n=0,censored=total,accepted=0,wilson_95=None)
                continue
            p=wins/n; z=1.959963984540054; denom=1+z*z/n
            center=(p+z*z/(2*n))/denom; half=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
            arms[policy]=dict(planned=total,n=n,censored=total-n,accepted=wins,wilson_95=[max(0,center-half),min(1,center+half)])
        pairs=[]
        for row in group:
            if row['policy']=='M0': continue
            base=next((other for other in group if other['policy']=='M0' and all(other[key]==row[key] for key in ('stage','item_id','model'))),None)
            if base: pairs.append(dict(policy=row['policy'],baseline=base['accepted'],managed=row['accepted'],
                cost_difference=None if row['cost_microusd'] is None or base['cost_microusd'] is None else row['cost_microusd']-base['cost_microusd']))
        tests={}
        for policy in sorted({pair['policy'] for pair in pairs}):
            selected=[pair for pair in pairs if pair['policy']==policy]
            plus=sum(pair['managed'] and not pair['baseline'] for pair in selected)
            minus=sum(pair['baseline'] and not pair['managed'] for pair in selected); n=plus+minus
            tests[policy]=dict(pairs=len(selected),discordant=n,exact_sign_p=min(1,2*sum(comb(n,k) for k in range(min(plus,minus)+1))/(2**n)) if n else 1,
                paired_cost_differences=[pair['cost_difference'] for pair in selected],interpretation='DESCRIPTIVE_SMALL_SAMPLE')
            differences=[pair['cost_difference'] for pair in selected if pair['cost_difference'] is not None]
            tests[policy]['bootstrap_cost_mean_95']=None
            if len(differences)==len(selected) and len(differences)>1:
                import random
                rng=random.Random(SEED)
                means=sorted(sum(rng.choices(differences,k=len(differences)))/len(differences) for _ in range(1000))
                tests[policy]['bootstrap_cost_mean_95']=[means[24],means[974]]
        report[stratum]=dict(arms=arms,paired=tests)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--accounting-path',type=Path,help='One existing continuing live ledger; never the frozen evidence copy.')
    parser.add_argument('--prepare-continuation',type=Path,metavar='PREDECESSOR',help='Prepare a linked amendment, without provider calls.')
    parser.add_argument('--reviewed-amendment',type=Path)
    parser.add_argument('--settle-retained-replies',type=Path,metavar='ACTIVE_REGISTRATION_DIRECTORY',
        help='Native read-only replay and exact settlement of retained answers, without provider calls.')
    parser.add_argument('--authorization-reference',help='Reference to the explicit human continuation/charge decision.')
    parser.add_argument('--prices-path',type=Path)
    parser.add_argument('--model-access-path',type=Path)
    parser.add_argument('--models-response-path',type=Path)
    args=parser.parse_args()
    observations={key:getattr(args,key) for key in ('prices_path','model_access_path','models_response_path') if getattr(args,key)}
    if args.settle_retained_replies:
        if args.execute or args.prepare_continuation or not args.accounting_path:
            parser.error('Retained settlement needs --accounting-path and cannot dispatch or prepare an amendment.')
        args.output.mkdir(exist_ok=True,parents=True)
        report=args.output/'retained_settlement.json'
        if report.exists(): parser.error('Settlement report already exists; retain it instead of overwriting.')
        result=settle_retained_replies(args.settle_retained_replies,args.accounting_path)
        with report.open('xb') as handle: handle.write(canonical(result))
        print(json.dumps(dict(status=result['status'],provider_calls=0,settlements=len(result['settlements']))))
        return 0
    if args.prepare_continuation:
        if args.execute or not args.accounting_path: parser.error('Continuation preparation needs --accounting-path and cannot execute.')
        amendment=continuation_amendment(args.prepare_continuation,args.output,args.accounting_path,
            authorization_reference=args.authorization_reference,observation_paths=observations)
        print(json.dumps(dict(status='REVIEW_REQUIRED',amendment_sha256=sha256(canonical(amendment)).hexdigest()),indent=2))
        return 0
    result=run_campaign(args.output,execute=args.execute,accounting_path=args.accounting_path,
        reviewed_amendment=args.reviewed_amendment,authorization_reference=args.authorization_reference,
        observation_paths=observations)
    print(json.dumps({key:result[key] for key in ('status','stages')},indent=2))
    return 0 if result['status'] in {'PREPARED_ONLY','COMPLETED_BOUNDED'} else 2


if __name__=='__main__':
    raise SystemExit(main())
