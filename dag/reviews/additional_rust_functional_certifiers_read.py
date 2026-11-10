"""Freeze pending original owners/tests and emit full source with exact template provenance."""
import hashlib,json,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent
P='additional_rust_functional_certifiers'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scope():
 out=HERE/(P+'_scope.json')
 if out.exists():return json.loads(out.read_text())
 prefixes=('code/rust/core_functional/','code/rust/core_certifiers/','code/rust/tests/core_functional/','code/rust/tests/core_certifiers/')
 c=json.loads((HERE/'coverage.json').read_text());inv=json.loads((ROOT/'dag/file_inventory.json').read_text())
 original={r['path']:r for r in inv['files']}
 prior=set()
 for p in HERE.glob('*.json'):
  try:d=json.loads(p.read_text(encoding='utf-8-sig'))
  except (UnicodeError,ValueError):continue
  if isinstance(d,dict):
   prior.update(r['path']for r in d.get('file_reviews',[])if r.get('full_source_read')is True)
 files=[]
 for r in c['files']:
  p=r['path']
  if not p.startswith(prefixes) or r['substantive_status']=='full_text_source_review_recorded' or p in prior:continue
  raw=(ROOT/p).read_bytes();digest=hashlib.sha256(raw).hexdigest();assert original[p]['sha256']==digest
  files.append({'path':p,'sha256':digest,'bytes':len(raw),'lines':len(raw.decode('utf-8-sig').splitlines()),'coverage_at_freeze':r['substantive_status']})
 d={'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','coverage_sha256':sha(HERE/'coverage.json'),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'files':files}
 out.write_text(json.dumps(d,indent=2)+'\n');return d
def read(path,start=1,end=None):
 rows={r['path']:r for r in scope()['files']};r=rows[path];p=ROOT/path;assert sha(p)==r['sha256']
 lines=p.read_bytes().decode('utf-8-sig').splitlines();end=min(end or len(lines),len(lines))
 print('FILE',path,'SHA256',r['sha256'],'LINES',len(lines),'READ',start,end)
 for i in range(start,end+1):print(f'{i}: {lines[i-1]}')
 ledger=HERE/(P+'_emissions.json');d=json.loads(ledger.read_text())if ledger.exists()else[]
 d.append({'path':path,'sha256':r['sha256'],'emitted_lines':[start,end],'note':'Emission is not semantic assessment.'});ledger.write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':
 if len(sys.argv)==1:
  rows=scope()['files'];print(json.dumps({'files':len(rows),'bytes':sum(r['bytes']for r in rows),'lines':sum(r['lines']for r in rows),'largest':sorted(rows,key=lambda r:r['lines'],reverse=True)[:10]},indent=2))
 else:read(sys.argv[1],int(sys.argv[2])if len(sys.argv)>2 else 1,int(sys.argv[3])if len(sys.argv)>3 else None)
