"""Persist completed direct/base-delta source readings only."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_006_support';BASE='papers/pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining/'
def load(s):return json.loads((HERE/(P+s)).read_text(encoding='utf-8'))
scope=load('_scope.json');rows={r['path']:r for r in scope['files']};notes={}
for p in sorted(HERE.glob(P+'_notes*.json')):notes.update(json.loads(p.read_text(encoding='utf-8')))
coverage={}
for r in load('_read_ledger.json'):
 if not r.get('output_truncated'):coverage.setdefault(r['path'],set()).update(n for a,b in r['reviewed_lines'] for n in range(a,b+1))
transfers={r['path']:r for r in load('_base_transfer.json')};old=json.loads((HERE/'additional_paper_004_support.json').read_text(encoding='utf-8'));old_full={r['path']:r for r in old['file_reviews'] if r['full_source_read']}
reviews=[]
for name,assessment in notes.items():
 path=BASE+name;row=rows[path];assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==row['sha256']
 item={'path':path,'sha256':row['sha256'],'full_source_read':True,'reviewed_lines':[[1,row['lines']]] if row['lines'] else [],'assessment':assessment}
 if path in transfers:
  t=transfers[path];assert t['base_sha256']==old_full[t['base_path']]['sha256'];assert t['raw_equal'] or name=='pyproject.toml';item['base_equality_delta_transfer']=t
 else:assert coverage[path]==set(range(1,row['lines']+1)),path
 reviews.append(item)
pending=[p for p in rows if p not in {r['path'] for r in reviews}]
report={'schema_version':'1.0','status':'in_progress','source_commit':scope['source_commit'],'scope_manifest':'dag/reviews/'+P+'_scope.json','file_reviews':sorted(reviews,key=lambda r:r['path']),'remaining_scope':pending,'claims':[],'findings':[],'limits':['Checkpoint; pending paths have no reading receipts.','Source-body reading and historical execution are distinct.','Exact equality transfers require a fully read base and contextual assessment; pyproject complete delta was manually read.']}
(HERE/(P+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(HERE/(P+'.md')).write_text(f'# Paper006 support audit\n\nCheckpoint: {len(reviews)}/{len(rows)} full source bodies assessed; {len(pending)} pending paths. Original bytes preserved.\n',encoding='utf-8')
print(json.dumps({'reviewed':len(reviews),'pending':len(pending),'scope':len(rows)}))
