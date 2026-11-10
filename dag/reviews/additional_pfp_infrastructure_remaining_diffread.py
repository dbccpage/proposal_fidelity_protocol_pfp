"""Lossless template plus complete difference emission, never semantic credit by itself."""
import difflib,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';rows=json.loads((H/(P+'_preparation.json')).read_text())['files'];lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text());base=int(sys.argv[1]);b=rows[base];raw=(R/b['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==b['sha256'];a=raw.decode('utf-8-sig').splitlines(keepends=True)
assert ledger[b['path']]['emitted_ranges']==[[1,b['lines']]],'fully emitted template required'
for index in map(int,sys.argv[2].split(',')):
 f=rows[index];raw=(R/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256'];z=raw.decode('utf-8-sig').splitlines(keepends=True);rebuilt=[];op=[]
 print(f'FILE {index} {f["path"]} SHA256 {f["sha256"]} LINES {len(z)} BASE {base} {b["sha256"]}')
 for kind,i,j,k,l in difflib.SequenceMatcher(None,a,z,autojunk=False).get_opcodes():
  op.append([kind,i+1,j,k+1,l]);rebuilt.extend(a[i:j]if kind=='equal'else z[k:l]);print(f'{kind} BASE {i+1}-{j} TARGET {k+1}-{l}')
  if kind!='equal':
   for m in range(k,l):print(f'{m+1}: {z[m].rstrip()}')
 assert ''.join(rebuilt).encode('utf-8')==raw,'encoding/line terminator reconstruction differs'
 ledger[f['path']]={'emitted_ranges':[[1,f['lines']]],'semantic_credit':False,'method':'full_known_template_plus_all_differences','base_path':b['path'],'base_sha256':b['sha256'],'reconstruction_sha256':hashlib.sha256(''.join(rebuilt).encode()).hexdigest(),'opcodes':op}
lp.write_text(json.dumps(ledger,indent=2)+'\n')
