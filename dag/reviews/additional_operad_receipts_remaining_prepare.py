from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
s=json.loads(Path(str(P)+'_scope.json').read_text());rows=[]
for i,r in enumerate(s['files']):
 p=R/r['path'];b=p.read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
 try:t=b.decode('utf8');lines=len(t.splitlines());encoding='utf8'
 except UnicodeError:lines=None;encoding='binary_or_non_utf8'
 rows.append(dict(r,index=i,lines=lines,encoding=encoding))
groups=defaultdict(list)
for r in rows:groups['/'.join(r['path'].split('/')[2:4])].append(r)
out=dict(scope_sha256=hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest(),files=rows,
 summary=dict(files=len(rows),bytes=sum(x['bytes'] for x in rows),text_lines=sum(x['lines'] or 0 for x in rows),extensions=dict(Counter(Path(x['path']).suffix for x in rows))),
 groups=[dict(group=k,count=len(v),bytes=sum(x['bytes'] for x in v),lines=sum(x['lines'] or 0 for x in v)) for k,v in groups.items()])
Path(str(P)+'_inventory.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out['summary']));print('\n'.join(str(x) for x in out['groups']))
print('LARGEST');print('\n'.join(str((x['index'],x['bytes'],x['lines'],x['path'])) for x in sorted(rows,key=lambda x:x['bytes'],reverse=True)[:18]))
coverage=json.loads((R/'dag/reviews/coverage.json').read_text());print('COVERAGE KEYS',list(coverage))
for k,v in coverage.items():
 if isinstance(v,list):print(k,len(v),str(v[:1])[:4000])
