"""Exhaustive public receipt parsing/custody checks; no owner imports or execution."""
import base64,collections,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
prep=json.loads((H/(P+'_preparation.json')).read_text());rows=prep['files']
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
digests=collections.defaultdict(list);parsed={};result=[]
for row in rows:
 raw=(R/row['path']).read_bytes()
 for method,b in [('raw',raw),('LF',raw.replace(b'\r\n',b'\n'))]:digests[sha(b)].append({'path':row['path'],'method':method})
for row in rows:
 p=row['path'];raw=(R/p).read_bytes();suffix=Path(p).suffix
 if suffix in {'.py','.rs','.md','.txt'}:continue
 item={'path':p,'sha256':row['sha256'],'bytes':len(raw),'full_source_read':False}
 if suffix=='.exe':
  item.update({'disposition':'opaque_executable_custody_only','PE_MZ_magic':raw[:2]==b'MZ','executed':False});result.append(item);continue
 if not raw:
  item.update({'disposition':'empty_retained_stream','empty':True});result.append(item);continue
 try:text=raw.decode('utf-8')
 except UnicodeDecodeError:item['disposition']='opaque_binary_custody_only';result.append(item);continue
 duplicates=[]
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:duplicates.append({'key':k,'equal_values':d[k]==v,'first':d[k],'last':v})
   d[k]=v
  return d
 try:
  v=[json.loads(l,object_pairs_hook=pairs) for l in text.splitlines() if l.strip()] if suffix=='.jsonl' else json.loads(text,object_pairs_hook=pairs)
 except Exception as e:
  item.update({'disposition':'text_stream_requires_body_review','parse_error':str(e),'lines':len(text.splitlines())});result.append(item);continue
 parsed[p]=v;item.update({'disposition':'complete_parse_pending_contextual_assessment','duplicates':duplicates,'root_type':type(v).__name__,'root_keys':list(v) if isinstance(v,dict) else None,'records':len(v) if isinstance(v,list) else None})
 if suffix=='.oeos-envelope':
  cipher=base64.b64decode(v['ciphertext_base64'],validate=True)
  claimed=v['plaintext_sha256'].removeprefix('sha256:')
  item.update({'disposition':'opaque_encrypted_payload_metadata_only','metadata':{k:x for k,x in v.items() if k!='ciphertext_base64'},'decoded_ciphertext_bytes':len(cipher),'filename_matches_plaintext_claim':Path(p).parent.name+Path(p).stem==claimed,'plaintext_available_or_authenticated':False,'decryption_attempted':False})
  result.append(item);continue
 self_checks=[]
 if isinstance(v,dict):
  for k in ['receipt_sha256','sha256']:
   if isinstance(v.get(k),str):
    q={a:b for a,b in v.items() if a!=k};b=enc(q)
    self_checks.append({'field':k,'expected':v[k],'canonical_without_field':sha(b),'matches_canonical':sha(b)==v[k].removeprefix('sha256:'),'matches_canonical_LF':sha(b+b'\n')==v[k].removeprefix('sha256:')})
  item['self_hash_checks']=self_checks
  item['top_scalars']={k:x for k,x in v.items() if isinstance(x,(bool,int,float)) or x is None or isinstance(x,str) and len(x)<500 and not k.endswith('sha256')}
  item['result_summary']={k:v[k] for k in ('result','families','checked_observations','native_controls','results','controls','scope','verification_scope','unperformed_obligations') if k in v and len(json.dumps(v[k]))<18000}
 value_counters=collections.defaultdict(collections.Counter);hash_bindings=[];before_after=[]
 def visit(x,loc=''):
  if isinstance(x,dict):
   for k,y in x.items():
    here=loc+'/'+k
    if k in {'status','status_class','grade','family','family_id','action','kind','outcome','error','success','accepted','admitted','model_calls','provider_calls','all_original_obligations_completed'} and isinstance(y,(str,int,bool,type(None))):value_counters[k][str(y)]+=1
    if isinstance(y,str) and re.fullmatch(r'(?:sha256:)?[0-9a-f]{64}',y):
     h=y.removeprefix('sha256:');matches=digests.get(h,[])
     if matches:hash_bindings.append({'location':here,'hash':h,'scoped_matches':matches})
    if k.endswith('_before') and k[:-7]+'_after' in x and isinstance(y,(dict,list)):
     other=x[k[:-7]+'_after'];before_after.append({'location':here,'equal':y==other,'before_count':len(y) if isinstance(y,(dict,list)) else None,'after_count':len(other) if isinstance(other,(dict,list)) else None})
    visit(y,here)
  elif isinstance(x,list):
   for i,y in enumerate(x):visit(y,loc+'/'+str(i))
 visit(v)
 item['value_counts']={k:dict(c) for k,c in value_counters.items()};item['scoped_hash_bindings']=hash_bindings;item['before_after_checks']=before_after
 if isinstance(v,list):item['record_keys']=dict(collections.Counter('|'.join(sorted(x)) if isinstance(x,dict) else type(x).__name__ for x in v))
 result.append(item)
(H/(P+'_data.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
summary={'files':len(result),'dispositions':dict(collections.Counter(x['disposition'] for x in result)),'duplicate_json_keys':sum(len(x.get('duplicates',[])) for x in result),'self_checks':sum(len(x.get('self_hash_checks',[])) for x in result),'self_mismatches':[{'path':x['path'],'checks':[c for c in x.get('self_hash_checks',[]) if not(c['matches_canonical'] or c['matches_canonical_LF'])]} for x in result if any(not(c['matches_canonical'] or c['matches_canonical_LF']) for c in x.get('self_hash_checks',[]))],'before_after_differences':[{'path':x['path'],'checks':[c for c in x.get('before_after_checks',[]) if not c['equal']]} for x in result if any(not c['equal'] for c in x.get('before_after_checks',[]))]}
(H/(P+'_data_summary.json')).write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in {'self_mismatches','before_after_differences'}},indent=2))
print('self_mismatch_paths',[x['path'].split('/docs/')[1] for x in summary['self_mismatches']])
print('before_after_difference_paths',[x['path'].split('/docs/')[1] for x in summary['before_after_differences']])
