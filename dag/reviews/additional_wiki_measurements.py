"""Reconcile finite published costs; do not execute provider or workflow code."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
OLD='workflows/library/evidence/measurements.json'
LIVE='workflows/library/evidence/live_20261106/measurements.json'
def strict(p):
    def pairs(items):
        result={}
        for key,value in items:
            assert key not in result,key
            result[key]=value
        return result
    return json.loads(p.read_bytes(),parse_float=Decimal,object_pairs_hook=pairs,
                      parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def sha(raw):return hashlib.sha256(raw).hexdigest()
old=strict(ROOT/OLD);base=old['rows'][0];october=[]
for r in old['rows']:
    assert r['total_tokens']==r['prompt_tokens']+r['completion_tokens']
    assert r['vs_baseline']['total_tokens']==r['total_tokens']-base['total_tokens']
    cost=r['cost_usd']-base['cost_usd']
    assert abs(r['vs_baseline']['cost_usd']-cost)<=Decimal('1e-18')
    wall=None if r['end_to_end_seconds'] is None else r['end_to_end_seconds']-base['end_to_end_seconds']
    if wall is not None:assert abs(wall-r['vs_baseline']['end_to_end_seconds'])<=Decimal('1e-12')
    october.append({'family':r['family'],'tokens':r['total_tokens'],'cost':r['cost_usd'],'additional_cost':cost,'additional_wall_seconds':wall})
timeline=old['wf3_history']['timeline'];all_wf3=old['wf3_history']['all_wf3']
for key in ['prompt_tokens','completion_tokens','total_tokens','captured_actions','cost_usd']:
    assert sum(r[key] for r in timeline)==all_wf3[key],key
assert abs(sum(r['provider_elapsed_seconds'] for r in timeline)-all_wf3['provider_elapsed_seconds'])<Decimal('1e-9')
assert old['rows'][3]['independent_new_two_call_trial'] is False
live=strict(ROOT/LIVE);november=[];bindings=[];reported_costs=[];unknown_cost_records=[]
for r in live['runs']:
    providers=r['provider_records'];known=[];unknown=[]
    for p in providers:
        cost=p.get('cost_usd',(p.get('wire_summary') or {}).get('cost_usd'))
        if cost is None:
            unknown.append(p);unknown_cost_records.append({'run':r['run'],'phase':p['phase'],'failure_class':p.get('failure_class')})
        else:
            assert isinstance(cost,(int,Decimal)) and cost>=0
            known.append(cost);reported_costs.append(cost)
    def total(field):
        vals=[p.get(field,(p.get('wire_summary') or {}).get(field)) for p in providers]
        return sum(vals) if all(v is not None for v in vals) else None
    summary={'run':r['run'],'workflow':r['workflow'],'status':r['outcome'],
         'provider_attempt_records':len(providers),'input_tokens':total('prompt_tokens'),
         'output_tokens':total('completion_tokens'),'cost_usd':sum(known) if not unknown else None,
         'known_reported_cost_subtotal':sum(known),'provider_seconds':total('elapsed_seconds')}
    november.append(summary)
    for p in providers:
        if 'response_raw' not in p:continue
        q=(ROOT/LIVE).parent/p['response_raw'];assert q.resolve().is_relative_to((ROOT/LIVE).parent.resolve())
        b=q.read_bytes();bindings.append({'path':q.relative_to(ROOT).as_posix(),'expected':p['response_sha256'],
            'raw_match':sha(b)==p['response_sha256'],'lf_match':sha(b.replace(b'\r\n',b'\n'))==p['response_sha256']})
known_total=sum(reported_costs)
assert known_total.quantize(Decimal('0.0000001'))==live['total_reported_cost_usd']
out={'status':'complete_bounded_measurement_review','file_reviews':[
    {'path':OLD,'sha256':sha((ROOT/OLD).read_bytes()),'full_source_read':True,
     'reviewed_lines':[[1,len((ROOT/OLD).read_text(encoding='utf-8').splitlines())]],
     'assessment':'Complete historical derived export read. Six baseline/WF rows and eight WF3 attempt records; exact cost/token sums and displayed baseline deltas recomputed. WF3 success is explicitly stitched, baseline task correctness post-hoc and portable full billing/replay sources absent. No model improvement or causal result follows.'},
    {'path':LIVE,'sha256':sha((ROOT/LIVE).read_bytes()),'full_source_read':False,'reviewed_lines':[],
     'assessment':'All17 live-round runs parsed with duplicate/nonfinite rejection; every supplied raw-response SHA binding and available token/cost sum reconciled. Published total rounds known costs including one charged refusal; nine HTTP429 records have unknown cost, not independently established zero liability. Results remain historical reported accounting; no new provider execution or independent billing authentication. Raw/LF mismatches remain explicit.',
     'review_level':'whole_population_provider_metadata_and_raw_digest_checks'}],
    'october':october,'wf3_eight_attempts_sum':all_wf3,'november':november,
    'november_total':live['total_reported_cost_usd'],'known_cost_sum_exact':known_total,
    'unknown_cost_attempt_records':unknown_cost_records,'raw_bindings':bindings,
    'limits':['One public integer-sum task, not the sealed QM benchmark.','Full archived/current checker or provider account replay was not performed.','Rate-limit/no-completion attempts may lack provider records; absent billing cannot be inferred zero solely from a missing record.'],
    'providers_called':0}
(REV/'additional_wiki_measurements.json').write_text(json.dumps(out,indent=2,default=str)+'\n',encoding='utf-8')
print(json.dumps({'october_rows':len(october),'wf3_attempts':len(timeline),'november_runs':len(november),'provider_records':len(bindings),
    'november_total':str(live['total_reported_cost_usd']),'known_exact_total':str(known_total),'unknown_cost_records':len(unknown_cost_records),
    'raw_hash_matches':sum(x['raw_match'] for x in bindings),'lf_hash_matches':sum(x['lf_match'] for x in bindings)}))
