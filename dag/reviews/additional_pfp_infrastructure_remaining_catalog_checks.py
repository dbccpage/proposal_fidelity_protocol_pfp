"""Bounded whole-population checks; never grants full semantic reading credit."""
import ast,collections,hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out={}
def load(i):
 f=fs[i];b=(R/f['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256'];return json.loads(b)
base=R/'pfp/infrastructure/adapters/mssn_research';a=load(1);b=load(138);c=load(519)
checks=[]
for row in b['checkers']:
 p=base/row['path'];q=base/row['fixture_path'];tree=ast.parse(p.read_text());constants={}
 for node in tree.body:
  if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
   try:constants[node.targets[0].id]=ast.literal_eval(node.value)
   except (ValueError,TypeError):pass
 fixture=json.loads(q.read_bytes());ids=[x['id']for x in fixture['cases']]
 checks.append({'level':row['level'],'checker_hash_matches':hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],'fixture_hash_matches':hashlib.sha256(q.read_bytes()).hexdigest()==row['fixture_sha256'],'stage_matches':constants.get('STAGE')==row['level']==fixture['level'],'row_pin_matches':constants.get('ROW_SHA256')==row['row_sha256'],'clauses_count':len(row['clauses']),'all_clauses_have_mutation_case':all('mutation-'+cl in ids for cl,_ in row['clauses']),'all_clause_refusal_codes_agree':all(next(x for x in fixture['cases']if x['id']=='mutation-'+cl)['expected']==['REFUSED',code]for cl,code in row['clauses']),'cases':len(ids),'unique_case_ids':len(ids)==len(set(ids))})
out['registry']={'path':fs[138]['path'],'sha256':fs[138]['sha256'],'root_metadata':{k:v for k,v in b.items()if k!='checkers'},'all101_levels':sorted(x['level']for x in checks)==list(range(101)),'records':checks,'scope':'Static pins and fixture-clause correspondence only; no checker execution or external research baseline validation.'}
sc=[]
for x in a['scenarios']:
 p=base/x['fixture_path'];s=x['scenario'];sc.append({'id':s['scenario_id'],'path':x['fixture_path'],'hash_matches':p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==x['fixture_sha256'],'kind':s['kind'],'level':s['level'],'scope':s['scope']})
impl=[{'path':root+'/'+p,'exists':(R/root/p).is_file()}for root,paths in a['implementation'].items()for p in paths]
out['catalog']={'path':fs[1]['path'],'sha256':fs[1]['sha256'],'metadata':{k:v for k,v in a.items()if k not in ('implementation','scenarios')},'scenario_count':len(sc),'unique_ids':len({x['id']for x in sc})==len(sc),'kinds':dict(collections.Counter(x['kind']for x in sc)),'scenarios':sc,'implementation_count':len(impl),'missing_implementation':[x['path']for x in impl if not x['exists']],'scope':'All134 scenario fixture pins and all implementation path existence checked; historical scenario prose not independently recertified.'}
pins=[]
for path,pin in c['sources'].items():
 p=R/path;status='historical_path_absent'
 actual=None
 if p.is_file():
  raw=p.read_bytes();actual={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};status='exact_match'if actual['sha256']==pin['sha256']and actual['bytes']==pin['byte_length']else'current_bytes_differ'
 pins.append({'path':path,'declared':pin,'actual':actual,'status':status})
records=[]
for e in c['entries']:
 records.append({'id':e.get('id'),'kind':e.get('kind'),'name':e.get('name'),'source':e.get('source'),'source_declared_or_external':e.get('source')in c['sources']or str(e.get('source')).startswith(('http://','https://')),'arity_matches':None if'arity'not in e or'inputs'not in e else e['arity']==len(e['inputs']),'evidence':e.get('evidence'),'executor_state':e.get('executor_state')})
counts=dict(collections.Counter(e['kind']for e in records))
out['operad_catalog']={'path':fs[519]['path'],'sha256':fs[519]['sha256'],'metadata':{k:v for k,v in c.items()if k not in ('entries','sources')},'entry_count':len(records),'unique_ids':len({x['id']for x in records})==len(records),'counts_match':counts==c['coverage']['counts'],'counts':counts,'source_status_counts':dict(collections.Counter(x['status']for x in pins)),'source_pins':pins,'records':records,'scope':'All744 entry IDs/kinds/sources/arities/evidence labels and52 source pins inspected mechanically; per-kind full examples and claim-hygiene metadata read substantively. Source bodies and literature not reopened. Historical path absence is not proof of deletion or broken runtime invocation.'}
(H/(P+'_catalog_checks.json')).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'registry':{'records':len(checks),'all_static_checks_pass':all(all(v for k,v in x.items()if k.endswith(('matches','case','agree','ids')))for x in checks),'cases':sum(x['cases']for x in checks)},'catalog':{k:out['catalog'][k]for k in('scenario_count','unique_ids','kinds','implementation_count','missing_implementation')},'scenario_hash_mismatches':[x for x in sc if not x['hash_matches']],'operad':{k:out['operad_catalog'][k]for k in('entry_count','unique_ids','counts_match','source_status_counts')},'undeclared_sources':[x for x in records if not x['source_declared_or_external']],'arity_mismatch':[x for x in records if x['arity_matches']is False]},indent=2))
