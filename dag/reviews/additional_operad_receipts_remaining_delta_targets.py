from pathlib import Path
import sys,json,difflib,hashlib
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files']
base=int(sys.argv[1]); b=(R/rows[base]['path']).read_text(encoding='utf8').splitlines()
out=[]
for arg in sys.argv[2:]:
 for i in (range(*[int(x) for x in arg.split(':')]) if ':' in arg else [int(arg)]):
  row=rows[i];raw=(R/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];t=raw.decode('utf8').splitlines()
  ops=difflib.SequenceMatcher(None,b,t,autojunk=False).get_opcodes()
  print(f'\nTARGET {i} {row["path"]} SHA {row["sha256"]} FULL BASE {base} TARGET LINES {len(t)}')
  for tag,a,z,c,d in ops:
   if tag!='equal':
    print(f'{tag} base[{a+1}:{z}] target[{c+1}:{d}]')
    for n,line in enumerate(t[c:d],c+1): print(f'{n}: {line}')
  out.append(dict(base_index=base,target_index=i,base_sha256=rows[base]['sha256'],target_sha256=row['sha256'],opcodes=ops))
p=Path(str(P)+'_target_delta_ledger.json');old=json.loads(p.read_text()) if p.exists() else [];old.extend(out);p.write_text(json.dumps(old,indent=2)+'\n',encoding='utf8')
