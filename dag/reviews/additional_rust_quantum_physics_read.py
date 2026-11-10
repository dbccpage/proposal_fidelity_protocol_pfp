import hashlib,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics'
scope=json.loads((H/(P+'_scope.json')).read_text());path=sys.argv[1];row=next(x for x in scope['files']if x['path']==path)
raw=(R/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];lines=raw.decode('utf-8').splitlines()
lo=int(sys.argv[2])if len(sys.argv)>2 else 1;hi=int(sys.argv[3])if len(sys.argv)>3 else len(lines)
assert 1<=lo<=hi<=len(lines)
print('FILE',path,'SHA256',row['sha256'],'LINES',len(lines),'READ',lo,hi)
for n in range(lo,hi+1):print(str(n)+': '+lines[n-1])
p=H/(P+'_emissions.json');d=json.loads(p.read_text())if p.exists()else[];d.append({'path':path,'sha256':row['sha256'],'emitted_lines':[lo,hi],'note':'Emission alone does not establish semantic assessment.'});p.write_text(json.dumps(d,indent=2)+'\n')
