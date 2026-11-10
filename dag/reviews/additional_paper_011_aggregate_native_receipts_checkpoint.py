import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
def load(s,default):
 p=H/(P+s);return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
prep=load('_preparation.json',{});notes=load('_notes.json',{});ledger=load('_read_ledger.json',[])
extras=load('_artifact_reviews.json',[]);transfers=load('_transfers.json',[])
reviews=[];pending=[]
for row in prep['files']:
 p=row['path'];assert hashlib.sha256((R/p).read_bytes()).hexdigest()==row['sha256']
 extra=next((r for r in extras if r['path']==p),None)
 if extra:reviews.append(extra);continue
 if row['relative'] not in notes:pending.append(row);continue
 ranges=set()
 for r in ledger:
  if r['path']==p and not r.get('output_truncated'):
   assert r['sha256']==row['sha256']
   for a,b in r['reviewed_lines']:ranges.update(range(a,b+1))
 t=next((t for t in transfers if t['path']==p),None)
 assert t or ranges==set(range(1,row['lines']+1)),p
 review={'path':p,'sha256':row['sha256'],'full_source_read':True,'reviewed_lines':[[1,row['lines']]] if row['lines'] else [],'assessment':notes[row['relative']],'review_level':'full_body_with_exact_baseline_and_all_differences' if t else 'complete_source_body','limits':'Written source or retained record review, not a fresh execution or authentication of historical model calls.'}
 if t:review['body_transfer']=t
 reviews.append(review)
report={'source_commit':prep['source_commit'],'scope_manifest':{'path':'dag/reviews/'+P+'_scope.json','sha256':prep['scope_sha256']},'status':'in_progress' if pending else 'complete','scope_summary':{'assigned':len(prep['files']),'full_body':sum(r['full_source_read'] for r in reviews),'bounded':sum(not r['full_source_read'] for r in reviews),'pending':len(pending)},'file_reviews':reviews,'claims':load('_claims.json',[]),'findings':load('_findings.json',[]),'checks':load('_checks.json',{}),'remaining_paths':[r['path'] for r in pending],'limits':['No new provider calls, native execution, private benchmark/key access or original-source edits.','Parsed populations and ciphertext/binary custody are distinct from full human body reading.','Historical successes and negative evidence remain historical.']}
(H/(P+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(H/(P+'_remaining_scope.json')).write_text(json.dumps({'parent_scope':report['scope_manifest'],'files':pending},indent=2)+'\n',encoding='utf-8')
(H/(P+'.md')).write_text('# Paper011 aggregate/native receipt audit\n\n'+json.dumps(report['scope_summary'])+'\n\n'+'\n\n'.join(r['path']+'\n\n'+r['assessment'] for r in reviews)+'\n',encoding='utf-8')
print(json.dumps(report['scope_summary']))
