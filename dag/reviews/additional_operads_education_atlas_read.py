"""Freeze and display assigned teaching sources without changing originals."""
from pathlib import Path
import hashlib,json,sys,zipfile,difflib
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_operads_education_atlas'
scopefile=Path(str(P)+'_scope.json')
if not scopefile.exists():
 parent=ROOT/'dag/reviews/additional_operads_education_remaining_scope.json'
 d=json.loads(parent.read_text()); exclude=set(d['parent_initial_paths']);rows=[]
 for r in d['files']:
  if r['path'] in exclude:continue
  b=(ROOT/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
  rows.append(dict(r,lines=None if r['path'].endswith('.png') else len(b.decode().splitlines())))
 assert len(rows)==52
 v=json.loads((ROOT/'dag/migrations/demo_support_verification.json').read_text())
 path='education/008_oeop/atlas/23_plan_oewas_consolidation_oeeis_and_demo_integration.md'
 supporting=next(r for r in v['retained_source_revisions'] if r['path']==path)
 archive=Path(supporting['original_archive']);b=(ROOT/path).read_bytes()
 with zipfile.ZipFile(archive) as z:o=z.read(supporting['archive_member'])
 assert hashlib.sha256(b).hexdigest()==supporting['current_sha256']
 assert hashlib.sha256(o).hexdigest()==supporting['original_sha256']
 supporting=dict(supporting,current_bytes=len(b),original_bytes=len(o),
                 current_lines=len(b.decode().splitlines()),original_lines=len(o.decode().splitlines()),
                 archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
 scope={'source_commit':d['source_commit'],'parent_scope':parent.relative_to(ROOT).as_posix(),
        'parent_scope_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'files':rows,
        'supporting_source':supporting,'excluded_parent_paths':sorted(exclude)}
 scopefile.write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
else:scope=json.loads(scopefile.read_text())
lp=Path(str(P)+'_read_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
 if arg=='list':
  for i,r in enumerate(scope['files']):print(i,r['bytes'],r['lines'],r['path'])
  print('SUPPORT',scope['supporting_source']);continue
 if arg=='delta':
  r=scope['supporting_source']
  with zipfile.ZipFile(r['original_archive']) as z:o=z.read(r['archive_member'])
  b=(ROOT/r['path']).read_bytes()
  print(''.join(difflib.unified_diff(o.decode().splitlines(True),b.decode().splitlines(True),fromfile='original',tofile='current')))
  continue
 bits=arg.split(':');key=bits[0]
 if key in ('original','current'):
  r=scope['supporting_source'];path=r['path']
  if key=='original':
   with zipfile.ZipFile(r['original_archive']) as z:b=z.read(r['archive_member'])
  else:b=(ROOT/path).read_bytes()
  sha=r[key+'_sha256']
 else:
  r=scope['files'][int(key)];path=r['path'];b=(ROOT/path).read_bytes();sha=r['sha256']
 assert hashlib.sha256(b).hexdigest()==sha
 lines=b.decode().splitlines();a=int(bits[1]) if len(bits)>1 else 1;z=int(bits[2]) if len(bits)>2 else len(lines)
 assert 1<=a<=z<=len(lines)
 print('\nFILE',key,path,'SHA',sha,'LINES',len(lines),'RANGE',a,z)
 for i in range(a,z+1):print(str(i)+': '+lines[i-1])
 ledger.append({'path':path,'sha256':sha,'version':key if key in ('original','current') else 'frozen_unchanged','reviewed_lines':[[a,z]]})
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
