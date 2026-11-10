"""Validate report shape, frozen source pins, source ranges and linked probe custody."""
import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent
P='additional_rust_pfp_foundations'
def strict(p):
 def unique(pairs):
  d={}
  for k,v in pairs:
   assert k not in d,('duplicate JSON key',str(p),k)
   d[k]=v
  return d
 return json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=unique)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=HERE/(P+'.json');d=strict(report);scope=strict(HERE/(P+'_scope.json'))
expected={x['path']:x for x in scope['files']}
assert d['source_commit']==scope['source_commit']=='8050c66900899771766f33e8f5fdd200b7dd9120'
assert d['status']=='complete' and d['scope']['files']==368 and d['scope']['pending']==0
assert d['scope']['full_source_reads']==368 and d['remaining_work']==[]
assert len(d['file_reviews'])==len(expected)==len({x['path']for x in d['file_reviews']})
for r in d['file_reviews']:
 s=expected[r['path']]
 assert r['full_source_read'] is True
 assert r['sha256']==s['sha256']==digest(ROOT/r['path'])
 assert r['reviewed_lines']==[[1,s['lines']]]
 assert isinstance(r['assessment'],str) and r['assessment'].strip()
for group,fields in [('claims',['id','claim','evidence','dependencies','limitations']),('findings',['id','severity','title','evidence','status','detail','limits']),('validation',['id'])]:
 rows=d[group];assert len(rows)==len({r['id']for r in rows})
 for r in rows:
  assert all(f in r for f in fields),(group,r.get('id'))
  for e in r.get('evidence',[]) if isinstance(r.get('evidence',[]),list) else []:
   if not isinstance(e,dict):continue
   assert e['path'].startswith(('code/rust/','dag/reviews/'+P,'pfp/domain/shared_kernel/')),e
   path=ROOT/e['path'];assert path.is_file()
   if 'lines' not in e:
    assert e['path'].startswith('dag/reviews/'+P),e
    continue
   count=len(path.read_bytes().decode('utf-8-sig').splitlines())
   a,b=e['lines'];assert 1<=a<=b<=count,(r['id'],e,count)
linked=0
for v in d['validation']:
 if 'details_file' in v:
  p=HERE/v['details_file'];details=strict(p)
  assert details==v['details'],v['id'];linked+=1
  for item in details.get('source_files',[]):
   assert digest(ROOT/item['path'])==item['sha256'],(v['id'],item['path'])
last=strict(HERE/(P+'_final_validation.json'))
assert all(r['compile_exit']==0 and r['exit_code']==0 for r in last['runs'])
assert len(last['runs'])==2
result={'source_commit':d['source_commit'],'result':'passed','scope_files':368,'full_source_reads':368,'pending':0,'claims':len(d['claims']),'findings':len(d['findings']),'validation_records':len(d['validation']),'linked_receipts_checked':linked,'report_sha256':digest(report),'markdown_sha256':digest(HERE/(P+'.md')),'checks':['Strict duplicate-free report JSON','Required claim/finding/file-review fields and unique IDs','Exact scope bijection and368 current-source SHA256 matches','Full ranges match frozen line counts','All structured claim/finding evidence ranges exist within source','Linked supplement validation contents and source hashes agree','Final native counterexample probes exit0 in both overflow modes'],'limits':'Structural/custody validation only; semantic coverage comes from explicit assessments and actual source reading, never inferred from this script.'}
(HERE/(P+'_completion_validation.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
