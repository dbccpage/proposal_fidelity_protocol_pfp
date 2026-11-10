"""Bounded numbered text emission; manual notes, not emission, grant review level."""
import hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';f=json.loads((H/(P+'_preparation.json')).read_text())['files'];lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())if lp.exists()else{}
for idx in map(int,sys.argv[1].split(',')):
 row=f[idx];assert row['kind']=='text';raw=(R/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];lines=raw.decode('utf8').splitlines();a=int(sys.argv[2])if len(sys.argv)>2 else 1;b=min(int(sys.argv[3]),len(lines))if len(sys.argv)>3 else len(lines)
 print(f"\nFILE {idx} {row['path']} SHA256 {row['sha256']} LINES {a}-{b}/{len(lines)}")
 for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
 q=ledger.setdefault(row['path'],{'path':row['path'],'sha256':row['sha256'],'lines':len(lines),'emitted_ranges':[],'semantic_credit':False});q['emitted_ranges'].append([a,b])
lp.write_text(json.dumps(ledger,indent=2)+'\n')
