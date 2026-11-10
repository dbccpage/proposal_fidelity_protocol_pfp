"""Independent strict report/source/citation validation, without production imports."""
import hashlib,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_wiki_tests'
def pairs(items):
 d={}
 for k,v in items:
  assert k not in d,('duplicate JSON key',k)
  d[k]=v
 return d
def load(s):return json.loads((H/(P+s)).read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
def sha(path):return hashlib.sha256((R/path).read_bytes()).hexdigest()
report=load('.json');scope=load('_scope.json');ledger=load('_read_ledger.json');notes=load('_notes.json');probes=load('_probes.json')
frozen={r['path']:r for r in scope['files']};rows={r['path']:r for r in report['file_reviews']};reads={r['path']:r for r in ledger}
assert len(frozen)==len(rows)==len(reads)==len(report['file_reviews'])==47
assert set(frozen)==set(rows)==set(reads)==set(notes)
assert not report['remaining_work']and report['scope']['pending']==0
assert scope['source_commit']==report['source_commit']=='8050c66900899771766f33e8f5fdd200b7dd9120'
lines=0;local_links=[]
for path,r in rows.items():
 raw=(R/path).read_bytes();text=raw.decode('utf-8');n=len(text.splitlines());lines+=n
 assert sha(path)==r['sha256']==frozen[path]['sha256']==reads[path]['sha256']
 assert len(raw)==r['bytes']==frozen[path]['bytes']
 assert r['full_source_read']is True and reads[path]['body_emitted']is True
 assert r['reviewed_lines']==[[1,n]]and reads[path]['lines']==n
 assert all(r[k]==notes[path][k]for k in ['assessment','limitations','mathematical_contribution'])
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if '://'in target or target.startswith('#'):continue
  bare=target.split('#',1)[0];resolved=(R/path).parent/bare
  local_links.append({'from':path,'target':target,'exists':resolved.is_file()})
assert sum(r['bytes']for r in rows.values())==report['scope']['bytes']==197686
assert report['scope']['full_source_read']==47
citations=0
def verify_evidence(e):
 global citations
 if 'artifact'in e:
  assert(H/e['artifact']).is_file();return
 path=e['path'];assert sha(path)==e['sha256'],path
 n=len((R/path).read_text(encoding='utf-8').splitlines())
 for a,b in e['lines']:assert type(a)is int and type(b)is int and 1<=a<=b<=n,(path,a,b,n)
 citations+=1
ids=[]
for kind in ['claims','findings']:
 for item in report[kind]:
  ids.append(item['id'])
  if kind=='claims':assert all(item[k]for k in ['claim','dependencies','limitations'])
  else:assert item['finding']and item['action']and item['reason']
  for e in item['evidence']:verify_evidence(e)
assert len(ids)==len(set(ids))==19
refs=0
for r in rows.values():
 for x in r['source_review_comparisons']:
  assert sha(x['report'])==x['report_sha256']
  original=json.loads((R/x['report']).read_text())
  f=next(f for f in original['findings']if f['id']==x['finding_id'])
  assert f.get('claim',f.get('finding',f.get('statement')))==x['finding']
  for e in x['source_pins_revalidated']:assert sha(e['path'])==e['sha256']
  refs+=1
assert len(report['prior_source_pin_validation']['pins'])==87
for path,pin in report['prior_source_pin_validation']['pins'].items():assert sha(path)==pin
for r in report['supporting_source_reads']:
 assert sha(r['path'])==r['sha256']and r['full_source_read']is True
 assert r['reviewed_lines']==[[1,len((R/r['path']).read_text().splitlines())]]
assert len(probes['controls'])==6
for e in probes['source_pins']:assert sha(e['path'])==e['sha256']
assert probes['controls'][1]['counts']=={'normal':261885,'subnormal':130,'nan':129}
receipt={'status':'PASS','source_commit':report['source_commit'],'scoped_pages':47,'full_page_lines':lines,'bytes':197686,
 'claims':8,'findings':11,'citations_validated':citations,'prior_finding_references_validated':refs,'prior_owner_source_pins_validated':87,
 'supporting_source_bodies_read':len(report['supporting_source_reads']),'bounded_controls':6,
 'local_markdown_links_checked':len(local_links),'broken_local_markdown_links':[x for x in local_links if not x['exists']],
 'source_and_range_validation':'All frozen hashes/lengths/full-body ranges, evidence pins, note mappings, prior report findings and referenced owner pins match.',
 'report_sha256':sha('dag/reviews/'+P+'.json'),'summary_sha256':sha('dag/reviews/'+P+'.md'),
 'scope_sha256':sha('dag/reviews/'+P+'_scope.json'),
 'limits':['Integrity PASS does not erase the documented semantic findings or rerun historical test claims.',
 'No provider, answer key, private benchmark, production source edit, native build or foreign-repository mutation.']}
(H/(P+'_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
