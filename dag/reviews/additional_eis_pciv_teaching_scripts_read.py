"""Hash-bound, unabridged reading of the31 assigned teaching bodies."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_eis_pciv_teaching_scripts'
rows=json.loads(Path(str(P)+'_scope.json').read_text())['files'];p=Path(str(P)+'_read_ledger.json');ledger=json.loads(p.read_text()) if p.exists() else []
for arg in sys.argv[1:]:
    i=int(arg);r=rows[i];b=(ROOT/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];ls=b.decode().splitlines()
    print('\nFILE',i,r['path'],'SHA',r['sha256'],'LINES',len(ls))
    for n,line in enumerate(ls,1):print(str(n)+': '+line)
    ledger.append({'path':r['path'],'sha256':r['sha256'],'reviewed_lines':[[1,len(ls)]],'full_source_read':True})
p.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
