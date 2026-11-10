"""Bounded parsed checks of the four frozen generated catalogs, not source prose proof."""
import json,hashlib,collections
from pathlib import Path
HERE=Path(__file__).parent; ROOT=HERE.parents[1]; PREFIX='additional_operads_core_remaining'
scope=json.loads((HERE/(PREFIX+'_scope.json')).read_text()); rows={r['path']:r for r in scope['files']}
names=['agent_capability_slices','anti_skill_catalog.v1','capability_catalog.v1','operad_signature']; data={}; evidence=[]
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate key '+k)
  d[k]=v
 return d
for name in names:
 path='operads/skill_operad/json/'+name+'.json'; raw=(ROOT/path).read_bytes(); assert hashlib.sha256(raw).hexdigest()==rows[path]['sha256'];data[name]=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
cap=data['capability_catalog.v1'];sig=data['operad_signature'];anti=data['anti_skill_catalog.v1'];slices=data['agent_capability_slices']['agents']; skills={r['skill_id']:r for r in cap['skills']}
checks={
 'unique_skill_ids':len(skills)==len(cap['skills']),
 'unique_agent_ids':len({a['agent_id'] for a in cap['agents']})==len(cap['agents']),
 'unique_anti_skill_ids':len({a['anti_skill_id'] for a in anti['anti_skills']})==len(anti['anti_skills']),
 'projection_operation_ids_equal':{x['skill_id'] for x in sig['operations']}==set(skills),
 'signature_projection_all_present_fields_equal':all(all(k in skills[r['skill_id']] and skills[r['skill_id']][k]==v for k,v in r.items()) for r in sig['operations']),
 'all_arities_exact_and_match':all(type(r['arity']) is int and r['arity']==len(r['source_colours']) for r in cap['skills']+sig['identities']),
 'all_nonnull_colours_in_vocabulary':all(set((r['source_colours'] or [])+([r['target_colour']] if r['target_colour'] else []))<=set(sig['colours']) for r in cap['skills']+sig['identities']+anti['anti_skills']),
 'identity_signatures_one_per_colour':{(tuple(r['source_colours']),r['target_colour']) for r in sig['identities']}=={((c,),c) for c in sig['colours']},
 'role_slices_equal_catalog':set(slices)=={a['agent_id'] for a in cap['agents']} and all(slices[a['agent_id']]['sub_operad']==a['licensed_colour_ids'] and slices[a['agent_id']]['licensed_skills']==a['licensed_skill_ids'] for a in cap['agents']),
 'role_licenses_exact_colour_subset':all(a['licensed_skill_ids']==sorted(sid for sid,s in skills.items() if set(s['source_colours']+[s['target_colour']])<=set(a['licensed_colour_ids'])) for a in cap['agents']),
 'all_anti_candidates_unbound':all(r['status']=='Candidate' and r['detector']=='UNBOUND' and r['authority_effect']=='none' for r in anti['anti_skills']),
 'bound_has_host_and_hex_digest':all((r['executor']['state']=='BOUND' and bool(r['executor']['host_executor_id']) and len(r['executor']['implementation_digest'])==64 and all(c in '0123456789abcdef' for c in r['executor']['implementation_digest'])) or (r['executor']=={'host_executor_id':None,'implementation_digest':None,'state':'UNBOUND'}) for r in cap['skills']),
 'resource_shapes_nonnegative_exact_lengths':all(type(x['byte_length']) is int and x['byte_length']>=0 and len(x['sha256'])==64 and all(c in '0123456789abcdef' for c in x['sha256']) for r in cap['skills'] for x in r['package_resources']),
}
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
without={k:v for k,v in cap.items() if k!='catalog_digest'}
checks['catalog_digest_recomputes']=hashlib.sha256(b'core.oewas.capability_catalog.v1\0'+canonical(without)).hexdigest()==cap['catalog_digest']
checks['catalog_raw_bytes_canonical']=(ROOT/'operads/skill_operad/json/capability_catalog.v1.json').read_bytes()==canonical(cap)
checks['agent_license_digests_recompute']=all(hashlib.sha256(b'core.oewas.agent_license.v1\0'+canonical({k:a[k] for k in ['agent_id','authority_effect','licensed_colour_ids','licensed_skill_ids','standalone','tools']})).hexdigest()==a['license_digest'] for a in cap['agents'])
def counts(records,field):return dict(collections.Counter(json.dumps(r.get(field),sort_keys=True) for r in records))
summary={'skills':len(skills),'agents':len(cap['agents']),'anti_skills':len(anti['anti_skills']),'colours':sig['colours'],'identities':sig['identities'],'checks':checks,'anti_missing_source_colours':[r['anti_skill_id'] for r in anti['anti_skills'] if r['source_colours'] is None],'anti_missing_target_colours':[r['anti_skill_id'] for r in anti['anti_skills'] if r['target_colour'] is None],'anti_summary_declared':anti['summary'],'anti_pairing':counts(anti['anti_skills'],'pairing'),'anti_detection_signature':counts(anti['anti_skills'],'detection_signature'),'skill_residuals':counts(cap['skills'],'residual_effect'),'executor_states':dict(collections.Counter(r['executor']['state'] for r in cap['skills'])),'bound_executors':[{ 'skill_id':r['skill_id'],**r['executor']} for r in cap['skills'] if r['executor']['state']=='BOUND'],'agent_counts':{a['agent_id']:len(a['licensed_skill_ids']) for a in cap['agents']},'resource_count':sum(len(r['package_resources']) for r in cap['skills']),'schemas':{'skill_keys':sorted({tuple(sorted(r)) for r in cap['skills']}),'agent_keys':sorted({tuple(sorted(r)) for r in cap['agents']}),'anti_keys':sorted({tuple(sorted(r)) for r in anti['anti_skills']})}}
assessments={
 'agent_capability_slices':'All12 agents parsed and compared exactly to catalog colour/skill lists; every license recomputed by colour-subset predicate. sub_operad denotes nominal capability slice, with no composition/unit closure certificate. Complete arrays processed automatically; individual skill descriptions were not fully read here.',
 'anti_skill_catalog.v1':'All93 records processed for ID uniqueness, field shapes, nonnull colour membership, status/detector and pairing distributions:71 have typed colours;22 retain null source/target colours,90 reciprocal and3 one-sided links. Every record is Candidate/UNBOUND despite residual labels. Reciprocal dual-path metadata and regex-presence booleans do not establish a detector, complement law or validated negative selection. Referenced source prose not reopened by this helper.',
 'capability_catalog.v1':'All237 skills,12 agents and every package-resource row processed. Role licenses equal exact nominal colour subsets; signatures/arity and BOUND shape guards checked. Resource hashes are declarations only here: external resource bytes and executable health not verified. Descriptions and named families do not certify capability efficacy or operad laws. Catalog and all12 license digests independently recompute under the declared newline/ASCII/domain-separated JSON profile; this does not authenticate external resource contents.',
 'operad_signature':'All237 operation projections compared field-for-field to capability catalog; ten unary identity signatures and ten-colour closure checked. IDs/residual/equivariant labels are not implementations or unit/equivariance proof. This is a generated signature inventory, not a complete operad with a composition table.'}
for name in names:
 path='operads/skill_operad/json/'+name+'.json';r=rows[path]
 evidence.append({'path':path,'sha256':r['sha256'],'full_source_read':False,'reviewed_lines':[],'parsed_value_read':True,'review_level':'bounded_automated_parsed_artifact_review','reading_method':'every JSON value parsed; representative complete row schemas inspected; all-record arithmetic/projection checks; no full raw text reading claimed','source_line_count':r['lines'],'automated_ranges':[[1,r['lines']]],'assessment':assessments[name]})
out={'method':'Strict duplicate-key JSON decoding and bounded all-record predicates, stdlib only; no referenced source imports, native execution or network','summary':summary,'file_reviews':evidence,'limits':['All catalog JSON parsed, not all free prose strings substantively read.','Cross-projection agreement is not independent semantic correctness or a mathematical proof.','No downstream source files, target papers, hidden benchmarks or model calls.']}
(HERE/(PREFIX+'_artifacts.json')).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(summary['checks'],indent=2))
