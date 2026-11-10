"""Frozen-source reading transport. Emission/hash checks do not grant semantic credit."""
import hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_quantum_probability_remaining';s=json.loads((H/(P+'_scope.json')).read_text());lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())if lp.exists()else{}
for i in map(int,sys.argv[1].split(',')):
 f=s['files'][i];raw=(R/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256'];assert len(raw)==f['size_bytes'];lines=raw.decode('utf-8-sig').splitlines();a=int(sys.argv[2])if len(sys.argv)>2 else 1;b=min(int(sys.argv[3]),len(lines))if len(sys.argv)>3 else len(lines);assert 1<=a<=b<=len(lines)
 print(f"FILE {i} {f['path']} SHA256 {f['sha256']} LINES {a}-{b}/{len(lines)}")
 for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
 item=ledger.setdefault(f['path'],{'sha256':f['sha256'],'emitted_ranges':[]});item['emitted_ranges'].append([a,b])
lp.write_text(json.dumps(ledger,indent=2)+'\n')
