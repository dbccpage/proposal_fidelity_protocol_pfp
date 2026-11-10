"""Emit bounded complete source ranges and hash-bound reading metadata; never execute source."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_native';B='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/'
prep=json.loads((H/(P+'_preparation.json')).read_text(encoding='utf-8'));rows={r['path']:r for r in prep['files']}
name=sys.argv[1];p=B+name;row=rows[p];raw=(R/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];lines=raw.decode('utf-8').splitlines()
a=int(sys.argv[2]) if len(sys.argv)>2 else 1;b=int(sys.argv[3]) if len(sys.argv)>3 else len(lines);assert 1<=a<=b<=len(lines)
print('SOURCE',p,'SHA',row['sha256'],'RANGE',a,b,'OF',len(lines));print('\n'.join(f'{i}: {lines[i-1]}' for i in range(a,b+1)))
ledger_path=H/(P+'_read_ledger.json');ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
ledger.append({'path':p,'sha256':row['sha256'],'source_lines':len(lines),'reviewed_lines':[[a,b]],'output_truncated':False})
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
