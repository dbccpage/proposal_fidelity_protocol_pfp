"""Bounded schema-specific JSON dispositions; never full-source-read credit."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,collections,re
import additional_pfp_tests_remaining_audit as a
rows=[]
def c(rule,status,**detail):return dict(rule=rule,status=status,**detail)
def walk(v):
 if isinstance(v,dict):
  for k,x in v.items():yield k,x;yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
for r in a.scope()['files']:
 p=r['path']
 if not p.endswith('.json'):continue
 raw=(a.ROOT/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256']
 dup=[]
 def pairs(ps):
  d={}
  for k,v in ps:
   if k in d:dup.append(k)
   d[k]=v
  return d
 d=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
 checks=[c('strict_json_parse_duplicate_and_nonfinite_scan','parsed',root_type=type(d).__name__,duplicate_keys=dup)]
 name=p.rsplit('/',1)[-1]
 if name=='manifest.json':
  pins=[]
  for ent in d:
   target='pfp/tests/fixtures/retired_quantum_reference/'+ent['retained_path'].rsplit('/',1)[-1]
   assert target in {x['path'] for x in a.scope()['files']}
   pins.append({'recorded_path':ent['retained_path'],'current_scoped_path':target,'recorded_sha256':ent['sha256'],'current_sha256':a.sha(a.ROOT/target),'matches':ent['sha256']==a.sha(a.ROOT/target)})
  checks.append(c('three_retired_source_hash_bindings_by_explicit_relocation','checked',count=len(d),bindings=pins))
  assess='Three historical Python reference bindings retain symbol_game paths. Explicit same-basename mapping to this frozen pfp fixture directory is checked bytewise; no archived source execution or body-read credit follows. They document custody, not native equivalence.'
 elif name=='golden_canonical_vectors.json':
  vs=d['vectors'];names=[v['name'] for v in vs];results=[]
  for v in vs:
   rawval=json.loads(v['raw_input_json']);wire=json.loads(v['canonical_json']);b=bytes.fromhex(v['canonical_bytes_hex']);domain=v['domain'].encode()
   frame=len(domain).to_bytes(4,'big')+domain+len(b).to_bytes(8,'big')+b
   results.append({'name':v['name'],'raw_json_type':type(rawval).__name__,'wire_matches_canonical_json':wire==v['wire_representation'],'utf8_matches_hex':v['canonical_json'].encode()==b,'domain_matches_envelope':v['domain']==d['domain'],'framed_sha256_matches':hashlib.sha256(frame).hexdigest()==v['domain_digest_sha256']})
  checks.append(c('core_canonical_vector_internal_wire_and_domain_frame_consistency','checked',declared_count=d['vector_count'],actual_count=len(vs),unique_names=len(set(names)),vectors=results))
  assess='23 tagged core-canonical vectors parsed; raw JSON, declared wire, canonical JSON/UTF8hex and length-framed domain hash are compared independently. This verifies internal custody/serialization consistency only: raw-to-wire semantic correctness, allcanonical inputs and RFC8785 equivalence are not inferred. Core tagged format differs from RFC8785.'
 elif name=='receipt_ddc_trace_replay.json':
  steps=d['steps'];bindings=[]
  for i,s in enumerate(steps):
   bindings.append({'index':i,'step_seq':s['step_seq'],'rune':s['step_rune'],'prev_matches_previous_root':None if not i else s['prev_step_hash']==steps[i-1]['merkle_root'],'state_before_matches_previous_after':None if not i else s['state_hash_before']==steps[i-1]['state_hash_after'],'hash_fields_hex64':all(isinstance(v,str) and bool(re.fullmatch('[0-9a-f]{64}',v)) for k,v in s.items() if k.endswith('hash') or k.startswith('state_hash') or k=='merkle_root')})
  checks.append(c('ddc_retained_trace_link_shape','checked',declared_steps=d['total_steps'],actual_steps=len(steps),rune_coverage=d['alphabet_coverage'],head_matches_last_root=d['merkle_head']==steps[-1]['merkle_root'],steps=bindings))
  assess='Eight retained DDC step summaries parsed; sequence/rune/hash shape, previous-root/state continuity and terminalhead compared. Payloads and full before/after states are absent, so no hash recomputation, semantic transition replay, authority or source/runtime binding claimed. Owning replay tests remain separately pending until full read.'
 elif name.startswith('receipt_'):
  props=d.get('properties_verified',[]);suites=d.get('suites_executed',[]);tranches=d.get('tranches_reviewed',[])
  hashes=[k for k,v in walk(d) if re.search('sha256|source_hash|source_digest|commit',k)]
  checks.append(c('historical_receipt_declarations','parsed',schema=d.get('schema',d.get('schema_version')),authority_effect=d.get('authority_effect'),property_count=len(props),property_names=[x.get('property_name') for x in props],property_statuses=dict(collections.Counter(x.get('status') for x in props)),suite_count=len(suites),suite_test_sum=sum(x.get('tests_run',0) for x in suites),tranche_count=len(tranches),tranche_test_sum=sum(x.get('test_count',0) for x in tranches),declared_totals={k:v for k,v in d.items() if k in ['test_count','total_new_tests','total_new_tests_verified','total_catalog_tests_verified','all_properties_satisfied','all_suites_passed','status']},theorem_name_count=len(d.get('lean4_theorems_aligned',[])),source_binding_keys=hashes))
  assess='Historical '+str(d.get('schema',d.get('schema_version')))+' receipt: parsed property/status/count/schema/authority declarations and source-binding-key census. PASS and theorem-alignment names are assertions, not reconstructed runner or Lean evidence; no executable, log or theorem was accessed. Old module paths and timestamps are retained historical context, not new instructions.'
  if name in ['receipt_pjnf_5nf_join_dependency_chase.json','receipt_tsnf_property_and_euler_poincare.json','receipt_tsnf_3complex_and_euler_poincare.json']:
   assess+=' Fully read owner emits unconditional PASS (PFPTESTS-F031); this JSON alone cannot establish successful execution.'
  if name=='receipt_cochain_physics_epistemic_property.json':assess+=' Fully read owner constructs local finite arithmetic examples and imports no production checker; theorem-name alignment is not checked proof linkage.'
  if name=='receipt_physics_and_observer_lattice_properties.json':assess+=' Fully read owner checks objective-value scaling and bounded observer chains, not LP feasibility or a general functor theorem.'
  if name=='receipt_pjnf_5nf_join_dependency_chase.json':assess+=' Receipt some-key-per-component claim is refuted by its own source parity counterexample (F032); valid same-common-key premise must be distinguished.'
 else:
  assert isinstance(d,list)
  info=[]
  for i,x in enumerate(d):
   e={'index':i,'keys':sorted(x)}
   if name=='cdc_events.json':e.update(op=x.get('event',{}).get('op'),relation=x.get('event',{}).get('relation'),old_keys=sorted(x.get('event',{}).get('old') or {}),new_keys=sorted(x.get('event',{}).get('new') or {}),boundary_keys=sorted(x.get('boundary',{})))
   elif name=='observers.json':e.update(packet_lag=x.get('packet',{}).get('replica_lag_seconds'),packet_scope=x.get('packet',{}).get('packet_scope'),observer_count=len(x.get('observers',[])),observer_ids=[o.get('observer_id') for o in x.get('observers',[])])
   elif name=='orders_before.json':e.update(order_id=x.get('order_id'),status=x.get('status'),amount_type=type(x.get('amount')).__name__)
   elif name=='transport_certificates.json':e.update(certificate_id=x.get('certificate_id'),verifier_outcome=x.get('verifier_outcome'),source_regime=x.get('source_regime'),target_regime=x.get('target_regime'))
   elif name=='cross_domain_reconciliation.json':e.update(case_id=x.get('case_id'),morphism_kind=x.get('morphism',{}).get('kind'),source_records=len(x.get('morphism',{}).get('source_records',[])),target_state_type=type(x.get('morphism',{}).get('target_state')).__name__,ledger_type=type(x.get('loss_ledger')).__name__,ledger_keys=sorted(x.get('loss_ledger') or {}),verifier_outcome=(x.get('target_verifier') or {}).get('outcome'))
   else:raise ValueError(name)
   info.append(e)
  checks.append(c('typed_fixture_shape_and_declared_policy_fields','parsed',case_count=len(d),cases=info))
  meanings={'cdc_events.json':'Six change-event fixtures expose old/new evidence and boundary relations/attributes/predicates/groups/aggregates; parsing does not establish delta correctness or predicate completeness.','observers.json':'Three packet/observer scenarios carry literal lag/SLA/scope inputs, not measured freshness or authenticated permissions.','orders_before.json':'Two initial order records are fixture state, not observed financial data; type/id/status census only, no execution.','transport_certificates.json':'Three transport proposals carry declared verifier outcomes and ledger/witness references; references and status labels are not verified proofs or authorization.','cross_domain_reconciliation.json':'Five reconciliation cases carry source/target and loss-ledger/verifier declarations; no concrete morphism proof, sealed ledger integrity or target verifier execution is inferred.'}
  assess=meanings[name]
 rows.append({'path':p,'sha256':r['sha256'],'full_source_read':False,'review_type':'bounded_schema_specific_json_assessment','assessment':assess,'checks':checks,'limits':['Parsed full JSON structure; not full human body reading.','No original test execution or external/private data access; statuses are retained declarations unless a named bounded check says checked.']})
a.write('_data_reviews.json',rows)
print(json.dumps({'bounded_data_files':len(rows),'files':[{'path':x['path'],'rules':[c['rule'] for c in x['checks']]} for x in rows]},indent=2))
