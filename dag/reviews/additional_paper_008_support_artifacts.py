"""Readonly original custody; output only this audit's inspection artifacts."""
import difflib,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_008_support';NAME='008_pfp_mssn_tower_challenges_and_retraction_benchmarks';BASE='papers/pfp/'+NAME+'/';PKG=ROOT/BASE;OUT=HERE/'paper_008_support_inspection';OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(s,x):(HERE/(P+s)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def lf(b):return b.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
def rename(p):return p.replace('_lev_landau_','_lev_examiner_').replace('_pfp_landau_companion','_pfp_examiner_companion')
def pairs(raw):
 out={}
 for line in lf(raw).splitlines():
  if not line or line.startswith('#'):continue
  h,p=line.split('  ',1);q=PurePosixPath(p);assert len(h)==64 and p not in out and not q.is_absolute() and '..' not in q.parts;out[p]=h
 return out
def custody():
 result={'current_manifests':[],'zip_members':[],'zip_manifests':[]}
 for name in ['MANIFEST.sha256','SHA256SUMS']:
  entries=[]
  for p,h in pairs((PKG/name).read_bytes()).items():
   f=PKG/p;assert f.resolve().is_relative_to(PKG.resolve());r={'path':p,'expected_sha256':h,'exists':f.is_file()}
   if f.is_file():
    b=f.read_bytes();r.update(actual_sha256=sha(b),raw_match=sha(b)==h)
    try:r['lf_match']=sha(lf(b).encode())==h
    except UnicodeDecodeError:r['lf_match']=None
   entries.append(r)
  result['current_manifests'].append({'path':name,'entries':entries})
 archive=next(PKG.glob('*.zip'));result['archive_path']=archive.relative_to(ROOT).as_posix();result['archive_sha256']=sha(archive.read_bytes())
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;assert len(z.namelist())==len(set(x.casefold() for x in z.namelist()));roots={PurePosixPath(x).parts[0] for x in z.namelist()};assert len(roots)==1;root=next(iter(roots));result['archive_root']=root
  for i,info in enumerate(z.infolist()):
   p=PurePosixPath(info.filename);assert not p.is_absolute() and '..' not in p.parts and not info.is_dir();rel=PurePosixPath(*p.parts[1:]).as_posix();raw=z.read(info);now=PKG/rename(rel)
   r={'member':info.filename,'sha256':sha(raw),'bytes':len(raw),'current_path':now.relative_to(ROOT).as_posix(),'current_exists':now.is_file()}
   if now.is_file():
    b=now.read_bytes();r.update(current_sha256=sha(b),current_raw_equal=raw==b)
    try:
     a,c=lf(raw),lf(b);r['current_lf_equal']=a==c
     if a!=c:
      delta=''.join(difflib.unified_diff(a.splitlines(True),c.splitlines(True),fromfile='archive/'+rel,tofile='current/'+rename(rel)));dp=OUT/f'zip_delta_{i:02d}.txt';dp.write_text(delta,encoding='utf-8');r.update(complete_diff_path=dp.relative_to(ROOT).as_posix(),complete_diff_lines=len(delta.splitlines()),complete_diff_sha256=sha(dp.read_bytes()))
    except UnicodeDecodeError:r['current_lf_equal']=None
   result['zip_members'].append(r)
  for name in ['MANIFEST.sha256','SHA256SUMS']:
   m=pairs(z.read(root+'/'+name));result['zip_manifests'].append({'path':name,'entries':len(m),'missing':[p for p in m if root+'/'+p not in z.namelist()],'mismatches':[p for p,h in m.items() if root+'/'+p in z.namelist() and sha(z.read(root+'/'+p))!=h]})
 write('_custody.json',result)
 print(json.dumps({'zip_members':len(result['zip_members']),'deltas':[{'path':r['complete_diff_path'],'lines':r['complete_diff_lines']} for r in result['zip_members'] if 'complete_diff_path' in r],'zip_manifests':result['zip_manifests'],'current_manifest_counts':[{'name':r['path'],'rows':len(r['entries']),'raw_failures':sum(not x.get('raw_match') for x in r['entries']),'unresolved_after_lf':sum(not(x.get('raw_match') or x.get('lf_match')) for x in r['entries'])} for r in result['current_manifests']]},indent=2))
def pdfs():
 spec=importlib.util.spec_from_file_location(P+'_pdf_shared_helper',HERE/'additional_paper_004_artifacts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.PREFIX=P;m.NAME=NAME;m.PACKAGE=PKG;m.OUT=OUT;m.pdfs()
def data():
 name='docs/first_publication_validation_2026_10_02.json';raw=(PKG/name).read_bytes();obj=json.loads(raw)
 omitted=[]
 def bounded(v,path=''):
  if isinstance(v,dict):return {k:bounded(w,path+'/'+k) for k,w in v.items()}
  if isinstance(v,list):return [bounded(w,path+'/'+str(i)) for i,w in enumerate(v)]
  if isinstance(v,str) and len(v)>1600:
   omitted.append({'pointer':path,'characters':len(v),'sha256_utf8':sha(v.encode())});return {'bounded_log_string':True,'characters':len(v),'first800':v[:800],'last400':v[-400:]}
  return v
 result={'path':BASE+name,'sha256':sha(raw),'parsed_summary':bounded(obj),'omitted_long_string_bodies':omitted,'limit':'Every JSON structural/short scalar field inspected; long command output strings bounded by head/tail and counts, not full body or new execution.'}
 write('_historical_receipt_summary.json',result);print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':{'custody':custody,'pdfs':pdfs,'data':data}[sys.argv[1]]()
