from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files'];coverage=json.loads((R/'dag/reviews/coverage.json').read_text())['files']
prior=defaultdict(list);dupes=defaultdict(list)
for r in coverage:
 if r.get('substantive_status')=='full_text_source_review_recorded':prior[r['sha256']].append(r)
for r in rows:dupes[r['sha256']].append(r['index'])
relations=[]
for r in rows:
 matches=[p for p in prior[r['sha256']] if p['path']!=r['path']]
 relations.append(dict(index=r['index'],path=r['path'],sha256=r['sha256'],scope_exact_matches=dupes[r['sha256']],prior_full_receipt_candidates=matches))
Path(str(P)+'_relations.json').write_text(json.dumps({'files':relations,'limit':'Candidates only. Hash equality does not itself grant reading transfer or semantic equivalence.'},indent=2)+'\n',encoding='utf8')
print('UNIQUE',len(dupes),'EXACT_PRIOR',sum(bool(x['prior_full_receipt_candidates']) for x in relations))
print('LARGEST DUPLICATE GROUPS')
for sha,ids in sorted(dupes.items(),key=lambda kv:len(kv[1]),reverse=True)[:25]:print(len(ids),ids,rows[ids[0]]['path'])
print('PRIOR SOURCE CANDIDATES')
for x in relations:
 if x['prior_full_receipt_candidates']:print(x['index'],x['path'],'BASE',x['prior_full_receipt_candidates'][0]['path'],'REPORT',x['prior_full_receipt_candidates'][0]['reading_receipts'])
