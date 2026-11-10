"""Bounded independent arithmetic and role-specific record controls; no source imports."""
from fractions import Fraction as Q
import collections,hashlib,itertools,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_paper_011_recreated_receipts';B='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/recreated_run/'
scope=json.loads((H/(P+'_scope.json')).read_text());files={x['path']:x for x in scope['files']};population=json.loads((H/(P+'_population_checks.json')).read_text());extra={};controls=[]
def get(p):
 raw=(R/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==files[p]['sha256'];return [json.loads(s)for s in raw.splitlines()]if p.endswith('.jsonl')else json.loads(raw)
def mat(a):return[[Q(x)for x in r]for r in a]
def vec(a):return[Q(x)for x in a]
def mv(a,v):assert all(len(r)==len(v)for r in a);return[sum(x*y for x,y in zip(r,v))for r in a]
def tr(a):assert a and len({len(r)for r in a})==1;return list(map(list,zip(*a)))
def certificate(a,f,p,y,w,reported):
 assert len(a)==len(f)==len(y)==len(w)and all(v>0 for v in w)
 residual=[v-z for v,z in zip(f,mv(a,p))];primal=sum(v*abs(z)for v,z in zip(w,residual));dual=sum(v*z for v,z in zip(f,y));ann=mv(tr(a),y);bounded=all(abs(v)<=z for v,z in zip(y,w))
 return {'primal':str(primal),'dual':str(dual),'reported':str(reported),'annihilator_zero':not any(ann),'dual_feasible':bounded,'exact_zero_gap':primal==dual==reported,'residual':list(map(str,residual))}
# Every supplied positive C011 certificate in this selected46-case stream.
p=B+'full_v2/C011/evaluations.jsonl';positive=[]
for line,e in enumerate(get(p),1):
 if 'input'not in e or not e.get('accepted')or e['answer'].get('status')!='SOLVED':continue
 c=e['case'];a=e['answer'];vs=c['vertices'];matrix=[];f=[];w=[];dual=[]
 for edge in c['edges']:
  row=[Q(0)]*len(vs);row[vs.index(edge['u'])]-=1;row[vs.index(edge['v'])]+=1;matrix.append(row);f.append(Q(edge['claim']));w.append(Q(edge['weight']));dual.append(Q(a['dual'].get(edge['id'],'0')))
 v=certificate(matrix,f,[Q(a['potential'][k])for k in vs],dual,w,Q(a['phi1']));positive.append({'line':line,'id':c['id'],**v})
assert len(positive)==46 and all(x['annihilator_zero']and x['dual_feasible']and x['exact_zero_gap']for x in positive)
controls.append({'kind':'exact rational primal-dual reconstruction','path':p,'cases':positive,'limits':'46 positive retained certificates only. Reconstructs finite LP optimum via matching feasible primal/dual values; does not validate all refusals, mutant grammar, global solver completeness or original input-file byte authenticity.'})
# Every explicitly positive local-complement sequence, not negative non-equivalence claims.
p=B+'final_bindings_v4/C024/evaluations.jsonl';lc=[];not_replayed=[]
for line,e in enumerate(get(p),1):
 if 'input'not in e:continue
 a=e.get('answer',{});c=e['case']
 if a.get('status')!='SOLVED'or not a.get('equivalent'):not_replayed.append({'line':line,'status':a.get('status'),'equivalent':a.get('equivalent')});continue
 edges={tuple(sorted(v))for v in c['g']}
 for vertex in a['sequence']:
  assert 0<=vertex<c['num_vertices'];neighbors={b if a==vertex else a for a,b in edges if vertex in(a,b)}
  for pair in itertools.combinations(sorted(neighbors),2):
   if pair in edges:edges.remove(pair)
   else:edges.add(pair)
 match=edges=={tuple(sorted(v))for v in c['g_prime']};assert match;lc.append({'line':line,'id':c['id'],'sequence_length':len(a['sequence']),'target_matches':match})
controls.append({'kind':'independent finite graph local complementation','path':p,'positive_sequences':lc,'other_original_records_not_solved':not_replayed,'limits':'Only supplied positive sequences are replayed. No exhaustive orbit search, negative-equivalence theorem or new model result.'})
# All six composed Phi2/Phi3/Phi4 request witnesses, plus consecutive boundary products.
compositions=[]
for rel,degree,flux,pot in [('composed_phi2_v6/demo_6/native_transport_calls.jsonl',2,'flux_b','potential_a'),('composed_phi3_phi4_v7/demo_7/native_transport_calls.jsonl',3,'flux_h','potential_b'),('composed_phi3_phi4_v7/demo_9/native_transport_calls.jsonl',4,'flux_g','potential_c')]:
 path=B+rel
 for line,e in enumerate(get(path),1):
  req=json.loads(bytes.fromhex(e['request_bytes_hex']));resp=json.loads(bytes.fromhex(e['stdout_bytes_hex']));ds=[mat(req['d'+str(i)])for i in range(degree)];v=certificate(ds[-1],vec(req[flux]),vec(req[pot]),vec(req['dual_witness']),vec(req['weights']),Q(req['reported_value']));chain=[]
  for i in range(1,degree):chain.append(all(not any(mv(ds[i],col))for col in tr(ds[i-1])))
  v.update(path=path,line=line,degree=degree,chain_products_zero=chain,stored_residual_matches=v['residual']==list(map(str,vec(req['primal_residual']))),historical_native_value_matches=Q(resp['reported_value'])==Q(v['reported']),historical_native_status=resp['status'])
  assert v['annihilator_zero']and v['dual_feasible']and v['exact_zero_gap']and all(chain)and v['stored_residual_matches']and v['historical_native_value_matches'];compositions.append(v)
controls.append({'kind':'exact finite composed LP witness reconstruction','cases':compositions,'limits':'Six fixed declared cochain carriers only. Mathematical optimum follows conditional on supplied matrix/flux/weight encoding; no topology, cup product, manifold, physics or native binary replay is inferred.'})
for path,x in files.items():
 name=pathlib.PurePosixPath(path).name
 if name=='native_calls.jsonl':
  rows=get(path);c={'records':len(rows),'actions':dict(collections.Counter(r['action']for r in rows)),'success_flags':dict(collections.Counter(str(r['response'].get('success'))for r in rows)),'action_response_alignment':all(r['action']==r['response'].get('action')for r in rows),'finite_certificate_controls':[]}
  for i,r in enumerate(rows,1):
   req=r['request'];resp=r['response'];v=None
   if r['action']=='exact_solve_l1_primal_dual'and resp.get('success'):
    z=resp['result'];v=certificate(mat(req['matrix']['rows']),vec(req['target']),vec(z['alpha']),vec(z['dual_witness']),vec(req['weights']),Q(z['phi1']))
   elif r['action']=='verify_l1_certificate'and resp.get('success')and resp['result'].get('accepted'):
    z=resp['result']['certificate'];v=certificate(mat(req['matrix']['rows']),vec(req['omega']),vec(req['p']),vec(req['y']),[Q(1)]*len(req['omega']),Q(z['dual_value']))
   if v is not None:c['finite_certificate_controls'].append({'line':i,**v});assert v['annihilator_zero']and v['dual_feasible']and v['exact_zero_gap']
  extra[path]=c
 elif name=='trace.jsonl':
  rows=get(path);hashed=[r for r in rows if'sha256'in r];extra[path]={'events':[r['event']for r in rows],'records':len(rows),'hashed_records':len(hashed),'sequential_indices':all(r.get('index')==i for i,r in enumerate(hashed))if hashed else None,'previous_digest_chain_matches':all(r['prev_sha256']==('0'*64 if i==0 else hashed[i-1]['sha256'])for i,r in enumerate(hashed))if hashed else None,'terminal_seal_present':any('sealed'in r['event'].lower()for r in rows),'limit':'Validating index/previous-link continuity only; does not authenticate source, event hash framing, event truth or durability.'}
 elif name=='answers.jsonl':
  rows=get(path);parent=str(pathlib.PurePosixPath(path).parent);receipt=get(parent+'/receipt.json');ids=[r.get('case_id',r.get('id'))for r in rows];statuses=collections.Counter((r.get('solution')or r).get('status')for r in rows);c={'records':len(rows),'unique_ids':len(set(ids)),'status_counts':dict(statuses),'ids':ids}
  if'solutions'in receipt:c['exact_solution_and_check_members_match']=all(r['solution']==receipt['solutions'][r['case_id']]and r['check']==receipt['cert_checks'][r['case_id']]for r in rows);c['receipt_population_matches']=len(rows)==receipt['total_cases_evaluated']and set(ids)==set(receipt['cases_evaluated'])
  else:c['receipt_count_matches']=len(rows)==receipt['total_cases_evaluated'];c['recorded_solved_matches']=statuses.get('SOLVED',0)==receipt['solved_cases_count'];c['recorded_out_of_scope_matches']=statuses.get('OUT_OF_SCOPE',0)==receipt['out_of_scope_cases_count'];c['limit']='Population/status reconciliation only; basis/energy/decomposition matrices are historical candidates, not freshly checked quantum eigenpairs.'
  extra[path]=c
 elif name=='receipt.json'and'/engine_run/'in path:
  d=get(path);result=d.get('result',d);c={'status':result.get('status',d.get('status',d.get('verdict'))),'schema':d.get('schema',d.get('schema_version')),'scope':d.get('scope',result.get('scope')),'role':'Historical engine output distinct from caller leaf; source fixture/native capability and mathematical target must be bound separately.'}
  if isinstance(result,dict)and'levels'in result:
   levels=result['levels'];events=[v for vs in levels.values()for v in vs];ring=result['product_cell_ring'];c.update(levels=len(levels),exact_000_100_census=set(levels)=={f'mss-{i:03}'for i in range(101)},cases=len(events),case_ids_unique_within_level=all(len({r['case_id']for r in vs})==len(vs)for vs in levels.values()),recorded_expectation_flags_consistent=all(r['matches_expectation']==([r['outcome'],r['code']]==r['expected'])for r in events),expectation_failures=sum(not r['matches_expectation']for r in events),product_pairings=len(ring['pairings']),product_pairings_2pq=all(Q(v['pairing'])==2*Q(v['p'])*Q(v['q'])for v in ring['pairings']),product_carrier_scope=ring['scope'])
  if isinstance(result,dict)and isinstance(result.get('cases'),list)and'screens'in result:
   cases=result['cases'];screens=result['screens'];c.update(pharmacology_cases=len(cases),case_ids_unique=len({r['case_id']for r in cases})==len(cases),clean_flags_match_empty_matches=all(r['clean']==(not r['immune']['matches'])for r in cases),screen_count=len(screens),screen_decisions=[r['decision']for r in screens],signal2_population=dict(collections.Counter(str(r.get('signal2'))for r in screens)),thymus_rule_counts=dict(collections.Counter(len(r['immune']['thymus_admitted'])for r in cases)),repertoire_rows=sum(len(r['immune']['repertoire_after'])for r in cases),scope_limit='Finite scripted pharmacology examples, not detector adequacy, independent signals, learning or model efficacy.')
  if'cells'in d:
   cells=d['cells'];expected={(a,f)for a in d['arms']for f in d['fixtures']};actual={(r['arm'],r['fixture_id'])for r in cells};c.update(cells=len(cells),arms=len(d['arms']),fixtures=len(d['fixtures']),cartesian_census=actual==expected and len(cells)==len(expected),live_enabled=d['live_enabled'],route=d['route'],terminal_counts=dict(collections.Counter(str(r['terminal_exit'])for r in cells)),step_count=sum(len(r['steps'])for r in cells),scope_limit='Supplied protocol traces under unavailable native route; no empirical six-arm experiment or independent solver theorem.')
  if'solutions'in d:
   c.update(solution_count=len(d['solutions']),case_count=len(d['input_cases']),unique_case_ids=len({r['case_id']for r in d['input_cases']}),certificate_pass_count=sum(r['passed']for r in d['cert_checks'].values()),recorded_certificate_count_matches=sum(r['passed']for r in d['cert_checks'].values())==d['certificate_checks_passed'],capability_pass=d['capability_pass'],provenance_status=d['provenance_status'])
  if'controls_evaluation'in d:
   c.update(control_records=len(d['controls_evaluation']),invariance_count=sum(r['invariant']for r in d['controls_evaluation']),invariance_flags_consistent=all(r['invariant']==(r['dimension_match']and r['energy_match']and r['status_match'])for r in d['controls_evaluation']),model_billing=d['openrouter_accounting'],provenance_status=d['provenance_status'])
  if'cases'in d and isinstance(d['cases'],list):c.update(case_count=len(d['cases']),statuses=dict(collections.Counter(str(r.get('status'))for r in d['cases'])),codes=dict(collections.Counter(str(r.get('code'))for r in d['cases'])))
  extra[path]=c
 elif name=='stdout.txt'and x['bytes']>10000:
  text=(R/path).read_text();decoder=json.JSONDecoder();objects=[];at=0
  while at<len(text):
   while at<len(text)and text[at].isspace():at+=1
   if at==len(text):break
   value,end=decoder.raw_decode(text,at);objects.append(value);at=end
  extra[path]={'complete_JSON_object_stream':True,'objects':len(objects),'top_level_keys':[list(o)if isinstance(o,dict)else type(o).__name__ for o in objects],'status_labels':[o.get('status',o.get('result'))if isinstance(o,dict)and not isinstance(o.get('result'),(dict,list))else None for o in objects],'limit':'Whole text parsed and object roles inspected; large nested receipt values remain bounded data review, not full human source reading. Corresponding engine receipt population supplies substantive checks.'}
 elif'/quarantine/'in path:
  d=get(path);extra[path]={'fields':d,'limit':'Retained quarantine rule disposition for supplied fixture; digest, matching and permanent flags are not current promoted authority or detector adequacy.'}
out={'controls':controls,'per_file_checks':extra,'limits':'Fresh deterministic Python Fraction/finite-graph checks only; no imported production checker, native rebuild/call, provider, private benchmark, original source mutation or historical command execution.'}
(H/(P+'_controls.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'independent_C011_certificates':len(positive),'independent_positive_C024_sequences':len(lc),'native_composition_witnesses':len(compositions),'additional_artifact_roles':len(extra)},indent=2))
