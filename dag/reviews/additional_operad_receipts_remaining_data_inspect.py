from pathlib import Path
import collections,gzip,hashlib,json,re
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files'];notes=json.loads(Path(str(P)+'_notes.json').read_text())['assessments']
by_path={r['path']:r for r in rows};cache={};outputs=[]
def variants(path):
 if path not in cache:
  raw=(R/path).read_bytes();lf=raw.replace(b'\r\n',b'\n');cache[path]={k:hashlib.sha256(v).hexdigest() for k,v in [('raw',raw),('LF',lf),('CRLF',lf.replace(b'\n',b'\r\n'))]}
 return cache[path]
def resolve(ref,parent):
 if not isinstance(ref,str) or '..' in Path(ref).parts or re.match(r'^[A-Za-z]:',ref) or ref.startswith(('/', '\\')):return None
 ref=ref.replace('\\','/').removeprefix('./')
 candidates=[(ref,'exact scoped path'),(ref.replace('workflows_agents_skills/receipts/','operads/receipts/'),'historical receipt-prefix locator only'),((Path(parent).parent/ref).as_posix(),'receipt-relative scoped path')]
 for marker in ('/baseline_bytes/','/observed_red_inputs/','/refused_manifest_inputs/','/predecessor_bytes/'):
  if marker in parent:
   prefix=parent.split(marker)[0]+marker
   candidates += [(prefix+ref,'capture-relative locator'),(prefix+ref+'.snapshot','capture-relative snapshot locator')]
 for c,method in candidates:
  if c in by_path:return c,method
 return None
def inspect(row):
 raw=(R/row['path']).read_bytes();duplicates=[];nonfinite=[]
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:duplicates.append({'key':k,'first_value':out[k],'later_value':v,'values_equal':out[k]==v})
   out[k]=v
  return out
 def constant(v):nonfinite.append(v);return v
 try:value=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
 except Exception as e:return {'index':row['index'],'path':row['path'],'parse_error':type(e).__name__+':'+str(e)}
 record={'index':row['index'],'path':row['path'],'sha256':row['sha256'],'bytes':len(raw),'duplicate_decoded_keys':duplicates,'nonfinite_tokens':nonfinite,'top_type':type(value).__name__,'top_keys':list(value) if isinstance(value,dict) else None,'top_length':len(value) if isinstance(value,(list,dict)) else None,'arrays':[],'status_fields':[],'narrative_fields':[],'command_fields':[],'pins':[],'before_after':[],'node_counts':collections.Counter()}
 def pin(ref,pin,loc):
  if isinstance(pin,dict):expected=pin.get('sha256',pin.get('digest'));size=pin.get('size_bytes',pin.get('bytes',pin.get('byte_length')))
  else:expected=pin;size=None
  if not isinstance(expected,str) or not re.fullmatch(r'(?:sha256:)?[a-f0-9]{64}',expected):return
  bound=resolve(ref,row['path']);item={'location':loc,'declared_path':ref,'expected_sha256':expected,'expected_bytes':size}
  if bound:
   actual,method=bound;v=variants(actual);item.update(current_path=actual,locator_method=method,current_sha256=v['raw'],hash_matches=[k for k,h in v.items() if h==expected.removeprefix('sha256:')],size_matches=size==by_path[actual]['bytes'] if type(size)is int else None)
  else:item['resolution']='outside scoped population or unresolved; not accessed'
  record['pins'].append(item)
 def walk(v,loc='$',key=''):
  record['node_counts'][type(v).__name__]+=1
  if isinstance(v,dict):
   for a,b in [('source_pins_before','source_pins_after'),('selected_source_pins_before','selected_source_pins_after'),('inputs_before','inputs_after'),('source_sha256_before','source_sha256_after'),('source_before','source_after'),('source_test_and_selected_dependency_pins_before','source_test_and_selected_dependency_pins_after')]:
    if a in v and b in v:record['before_after'].append({'location':loc,'fields':[a,b],'equal':v[a]==v[b],'before_count':len(v[a]),'after_count':len(v[b])})
   if 'path' in v:pin(v['path'],v,loc)
   for pathkey,hashkey in [('snapshot_path','base_sha256'),('before_path','before_sha256'),('path','after_sha256'),('source_path','source_sha256'),('test_path','test_sha256'),('test_snapshot_path','test_sha256')]:
    if pathkey in v and hashkey in v:pin(v[pathkey],v[hashkey],loc+'/'+pathkey)
   for k,item in v.items():
    if '/' in k or k.endswith(('.py','.json','.md','.snapshot','.log')):pin(k,item,loc+'/'+k)
    walk(item,loc+'/'+k,k)
  elif isinstance(v,list):
   record['arrays'].append({'location':loc,'length':len(v),'element_types':dict(collections.Counter(type(x).__name__ for x in v))})
   if re.search(r'command|argv',key,re.I):record['command_fields'].append({'location':loc,'value':v})
   for i,item in enumerate(v):walk(item,loc+'/'+str(i),key)
  elif isinstance(v,(str,bool,int,float)):
   if re.search(r'^(?:status|result|verdict|outcome|exit_code|returncode|authority_effect|can_authorize|runtime_activation|admission|passed|failed|tests|files|rows|count|epic_count|source_snapshot_count|certifies_.*)$',key,re.I):record['status_fields'].append({'location':loc,'value':v})
   if isinstance(v,str) and re.search(r'claim|scope|limit|nonclaim|residual|conclusion|finding|rationale|note|description|review|summary|reason|error|failure|purpose|observation|interpretation|caveat',key,re.I) and not re.fullmatch(r'(?:sha256:)?[a-f0-9]{40,64}',v):record['narrative_fields'].append({'location':loc,'value':v})
 walk(value);record['node_counts']=dict(record['node_counts']);return record
for row in rows:
 if str(row['index']) in notes:continue
 if '.json' in row['path']:outputs.append(inspect(row))
Path(str(P)+'_data_inspection.json').write_text(json.dumps({'method':'Whole JSON values parsed with duplicate and nonfinite diagnostics; semantic displays/selective fields are bounded reading, not complete original text. Scoped pins only; legacy prefix maps locators, not provenance. No original archive assumed.','files':outputs},indent=2)+'\n',encoding='utf8')
for r in outputs:
 print(r['index'],r.get('parse_error') or (' '.join(r['top_keys'] or [])[:220]+' | '+str(r.get('top_length'))+' fields/rows; '+str(len(r['narrative_fields']))+' prose; '+str(len(r['pins']))+' pins'))
print('TOTAL',len(outputs))
