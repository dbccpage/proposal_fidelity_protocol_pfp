"""Persist only completed, hash-bound body reads with substantive assessments."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_009_support';B='papers/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/'
def load(s):return json.loads((H/(P+s)).read_text(encoding='utf-8'))
s=load('_scope.json');rows={r['path']:r for r in s['files']};notes={}
for p in sorted(H.glob(P+'_notes*.json')):notes.update(json.loads(p.read_text()))
coverage={}
for r in load('_read_ledger.json'):
 if not r.get('output_truncated'):coverage.setdefault(r['path'],set()).update(i for a,b in r['reviewed_lines'] for i in range(a,b+1))
transfers={r['path']:r for r in load('_base_transfer_candidates.json')};reviews=[]
for name,assessment in notes.items():
 p=B+name;r=rows[p];assert hashlib.sha256((R/p).read_bytes()).hexdigest()==r['sha256'];n=r['lines'];q={'path':p,'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,n]] if n else [],'assessment':assessment}
 if p in transfers:
  t=transfers[p];a=json.loads((R/t['base_report']).read_text());base=next(v for v in a['file_reviews'] if v['path']==t['base_path']);assert base['full_source_read'] and base['sha256']==t['base_sha256'];assert t['raw_equal'] or t.get('diff_read');q['base_equality_delta_transfer']=t
 else:assert coverage[p]==set(range(1,n+1)),p
 reviews.append(q)
pending=[p for p in rows if p not in {r['path'] for r in reviews}];a={'schema_version':'1.0','status':'in_progress','source_commit':s['source_commit'],'scope_manifest':'dag/reviews/'+P+'_scope.json','file_reviews':sorted(reviews,key=lambda r:r['path']),'remaining_scope':pending,'claims':[],'findings':[],'limits':['Checkpoint only; pending artifacts have no reading receipt.','Every completed executable/prose body reviewed directly or through hash-bound full base and complete differences; not an execution claim.']}
(H/(P+'.json')).write_text(json.dumps(a,indent=2)+'\n');(H/(P+'.md')).write_text(f'# Paper009 supporting-file audit\n\nCheckpoint: {len(reviews)}/66 full source bodies assessed; {len(pending)} remain. Original bytes unchanged.\n');(H/(P+'_remaining_scope.json')).write_text(json.dumps({'files':[rows[p] for p in pending]},indent=2)+'\n');print(json.dumps({'full':len(reviews),'remaining':len(pending)}))
