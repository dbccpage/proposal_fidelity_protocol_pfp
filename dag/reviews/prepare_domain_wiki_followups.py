"""Freeze disjoint outstanding domain and wiki paths from the original inventory."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
coverage=json.loads((REV/'coverage.json').read_text(encoding='utf-8'))
for name,prefix in [('additional_pfp_domain_remaining','pfp/domain/'),('additional_wiki_remaining','wiki/')]:
    rows=[]
    for r in coverage['files']:
        if not r['path'].startswith(prefix) or r['substantive_status']=='full_text_source_review_recorded':continue
        p=ROOT/r['path'];raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest==r['sha256'],r['path']
        rows.append({'path':r['path'],'sha256':digest,'bytes':len(raw),'coverage_at_freeze':r['substantive_status']})
    target=REV/(name+'_scope.json')
    target.write_text(json.dumps({'source_commit':coverage['source_commit'],'scope':prefix,
        'files':rows,'limits':'Read-only original source review. Excludes complete prior body reviews; partial and automated-only checks do not remove substantive work. No private benchmark/provider/foreign source access.'},indent=2)+'\n',encoding='utf-8')
    print(name,len(rows),sum(x['bytes'] for x in rows))
