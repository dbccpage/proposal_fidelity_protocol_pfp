"""Emit hash-verified full bodies or explicit ranges from the frozen scope."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_workflow_library_remaining'
rows=json.loads(Path(str(P)+'_preparation.json').read_text(encoding='utf-8'))['files']
ledger_path=Path(str(P)+'_read_ledger.json')
ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else []
for arg in sys.argv[1:]:
    parts=arg.split(':');i=int(parts[0]);row=rows[i];p=ROOT/row['path'];b=p.read_bytes()
    assert hashlib.sha256(b).hexdigest()==row['sha256']
    lines=b.decode('utf-8').splitlines();a=int(parts[1]) if len(parts)>1 else 1;e=int(parts[2]) if len(parts)>2 else len(lines)
    if lines:assert 1<=a<=e<=len(lines)
    else: assert a==1 and e==0
    print('\nFILE',i,row['path'],'SHA',row['sha256'],'RANGE',a,e,'TOTAL',len(lines))
    for n in range(a,e+1):print(f'{n}: {lines[n-1]}')
    ledger.append({'path':row['path'],'sha256':row['sha256'],'reviewed_lines':[[a,e]] if lines else [],'empty_file':not lines,'emitted_complete_requested_range':True})
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
