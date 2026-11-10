from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
P=R/'dag/reviews/rust_category_delegate_relations'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(suffix):return json.loads(Path(str(P)+suffix).read_text(encoding='utf8'))
s=read('_scope.json');r=read('.json');c=read('_controls.json');ledger=read('_read_ledger.json')
assert h(R/s['parent_scope'])==s['parent_scope_sha256']
rows={x['path']:x for x in s['files']}
assert set(rows)=={x['path'] for x in r['file_reviews']}
for x in r['file_reviews']:
 p=R/x['path'];raw=p.read_bytes();n=len(raw.decode('utf8').splitlines())
 assert h(p)==x['sha256']==rows[x['path']]['sha256']
 assert len(raw)==x['bytes']==rows[x['path']]['bytes']
 assert n==x['source_line_count']==rows[x['path']]['lines']
 assert x['full_source_read'] and x['reviewed_lines']==[[1,n]] and x['assessment']
 seen=set()
 for z in ledger:
  if z['path']==x['path']:
   assert z['sha256']==x['sha256'];a,b=z['displayed_lines'];assert 1<=a<=b<=n
   seen.update(range(a,b+1))
 assert seen==set(range(1,n+1))
count=0
def evidence(obj):
 global count
 if isinstance(obj,dict):
  if {'path','sha256','lines'}<=obj.keys():
   x=rows[obj['path']];a,b=obj['lines'];assert obj['sha256']==x['sha256'] and 1<=a<=b<=x['lines'];count+=1
  for v in obj.values():evidence(v)
 elif isinstance(obj,list):
  for v in obj:evidence(v)
evidence(r);evidence(c)
ids=[x['id'] for group in (r['claims'],r['findings'],c['controls']) for x in group]
assert len(ids)==len(set(ids))
assert all(x['status']=='confirmed' for x in c['controls'])
assert h(R/r['controls_artifact']['path'])==r['controls_artifact']['sha256']
for x in r['dependency_prior_evidence']:assert h(R/x['path'])==x['sha256'] and not x['fresh_reading_credit']
out={'status':'passed','source_pins':len(rows),'full_source_reads':5,'lines':sum(x['lines'] for x in rows.values()),'bytes':sum(x['bytes'] for x in rows.values()),'evidence_ranges':count,'claims':4,'findings':7,'controls':8,'native_or_provider_runs':0,'artifacts':{suffix:h(Path(str(P)+suffix)) for suffix in ('.json','.md','_controls.json','_scope.json','_read_ledger.json')},'limit':'Hash/range/receipt validation; independent Python controls do not claim Rust execution. Prior parent report snapshot hash is recorded, not required to remain unchanged while parent integrates.'}
Path(str(P)+'_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2));print('validation_sha256',h(Path(str(P)+'_validation.json')))
