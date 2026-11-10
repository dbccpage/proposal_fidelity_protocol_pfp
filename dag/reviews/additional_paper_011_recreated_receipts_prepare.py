"""Frozen-scope inventory and strict structured-data diagnostics, not semantic credit."""
import collections,hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_paper_011_recreated_receipts'
scope=json.loads((H/(P+'_scope.json')).read_text());files=[];shapes=collections.defaultdict(list)
for original in scope['files']:
 p=R/original['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==original['sha256'];assert len(raw)==original['bytes'];text=raw.decode('utf-8');duplicates=[];constants=[];errors=[]
 def pairs(items):
  result={}
  for k,v in items:
   if k in result:duplicates.append({'key':k,'values_equal':result[k]==v})
   result[k]=v
  return result
 def parse(s):return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda x:constants.append(x)or x)
 objects=[]
 if p.suffix in {'.json','.oeos-envelope'}:
  try:objects=[parse(text)]
  except (ValueError,TypeError)as e:errors.append(str(e))
 elif p.suffix=='.jsonl':
  for i,line in enumerate(text.splitlines(),1):
   try:objects.append(parse(line))
   except (ValueError,TypeError)as e:errors.append({'line':i,'error':str(e)})
 keys=collections.Counter('|'.join(sorted(o))if isinstance(o,dict)else type(o).__name__ for o in objects)
 row={**original,'lines':len(text.splitlines()),'utf8':True,'strict_parse_errors':errors,'duplicate_keys':duplicates,'nonfinite_tokens':constants,'records':len(objects),'root_key_populations':dict(keys),'empty':len(raw)==0,'full_source_read':False}
 files.append(row)
 for shape in keys:shapes[(p.name,shape)].append(original['path'])
out={'source_commit':scope['source_commit'],'files':files,'shape_families':[{'filename':name,'keys':shape.split('|'),'files':paths}for(name,shape),paths in shapes.items()],'summary':{'files':len(files),'bytes':sum(x['bytes']for x in files),'empty':sum(x['empty']for x in files),'strict_parse_error_files':sum(bool(x['strict_parse_errors'])for x in files),'duplicate_key_files':sum(bool(x['duplicate_keys'])for x in files),'nonfinite_token_files':sum(bool(x['nonfinite_tokens'])for x in files),'shape_families':len(shapes)},'limits':'Complete byte custody/UTF8 parsing and root-schema census only. No file is granted substantive review credit by this script.'}
(H/(P+'_preparation.json')).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['summary'],indent=2))
for row in out['shape_families']:print(row['filename'],len(row['files']),row['keys'])
