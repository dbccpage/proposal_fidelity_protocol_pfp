import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
prep=json.loads((H/(P+'_preparation.json')).read_text()); rows=prep['files']
name=sys.argv[1]; row=next(x for x in rows if x['relative']==name or x['path']==name)
raw=(R/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
lines=raw.decode('utf-8').splitlines();a=int(sys.argv[2]) if len(sys.argv)>2 else 1;b=int(sys.argv[3]) if len(sys.argv)>3 else len(lines)
assert (not lines and a==1 and b==0) or 1<=a<=b<=len(lines)
print('SOURCE',row['relative'],'SHA',row['sha256'],'RANGE',a,b,'OF',len(lines))
for i in range(a-1,b):print(str(i+1)+': '+lines[i])
p=H/(P+'_read_ledger.json');ledger=json.loads(p.read_text()) if p.exists() else []
ledger.append({'path':row['path'],'sha256':row['sha256'],'source_lines':len(lines),'reviewed_lines':[[a,b]] if lines else [],'output_truncated':False})
p.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
