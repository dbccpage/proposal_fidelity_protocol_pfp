from pathlib import Path
import collections,hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_adversary_remaining'
scope=json.loads(Path(str(P)+'_scope.json').read_text());rows=[]
for i,x in enumerate(scope['files']):
 b=(R/x['path']).read_bytes();h=hashlib.sha256(b).hexdigest();assert h==x['sha256'],x['path'];assert len(b)==x['size_bytes']
 try:t=b.decode('utf8');encoding='utf8';lines=len(t.splitlines())
 except UnicodeDecodeError:encoding='binary';lines=None
 rows.append({'index':i,'path':x['path'],'sha256':h,'bytes':len(b),'lines':lines,'encoding':encoding})
out={'scope_sha256':hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest(),'files':rows,'summary':{'paths':len(rows),'bytes':sum(x['bytes'] for x in rows),'text_lines':sum(x['lines'] or 0 for x in rows),'extensions':dict(collections.Counter(Path(x['path']).suffix for x in rows))}}
Path(str(P)+'_inventory.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(out['summary'])
for r in rows:print(r['index'],r['lines'],r['bytes'],r['path'].removeprefix('ops/adversary/'))
