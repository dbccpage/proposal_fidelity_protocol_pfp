from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/rust_category_delegate_relations'
source=R/'dag/reviews/additional_rust_category_remaining_scope.json'
scope=json.loads(source.read_text());names={'finite_relational.rs','finite_profunctor.rs','finite_section_separation.rs','grothendieck_construction.rs','family_category.rs'}
rows=[]
for r in scope['files']:
 if Path(r['path']).name in names:
  b=(R/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
  rows.append({'index':len(rows),'path':r['path'],'sha256':r['sha256'],'bytes':len(b),'lines':len(b.decode('utf8').splitlines())})
assert len(rows)==5
frozen={'parent_scope':source.relative_to(R).as_posix(),'parent_scope_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'files':rows}
fp=Path(str(P)+'_scope.json')
if fp.exists():assert json.loads(fp.read_text())==frozen
else:fp.write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf8')
lp=Path(str(P)+'_read_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
 if '@' in arg:i,s=arg.split('@');lo,hi=map(int,s.split(':'));i=int(i)
 else:i=int(arg);lo=1;hi=rows[i]['lines']
 r=rows[i];assert 1<=lo<=hi<=r['lines'];lines=(R/r['path']).read_text(encoding='utf8').splitlines()
 print('\nFILE',i,r['path'],'SHA',r['sha256'],'LINES',r['lines'])
 for n in range(lo,hi+1):print(str(n)+': '+lines[n-1])
 ledger.append({'path':r['path'],'sha256':r['sha256'],'displayed_lines':[lo,hi],'reading_credit':'display only; semantic assessment required'})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
