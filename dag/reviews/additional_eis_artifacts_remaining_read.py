from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_eis_artifacts_remaining'
S=json.loads(Path(str(P)+'_scope.json').read_text(encoding='utf8'));rows=S['files']
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(Path(str(P)+'_scope.json').read_bytes())=='57383045b5b17029d822a586201987b6ada589d0e8a82138efdf1d0fd44ffa60'
ledgerp=Path(str(P)+'_read_ledger.json');ledger=json.loads(ledgerp.read_text()) if ledgerp.exists() else []
for arg in sys.argv[1:]:
 parts=arg.split(':');i=int(parts[0]);r=rows[i];raw=(R/r['path']).read_bytes();assert sha(raw)==r['sha256'];lines=raw.decode('utf8').splitlines();a=int(parts[1]) if len(parts)>1 else 1;b=int(parts[2]) if len(parts)>2 else len(lines)
 assert 1<=a<=b<=len(lines)
 print(f"\nFILE {i} {r['path']} SHA {r['sha256']} LINES {a}-{b}/{len(lines)}")
 for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
 ledger.append({'path':r['path'],'sha256':r['sha256'],'displayed_lines':[a,b],'full_line_count':len(lines),'method':'numbered raw source display; assessment/truncation must be checked separately'})
ledgerp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
