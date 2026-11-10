"""Independent bounded reductions of fully read public JSON; no imported source execution."""
import collections,hashlib,itertools,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_010_data';B=R/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots'
scope=json.loads((H/(P+'_scope.json')).read_text(encoding='utf-8'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name):return json.loads((B/name).read_text(encoding='utf-8'))
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def save(name,value):(H/(P+name)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
for row in scope['files']:assert sha((R/row['path']).read_bytes())==row['sha256']
fixtures={}
for name in ('base_01','base_02','base_03','base_13','pois_01'):
 d=load('code/data/c017/'+name+'.json');g=d['group'];els=g['elements'];table=g['table'];identity=g['identity'];inv=g['inverses']
 assert len(set(els))==len(els)==g['order'] and set(table)==set(els) and set(inv)==set(els)
 assert all(set(table[a])==set(els) and all(v in els for v in table[a].values()) for a in els)
 assert all(table[identity][a]==a==table[a][identity] and table[a][inv[a]]==identity==table[inv[a]][a] for a in els)
 assert all(table[table[a][b]][c]==table[a][table[b][c]] for a,b,c in itertools.product(els,repeat=3))
 edges={}
 for label,value in d['edges'].items():
  a,b=label.split('->');u=tuple(map(int,a.split(',')));v=tuple(map(int,b.split(',')));edges[u,v]=value
 vertices={(i,j) for i in range(d['L']) for j in range(d['M'])};expected=set()
 for u in vertices:
  for di,dj in ((1,0),(0,1)):
   v=(u[0]+di,u[1]+dj)
   if d['boundary']=='periodic':v=(v[0]%d['L'],v[1]%d['M'])
   if v in vertices:expected.update(((u,v),(v,u)))
 assert set(edges)==expected and all(value in els and edges[v,u]==inv[value] for (u,v),value in edges.items())
 def walk(path):
  acc=identity
  for u,v in zip(path,path[1:]):acc=table[acc][edges[u,v]]
  return acc
 products=[]
 for i in range(d['L'] if d['boundary']=='periodic' else d['L']-1):
  for j in range(d['M'] if d['boundary']=='periodic' else d['M']-1):
   p=[(i,j),((i+1)%d['L'],j),((i+1)%d['L'],(j+1)%d['M']),(i,(j+1)%d['M']),(i,j)]
   products.append({'base':[i,j],'product':walk(p)})
 labels={(0,0):identity};queue=collections.deque([(0,0)]);conflicts=[]
 while queue:
  u=queue.popleft()
  for (a,v),value in edges.items():
   if a!=u:continue
   target=table[labels[u]][value]
   if v not in labels:labels[v]=target;queue.append(v)
   elif labels[v]!=target:conflicts.append([list(u),list(v)])
 assert set(labels)==vertices
 result={'path':(B/'code/data/c017'/f'{name}.json').relative_to(R).as_posix(),'sha256':sha((B/'code/data/c017'/f'{name}.json').read_bytes()),
         'declared_id':d['id'],'vertices':len(vertices),'directed_edges':len(edges),'group_associativity_triples':len(els)**3,
         'group_identity_inverse_closure':True,'grid_and_edge_inverse_complete':True,'plaquettes':products,
         'nonidentity_plaquettes':sum(x['product']!=identity for x in products),'global_potential_exists':not conflicts}
 if d['boundary']=='periodic':
  ha=walk([(0,j) for j in range(d['M'])]+[(0,0)]);hb=walk([(i,0) for i in range(d['L'])]+[(0,0)])
  result['global_cycle_products']={'horizontal':ha,'vertical':hb,'commute':table[ha][hb]==table[hb][ha]}
 fixtures[name]=result
assert [(n,fixtures[n]['nonidentity_plaquettes'],fixtures[n]['global_potential_exists']) for n in fixtures]==[
 ('base_01',1,False),('base_02',0,True),('base_03',0,False),('base_13',1,False),('pois_01',1,False)]

d=load('code/data/c017/base_02.json');table=d['group']['table']
mistakes=[{'source':'docs/historical_evidence/arm5_hybrid_report.json','lines':[[240,251]],'type':'group_product',
 'stored':'sr2*s=r','actual':'sr2*s='+table['sr2']['s'],'downstream_true_product':table[table['sr2']['s']]['r']},
 {'source':'docs/historical_evidence/arm5_stealth_space_bunny_alpha_report.json','lines':[[457,467]],'type':'edge_binding',
 'edge':'2,3->1,3','stored':'sr','actual':d['edges']['2,3->1,3'],
 'true_full_plaquette_product':table[table[table['e']['r']]['r']][table[d['edges']['2,3->1,3']]['sr2']]},
 {'source':'docs/historical_evidence/arm6_stealth_space_bunny_alpha_report.json','lines':[[243,257]],'type':'group_product',
 'stored':'r*sr=s','actual':'r*sr='+table['r']['sr'],'downstream_true_product':table[table['r']['sr']]['sr2']}]
assert mistakes[0]['actual']=='sr2*s=r2' and mistakes[0]['downstream_true_product']=='e'
assert mistakes[1]['actual']=='s' and mistakes[1]['true_full_plaquette_product']=='e'
assert mistakes[2]['actual']=='r*sr=sr2' and mistakes[2]['downstream_true_product']=='e'

identity=[]
for item in load('docs/historical_evidence/provenance.json')['files']:
 raw=(B/'docs/historical_evidence'/item['file']).read_bytes();lf=raw.replace(b'\r\n',b'\n')
 identity.append({'path':'docs/historical_evidence/'+item['file'],'expected_sha256':item['sha256'],
                  'current_sha256':sha(raw),'raw_sha_matches':sha(raw)==item['sha256'],'lf_sha_matches':sha(lf)==item['sha256'],
                  'raw_git_matches':blob(raw)==item['git_blob_sha'],'lf_git_matches':blob(lf)==item['git_blob_sha']})
case_identity=[]
for item in load('code/data/c017/provenance.json')['cases']:
 raw=(B/'code/data/c017'/item['file']).read_bytes()
 case_identity.append({'path':'code/data/c017/'+item['file'],'raw_matches_declared_lf':sha(raw)==item['sha256'],
                       'normalized_lf_matches':sha(raw.replace(b'\r\n',b'\n'))==item['sha256'],
                       'raw_matches_declared_crlf':sha(raw)==item['judge_manifest_sha256_crlf']})

extraction=[]
for run in load('code/data/c017/model_claims.json')['runs']:
 source_name=Path(run['source']).name;data=load('docs/historical_evidence/'+source_name);rec={row['case_id']:row for row in data['cases_evaluated']}
 assert run['model']==data['model'] and run['timestamp_utc']==data['timestamp_utc']
 for entry in run['cases']:
  raw_record=rec[entry['harness_case_id']];actual=raw_record['baseline' if run['run']=='arm1' else 'immune_assisted'] if run['run'] in ('arm1','arm2') else raw_record
  matches={'expected_verdict':entry['harness_expected_verdict']==raw_record['expected_verdict'],
           'verdict':entry['recorded_verdict']==actual['verdict'],'passed':entry['recorded_passed']==actual['passed'],
           'reason':entry['recorded_reason']==actual['reason'],'tokens':entry['completion_tokens']==actual['meta']['out_tokens']}
  if entry['claim'] is None:matches['payload']=run['run'] in ('arm1','arm2')
  else:matches['payload']=entry['claim']=={k:v for k,v in actual['solution'].items() if k not in ('scratchpad','raw')}
  assert all(matches.values())
  extraction.append({'run':run['run'],'case':entry['case'],'all_extracted_fields_match':True,'recorded_passed':entry['recorded_passed'],
                      'payload_status':'missing' if entry['claim'] is None else entry['claim']['status']})

panels=[]
for name in ['c045','c046','c047','c048','c049_panel_b','c050_run_1','c050_run_2']:
 report=load('docs/historical_evidence/'+name+'.json')
 for model,entry in report['models'].items():
  records=entry['records'];passed=sum(row.get('passed',row.get('pass',False)) is True for row in records)
  missing=[row['case_id'] for row in records if 'passed' not in row and 'pass' not in row]
  assert len(records)==report['total_cases']==10 and passed==entry['passed']
  assert all(type(row.get('passed',row.get('pass',False))) is bool for row in records)
  panels.append({'file':name+'.json','model':entry['model_id'],'recorded_acceptances':passed,'records':len(records),
                 'missing_acceptance_flag_ids':missing,'interpretation':'Missing flag is not acceptance; c045 JSON_ERROR retained explicitly.'})
for n in range(3):
 name=f'c049_panel_a_{n}.json';data=load('docs/historical_evidence/'+name);passed=sum(row['passed'] is True for row in data['results'])
 assert passed==data['passed'] and len(data['results'])==data['total']==10
 panels.append({'file':name,'model':data['model'],'recorded_acceptances':passed,'records':10})
assert sum(row['records'] for row in panels)==240
baselines=[]
for key,value in load('docs/historical_evidence/formal_math_baselines.json')['challenges'].items():
 categories=value['identifier_reading_ids'];ids=[cid for group in categories.values() for cid in group]
 assert len(set(ids))==10 and set(ids)==set(value['panel_case_ids'])
 assert {k:len(v) for k,v in categories.items()}==value['identifier_reading']
 for policy,record in value['trivial_answers'].items():
  assert len(set(record['cases_passed']))==record['both_accept'] and set(record['cases_passed'])<=set(ids)
  assert record['both_accept']<=record['exact_checker_accepts']<=10 and record['both_accept']<=record['second_checker_accepts']<=10
 best=max(row['both_accept'] for row in value['trivial_answers'].values());assert best==value['best_trivial_both_accept']
 baselines.append({'challenge':key,'author_category_counts':value['identifier_reading'],'recorded_best_trivial_acceptance':best,
                   'policies':len(value['trivial_answers']),'limits':'All record partitions/counts consistent; historical checker execution and author leakage annotation not independently repeated.'})
for row in scope['files']:assert sha((R/row['path']).read_bytes())==row['sha256']
result={'scope':'Bounded independent stdlib reductions of fully read public JSON; no imported production/checker/provider execution.',
        'fixtures':fixtures,'scratchpad_counterexamples':mistakes,'historical_identity':identity,'case_identity':case_identity,
        'extraction':extraction,'formal_pilot_panels':panels,'baseline_partitions':baselines,'originals_unchanged':27,'provider_calls':0,'native_calls':0}
save('_checks.json',result)
print(json.dumps({'fixtures':{n:{k:v for k,v in row.items() if k in ('vertices','directed_edges','nonidentity_plaquettes','global_potential_exists','global_cycle_products')} for n,row in fixtures.items()},
 'historical_raw_match':sum(row['raw_sha_matches'] for row in identity),'historical_lf_and_git_match':sum(row['lf_sha_matches'] and row['lf_git_matches'] for row in identity),
 'case_crlf_match':sum(row['raw_matches_declared_crlf'] for row in case_identity),'extraction':len(extraction),'formal_records':240,
 'best_historical_baselines':[row['recorded_best_trivial_acceptance'] for row in baselines],'originals_unchanged':27},indent=2))
