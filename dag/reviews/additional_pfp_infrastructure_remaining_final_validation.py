"""Independent frozen-scope/schema/hash/range audit; no semantic credit inferred."""
import collections,hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining'
def strict(path):
 def pairs(xs):
  d={}
  for k,v in xs:
   assert k not in d,('duplicate JSON key',str(path),k)
   d[k]=v
  return d
 return json.loads(path.read_bytes(),object_pairs_hook=pairs)
scope=strict(H/(P+'_scope.json'));report=strict(H/(P+'.json'));prep=strict(H/(P+'_preparation.json'));ledger=strict(H/(P+'_read_ledger.json'));expected={x['path']:x for x in scope['files']};metadata={x['path']:x for x in prep['files']};reviews=report['file_reviews']
assert len(expected)==594==len(reviews);assert{r['path']for r in reviews}==set(expected);assert len({r['path']for r in reviews})==len(reviews);assert report['remaining_work']==[];assert report['source_commit']==scope['source_commit']
lines={};methods=collections.Counter();body_hashes={}
for rv in reviews:
 path=rv['path'];raw=(R/path).read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest==rv['sha256']==expected[path]['sha256'];assert len(raw)==expected[path]['bytes'];body_hashes[path]=digest
 assert type(rv['full_source_read'])is bool and rv['assessment']and rv['limitations']and rv['review_level']
 if metadata[path]['kind']=='text':
  count=len(raw.decode('utf-8-sig').splitlines());lines[path]=count;assert count==metadata[path]['lines'],(path,count,metadata[path]['lines'])
 else:count=0
 covered=set()
 for a,b in rv['reviewed_lines']:assert 1<=a<=b<=count;(covered.update(range(a,b+1)))
 if rv['full_source_read']:
  assert covered==set(range(1,count+1));entry=ledger[path];assert entry.get('sha256',entry.get('reconstruction_sha256'))==digest
  if'base_path'in entry:assert hashlib.sha256((R/entry['base_path']).read_bytes()).hexdigest()==entry['base_sha256']
  emitted=set()
  for a,b in entry['emitted_ranges']:emitted.update(range(a,b+1))
  assert emitted==set(range(1,count+1));methods[entry.get('method','full_literal_body_emission')]+=1
  if'reconstruction_sha256'in entry:assert entry['reconstruction_sha256']==digest
assert sum(x['full_source_read']for x in reviews)==587==report['full_source_read_count'];assert sum(not x['full_source_read']for x in reviews)==7==report['bounded_review_count']
evidence_refs=0
for kind,required in [('claims',{'id','claim','evidence','dependencies','limitations'}),('findings',{'id','title','finding','evidence','next_action','status'})]:
 ids=[x['id']for x in report[kind]];assert len(ids)==len(set(ids))
 for item in report[kind]:
  assert required<=set(item),(kind,item['id'])
  for e in item['evidence']:
   assert e['path']in expected,e;assert e['sha256']==expected[e['path']]['sha256'];a,b=e['lines'];assert 1<=a<=b<=lines[e['path']],e;evidence_refs+=1
allprobes={};receipts=[]
for v in report['validation']:
 p=H/v['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==v['sha256'];d=strict(p);outcomes=d.get('outcomes',d.get('controls'));assert len(outcomes)==v['controls']
 for x in outcomes:
  assert x['id']not in allprobes,x['id'];allprobes[x['id']]=x
 for path,pin in d['source_pins'].items():
  assert not any(s in path.lower()for s in('private','seed_prompt.txt','answer_key'));assert hashlib.sha256((R/path).read_bytes()).hexdigest()==pin,(v['path'],path)
 receipts.append({'path':v['path'],'sha256':v['sha256'],'outcomes':len(outcomes)})
for finding in report['findings']:
 for probe in finding.get('probes',[]):assert probe in allprobes,(finding['id'],probe)
for v in report.get('related_context',[])+report.get('population_checks',[]):assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
result={'source_commit':scope['source_commit'],'status':'passed','scope_paths':594,'source_hashes_verified':594,'source_bytes_verified':sum(x['bytes']for x in scope['files']),'full_source_read_count':587,'bounded_dispositions':7,'pending':0,'claims':len(report['claims']),'findings':len(report['findings']),'evidence_refs_validated':evidence_refs,'full_read_emission_methods':dict(methods),'probe_receipts':receipts,'probe_outcome_count':len(allprobes),'probe_status_census':dict(collections.Counter(x.get('status',x.get('result','unspecified'))for x in allprobes.values())),'report_sha256':hashlib.sha256((H/(P+'.json')).read_bytes()).hexdigest(),'scope_sha256':hashlib.sha256((H/(P+'_scope.json')).read_bytes()).hexdigest(),'limits':'Hashes/ranges/schema validate custody and internal bookkeeping, not mathematical soundness or whether a human substantively read the emitted text. Full-read decisions remain explicit manual assessments; bounded catalogs/images remain bounded. No probe reruns, provider/native/network execution or original edits.'}
(H/(P+'_final_validation.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
