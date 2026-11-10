"""Read only pinned original sources; write only this review's display ledger."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
P=R/'dag/reviews/additional_ops_governance_domain_remaining'
raw=Path(str(P)+'_scope.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='c68c6e94776473c2a759da43724b5a6c74fc33dfc07927e1fc6ece096b535ea9'
scope=json.loads(raw)['files']; lp=Path(str(P)+'_read_ledger.json')
ledger=json.loads(lp.read_bytes()) if lp.exists() else []
for arg in sys.argv[1:]:
 parts=arg.split(':'); idx=int(parts[0]); row=scope[idx]
 b=(R/row['path']).read_bytes();assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 lines=b.decode('utf8').splitlines(); a=int(parts[1]) if len(parts)>1 else 1;z=int(parts[2]) if len(parts)>2 else len(lines)
 assert 1<=a<=z<=len(lines)
 print(f"FILE {idx} {row['path']} SHA {row['sha256']} LINES {a}..{z}/{len(lines)}")
 for n in range(a,z+1):print(f'{n}: {lines[n-1]}')
 ledger.append({'index':idx,'path':row['path'],'sha256':row['sha256'],'displayed_lines':[a,z],'total_lines':len(lines),'status':'display only; full reading requires untruncated output and substantive assessment'})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
