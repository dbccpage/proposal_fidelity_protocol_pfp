"""Validate custody/schema/coverage; does not infer substantive reading from emission."""
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
def load(s):return json.loads((H/(P+s)).read_text())
scope=load('_scope.json');report=load('.json');emissions=load('_emissions.json');notes=load('_notes.json')
by={x['path']:x for x in scope['files']};assert len(by)==64
assert report['source_commit']==scope['source_commit']=='8050c66900899771766f33e8f5fdd200b7dd9120'
assert report['status']=='complete' and report['remaining_work']==[]
assert set(notes)==set(by)=={x['path']for x in report['file_reviews']}
assert len(report['file_reviews'])==64
for x in report['file_reviews']:
 src=by[x['path']];raw=(R/x['path']).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==src['sha256']==x['sha256']
 assert x['full_source_read']is True and x['reviewed_lines']==[[1,src['lines']]]
 assert x['assessment']==notes[x['path']]
 intervals=[v['emitted_lines']for v in emissions if v['path']==x['path']]
 seen=set()
 for lo,hi in intervals:seen.update(range(lo,hi+1))
 assert set(range(1,src['lines']+1))<=seen,x['path']
ids=[];refs=0
for kind in ['claims','findings','validation']:
 for item in report[kind]:
  ids.append(item['id'])
  if kind=='claims':assert set(['id','claim','evidence','dependencies','limitations'])<=set(item)
  for ev in item.get('evidence',[]):
   p=R/ev['path'];lo,hi=ev['lines'];assert p.is_file()and 1<=lo<=hi<=len(p.read_text(encoding='utf-8').splitlines()),ev
   refs+=1
  if item.get('details_file'):
   receipt=json.loads((R/item['details_file']).read_text())
   for pin in receipt.get('source_files',[])+receipt.get('libraries',[]):assert hashlib.sha256((R/pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin
assert len(ids)==len(set(ids))
py=load('_validation_05.json');native=load('_validation_06.json')
actual={x['fixture']:{k:v['actual']for k,v in x['fields'].items()}for x in py['checks']if 'fields'in x}
for ln in native['runs'][0]['output'].splitlines():
 x=json.loads(ln)
 if 'actual_record'in x:
  assert all(x['actual_record'][k]==v for k,v in actual[x['name']].items()),x['name']
assert len(py['checks'])==15
out={'source_commit':report['source_commit'],'files':64,'lines':sum(x['lines']for x in by.values()),'bytes':sum(x['bytes']for x in by.values()),'source_hashes':'all match','full_read_assessments':'64 explicit manual assessments; emission coverage separately checked, not promoted automatically','evidence_references_checked':refs,'claims':len(report['claims']),'findings':len(report['findings']),'validation':len(report['validation']),'unique_ids':True,'native_python_factory_hash_correspondence':'both vectors, all reconstructed hash/reference fields match','report_sha256':hashlib.sha256((H/(P+'.json')).read_bytes()).hexdigest()}
(H/(P+'_final_validation.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
