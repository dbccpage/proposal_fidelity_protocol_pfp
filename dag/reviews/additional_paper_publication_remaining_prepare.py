"""Freeze original inventory/coverage scope; metadata is not reading credit."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_paper_publication_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
paths=[R/'dag/file_inventory.json',R/'dag/reviews/coverage.json',R/'dag/reviews/papers_audit.json']
data=[json.loads(p.read_bytes()) for p in paths];inventory,coverage,prior=data
im={r['path']:r for r in inventory['files']};pm={r['path']:r for r in prior['files']}
rows=[]
for c in coverage['files']:
 if not c['path'].startswith('papers/pfp/publication/') or c['substantive_status']!='pending':continue
 r=im[c['path']];assert r['sha256']==c['sha256'];b=(R/r['path']).read_bytes();assert h(b)==r['sha256'] and len(b)==r['size_bytes']
 rows.append({'path':r['path'],'sha256':r['sha256'],'size_bytes':r['size_bytes'],'category':r['category'],'coverage_status_at_freeze':c['substantive_status'],'prior_paper_audit_status':pm[r['path']]['review_status']})
rows.sort(key=lambda r:r['path']);assert len(rows)==585
out={'schema_version':'1.0','created_utc':datetime.now(timezone.utc).isoformat(),'source_commit':coverage['source_commit'],'root':'papers/pfp/publication/','scope':'All pending original-inventory paths under the publication root, frozen from current coverage; no source-body credit from this preparation.','inputs':[{'path':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes())} for p in paths],'file_count':len(rows),'size_bytes':sum(r['size_bytes'] for r in rows),'extensions':dict(sorted(Counter(Path(r['path']).suffix.lower() for r in rows).items())),'files':rows,'constraints':['Only this audit prefix may be written. Originals remain unchanged.','No private answer/evaluator storage, provider calls, native builds or retained executable runs.','Exact equality is a custody relation, not automatic contextual semantic review.','Large artifacts may retain explicit bounded dispositions; full body/pages/cells require actual review.','Live sixteen-thousand-token control output is out of scope until parent confirms final freeze.']}
target=Path(str(P)+'_scope.json');assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
Path(str(P)+'_remaining_scope.json').write_bytes(target.read_bytes())
print(json.dumps({'file_count':len(rows),'bytes':out['size_bytes'],'extensions':out['extensions'],'scope_sha256':h(target.read_bytes())},indent=2))
for i,r in enumerate(rows):
 if i<30 or r['path'].count('/')<=3:print(i,r['size_bytes'],r['path'])
