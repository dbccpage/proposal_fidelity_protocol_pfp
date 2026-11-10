"""Nonexecuting complete-population checks on frozen public artifacts only."""
import collections,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts';D='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/'
rows=json.loads((H/(P+'_preparation.json')).read_text())['files'];byrel={x['relative']:x for x in rows}
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(r):
 raw=(R/r['path']).read_bytes()
 return [json.loads(l) for l in raw.splitlines() if l.strip()] if r['path'].endswith('.jsonl') else json.loads(raw)
raws={r['relative']:(R/r['path']).read_bytes() for r in rows};values={}
for r in rows:
 if Path(r['path']).suffix in {'.json','.jsonl','.bin'} and r['bytes']:
  try:values[r['relative']]=parse(r)
  except (ValueError,UnicodeDecodeError):pass
results=[]
for rel,v in values.items():
 r=byrel[rel];item={'path':r['path'],'sha256':r['sha256'],'hex_fields':[],'local_artifact_bindings':[],'self_bindings':[]}
 def walk(x,loc=''):
  if isinstance(x,dict):
   for k,y in x.items():
    if k.endswith('_hex') and isinstance(y,str):
     try:
      b=bytes.fromhex(y);prefix=k[:-4];claim_fields=[prefix+'_sha256']+(['sha256'] if k=='bytes_hex' else []);claims=[(s,x[s]) for s in claim_fields if s in x and isinstance(x[s],str)]
      item['hex_fields'].append({'location':loc+'/'+k,'decoded_bytes':len(b),'sha256':sha(b),'declared_checks':[{'field':s,'expected':h,'matches':sha(b)==h.removeprefix('sha256:')} for s,h in claims]})
     except ValueError:item['hex_fields'].append({'location':loc+'/'+k,'invalid_hex':True})
    if k in ('artifacts_sha256','outputs','artifacts') and isinstance(y,dict):
     for name,binding in y.items():
      expected=binding if isinstance(binding,str) else binding.get('sha256') if isinstance(binding,dict) else None
      local=(Path(rel).parent/name).as_posix()
      if local in raws and expected:
       raw=raws[local];item['local_artifact_bindings'].append({'location':loc+'/'+k+'/'+name,'path':D+local,'expected':expected,'raw_matches':sha(raw)==expected.removeprefix('sha256:'),'LF_matches':sha(raw.replace(b'\r\n',b'\n'))==expected.removeprefix('sha256:')})
    walk(y,loc+'/'+k)
  elif isinstance(x,list):
   for i,y in enumerate(x):walk(y,loc+'/'+str(i))
 walk(v)
 if isinstance(v,dict):
  for field in ('self_sha256','receipt_sha256','sha256'):
   if field not in v or not isinstance(v[field],str):continue
   payload={k:x for k,x in v.items() if k!=field};methods={}
   for sort in (False,True):
    for ascii_ in (False,True):
     b=json.dumps(payload,sort_keys=sort,ensure_ascii=ascii_,separators=(',',':'),allow_nan=False).encode();methods[f'sorted={sort};ascii={ascii_}']=sha(b)
   item['self_bindings'].append({'field':field,'expected':v[field],'computed':methods,'matching_methods':[k for k,h in methods.items() if h==v[field]]})
 item['hex_count']=len(item['hex_fields']);item['hex_decoded_bytes']=sum(x.get('decoded_bytes',0) for x in item['hex_fields']);results.append(item)
equalities=[]
for group,versions,names in [('native_dossier_integral',['run_v1','run_v2','run_v3'],['compute_request.json','compute_stdout.bin','replay_request.json','replay_stdout.bin','result.json']),('native_dossier_homology',['run_v2','run_v3','run_v4'],['request.json','result.json','stdout.bin'])]:
 for name in names:
  rels=[group+'/'+v+'/'+name for v in versions];equalities.append({'paths':[D+x for x in rels],'raw_sha256':[sha(raws[x]) for x in rels],'all_raw_equal':len({raws[x] for x in rels})==1,'all_parsed_equal':all(values[x]==values[rels[0]] for x in rels)})
summary={'files_checked':len(results),'hex_fields':sum(x['hex_count'] for x in results),'hex_decoded_bytes':sum(x['hex_decoded_bytes'] for x in results),'bad_hex':[{'path':x['path'],'entry':a} for x in results for a in x['hex_fields'] if a.get('invalid_hex') or any(not q['matches'] for q in a.get('declared_checks',[]))],'local_bindings':sum(len(x['local_artifact_bindings']) for x in results),'local_mismatches':[{'path':x['path'],'entry':a} for x in results for a in x['local_artifact_bindings'] if not a['raw_matches']],'self_unmatched':[{'path':x['path'],'entry':a} for x in results for a in x['self_bindings'] if not a['matching_methods']],'version_equalities':equalities}
(H/(P+'_custody_checks.json')).write_text(json.dumps({'summary':summary,'files':results},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('bad_hex','local_mismatches','self_unmatched','version_equalities')},indent=2))
for key in ['bad_hex','local_mismatches','self_unmatched']:print(key,len(summary[key]))
for x in equalities:print('EQUALITY',x['paths'][0].removeprefix(D),x['all_raw_equal'],x['all_parsed_equal'])
