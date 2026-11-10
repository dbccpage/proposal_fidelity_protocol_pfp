"""Display pinned full text/ranges. Display alone is not semantic assessment."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_paper_publication_remaining'
S=json.loads(Path(str(P)+'_scope.json').read_bytes())['files']
lp=Path(str(P)+'_read_ledger.json');ledger=json.loads(lp.read_bytes()) if lp.exists() else []
for arg in sys.argv[1:]:
 parts=arg.split(':');i=int(parts[0]);r=S[i];b=(R/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];lines=b.decode('utf8').splitlines();a=int(parts[1]) if len(parts)>1 else 1;z=int(parts[2]) if len(parts)>2 else len(lines);assert 1<=a<=z<=len(lines)
 print(f"FILE {i} {r['path']} SHA {r['sha256']} LINES {a}..{z}/{len(lines)}")
 for n in range(a,z+1):print(f'{n}: {lines[n-1]}')
 ledger.append({'index':i,'path':r['path'],'sha256':r['sha256'],'displayed_lines':[a,z],'source_lines':len(lines),'assessment_status':'displayed; full semantic credit requires explicit assessment'})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
