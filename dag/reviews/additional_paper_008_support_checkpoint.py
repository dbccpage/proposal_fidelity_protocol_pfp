"""Compile only fully observed readings into an honest current checkpoint."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_008_support';BASE='papers/pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks/'
def load(s):return json.loads((HERE/(P+s)).read_text(encoding='utf-8'))
scope=load('_scope.json');validation=load('_scope_validation.json');rows={r['path']:r for r in validation['files']};notes={}
for p in sorted(HERE.glob(P+'_notes*.json')):notes.update(json.loads(p.read_text(encoding='utf-8')))
coverage={}
for r in load('_read_ledger.json'):
 if not r.get('output_truncated'):coverage.setdefault(r['path'],set()).update(i for a,b in r['reviewed_lines'] for i in range(a,b+1))
transfers={r['path']:r for r in load('_base_transfer.json')};old=json.loads((HERE/'additional_paper_004_support.json').read_text());oldfull={r['path']:r for r in old['file_reviews'] if r['full_source_read']};reviews=[]
for name,assessment in notes.items():
 path=BASE+name;r=rows[path];assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==r['sha256'];item={'path':path,'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,r['lines']]] if r['lines'] else [],'assessment':assessment}
 if path in transfers:
  t=transfers[path];assert t['base_sha256']==oldfull[t['base_path']]['sha256'];assert t['raw_equal'] or name in ['pyproject.toml','verify_deposit.py'];item['base_equality_delta_transfer']=t
 else:assert coverage[path]==set(range(1,r['lines']+1)),path
 reviews.append(item)
pending=[p for p in rows if p not in {r['path'] for r in reviews}];report={'schema_version':'1.0','status':'in_progress','source_commit':scope['source_commit'],'scope_manifest':'dag/reviews/'+P+'_scope.json','file_reviews':sorted(reviews,key=lambda r:r['path']),'remaining_scope':pending,'claims':[],'findings':[],'limits':['Checkpoint: pending files have no full reading receipt.','Direct bodies or exact fully-read base plus complete manually read diffs; semantic assessment supplied per owner.','Historical execution, fresh tests and source reading remain distinct.']}
(HERE/(P+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');(HERE/(P+'.md')).write_text(f'# Paper 008 support audit\n\nCheckpoint: {len(reviews)} of {len(rows)} assigned full source bodies assessed; {len(pending)} paths remain. No original bytes altered.\n',encoding='utf-8');print(json.dumps({'full':len(reviews),'remaining':len(pending)}))
