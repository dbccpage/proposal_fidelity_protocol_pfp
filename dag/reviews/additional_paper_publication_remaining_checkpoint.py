"""Persist a truthful publication reading checkpoint; no source mutations."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_paper_publication_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads(Path(str(P)+s).read_bytes())
scope=load('_scope.json');assert h(Path(str(P)+'_scope.json').read_bytes())=='79e512c0abeda630d0485260b9f67387f96fa2829646068e0c3bb64600029430'
S=scope['files'];ledger=load('_read_ledger.json')
notes={
0:'Full14-line wrapper. This is author-review packaging, explicitly no deposit/DOI/acceptance. It distinguishes retained original Markdown from linked publication rendering and pins a conceptual code baseline. Keeping source and publication copies is useful provenance, but original relative links remain dependent on the source layout. This wrapper supplies no new theorem, code execution or learning-effectiveness evidence.',
1:'Full20-line JSON receipt. Tool/version, conceptual source commit, source/ledger/render/PDF/TeX hashes and compiled status are historical declarations. Checked current raw/LF/CRLF candidate bindings separately below; mismatches alone do not prove the historic build failed or identify an unknown historical normalization. No compiler/render process was run. Useful as a historical build inventory, not present-source mathematical validation.',
2:'Full51-line rendered ledger. Its finite claim list is substantively the same declared teaching scope as the source ledger: carrier/goal/type guards, exact counts, supplied separation tables, request-bound return/replay, bijective renaming and finite fuel. It explicitly denies broader runtime security, producer authentication, convergence and universal canonicalization. Workbook execution is a reproduction obligation backed only by a named historical receipt here; no new replay credit. Publication rendering contributes accessibility/packaging, not an independent corroborating check.',
3:'Full17-line source ledger. Each claim is tied to a finite teaching mechanism and its limits. The distinction between supplied observation-table separation and arbitrary observations is sound. Model-prompt override resistance here means English is inert data for this deterministic checker, not demonstrated resistance of live model/tool transport. Tests/receipt references are pointers rather than newly reviewed or executed owners in this slice.',
4:'All771 lines of the linked manuscript read. Useful mechanisms are the fixed declared board/checker, candidate/problem identity, same-task repair, explicitly changed inputs, exact finite separation, bijective renaming, retained failures and budget exhaustion as UNKNOWN. These are finite educational workflows, not a derivation of Genesis from typography or a general proof/search algorithm. The text correctly separates finite validity, semantic interpretation and practical usefulness, explicitly limits its quantum/physical and model-ranking implications, and does not infer learning transfer. The tiny extension down function is only illustrated on well-formed tuples; it is not a total hostile-input parser. Referenced tests/notebook release receipts were not rerun or newly read here. This fresh publication-body assessment agrees with prior primary-manuscript review without claiming new efficacy evidence.',
7:'Complete604-logical-line body transferred by exact byte identity from a prior pinned full primary-manuscript read (its1–605 receipt includes the terminal empty split line), with fresh publication wrapper/linked-manuscript context reviewed. This source copy preserves the supplied teaching definitions and nonclaims; it is not a second independent derivation or experiment. Original relative links can resolve differently in the publication tree; the wrapper intentionally directs readers to the linked rendering. No fresh source-body display or execution is claimed for this exact copy.'
}
prior=R/'dag/reviews/papers_audit.json';pr=json.loads(prior.read_bytes());basepath='papers/pfp/000_pfp_introduction/paper.md'
base=next(r for r in pr['files'] if r['path']==basepath);assert base['review_status']=='full-text-read' and base['reviewed_ranges']==[{'start':1,'end':605}]
reviews=[];allpins=[]
for i,r in enumerate(S):
 b=(R/r['path']).read_bytes();assert h(b)==r['sha256'] and len(b)==r['size_bytes'];allpins.append(r['sha256'])
 if i not in notes:continue
 lines=b.decode('utf8').splitlines();n=len(lines);transfer=None
 if i==7:
  bb=(R/basepath).read_bytes();assert bb==b and h(bb)==base['sha256'] and n==604 and len(b.decode('utf8').split('\n'))==605
  transfer={'method':'exact_complete_body_copy_with_prior_full_read_receipt_and_fresh_context_assessment','base_path':basepath,'base_sha256':h(bb),'base_review_report':'dag/reviews/papers_audit.json','base_review_report_sha256':h(prior.read_bytes()),'base_reviewed_lines':[[1,605]],'target_reviewed_lines':[[1,604]],'line_convention':'Prior receipt counts the terminal empty newline-split line; target splitlines has604 logical lines. Both cover every identical byte.','complete_byte_equality':True,'residual_bytes':0,'fresh_context_paths':[S[j]['path'] for j in [0,2,3,4]],'fresh_raw_body_display':False}
 else:
  got=set()
  for rec in ledger:
   if rec['index']==i:assert rec['sha256']==r['sha256'];a,z=rec['displayed_lines'];got.update(range(a,z+1))
  assert got==set(range(1,n+1))
 row={'path':r['path'],'sha256':r['sha256'],'source_line_count':n,'full_source_read':True,'reviewed_lines':[[1,n]],'review_level':'full_body_via_prior_pinned_read_exact_copy_and_context_review' if transfer else 'full_raw_source_body_review','assessment':notes[i],'source_evidence':[{'path':r['path'],'sha256':r['sha256'],'lines':[1,n]}],'actual_execution_status':'No original/native/provider execution. Historical status and fresh source review are distinct.'}
 if transfer:row['transfer']=transfer
 reviews.append(row)
receipt=json.loads((R/S[1]['path']).read_bytes());bindings=[]
for key,i in [('source_sha256',7),('ledger_sha256',3),('markdown_sha256',4),('ledger_markdown_sha256',2),('tex_sha256',6),('pdf_sha256',5)]:
 b=(R/S[i]['path']).read_bytes();variants={'raw':h(b)}
 if i!=5:
  lf=b.replace(b'\r\n',b'\n');variants.update(lf=h(lf),crlf=h(lf.replace(b'\n',b'\r\n')))
 bindings.append({'receipt_field':key,'declared_sha256':receipt[key],'current_candidate_path':S[i]['path'],'current_candidate_sha256':S[i]['sha256'],'tested_encodings':variants,'matching_tested_encodings':[k for k,v in variants.items() if v==receipt[key]],'limit':'These are current candidates/explicit newline variants, not a reconstructed original build. Unknown historical transformation remains unresolved.'})
done={r['path'] for r in reviews};remaining=[r for r in S if r['path'] not in done]
def ev(i,a,z):return {'path':S[i]['path'],'sha256':S[i]['sha256'],'lines':[a,z]}
out={'review_id':'additional_paper_publication_remaining','status':'checkpoint_reading_continues','scope_manifest':'dag/reviews/additional_paper_publication_remaining_scope.json','scope_sha256':h(Path(str(P)+'_scope.json').read_bytes()),'source_commit':scope['source_commit'],'summary':{'frozen_paths':585,'full_source_reads':6,'direct_full_body_reads':5,'exact_prior_read_transfers':1,'partial_source_reads':0,'bounded_dispositions':0,'pending':579,'full_body_lines':sum(r['source_line_count'] for r in reviews),'original_execution':0},'claims':[{'id':'PUB-C01','title':'Publication000 preserves a useful bounded teaching workflow without broad efficacy claims.','assessment':'Task declaration, fixed candidate binding, same-board repair, independent finite predicates, retained failure and explicit UNKNOWN after fuel are reusable pedagogical control mechanisms. Publication form adds no independent correctness, model performance or learner-transfer evidence.','source_evidence':[ev(4,111,192),ev(4,302,337),ev(4,435,478),ev(4,550,603)],'limits':'Source reading only. The primary manuscript assessment was already present in papers_audit; this claim concerns the actual publication rendering and preservation of its scope fences.','workflow_reuse':'Use these mechanisms as explicit finite task contracts and controls; keep benchmark accuracy and real task usefulness separate.'}],'findings':[],'file_reviews':reviews,'custody_checks':bindings,'reading_ledger':'dag/reviews/additional_paper_publication_remaining_read_ledger.json','reading_ledger_sha256':h(Path(str(P)+'_read_ledger.json').read_bytes()),'limitations':['Only6 of585 files have substantive reading receipts. All579 others remain pending, including publication000 PDF/TeX.','Prior audit consultation and scope hash/count scans confer no fresh full-body credit. A truncated initial metadata listing is not a reviewed source body.','No publication status, DOI, external acceptance, historical compiler run, provider performance or learner effectiveness is newly verified.','Current build-pin mismatches do not establish failure of unknown historical byte transformations.','No source originals, shared coverage/DAGs or live benchmark outputs were changed/read.']}
Path(str(P)+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
Path(str(P)+'_remaining_scope.json').write_text(json.dumps({'scope_sha256':out['scope_sha256'],'pending_files':len(remaining),'files':remaining},indent=2)+'\n',encoding='utf8')
md=['# Publication audit checkpoint','',f"6/585 source bodies covered:5 direct full reads and1 prior pinned full-body exact-copy/context transfer;579 pending. {out['summary']['full_body_lines']} covered lines. No original/native/provider execution.",'','Publication000 contributes bounded teaching mechanisms, not a second independent scientific result. Its historical build receipt is kept separate from current-byte binding and from mathematical correctness.','']
for r in reviews:md.extend([f"- `{r['path']}` (lines1–{r['source_line_count']}): {r['assessment']}",''])
md.extend(['## Limits','']+['- '+x for x in out['limitations']])
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf8')
snap=Path(str(P)+'_checkpoint006.json.snapshot')
if snap.exists():assert snap.read_bytes()==Path(str(P)+'.json').read_bytes()
else:snap.write_bytes(Path(str(P)+'.json').read_bytes())
validation={'status':'PASS_checkpoint_only','source_pins_checked':585,'full_reviewed_paths_checked':6,'direct_full_body_reads':5,'exact_body_transfers_checked':1,'pending':579,'report_sha256':h(Path(str(P)+'.json').read_bytes()),'scope_sha256':out['scope_sha256'],'limits':'Hash/range validation is not proof of the claims; remaining source bodies and artifacts are explicitly pending.'}
Path(str(P)+'_validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf8')
print(json.dumps(validation,indent=2));print('CURRENT_PIN_MATCHES',[(r['receipt_field'],r['matching_tested_encodings']) for r in bindings])
