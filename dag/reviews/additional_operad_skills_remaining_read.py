"""Emit exact pinned full bodies/ranges; credit requires separate manual notes."""
import hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';rows=json.loads((H/(P+'_preparation.json')).read_text())['files'];lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())if lp.exists()else{}
for i in map(int,sys.argv[1].split(',')):
 f=rows[i];raw=(R/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256'];lines=raw.decode('utf-8-sig').splitlines();a=int(sys.argv[2])if len(sys.argv)>2 else 1;b=min(len(lines),int(sys.argv[3]))if len(sys.argv)>3 else len(lines);print(f'FILE {i} {f["path"]} SHA256 {f["sha256"]} LINES {a}-{b}/{len(lines)}')
 for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
 e=ledger.setdefault(f['path'],{'sha256':f['sha256'],'emitted_ranges':[],'semantic_credit':False});e['emitted_ranges'].append([a,b]);lp.write_text(json.dumps(ledger,indent=2)+'\n')
