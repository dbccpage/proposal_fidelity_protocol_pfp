"""Emit exact complete source ranges and record hash-bound inspection, never execute sources."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_010_data';B='papers/pfp/010_pfp_holonomy_checks_and_model_pilots/'
scope=json.loads((H/(P+'_scope.json')).read_text(encoding='utf-8'));rows={r['path']:r for r in scope['files']}
name=sys.argv[1];path=B+name;row=rows[path];raw=(R/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
lines=raw.decode('utf-8').splitlines();a=int(sys.argv[2]) if len(sys.argv)>2 else 1;b=int(sys.argv[3]) if len(sys.argv)>3 else len(lines)
assert 1<=a<=b<=len(lines)
print('SOURCE',path,'SHA256',row['sha256'],'RANGE',a,b,'OF',len(lines))
print('\n'.join(f'{i}: {lines[i-1]}' for i in range(a,b+1)))
p=H/(P+'_read_ledger.json');ledger=json.loads(p.read_text()) if p.exists() else []
ledger.append({'path':path,'sha256':row['sha256'],'source_lines':len(lines),'reviewed_lines':[[a,b]],'output_truncated':False})
p.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
