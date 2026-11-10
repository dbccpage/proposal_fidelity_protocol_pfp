"""Frozen custody and structural preparation only; never grants semantic review credit."""
import collections,gzip,hashlib,json,pathlib,struct
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining'
scope=json.loads((H/(P+'_scope.json')).read_text());rows=[]
for i,entry in enumerate(scope['files']):
 p=entry['path'];raw=(R/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256'];assert len(raw)==entry['bytes']
 r={**entry,'index':i,'full_source_read':False,'emitted_ranges':[],'structural_inspection_only':True}
 payload=gzip.decompress(raw)if p.endswith('.gz')else raw
 r['decoded_bytes']=len(payload)
 try:text=payload.decode('utf-8');r['lines']=len(text.splitlines());r['utf8']=True
 except UnicodeError:r['utf8']=False;rows.append(r);continue
 if p.endswith(('.json','.jsonl','.json.gz','.jsonl.gz')):
  duplicates=[];nonfinite=[]
  def pairs(items):
   d={}
   for k,v in items:
    if k in d:duplicates.append({'key':k,'values_equal':d[k]==v})
    d[k]=v
   return d
  def constant(s):nonfinite.append(s);return {'nonfinite_token':s}
  try:
   objects=[json.loads(line,object_pairs_hook=pairs,parse_constant=constant)for line in text.splitlines()if line.strip()]if '.jsonl'in p else[json.loads(text,object_pairs_hook=pairs,parse_constant=constant)]
   r['records']=len(objects);r['root_types']=dict(collections.Counter(type(x).__name__ for x in objects));r['root_keys']=dict(collections.Counter(k for x in objects if isinstance(x,dict)for k in x))
   r['root_list_lengths']=[len(x)for x in objects if isinstance(x,list)];r['duplicate_keys']=duplicates;r['nonfinite_tokens']=nonfinite;r['parse_error']=None
  except Exception as e:r['parse_error']=type(e).__name__+': '+str(e);r['duplicate_keys']=duplicates;r['nonfinite_tokens']=nonfinite
 rows.append(r)
out={'source_commit':scope['source_commit'],'files':rows,'summary':{'files':len(rows),'bytes':sum(x['bytes']for x in rows),'decoded_bytes':sum(x['decoded_bytes']for x in rows),'lines':sum(x.get('lines',0)for x in rows)},'limits':'Hashes, decoding and parsing only; not mathematical or source semantic review.'}
(H/(P+'_preparation.json')).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['summary']))
print('parse problems',[(x['path'],x.get('parse_error'),len(x.get('duplicate_keys',[])),x.get('nonfinite_tokens'))for x in rows if x.get('parse_error')or x.get('duplicate_keys')or x.get('nonfinite_tokens')])
