"""Pin and display complete assigned pattern bodies; never imports their owners."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_operad_patterns_remaining'
scope=json.loads(Path(str(P)+'_scope.json').read_text())
inventory=Path(str(P)+'_inventory.json')
if not inventory.exists():
    rows=[]
    for i,r in enumerate(scope['files']):
        b=(ROOT/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
        rows.append(dict(r,index=i,lines=len(b.decode().splitlines())))
    assert len(rows)==198 and sum(x['size_bytes'] for x in rows)==327419 and sum(x['lines'] for x in rows)==7066
    inventory.write_text(json.dumps({'scope_sha256':hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest(),'files':rows},indent=2)+'\n',encoding='utf-8')
rows=json.loads(inventory.read_text())['files']
lp=Path(str(P)+'_read_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
    if arg=='list':
        for r in rows:print(r['index'],r['lines'],r['size_bytes'],r['path'])
        continue
    if '-' in arg:
        a,z=map(int,arg.split('-'));indices=range(a,z+1)
    else:indices=[int(arg)]
    for i in indices:
        r=rows[i];b=(ROOT/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
        print('\nFILE',i,r['path'],'SHA',r['sha256'],'LINES',r['lines'])
        for n,line in enumerate(b.decode().splitlines(),1):print(f'{n}: {line}')
        ledger.append({'path':r['path'],'sha256':r['sha256'],'reviewed_lines':[[1,r['lines']]],'display_index':i})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
