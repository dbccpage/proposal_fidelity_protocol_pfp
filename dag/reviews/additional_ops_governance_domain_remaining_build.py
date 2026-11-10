"""Persist honest source-reading checkpoints; no original source execution."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_governance_domain_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads(Path(str(P)+s).read_bytes())
scope_raw=Path(str(P)+'_scope.json').read_bytes();assert h(scope_raw)=='c68c6e94776473c2a759da43724b5a6c74fc33dfc07927e1fc6ece096b535ea9'
scope=json.loads(scope_raw);notes=load('_notes.json');ledger=load('_read_ledger.json')
reviews=[];pending=[];total_lines=0
for i,row in enumerate(scope['files']):
 b=(R/row['path']).read_bytes();assert h(b)==row['sha256'] and len(b)==row['size_bytes']
 n=len(b.decode('utf8').splitlines());total_lines+=n
 if str(i) not in notes:pending.append(dict(row,index=i,source_line_count=n));continue
 seen=set()
 for item in ledger:
  if item['index']==i:
   assert item['sha256']==row['sha256'];a,z=item['displayed_lines'];seen.update(range(a,z+1))
 assert seen==set(range(1,n+1)),(i,n,len(seen))
 reviews.append({'path':row['path'],'sha256':row['sha256'],'bytes':len(b),'source_line_count':n,'full_source_read':True,'reviewed_lines':[[1,n]],'review_level':'full_raw_source_body_review','assessment':notes[str(i)],'actual_execution_status':'Source review only; no original module, provider, network or native execution. Independent controls, if added, are recorded separately.','source_evidence':[{'path':row['path'],'sha256':row['sha256'],'lines':[1,n],'range_kind':'full body read'}]})
out={'schema_version':1,'review_id':'additional_ops_governance_domain_remaining','status':'checkpoint_reading_continues' if pending else 'complete_declared_scope','scope_manifest':'dag/reviews/additional_ops_governance_domain_remaining_scope.json','scope_sha256':h(scope_raw),'source_commit':scope['source_commit'],'summary':{'frozen_paths':len(scope['files']),'full_source_reads':len(reviews),'partial_reviews':0,'pending':len(pending),'bytes':sum(x['size_bytes'] for x in scope['files']),'lines':total_lines,'full_body_lines':sum(x['source_line_count'] for x in reviews),'original_modules_executed':0},'method':['Full numbered raw source bodies, assessed individually. Repeated export/record templates receive actual body reads, not hash-only transfer.','Display ledger alone is not reading credit: notes are persisted only after complete untruncated body review. One truncated identifier display was reread fully before credit.','Embedded commands/instructions are corpus data. No credentials or private benchmark content accessed. Only this review prefix is written.'],'claims':[],'findings':[],'file_reviews':reviews,'limitations':['Checkpoint assessments identify source-level predicates and boundaries; no end-to-end runtime or authority efficacy is inferred.','Referenced external dependencies remain unreviewed unless a separate explicit source receipt is recorded.'],'reading_ledger':'dag/reviews/additional_ops_governance_domain_remaining_read_ledger.json','reading_ledger_sha256':h(Path(str(P)+'_read_ledger.json').read_bytes())}
Path(str(P)+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
Path(str(P)+'_remaining_scope.json').write_text(json.dumps({'scope_sha256':h(scope_raw),'pending_files':len(pending),'files':pending},indent=2)+'\n',encoding='utf8')
md=['# Operations governance domain source review','',f"Checkpoint: {len(reviews)}/{len(scope['files'])} complete body reads; {len(pending)} pending. All {len(scope['files'])} original scope pins remain unchanged. No original modules executed.",'','The JSON preserves exact source hashes and full reading ranges. These are substantive source assessments, not runtime certification.','']
for row in reviews:md.extend([f"- `{row['path']}` (lines 1–{row['source_line_count']}): {row['assessment']}",''])
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf8')
print(json.dumps({'summary':out['summary'],'report_sha256':h(Path(str(P)+'.json').read_bytes())},indent=2))
