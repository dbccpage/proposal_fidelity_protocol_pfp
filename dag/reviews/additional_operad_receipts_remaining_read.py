from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files'];lp=Path(str(P)+'_read_ledger.json')
ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
 span=None
 if '@' in arg:
  arg,segment=arg.split('@');span=tuple(map(int,segment.split(':')))
 if arg=='list':
  for r in rows:print(r['index'],r['bytes'],r['lines'],r['path'])
  continue
 if '-' in arg:a,z=map(int,arg.split('-'));ids=range(a,z+1)
 else:ids=[int(arg)]
 for i in ids:
  r=rows[i];b=(R/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];lines=b.decode().splitlines()
  print('\nFILE',i,r['path'],'SHA',r['sha256'],'LINES',len(lines))
  a,z=span or (1,len(lines))
  for n,l in enumerate(lines[a-1:z],a):print(str(n)+': '+l)
  ledger.append(dict(index=i,path=r['path'],sha256=r['sha256'],displayed_lines=[[a,z]]))
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
