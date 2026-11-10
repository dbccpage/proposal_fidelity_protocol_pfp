"""Lossless page emission; body_emitted is not automatic semantic credit."""
import hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent
R=H.parents[1]
P='additional_wiki_tests'
ledger=json.loads((H/(P+'_read_ledger.json')).read_text())
for i in range(int(sys.argv[1]),int(sys.argv[2])):
    row=ledger[i]
    raw=(R/row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    print('\nFILE',i,row['path'],row['sha256'])
    for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
        print(str(n)+': '+line)
    row['body_emitted']=True
(H/(P+'_read_ledger.json')).write_text(json.dumps(ledger,indent=2)+'\n')
