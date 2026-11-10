"""Independent, read-only population consistency checks. Does not execute receipts."""
import base64,collections,hashlib,json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_paper_011_recreated_receipts';B='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/';RUN=B+'docs/recreated_run/'
scope=json.loads((H/(P+'_scope.json')).read_text());files={x['path']:x for x in scope['files']};prep={x['path']:x for x in json.loads((H/(P+'_preparation.json')).read_text())['files']};cache={}
def load(p):
 if p not in cache:
  raw=(R/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==files[p]['sha256']
  cache[p]=[json.loads(x)for x in raw.splitlines()]if p.endswith('.jsonl')else json.loads(raw)
 return cache[p]
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def digest(x):return hashlib.sha256(x).hexdigest()
def mapped(s):
 s=s.replace('\\','/');marker='011_recreated_demos_and_proposal_fidelity_evidence/'
 return B+s.split(marker,1)[1]if marker in s else s
def flag(x):
 if type(x)is bool:return x
 if isinstance(x,list)and x and type(x[0])is bool:return x[0]
 if isinstance(x,dict):
  for k in ['valid','passed','accepted','ok','success','verified']:
   if type(x.get(k))is bool:return x[k]
  v=str(x.get('verdict','')).upper()
  if v in {'PASS','ACCEPT','VALID','VERIFIED'}:return True
  if v in {'FAIL','REFUSE','REJECT','INVALID'}:return False
 return None
def kind(a):
 if not isinstance(a,dict):return 'UNLABELED'
 s=a.get('status',a.get('verdict'))
 if s=='UNKNOWN':return 'ABSTENTION'
 if s in {'REFUSED','OUT_OF_SCOPE','UNSUPPORTED','NO_SOLUTION','REFUSE','NO_NATIVE_PORT','UNSUPPORTED_NATIVE_PORT'}:return 'TYPED_REFUSAL'
 if s in {'INCONSISTENT','UNSAT','UNSATISFIABLE','INFEASIBLE'}or a.get('kind')in {'DOES_NOT_EXIST','NOT_ADJOINT','UNSAT','REFUTATION'}:return 'NEGATIVE_CLAIM'
 if 'verdict'in a and 'status'not in a:return 'CLASSIFIER_DECISION'
 return 'CANDIDATE'
checks={p:{}for p in files};leafs=[];batches=[];matrices=[];streams=[];native=[]
for p,x in files.items():
 name=pathlib.PurePosixPath(p).name
 if not p.endswith(('.json','.jsonl','.oeos-envelope')):continue
 d=load(p);c=checks[p]
 if isinstance(d,dict)and'receipt_sha256'in d:
  c['self_digest']={'recorded':d['receipt_sha256'],'computed':digest(canon({k:v for k,v in d.items()if k!='receipt_sha256'}))};c['self_digest']['matches']=c['self_digest']['recorded']==c['self_digest']['computed']
  c['canonical_file_bytes_match']=(R/p).read_bytes()==canon(d)
 if name=='job.json':
  cap=d['capability'];c.update(id=d['row'].get('id'),kind=d['kind'],row_digest=digest(canon(d['row'])),capability_digest=digest(canon(cap)),capability_inventory_count=len(cap['files']),binary_pins=cap['binaries'],runtime_claim=cap['python'],source_git_head=cap.get('source_git_head'),source_to_binary_provenance=cap.get('source_to_binary_provenance'),capability_inventory_all_sha256=all(re.fullmatch('[0-9a-f]{64}',v)for v in cap['files'].values()),declared_cases=len(d['row'].get('cases',[])),declared_mutations=len(d['row'].get('mutations',[])),control_file_pins=d.get('control_files',{}),row_keys=list(d['row']))
 elif name.startswith('engine_capability'):
  c.update(capability_digest=digest(canon(d)),inventory_count=len(d['files']),inventory_all_sha256=all(re.fullmatch('[0-9a-f]{64}',v)for v in d['files'].values()),binary_pins=d['binaries'],runtime_claim=d['python'],source_to_binary_provenance=d.get('source_to_binary_provenance'))
 elif name=='import_adaptations.json':
  source_rows=[r for r in d if 'path'in r];transport_rows=[r for r in d if 'binary_name'in r]
  c.update(records=len(d),source_rows=len(source_rows),native_transport_rebindings=transport_rows,paths_unique=len({r['path']for r in source_rows})==len(source_rows),all_hash_fields_valid=all(re.fullmatch('[0-9a-f]{64}',r[k])for r in source_rows for k in ['source_sha256','transformed_sha256']),declared_changes=dict(collections.Counter(v['kind']for r in source_rows for v in r['allowed_changes'])),unchanged_hashes=sum(r['source_sha256']==r['transformed_sha256']for r in source_rows),semantic_equivalence='Not established by hash pairs or declared allowed_changes; transformer overreach documented in P011CORE-F10.')
 elif name=='evaluations.jsonl':
  counts=collections.Counter();classes=collections.Counter();statuses=collections.Counter();issues=[];inputs=[];mutrefs=[];mutants=set();errors=[];accepted_classes=collections.Counter();mutation=collections.Counter()
  for lineno,event in enumerate(d,1):
   fs=[flag(v)for v in event.get('checks',[])];is_mut=any(k in event for k in ['mutation','checker_mutant','supplemental_control'])
   if is_mut:
    counts['mutation_records']+=1
    if'mutation'in event:mutrefs.append(event['mutation'])
    if'checker_mutant'in event:mutants.add(event['checker_mutant'])
    if 'kill_by_exception'in event or'error'in event:mutation['execution_errors']+=1;errors.append({'line':lineno,'error':event.get('kill_by_exception',event.get('error'))})
    elif event.get('status')=='MALFORMED_SOURCE_BYTES_REFUSED':mutation['malformed_bytes_refused']+=1
    elif str(event.get('status','')).startswith('UNBOUND_MUTATION'):mutation['unbound_records']+=1
    elif 'checks'in event:
     dual=len(fs)>=2 and all(v is False for v in fs);allrej=bool(fs)and all(v is False for v in fs)
     mutation['dual_rejections']+=dual;mutation['all_declared_rejections']+=allrej;mutation['joint_detections']+=any(v is False for v in fs);mutation['disagreements']+=True in fs and False in fs;mutation['incomparable']+=any(v is None for v in fs);mutation['both_accept']+='checker_mutant'not in event and bool(fs)and all(v is True for v in fs)
     for key in ['both_reject','dual_rejected','dual_rejection']:
      if key in event and event[key]!=allrej:issues.append({'line':lineno,'field':key,'recorded':event[key],'computed':allrej})
   else:
    counts['case_records']+=1;cl=kind(event.get('answer'));classes[cl]+=1
    a=event.get('answer');statuses[str(a.get('status',a.get('verdict','UNLABELED'))if isinstance(a,dict)else'NON_OBJECT')]+=1
    if'input'in event:inputs.append(event['input'])
    if'error'in event:counts['case_errors']+=1;errors.append({'line':lineno,'error':event['error']})
    elif'checks'in event:
     computed=bool(fs)and all(v is True for v in fs)and cl!='ABSTENTION';counts['accepted']+=computed;counts['both_accept']+=len(fs)>=2 and computed;counts['incomparable_case_checks']+=any(v is None for v in fs)
     if computed:accepted_classes[cl]+=1
     if event.get('accepted')!=computed:issues.append({'line':lineno,'field':'accepted','recorded':event.get('accepted'),'computed':computed})
  c.update(records=len(d),counts=dict(counts),candidate_classes=dict(classes),accepted_classes=dict(accepted_classes),answer_statuses=dict(statuses),mutation_outcomes=dict(mutation),distinct_checker_mutants=len(mutants),result_flag_mismatches=issues,execution_errors=errors,input_reference_count=len(inputs),unique_input_references=len({canon(v)for v in inputs}),mutation_reference_count=len(mutrefs),unique_mutation_references=len({canon(v)for v in mutrefs}))
  job=str(pathlib.PurePosixPath(p).parent/'job.json')
  if job in files:
   row=load(job)['row'];expected=row.get('cases',[]);declared=row.get('mutations',[]);c['job_case_reference_sequence_matches']=inputs==expected;c['job_case_reference_subset']=all(v in expected for v in inputs);c['job_mutation_reference_sequence_matches']=mutrefs==declared;c['declared_cases']=len(expected);c['declared_mutation_refs']=len(declared)
  streams.append({'path':p,**c})
 elif name=='native_transport_calls.jsonl':
  errors=[];exits=collections.Counter();captures=collections.Counter();binaries=collections.Counter();responses=collections.Counter();work_count=0;raw_sizes=collections.Counter();job=str(pathlib.PurePosixPath(p).parent/'job.json');pins=load(job)['capability']['binaries']if job in files else{}
  for lineno,event in enumerate(d,1):
   exits[str(event['process_exit'])]+=1;captures[event.get('stdio_capture','LEGACY_DECODED_OR_UNSPECIFIED')]+=1;binaries[event.get('binary_key',event['binary_sha256'])]+=1
   if event['binary_sha256']not in {q['sha256']for q in pins.values()}:errors.append({'line':lineno,'kind':'binary_not_in_job_capability'})
   for fld in ['request_bytes_hex','stdout_bytes_hex','stderr_bytes_hex']:
    try:raw=bytes.fromhex(event[fld]);raw_sizes[fld]+=len(raw)
    except ValueError:errors.append({'line':lineno,'kind':'invalid_hex','field':fld});continue
    if fld=='stdout_bytes_hex'and event.get('binary_key')!='lean':
     try:reply=json.loads(raw);responses[str(reply.get('status',reply.get('success'))if isinstance(reply,dict)else type(reply).__name__)]+=1
     except ValueError:responses['non_JSON_stdout']+=1
   for stage in ['work_files_before','work_files_after']:
    for filename,binding in event.get(stage,{}).items():
     work_count+=1
     if digest(bytes.fromhex(binding['bytes_hex']))!=binding['sha256']:errors.append({'line':lineno,'kind':'work_snapshot_sha_mismatch','stage':stage,'filename':filename})
   for filename,binding in event.get('work_files_before',{}).items():
    if filename.endswith('.lean')and event.get('work_files_after',{}).get(filename)!=binding:errors.append({'line':lineno,'kind':'Lean_input_changed','filename':filename})
  c.update(records=len(d),exits=dict(exits),capture_modes=dict(captures),binary_population=dict(binaries),response_statuses=dict(responses),embedded_work_snapshot_bindings_checked=work_count,decoded_byte_counts=dict(raw_sizes),binding_errors=errors)
  native.append({'path':p,**c})
 elif name=='execution_configuration.json':c.update(dont_write_bytecode=d.get('dont_write_bytecode'),initial_cache_entries=d.get('initial_cache_entries'),runtime_environment=d.get('runtime_environment'),pycache_prefix_recorded=bool(d.get('pycache_prefix')))
 elif p.endswith('.oeos-envelope'):
  ciphertext=base64.b64decode(d['ciphertext_base64'],validate=True);c.update(schema=d['schema'],artifact_schema=d['artifact_schema'],protector_id=d['protector_id'],declared_byte_length=d['byte_length'],decoded_ciphertext_bytes=len(ciphertext),plaintext_sha256=d['plaintext_sha256'],plaintext_recovery='Not attempted; opaque encrypted content receives no semantic/full-read credit.')
for p,x in files.items():
 name=pathlib.PurePosixPath(p).name
 if name=='recreation_receipt.json':
  d=load(p);c=checks[p];parent=str(pathlib.PurePosixPath(p).parent);art=[]
  for rel,pin in d['artifacts_sha256'].items():
   target=parent+'/'+rel;art.append({'artifact':rel,'expected':pin,'current':files.get(target,{}).get('sha256'),'matches':files.get(target,{}).get('sha256')==pin,'in_assigned_scope':target in files})
  member_paths={parent+'/'+s for s in d['artifacts_sha256']};unlisted=[s for s in files if s.startswith(parent+'/')and s!=p and s not in member_paths]
  job=parent+'/job.json';worker=parent+'/worker_result.json';j=load(job);result=d['result'];c.update(id=d['id'],kind=d['kind'],status=result.get('status'),grade=result.get('grade'),process_exit=d['process_exit'],model_calls=d['model_calls'],model_accuracy=d['model_accuracy'],counts=result.get('counts'),artifact_bindings=art,unlisted_assigned_descendants=unlisted,job_id_matches=j['row'].get('id')==d['id'],job_kind_matches=j['kind']==d['kind'],job_row_digest_matches=digest(canon(j['row']))==d['catalog_row_sha256'],job_capability_digest_matches=digest(canon(j['capability']))==d['capability_sha256'],worker_result_matches=(load(worker)==result if worker in files else None),runner_sha_matches_job=(j.get('runner_sha256')==d.get('runner_sha256')if'runner_sha256'in j else None),custody_recheck=d.get('custody_recheck'))
  ep=parent+'/evaluations.jsonl'
  if ep in checks and c['counts']:
   ec=checks[ep];compare={'cases':ec['counts'].get('case_records',0),'both_accept':ec['counts'].get('both_accept',0),'abstentions':ec['candidate_classes'].get('ABSTENTION',0),'accepted_typed_refusals':ec['accepted_classes'].get('TYPED_REFUSAL',0),'accepted_negative_claims':ec['accepted_classes'].get('NEGATIVE_CLAIM',0),'accepted_non_refusal_outputs':ec['accepted_classes'].get('CANDIDATE',0),'accepted_classifier_decisions':ec['accepted_classes'].get('CLASSIFIER_DECISION',0),'mutation_execution_errors':ec['mutation_outcomes'].get('execution_errors',0),'mutation_checker_disagreements':ec['mutation_outcomes'].get('disagreements',0),'both_reject':ec['mutation_outcomes'].get('dual_rejections',0)};c['count_comparisons']={k:{'recorded':c['counts'][k],'computed_from_retained_stream':v,'matches':c['counts'][k]==v}for k,v in compare.items()if k in c['counts']}
  leafs.append({'path':p,**c})
 elif name=='batch_receipt.json':
  d=load(p);c=checks[p];parent=str(pathlib.PurePosixPath(p).parent);items=[]
  for run in d['runs']:
   leaf=parent+'/'+run['id']+'/recreation_receipt.json';z=load(leaf)if leaf in files else{};items.append({'id':run['id'],'in_assigned_scope':leaf in files,'recorded_leaf_self_digest_matches':z.get('receipt_sha256')==run['receipt_sha256'],'status_matches':z.get('result',{}).get('status')==run['result_status'],'exit_matches':z.get('process_exit')==run['process_exit']})
  c.update(run_count=len(items),unique_ids=len({x['id']for x in items}),status_population=dict(collections.Counter(x['result_status']for x in d['runs'])),exit_population=dict(collections.Counter(str(x['process_exit'])for x in d['runs'])),full_catalog_requested=d['full_catalog_requested'],requested_ids_complete=d['requested_ids_complete'],all_demonstrations_completed=d['all_demonstrations_completed'],leaf_binding_checks=items);batches.append({'path':p,**c})
 elif name.startswith('coverage_matrix_'):
  d=load(p);c=checks[p];rows=[];closures=[]
  for z in d['rows']:
   target=mapped(z['receipt_path']);leaf=load(target)if target in files else{};rows.append({'id':z['id'],'target':target,'in_assigned_scope':target in files,'receipt_bytes_match':files.get(target,{}).get('sha256')==z['receipt_bytes_sha256'],'recorded_status_matches':leaf.get('result',{}).get('status')==z['recorded_status'],'process_exit_matches':leaf.get('process_exit')==z['process_exit'],'counts_match':leaf.get('result',{}).get('counts')==z['counts'],'recorded_status':z['recorded_status'],'audited_execution_status':z['audited_execution_status'],'candidate_kinds':z['candidate_kinds'],'mutation_outcomes':z['mutation_outcomes'],'unresolved_inputs':len(z['unresolved_case_inputs'])})
  for z in d['batch_closures']:
   target=mapped(z['path']);closures.append({'target':target,'raw_sha_match':files.get(target,{}).get('sha256')==z['sha256'],'recorded_self_digest_match':load(target).get('receipt_sha256')==z['receipt_sha256']if target in files else False})
  c.update(declared_entries=d['declared_entries'],row_count=len(rows),unique_ids=len({x['id']for x in rows}),all_recreations_completed=d['all_recreations_completed'],row_bindings=rows,batch_bindings=closures,supplemental_candidates=d.get('supplemental_candidate_checks',[]));matrices.append({'path':p,**c})
out={'source_commit':scope['source_commit'],'per_file_checks':checks,'leaf_runs':leafs,'batches':batches,'coverage_matrices':matrices,'evaluation_streams':streams,'native_transport_streams':native,'limits':'All checks operate only on frozen public receipt bytes. Historical absolute paths are mapped only when they identify an assigned paper path; no foreign file or binary is opened, no historical command executed. Boolean/status reconciliation does not prove checker mathematics, authenticity, independence or new execution.'}
(H/(P+'_population_checks.json')).write_text(json.dumps(out,indent=2)+'\n')
summary={'leaves':len(leafs),'batches':len(batches),'overlays':len(matrices),'evaluation_streams':len(streams),'native_transport_streams':len(native),'self_digests':dict(collections.Counter(str(c['self_digest']['matches'])for c in checks.values()if'self_digest'in c)),'leaf_artifact_bindings':dict(collections.Counter(str(a['matches'])for c in leafs for a in c['artifact_bindings'])),'worker_equality':dict(collections.Counter(str(c['worker_result_matches'])for c in leafs)),'native_events':sum(x['records']for x in native),'work_snapshot_bindings':sum(x['embedded_work_snapshot_bindings_checked']for x in native),'native_binding_errors':sum(len(x['binding_errors'])for x in native),'evaluation_records':sum(x['records']for x in streams),'flag_mismatches':sum(len(x['result_flag_mismatches'])for x in streams)}
(H/(P+'_population_summary.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
