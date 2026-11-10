import sys
sys.dont_write_bytecode=True
import json,collections
import additional_pfp_tests_remaining_audit as a
def shape(v,depth=0):
 if isinstance(v,dict):return {k:shape(x,depth+1) if depth<2 else type(x).__name__ for k,x in v.items()}
 if isinstance(v,list):return {'kind':'list','count':len(v),'first_shape':shape(v[0],depth+1) if v and depth<3 else None}
 if isinstance(v,str):return v if len(v)<160 else v[:157]+'...'
 return v
for r in a.scope()['files']:
 if r['path'].endswith('.json'):
  p=a.ROOT/r['path'];assert a.sha(p)==r['sha256'];d=json.loads(p.read_text(encoding='utf8'))
  print(r['path']+' SHA '+r['sha256']);print(json.dumps(shape(d),ensure_ascii=False))
