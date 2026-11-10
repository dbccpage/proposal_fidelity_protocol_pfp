"""Bounded structure presentation, never full semantic credit."""
import pathlib,json,gzip,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining'
s=json.loads((H/(P+'_preparation.json')).read_text())['files']
def shape(x,depth=0):
 if isinstance(x,dict):return {k:shape(v,depth+1)if depth<2 else type(v).__name__+(f'[{len(v)}]'if isinstance(v,(list,dict,str))else'')for k,v in x.items()}
 if isinstance(x,list):return {'count':len(x),'first_shape':shape(x[0],depth+1)if x else None}
 return str(x)[:200]
for i in map(int,sys.argv[1].split(',')):
 r=s[i];b=(R/r['path']).read_bytes();b=gzip.decompress(b)if r['path'].endswith('.gz')else b
 x=[json.loads(l)for l in b.splitlines()]if '.jsonl'in r['path']else json.loads(b)
 print(i,r['path'],json.dumps(shape(x),ensure_ascii=True))
