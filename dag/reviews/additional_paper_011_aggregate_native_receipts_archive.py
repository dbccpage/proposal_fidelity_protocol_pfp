"""Compare frozen current scope with original outer ZIP; never extract/execute."""
import collections,difflib,hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts';B='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/';D=B+'docs/'
Z=B+'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip';ZH='8bf43405313439d05383552f1281eaec96442dac7eb733134bcae1394863d6b3';prefix='021_recreated_demos_and_proposal_fidelity_evidence/'
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha((R/Z).read_bytes())==ZH
rows=json.loads((H/(P+'_preparation.json')).read_text())['files'];checks=json.loads((H/(P+'_custody_checks.json')).read_text());output=[]
with zipfile.ZipFile(R/Z) as z:
 names=set(z.namelist())
 for r in rows:
  member=prefix+'docs/'+r['relative'];original_member=member
  if member not in names and '/source_files/symbol_game/' in member:member=member.replace('/source_files/symbol_game/','/source_files/omega_engine_symbol_game/')
  cur=(R/r['path']).read_bytes();item={'path':r['path'],'sha256':r['sha256'],'archive_member':member,'archive_present':member in names,'explicit_name_mapping':None if member==original_member else {'current':original_member,'archive':member}}
  if member not in names:output.append(item);continue
  old=z.read(member);item.update({'archive_sha256':sha(old),'archive_bytes':len(old),'raw_equal':old==cur,'LF_equal':old.replace(b'\r\n',b'\n')==cur.replace(b'\r\n',b'\n')})
  if Path(r['path']).suffix in ('.py','.rs'):
   item['source_delta']=list(difflib.unified_diff(cur.decode().splitlines(),old.decode().splitlines(),fromfile=r['path'],tofile=member,n=2))
  if Path(r['path']).suffix not in ('.json','.jsonl'):output.append(item);continue
  duplicates=[]
  def pairs(xs):
   d={}
   for k,v in xs:
    if k in d:duplicates.append({'key':k,'equal':d[k]==v})
    d[k]=v
   return d
  try:v=[json.loads(l,object_pairs_hook=pairs) for l in old.splitlines() if l.strip()] if r['path'].endswith('.jsonl') else json.loads(old,object_pairs_hook=pairs)
  except ValueError:item['empty_or_non_JSON']=True;output.append(item);continue
  item['archive_duplicate_keys']=duplicates
  if isinstance(v,dict):
   ss=[]
   for field in ('self_sha256','receipt_sha256','sha256'):
    if not isinstance(v.get(field),str):continue
    payload={k:x for k,x in v.items() if k!=field};methods={}
    for sort in (False,True):
     for ascii_ in (False,True):
      b=json.dumps(payload,sort_keys=sort,ensure_ascii=ascii_,separators=(',',':'),allow_nan=False).encode()
      for newline in (False,True):methods[f'sorted={sort};ascii={ascii_};newline={newline}']=sha(b+(b'\n' if newline else b''))
    ss.append({'field':field,'expected':v[field],'matching_methods':[k for k,h in methods.items() if h==v[field]],'computed':methods})
   item['archive_self_checks']=ss
  currentcheck=next((x for x in checks['files'] if x['path']==r['path']),None)
  refs=[]
  if currentcheck:
   for q in currentcheck['local_artifact_bindings']:
    m=prefix+q['path'].removeprefix(B);old_expected=v
    try:
     parts=q['location'].strip('/').split('/')
     while parts:
      if '/'.join(parts) in old_expected:old_expected=old_expected['/'.join(parts)];parts=[]
      else:old_expected=old_expected[parts.pop(0)]
     if isinstance(old_expected,dict):old_expected=old_expected.get('sha256')
    except (TypeError,KeyError):old_expected=None
    refs.append({'current_reference_location':q['location'],'target_member':m,'current_recorded_expected':q['expected'],'archive_recorded_expected':old_expected,'archive_target_sha256':sha(z.read(m)) if m in names else None,'archive_target_matches_current_reference':m in names and sha(z.read(m))==q['expected'].removeprefix('sha256:'),'archive_target_matches_archive_reference':m in names and isinstance(old_expected,str) and sha(z.read(m))==old_expected.removeprefix('sha256:')})
  item['archive_target_reference_checks']=refs
  if r['relative'].endswith('actual_inputs.jsonl'):
   item['archive_embedded_checks']=[{'index':i,'path':x.get('path'),'matches':sha(bytes.fromhex(x['bytes_hex']))==x['sha256']} for i,x in enumerate(v)]
  if '/execution_machinery_' in r['relative'] and r['relative'].endswith('/receipt.json'):
   files=v.get('files',{});files=[{'snapshot':n,**x} for n,x in files.items()] if isinstance(files,dict) else files
   item['archive_capture_bindings']=[{'name':x['snapshot'],'matches':sha(z.read(str(Path(member).parent/x['snapshot']).replace('\\','/')))==x['sha256']} for x in files]
  output.append(item)
summary={'scope_files':len(rows),'archive_present':sum(x['archive_present'] for x in output),'raw_equal':sum(x.get('raw_equal',False) for x in output),'LF_equal':sum(x.get('LF_equal',False) for x in output),'archive_reference_checks':sum(len(x.get('archive_target_reference_checks',[])) for x in output),'archive_reference_matches':sum(q['archive_target_matches_current_reference'] for x in output for q in x.get('archive_target_reference_checks',[])),'archive_self_checks':sum(len(x.get('archive_self_checks',[])) for x in output),'archive_self_no_tested_encoding_matches':[x['path'] for x in output if any(not q['matching_methods'] for q in x.get('archive_self_checks',[]))],'archive_embedded_mismatches':[(x['path'],q['index']) for x in output for q in x.get('archive_embedded_checks',[]) if not q['matches']],'archive_duplicates':[(x['path'],x['archive_duplicate_keys']) for x in output if x.get('archive_duplicate_keys')],'archive_capture_mismatches':[(x['path'],q) for x in output for q in x.get('archive_capture_bindings',[]) if not q['matches']]}
(H/(P+'_archive_checks.json')).write_text(json.dumps({'archive':Z,'archive_sha256':ZH,'summary':summary,'files':output},indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
for x in output:
 if x.get('source_delta'):print('SOURCE_DIFF',len(x['source_delta']),x['path'].removeprefix(D))
