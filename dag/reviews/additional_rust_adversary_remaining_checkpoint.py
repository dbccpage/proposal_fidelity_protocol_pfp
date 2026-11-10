"""Persist exact reading/transfer coverage and individual source assessments."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_rust_adversary_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads(Path(str(P)+s).read_bytes())
raw=Path(str(P)+'_scope.json').read_bytes();assert h(raw)=='d0547aab64c96d5e8cb280c02ad499283cff257d6931ca886f113cb4235ccd27'
s=json.loads(raw);notes=load('_notes.json');ledger=load('_read_ledger.json');transfers=load('_template_transfers.json');tm={r['index']:r for r in transfers['transfers']}
reviews=[];pending=[];total=0;direct=0;transferred=0
for i,row in enumerate(s['files']):
 b=(R/row['path']).read_bytes();assert h(b)==row['sha256'] and len(b)==row['size_bytes'];n=len(b.decode('utf8').splitlines());total+=n
 if str(i) not in notes:pending.append(dict(row,index=i,source_lines=n));continue
 seen=set()
 for rec in ledger:
  if rec['index']==i:
   assert rec['sha256']==row['sha256'];a,z=rec['displayed_lines'];seen.update(range(a,z+1))
 raw_full=seen==set(range(1,n+1))
 if not raw_full:
  tr=tm[i];assert tr['sha256']==row['sha256'] and tr['all_other_text_exactly_equal'];a,z=tr['reviewed_lines'];seen.update(range(a,z+1));transferred+=1
 else:direct+=1
 assert seen==set(range(1,n+1)),(i,n,len(seen))
 fr={'path':row['path'],'sha256':row['sha256'],'source_line_count':n,'full_source_read':True,'reviewed_lines':[[1,n]],'review_level':'full_raw_source_body_review' if raw_full else 'full_owner_prefix_plus_exact_pinned_template_and_complete_residual_review','assessment':notes[str(i)],'source_evidence':[{'path':row['path'],'sha256':row['sha256'],'lines':[1,n]}],'actual_execution_status':'No Rust/original module/native/Cargo/provider execution. Source review only; independent finite controls, if added, are separate.'}
 if not raw_full:fr['template_transfer']=tr
 reviews.append(fr)
out={'review_id':'additional_rust_adversary_remaining','scope_sha256':h(raw),'scope_manifest':'dag/reviews/additional_rust_adversary_remaining_scope.json','status':'checkpoint_reading_continues' if pending else 'complete_declared_scope','source_commit':s['source_commit'],'summary':{'frozen_paths':99,'full_source_reads':len(reviews),'full_direct_raw_reads':direct,'full_prefix_and_exact_template_reads':transferred,'pending':len(pending),'bytes':1602171,'source_lines':total,'full_body_lines':sum(r['source_line_count'] for r in reviews),'original_functions_or_modules_executed':0},'method':['Every completed file has its own substantive owner assessment. Full display ledger is not by itself semantic review.','Generated trailers may use two complete pinned manually read bases plus all origin/claim/identifier residuals. The complete remaining text must be exact; owner prefixes are independently fully read before whole-file credit.','Generated mutation-accounting comments and tests are retained source declarations, not new executions or qualification of enclosing owners.','No original bytes edited; only this audit prefix is written. No Cargo/native/provider/credential/private benchmark access.'], 'claims':[],'findings':[],'file_reviews':reviews,'partial_read_context':[{'path':s['files'][17]['path'],'sha256':s['files'][17]['sha256'],'reviewed_lines':[[952,1074]],'full_source_read':False,'assessment':'Only the complete generated count-template trailer is read as a transfer base. Dialectic production prefix remains pending; no whole-file credit.'}] if '17' not in notes else [],'reading_ledger':'dag/reviews/additional_rust_adversary_remaining_read_ledger.json','reading_ledger_sha256':h(Path(str(P)+'_read_ledger.json').read_bytes()),'template_transfer_artifact':'dag/reviews/additional_rust_adversary_remaining_template_transfers.json','template_transfer_sha256':h(Path(str(P)+'_template_transfers.json').read_bytes()),'limitations':['Checkpoint only: incomplete owners are pending, even if a generated suffix has been transferred.','External dependencies/tests are not newly read or executed unless explicitly recorded. Source admission and finite checks are not deployment or efficacy certification.']}
Path(str(P)+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
Path(str(P)+'_remaining_scope.json').write_text(json.dumps({'scope_sha256':h(raw),'pending_files':len(pending),'files':pending},indent=2)+'\n',encoding='utf8')
md=['# Rust adversary source review checkpoint','',f"{len(reviews)}/99 full source bodies; {direct} direct raw reads and {transferred} complete owner-prefix plus exact-template/residual reads. {len(pending)} paths remain pending. No original/native/Cargo/provider execution.",'','Template transfer preserves exact raw file hashes and complete difference receipts. Repeated counter tests are not production proof.','']
for r in reviews:md.extend([f"- `{r['path']}` (1–{r['source_line_count']}): {r['assessment']}",''])
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf8')
snapshot=Path(str(P)+f"_checkpoint{len(reviews):03d}.json.snapshot")
if snapshot.exists():assert snapshot.read_bytes()==Path(str(P)+'.json').read_bytes()
else:snapshot.write_bytes(Path(str(P)+'.json').read_bytes())
print(json.dumps({'summary':out['summary'],'report_sha256':h(Path(str(P)+'.json').read_bytes())},indent=2))
