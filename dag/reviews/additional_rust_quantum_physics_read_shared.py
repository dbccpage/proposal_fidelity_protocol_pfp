"""Lossless full differences against a previously fully read shared-count template.
Matched segments are explicit source references, not automatic semantic credit.
Only generated symbol suffixes are normalized; all other full differences emitted.
"""
import difflib,hashlib,json,pathlib,re,sys
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics'
s=json.loads((H/(P+'_scope.json')).read_text());rows={x['path']:x for x in s['files']}
canonical=sys.argv[2] if len(sys.argv)>2 else 'code/rust/core_quantum_physics/src/anyon.rs';target=sys.argv[1]
notes=json.loads((H/(P+'_notes.json')).read_text())
assert canonical in notes, 'Shared canonical source must already have a substantive full-read assessment'
def fetch(p):
 raw=(R/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==rows[p]['sha256'];return raw,raw.decode().splitlines(keepends=True)
a_raw,a=fetch(canonical);b_raw,b=fetch(target)
def norm(t):return re.sub(r'(?<=BoundaryRecord)[0-9a-f]{8}|(?<=BoundaryError)[0-9a-f]{8}|(?<=l4_boundary_tests_)[0-9a-f]{8}','TEMPLATE',t)
aa=list(map(norm,a));bb=list(map(norm,b));chunks=[];reconstructed=[]
print('SOURCE',target,'SHA',rows[target]['sha256'],'LINES',len(b),'CANONICAL_FULL_READ',canonical)
for op,i,j,k,l in difflib.SequenceMatcher(a=aa,b=bb,autojunk=False).get_opcodes():
 if op=='equal'and l-k>=12:
  substitutions=[{'target_line':k+t+1,'canonical_line':i+t+1,'canonical':a[i+t].rstrip(),'target':b[k+t].rstrip()}for t in range(l-k)if a[i+t]!=b[k+t]]
  renamings=sorted(set((x,y)for t in range(l-k)for x,y in zip(re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)[0-9a-f]{8}',a[i+t]),re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)[0-9a-f]{8}',b[k+t]))if x!=y))
  print('SHARED_FULL_SEGMENT target',k+1,l,'canonical',i+1,j,'ALL_GENERATED_SYMBOL_RENAMINGS',json.dumps(renamings),'affected target lines',[x['target_line']for x in substitutions])
  chunks.append({'kind':'shared_full_segment','target_lines':[k+1,l],'canonical_lines':[i+1,j],'substitutions':substitutions,'target_text':b[k:l]})
 else:
  for q in range(k,l):print(str(q+1)+': '+b[q].rstrip('\r\n'))
  if l>k:chunks.append({'kind':'full_source_text','target_lines':[k+1,l],'target_text':b[k:l]})
 reconstructed+=b[k:l]
rebuilt=''.join(reconstructed).encode();assert rebuilt==b_raw
p=H/(P+'_template_receipts.json');receipts=json.loads(p.read_text())if p.exists()else[]
receipts.append({'path':target,'sha256':rows[target]['sha256'],'canonical_path':canonical,'canonical_sha256':rows[canonical]['sha256'],'method':'Complete semantic body/differences plus exact shared count-boundary segments; only cosmetic generated suffixes normalized. Requires manual per-file assessment.','reconstruction_sha256':hashlib.sha256(rebuilt).hexdigest(),'chunks':chunks})
p.write_text(json.dumps(receipts,indent=2)+'\n')
