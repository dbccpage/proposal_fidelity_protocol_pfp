"""Display frozen source ranges; custody only, no Rust/original execution."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_rust_adversary_remaining'
raw=Path(str(P)+'_scope.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d0547aab64c96d5e8cb280c02ad499283cff257d6931ca886f113cb4235ccd27'
scope=json.loads(raw)['files'];lp=Path(str(P)+'_read_ledger.json');ledger=json.loads(lp.read_bytes()) if lp.exists() else []
if not sys.argv[1:]:
 rows=[]
 for i,row in enumerate(scope):
  b=(R/row['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['size_bytes']
  rows.append(dict(row,index=i,lines=len(b.decode('utf8').splitlines())))
 Path(str(P)+'_inventory.json').write_text(json.dumps({'scope_sha256':hashlib.sha256(raw).hexdigest(),'files':rows},indent=2)+'\n',encoding='utf8')
 for r in rows:print(r['index'],r['lines'],r['size_bytes'],r['path'])
else:
 for arg in sys.argv[1:]:
  parts=arg.split(':');i=int(parts[0]);row=scope[i];b=(R/row['path']).read_bytes()
  assert hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['size_bytes']
  lines=b.decode('utf8').splitlines();a=int(parts[1]) if len(parts)>1 else 1;z=int(parts[2]) if len(parts)>2 else len(lines)
  assert 1<=a<=z<=len(lines)
  print(f"FILE {i} {row['path']} SHA {row['sha256']} LINES {a}..{z}/{len(lines)}")
  for n in range(a,z+1):print(f'{n}: {lines[n-1]}')
  ledger.append({'index':i,'path':row['path'],'sha256':row['sha256'],'displayed_lines':[a,z],'total_lines':len(lines),'status':'display only; no semantic reading credit without assessment'})
 lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
