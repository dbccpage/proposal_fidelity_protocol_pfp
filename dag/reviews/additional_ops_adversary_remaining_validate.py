from pathlib import Path
from collections import Counter
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_adversary_remaining'
def load(s):return json.loads(Path(str(P)+s).read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
scope=load('_scope.json');inv=load('_inventory.json');report=load('.json');ledger=load('_read_ledger.json');controls=load('_controls.json')
frozen={r['path']:r for r in scope['files']};current={r['path']:r for r in inv['files']};reviews={r['path']:r for r in report['file_reviews']}
assert len(frozen)==len(current)==len(reviews)==len(report['file_reviews'])==307
assert set(frozen)==set(current)==set(reviews)
assert sha(Path(str(P)+'_scope.json'))==inv['scope_sha256']==report['scope_sha256']==controls['scope_sha256']
assert report['status']=='complete' and not report['pending_paths'] and not load('_remaining_scope.json')['files']
displays={}
for item in ledger:
 assert item['path'] in current and item['sha256']==current[item['path']]['sha256']
 for lo,hi in item['displayed_lines']:displays.setdefault(item['path'],set()).update(range(lo,hi+1))
for path,entry in current.items():
 raw=(R/path).read_bytes();lines=raw.decode('utf8').splitlines();r=reviews[path]
 assert sha(R/path)==entry['sha256']==frozen[path]['sha256']==r['sha256']
 assert len(raw)==entry['bytes']==frozen[path]['size_bytes']==r['bytes']
 assert len(lines)==entry['lines']==r['source_line_count']
 assert r['full_source_read'] is True and r['reviewed_lines']==[[1,len(lines)]] and r['assessment'].strip()
 assert set(range(1,len(lines)+1))<=displays[path]
ev_count=0
for group in [report['claims'],report['findings'],report['file_reviews'],controls['controls']]:
 for row in group:
  for ev in row.get('source_evidence',[]):
   assert ev['path'] in current and ev['sha256']==current[ev['path']]['sha256']
   lo,hi=ev['lines'];assert 1<=lo<=hi<=current[ev['path']]['lines'];ev_count+=1
ids=[r['id'] for r in report['claims']+report['findings']];assert len(ids)==len(set(ids))
control_ids={r['id'] for r in controls['controls']}
assert len(control_ids)==19 and all(set(r['independent_controls'])<=control_ids for r in report['findings'])
assert report['independent_control_artifact']['sha256']==sha(Path(str(P)+'_controls.json'))
prior_drift=[]
for prior in report['prior_review_reconciliation']:
 if sha(R/prior['path'])!=prior['sha256']:prior_drift.append(prior['path'])
assert not prior_drift
out={'status':'validated','scope_sha256':inv['scope_sha256'],
 'coverage':{'frozen_files':307,'full_body_reads':307,'partial_body_reads':0,'bounded_only':0,'pending':0,
 'bytes':sum(r['bytes'] for r in current.values()),'lines':sum(r['lines'] for r in current.values())},
 'source_pins_matching':307,'source_ranges_validated':ev_count,'source_mutations':0,
 'claims':len(report['claims']),'findings':len(report['findings']),'controls':19,
 'reading_ledger_note':'Complete display union checked; substantive credit comes from explicit notes, not programmatic union. Truncated batches were read again.',
 'fresh_execution':'19 source-only controls; no retained/native/provider/broad tests',
 'artifacts':{s:{'path':str(P.relative_to(R))+s,'sha256':sha(Path(str(P)+s))} for s in ['.json','.md','_controls.json','_notes.json','_read_ledger.json','_scope.json']}}
Path(str(P)+'_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2))
