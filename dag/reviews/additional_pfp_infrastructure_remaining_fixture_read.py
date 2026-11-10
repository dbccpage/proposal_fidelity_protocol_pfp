"""Lossless semantic expansion: full first payload plus every complete case delta.

Never gives semantic credit. Exact raw reconstruction is required before recording
the emission; manual per-file assessment is maintained separately.
"""
import copy,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining'
rows=json.loads((H/(P+'_preparation.json')).read_text())['files']
lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())
def delta(a,b,path=()):
 if type(a)!=type(b):return [{'op':'replace','path':list(path),'value':b}]
 if isinstance(a,dict):
  d=[{'op':'remove','path':list(path+(k,))}for k in a if k not in b]
  for k,v in b.items():
   d+=delta(a[k],v,path+(k,))if k in a else[{'op':'add','path':list(path+(k,)),'value':v}]
  return d
 if isinstance(a,list)and len(a)==len(b):
  return [d for i,(x,y)in enumerate(zip(a,b))for d in delta(x,y,path+(i,))]
 return []if a==b else[{'op':'replace','path':list(path),'value':b}]
def apply(a,ops):
 a=copy.deepcopy(a)
 for op in ops:
  p=op['path']
  if not p:a=copy.deepcopy(op['value']);continue
  t=a
  for k in p[:-1]:t=t[k]
  if op['op']=='remove':del t[p[-1]]
  else:t[p[-1]]=copy.deepcopy(op['value'])
 return a
for i in map(int,sys.argv[1].split(',')):
 f=rows[i];raw=(R/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256']
 d=json.loads(raw);cases=d['cases'];assert cases and 'payload'in cases[0];base=cases[0]['payload']
 rebuilt={k:v for k,v in d.items()if k!='cases'};rebuilt['cases']=[]
 print(f'FILE {i} {f["path"]} SHA256 {f["sha256"]} ALL {f["lines"]} ORIGINAL LINES; FULL ROOT',json.dumps({k:v for k,v in d.items()if k!='cases'},ensure_ascii=True))
 print('FULL BASELINE PAYLOAD',json.dumps(base,ensure_ascii=True,separators=(',',':')))
 for c in cases:
  meta={k:v for k,v in c.items()if k!='payload'};ops=delta(base,c['payload']);payload=apply(base,ops);assert payload==c['payload'];rebuilt['cases'].append(dict(meta,payload=payload))
  print('CASE',json.dumps(meta,ensure_ascii=True,separators=(',',':')),'COMPLETE DELTA',json.dumps(ops,ensure_ascii=True,separators=(',',':')))
 suffix=raw[len(raw.rstrip(b'\r\n')):];out=json.dumps(rebuilt,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()+suffix
 assert out==raw,('raw reconstruction mismatch',i)
 ledger[f['path']]={'sha256':f['sha256'],'emitted_ranges':[[1,f['lines']]],'semantic_credit':False,'method':'full_first_payload_plus_all_semantic_case_differences','reconstruction_sha256':hashlib.sha256(out).hexdigest(),'case_count':len(cases)}
 print('EXACT BYTE RECONSTRUCTION CONFIRMED',len(raw),'bytes')
 lp.write_text(json.dumps(ledger,indent=2)+'\n')
