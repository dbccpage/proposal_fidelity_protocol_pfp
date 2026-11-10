"""Print complete source-line deltas against already fully read bases."""
import difflib,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_workflow_library_remaining'
rows=json.loads(Path(str(P)+'_preparation.json').read_text())['files']
lp=Path(str(P)+'_delta_ledger.json')
ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
    a,b=map(int,arg.split(':'));x,y=rows[a],rows[b]
    xb=(ROOT/x['path']).read_bytes();yb=(ROOT/y['path']).read_bytes()
    assert hashlib.sha256(xb).hexdigest()==x['sha256'] and hashlib.sha256(yb).hexdigest()==y['sha256']
    xs=xb.decode().splitlines();ys=yb.decode().splitlines()
    ops=difflib.SequenceMatcher(None,xs,ys,autojunk=False).get_opcodes()
    print('\nDELTA',a,'TO',b,y['path'],'SHA',y['sha256'],'BYTES_EQUAL',xb==yb)
    changes=[]
    for tag,i,j,k,l in ops:
        if tag=='equal':continue
        print(tag,'base',i+1,j,'target',k+1,l)
        for z in range(i,j):print('-',str(z+1)+':',xs[z])
        for z in range(k,l):print('+',str(z+1)+':',ys[z])
        changes.append({'kind':tag,'base_lines':[i+1,j],'target_lines':[k+1,l]})
    ledger.append({'path':y['path'],'sha256':y['sha256'],'base_path':x['path'],'base_sha256':x['sha256'],'byte_equal':xb==yb,'complete_line_delta_emitted':True,'changes':changes,'target_total_lines':len(ys)})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
