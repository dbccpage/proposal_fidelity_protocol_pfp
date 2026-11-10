"""Lossless shared-template transport; prints every other line and exact substitutions.

Only two already fully read finite_set.rs spans are eligible. Exact byte matching
after explicit hexadecimal symbol renaming is required. No semantic credit is
granted by matching; per-file caller/context assessment remains manual.
"""
import hashlib,json,pathlib,re,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_quantum_probability_remaining';s=json.loads((H/(P+'_scope.json')).read_text());lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text());base=s['files'][3];br=(R/base['path']).read_bytes();assert hashlib.sha256(br).hexdigest()==base['sha256'];bl=br.splitlines(keepends=True)
templates=[(96,180),(247,272)]
for index in map(int,sys.argv[1].split(',')):
 f=s['files'][index];raw=(R/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256'];lines=raw.splitlines(keepends=True);masked=set();trans=[]
 for a,b in templates:
  original=b''.join(bl[a-1:b]);n=b-a+1
  for start in range(len(lines)-n+1):
   chunk=b''.join(lines[start:start+n]);matches=set(re.findall(rb'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)([0-9a-f]{8})',chunk))
   if len(matches)!=1:continue
   suffix=next(iter(matches));reconstructed=original.replace(b'599a3226',suffix)
   if reconstructed!=chunk:continue
   assert not masked.intersection(range(start+1,start+n+1));masked.update(range(start+1,start+n+1));trans.append({'target_lines':[start+1,start+n],'template_path':base['path'],'template_sha256':base['sha256'],'template_lines':[a,b],'substitutions':{'599a3226':suffix.decode()},'template_chunk_sha256':hashlib.sha256(original).hexdigest(),'target_chunk_sha256':hashlib.sha256(chunk).hexdigest(),'reconstruction_exact_bytes':True})
 print(f"FILE {index} {f['path']} SHA256 {f['sha256']} LINES 1-{len(lines)}/{len(lines)}")
 for t in trans:print('FULLY-READ TEMPLATE TRANSFER '+json.dumps(t))
 for i,line in enumerate(lines,1):
  if i not in masked:print(f'{i}: '+line.decode('utf-8-sig').rstrip('\r\n'))
 row=ledger.setdefault(f['path'],{'sha256':f['sha256'],'emitted_ranges':[],'semantic_credit':False});row['template_transfers']=trans
 row['emitted_ranges'] += [[i,i]for i in range(1,len(lines)+1)if i not in masked];lp.write_text(json.dumps(ledger,indent=2)+'\n')
