"""Comprehensive structural checks, not human body or proof receipts."""
import collections,hashlib,json,re
from pathlib import Path
H=Path(__file__).parent
rows=json.loads((H/'additional_eis_pciv_remaining_scan.json').read_text())
metrics={}
def walk(x,path='$'):
 yield path,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,path+'/'+k)
 if isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+'/'+str(i))
for r in rows:
 if 'data' not in r:continue
 p=r['path'];d=r['data'];m={'sha256':r['sha256'],'duplicate_json_keys':r.get('duplicate_json_keys',[]),'method':'whole_parsed_structure_schema_and_arithmetic_only','full_source_read':False}
 if p.endswith('pharmacy_catalog.json'):
  vals=d['antibodies'];m['records']=len(vals)
  m['classes']=dict(collections.Counter(v.get('failure_class') for v in vals.values()))
  m['status_counts']=dict(collections.Counter(v.get('pharmacy_status') for v in vals.values()))
  m['admitted_without_admission']=[k for k,v in vals.items() if v.get('pharmacy_status')=='admitted' and not v.get('admission')]
  m['invalid_evidence_digest_shape']=[k for k,v in vals.items() if not re.fullmatch('[0-9a-f]{64}',str(v.get('evidence_sha256','')))]
  m['id_key_mismatches']=[k for k,v in vals.items() if k!=v.get('antibody_id')]
  m['general_templates']={key:dict(collections.Counter(json.dumps(v.get(key),sort_keys=True,ensure_ascii=False) for v in vals.values() if v.get('failure_class')=='general_obstruction')) for key in ('description','positive_fixture','negative_fixture','constraint_type','action','severity')}
  m['root_file_comparisons']=[]
  for rr in rows:
   if rr['path'].startswith('eis/antibodies/ab_') or rr['path'].startswith('eis/antibodies/candidates/'):
    item=rr['data'];v=vals.get(item.get('antibody_id'));m['root_file_comparisons'].append({'path':rr['path'],'present':v is not None,'equal':v==item,'different_fields':[] if v is None else sorted(k for k in set(v)|set(item) if v.get(k)!=item.get(k))})
  m['managed_projections']=d.get('managed_projections');m['metadata']={k:v for k,v in d.items() if k not in ('antibodies','managed_projections')}
 elif '/receipts/' in p:
  m['top_level']=sorted(d) if isinstance(d,dict) else 'list';m['records_count']=len(d.get('records',[])) if isinstance(d,dict) else len(d)
  m['embedded_output_hash_checks']=[]
  for loc,v in walk(d):
   if isinstance(v,dict) and isinstance(v.get('output_utf8'),str) and 'output_sha256' in v:
    m['embedded_output_hash_checks'].append({'location':loc,'valid':hashlib.sha256(v['output_utf8'].encode()).hexdigest()==v['output_sha256'].removeprefix('sha256:'),'exit_status':v.get('exit_status'),'output_chars':len(v['output_utf8'])})
  m['mutation_summary']=[]
  for v in (d if isinstance(d,list) else d.get('mutations',[])):
   m['mutation_summary'].append({k:v[k] for k in ('id','mutant_id','file','target','mutated_from','mutated_to','anchor','applied','mutant_exit','restored_exit','detected','restored','status','digest_before','digest_restored') if k in v})
  m['record_summary']=[{k:v[k] for k in ('name','check','label','command','exit_status','status','duration_ms','output_sha256') if k in v} for v in d.get('records',[])] if isinstance(d,dict) else []
  m['retained_obligations']=d.get('retained_obligations',[]) if isinstance(d,dict) else []
  m['status']=d.get('status') if isinstance(d,dict) else None
 elif p.endswith('evidence_mined_candidates.json'):
  vals=d['candidates'];m['records']=len(vals);m['unique_candidate_ids']=len({v['candidate_id'] for v in vals});m['duplicate_ids']={k:n for k,n in collections.Counter(v['candidate_id'] for v in vals).items() if n>1}
  m['status_counts']=dict(collections.Counter(v['status'] for v in vals));m['auto_admit']=d.get('auto_admit');m['human_review_required']=all(v['activation_kind']=='human_review_required' for v in vals)
  m['candidate_claims']=[{k:v[k] for k in ('name','failure_code','proposed_invariant','counterexamples','protected_fields','context_keys')} for v in vals]
 else:continue
 metrics[p]=m
(H/'additional_eis_pciv_remaining_artifacts.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p,m in metrics.items():
 print(p)
 if 'records' in m:print({k:m[k] for k in ('records','unique_candidate_ids','status_counts','human_review_required') if k in m})
 if p.endswith('pharmacy_catalog.json'):
  print('ADMITTED_WITHOUT_RECORD',len(m['admitted_without_admission']),'BAD_DIGEST_SHAPE',len(m['invalid_evidence_digest_shape']),'KEY_ID_MISMATCHES',len(m['id_key_mismatches']))
  print('ROOT_COMPARISONS',collections.Counter((v['present'],v['equal']) for v in m['root_file_comparisons']))
  print('GENERAL_TEMPLATE_COUNTS',{k:len(v) for k,v in m['general_templates'].items()})
  for k in ('constraint_type','action','severity'):print(k,m['general_templates'][k])
 if '/receipts/' in p:
  print('STATUS',m['status'],'RECORDS',m['records_count'],'OUTPUT_HASH_CHECKS',len(m['embedded_output_hash_checks']),'FAILURES',[v for v in m['embedded_output_hash_checks'] if not v['valid']])
  print('MUTATIONS',json.dumps([{k:v for k,v in mm.items() if not isinstance(v,dict)} for mm in m['mutation_summary']]))
  print('RECORDS',len(m['record_summary']))
