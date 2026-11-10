from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_adversary_remaining';rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files']
lp=Path(str(P)+'_read_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
 if '@' in arg:
  x,span=arg.split('@');a,z=map(int,span.split(':'));targets=[int(x)]
 else:a=1;z=None;targets=range(int(arg.split('-')[0]),int(arg.split('-')[-1])+1)
 for i in targets:
  r=rows[i];b=(R/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];ls=b.decode('utf8').splitlines();end=min(z or len(ls),len(ls))
  print('\nFILE',i,r['path'],'SHA',r['sha256'],'LINES',len(ls))
  for n in range(a,end+1):print(str(n)+': '+ls[n-1])
  ledger.append({'index':i,'path':r['path'],'sha256':r['sha256'],'displayed_lines':[[a,end]],'method':'numbered display; not automatic reading credit'})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
