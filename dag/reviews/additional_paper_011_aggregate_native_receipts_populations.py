import collections,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts';D='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/'
rows=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def count(xs):return dict(collections.Counter(map(str,xs)))
def trim(x):
 if isinstance(x,dict):return {k:trim(v) for k,v in x.items() if k not in ('repertoire_after','repertoire_before','raw_span_hex','stdlib_runtime_files','runtime_files','bytes_hex','raw_bytes_hex','source_maps') and not k.endswith('sha256')}
 if isinstance(x,list):return [trim(v) for v in x]
 return x
for r in rows:
 rel=r['relative'];name=Path(rel).name
 if Path(rel).suffix not in ('.json','.jsonl','.bin') or not r['bytes']:continue
 raw=(R/r['path']).read_bytes()
 try:v=[json.loads(l) for l in raw.splitlines() if l.strip()] if rel.endswith('.jsonl') else json.loads(raw)
 except (ValueError,UnicodeDecodeError):continue
 d={'path':r['path'],'sha256':r['sha256'],'root_type':type(v).__name__,'root_keys':list(v) if isinstance(v,dict) else None,'records':len(v) if isinstance(v,list) else None}
 if isinstance(v,list) and v and all(isinstance(x,dict) for x in v):
  d['record_fields']=count('|'.join(sorted(x)) for x in v)
  for k in ('family','grade','verification_status','coverage_class','accepted','dual_rejected','process_exit','binary_key','stdio_capture','event','provider','model','status','terminal','move_type'):
   c=count(x[k] for x in v if k in x)
   if c:d[k]=c
 if name.endswith('observations.jsonl'):
  d['observation_controls']=[{'name':x.get('name'),'family':x.get('family'),'asserted':x.get('asserted'),'passed':x.get('passed'),'grade':x.get('grade'),'actual_expected_equal':canonical(x.get('actual'))==canonical(x.get('expected')) if 'expected' in x else None} for x in v]
  d['asserted_count']=sum(x.get('asserted') is True for x in v);d['passed_count']=sum(x.get('passed') is True for x in v)
  d['claim_flag_disagreements']=[x for x in d['observation_controls'] if x['asserted'] and x['passed']!=x['actual_expected_equal']]
 if name=='challenge_actual_evaluations.jsonl':
  d['dual_result_shapes']=count('|'.join(type(y).__name__ for y in x.get('checks',[])) for x in v)
  d['input_files']=count(x.get('input',{}).get('path') for x in v)
  d['case_ids']=count(x.get('case',{}).get('id',x.get('case',{}).get('case_id')) for x in v)
  d['accepted_check_disagreements']=[i for i,x in enumerate(v) if 'accepted' in x and x.get('checks') and all(isinstance(y,list) and y and type(y[0])==bool for y in x['checks']) and x['accepted']!=all(y[0] for y in x['checks'])]
 if name in ('native_transport_calls.jsonl','native_calls.jsonl'):
  decoded=[]
  for i,x in enumerate(v):
   z={'index':i,'action':x.get('action'),'exit':x.get('process_exit'),'binary':x.get('binary_key')}
   for key in ('request_bytes_hex','stdout_bytes_hex'):
    if key not in x:continue
    try:
     p=json.loads(bytes.fromhex(x[key]));z[key]={'type':type(p).__name__,'keys':list(p) if isinstance(p,dict) else None}
     if isinstance(p,dict):z[key].update({k:p[k] for k in ('action','status','success','error','accepted','message') if k in p})
    except (ValueError,UnicodeDecodeError) as e:z[key]={'not_single_JSON':type(e).__name__}
   decoded.append(z)
  d['decoded_transport_outcomes']=decoded
 if name=='trace.jsonl':
  checks=[];prev='0'*64
  for i,x in enumerate(v):
   payload={k:y for k,y in x.items() if k!='sha256'};variants=[sha(json.dumps(payload,sort_keys=s,ensure_ascii=a,separators=(',',':')).encode()) for s in (False,True) for a in (False,True)]
   checks.append({'index':i,'index_matches':x.get('index')==i,'previous_matches':x.get('prev_sha256')==prev,'self_matches_one_standard_encoding':x.get('sha256') in variants});prev=x.get('sha256')
  d['chain_checks']=checks;d['all_chain_links_match']=all(x['index_matches'] and x['previous_matches'] for x in checks);d['terminal_sha256']=prev
 if name=='transcript.json':
  d['prompt_unique']=len({x.get('prompt') for x in v});d['response_unique']=len({x.get('response') for x in v});d['response_characters']=sum(len(x.get('response','')) for x in v)
  pars=[]
  for i,x in enumerate(v):
   text=x.get('response','');unfenced=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip());item={'index':i,'prompt_sha256':sha(x.get('prompt','').encode()),'response_sha256':sha(text.encode()),'response_chars':len(text)}
   try:item['parsed_response']=json.loads(unfenced)
   except ValueError:item['parsed_response']=None
   pars.append(item)
  d['response_values']=pars
 if isinstance(v,dict):
  d['top_scalars']={k:x for k,x in v.items() if type(x) in (str,int,bool,float,type(None)) and len(str(x))<600 and 'sha' not in k}
  d['container_sizes']={k:len(x) for k,x in v.items() if isinstance(x,(dict,list))}
  if isinstance(v.get('families'),list):d['families']=v['families']
  if isinstance(v.get('result'),dict):
   z=v['result'];d['result_scalars']={k:x for k,x in z.items() if type(x) in (str,int,bool,float,type(None)) and len(str(x))<600 and 'sha' not in k};d['result_container_sizes']={k:len(x) for k,x in z.items() if isinstance(x,(dict,list))}
   if isinstance(z.get('families'),list):d['families']=z['families']
   if 'matrix' in z:
    mat=z['matrix'];d['protocol_runs']=[{'fixture':fixture,'arm':arm,**{k:x for k,x in val.items() if k!='turns'},'turn_host_decisions':count(t.get('host_decision') for t in val.get('turns',[]))} for fixture,arms in mat['runs'].items() for arm,val in arms.items()];d['protocol_totals']={k:x for k,x in mat.items() if k!='runs'}
   if 'cases' in z:d['immune_cases']=[{'case_id':x.get('case_id'),'clean':x.get('clean'),'decision':x.get('immune',{}).get('decision'),'matches':x.get('immune',{}).get('matches'),'host_refusal':x.get('immune',{}).get('host_refusal')} for x in z['cases']]
   if 'screens' in z:d['screens']=trim(z['screens'])
   if 'farm' in z:d['farm']=trim(z['farm'])
  if 'dialogue_audit' in v:d['dialogue_audit']=trim(v['dialogue_audit'])
  for key in ('historical_trace_replays','original_source_tests','restricted_TFI_positive','original_source_projections','dialogue_outcomes','remaining_eight_beat_native_obligations','all_role_comparisons','changes','summary'):
   if key in v:d[key]=trim(v[key])
 out.append(d)
(H/(P+'_populations.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
for d in out:
 rel=d['path'].removeprefix(D)
 if any(k in d for k in ('asserted_count','accepted','dual_rejected','protocol_runs','immune_cases','families')):
  print(rel,{k:d[k] for k in ('records','asserted_count','passed_count','accepted','dual_rejected','claim_flag_disagreements','accepted_check_disagreements') if k in d})
  if 'families' in d:print('families',[(x['id'],x.get('finite_computation_passed'),x.get('explicit_control_outcome')) for x in d['families']])
  if 'protocol_runs' in d:print('protocol',d['protocol_totals'],[(x['fixture'],x['arm'],x.get('terminal_label'),x.get('provider_calls')) for x in d['protocol_runs']])
  if 'immune_cases' in d:print('immune',len(d['immune_cases']),count(x['decision'] for x in d['immune_cases']),'screens',[(x.get('decision'),x.get('host_refusal')) for x in d['screens']])
