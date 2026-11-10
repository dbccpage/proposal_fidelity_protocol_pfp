"""Bounded Paper006 archive/data custody and PDF render aids; no original writes."""
import difflib,hashlib,importlib.util,json,sys,zipfile
from collections import Counter
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_006_support';NAME='006_pfp_epistemic_immune_system_and_cemetery_dag_mining';BASE='papers/pfp/'+NAME+'/';PKG=ROOT/BASE;OUT=HERE/(P+'_inspection');OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(s,x):(HERE/(P+s)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def lf(b):return b.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
def rename(p):return p.replace('_lev_landau_','_lev_examiner_').replace('_pfp_landau_companion','_pfp_examiner_companion').replace('code/landau_worksheet.py','code/examiner_worksheet.py')
def pairs(raw):
 out={}
 for l in lf(raw).splitlines():
  if not l or l.startswith('#'):continue
  h,p=l.split('  ',1);q=PurePosixPath(p);assert len(h)==64 and p not in out and not q.is_absolute() and '..' not in q.parts;out[p]=h
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
  current=(PKG/'code/fixtures/pharmacy_catalog_52cb5457f6c4.json').read_bytes();historical=z.read(root+'/code/fixtures/pharmacy_catalog_52cb5457f6c4.json');result['catalog_comparison']={'current_sha256':sha(current),'historical_sha256':sha(historical),'current_crlf_to_lf_sha256':sha(lf(current).encode()),'historical_lf_sha256':sha(lf(historical).encode())}
 write('_custody.json',result)
 print(json.dumps({'zip':len(result['zip_members']),'root':root,'missing_current':[r['member'] for r in result['zip_members'] if not r['current_exists']],'deltas':[{'path':r['complete_diff_path'],'lines':r['complete_diff_lines']} for r in result['zip_members'] if 'complete_diff_path' in r],'zip_manifests':result['zip_manifests'],'current_manifest_counts':[{'name':r['path'],'rows':len(r['entries']),'raw_failures':sum(not x.get('raw_match') for x in r['entries']),'unresolved_after_lf':sum(not(x.get('raw_match') or x.get('lf_match')) for x in r['entries'])} for r in result['current_manifests']],'catalog_comparison':result['catalog_comparison']},indent=2))
def pdfs():
 spec=importlib.util.spec_from_file_location(P+'_pdf_shared_helper',HERE/'additional_paper_004_artifacts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.PREFIX=P;m.NAME=NAME;m.PACKAGE=PKG;m.OUT=OUT;m.pdfs()
def data():
 path=PKG/'code/fixtures/pharmacy_catalog_52cb5457f6c4.json';raw=path.read_bytes();obj=json.loads(raw);records=list(obj['antibodies'].values());place=lambda r:r['negative_fixture']==f"# Triggering defect: {r['target_pattern']}\n" and r['positive_fixture']=='# Repaired exact state\n'
 result={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(raw),'top_level_other_fields':{k:v for k,v in obj.items() if k!='antibodies'},'rows':len(records),'schemas':[[list(k),v] for k,v in Counter(tuple(sorted(r)) for r in records).items()],'statuses':dict(Counter(r['pharmacy_status'] for r in records)),'classes':dict(Counter(r['failure_class'] for r in records)),'placeholder_count':sum(place(r) for r in records),'field_value_sets':{k:list(dict.fromkeys(json.dumps(r[k],sort_keys=True,ensure_ascii=False) for r in records)) for k in records[0] if k not in ['evidence_sha256','created_at','last_seen','antibody_id']},'nonplaceholder_rows':[r for r in records if not place(r)],'limit':'All parsed rows/schema/field values and exact arithmetic reviewed; no full raw-JSON textual read or detector execution claimed.'}
 write('_catalog.json',result);print(json.dumps(result,indent=2,ensure_ascii=False))
def equality():
 from PIL import Image
 inv=json.loads((OUT/'pdf_inventory.json').read_text(encoding='utf-8'));base=inv[1];result=[]
 for idx,offset in [(2,0),(5,1),(3,5),(4,11)]:
  matches=[]
  for j,p in enumerate(inv[idx]['page_images']):
   with Image.open(ROOT/p) as a,Image.open(ROOT/base['page_images'][offset+j]) as b:matches.append(a.size==b.size and a.tobytes()==b.tobytes())
  assert all(matches)
  result.append({'path':inv[idx]['path'],'sha256':inv[idx]['sha256'],'base_path':base['path'],'base_sha256':base['sha256'],'base_pages':[offset+1,offset+len(matches)],'all_page_pixels_equal':matches})
 write('_pdf_equality.json',result);print(json.dumps(result,indent=2))
def deltas():
 archive=next(PKG.glob('*.zip'));results=[]
 with zipfile.ZipFile(archive) as z:
  root=z.namelist()[0].split('/')[0]
  for name in ['MANIFEST.sha256','SHA256SUMS']:
   before=pairs(z.read(root+'/'+name));after=pairs((PKG/name).read_bytes());translated={rename(k):v for k,v in before.items()}
   results.append({'path':BASE+name,'sha256':sha((PKG/name).read_bytes()),'historical_records':len(before),'current_records':len(after),'same_path_set_after_explicit_rename':set(translated)==set(after),'changed_digest_paths':[k for k,v in translated.items() if after.get(k)!=v],'all_records_compared':True})
 write('_manifest_deltas.json',results);print(json.dumps(results,indent=2))
if __name__=='__main__':{'custody':custody,'pdfs':pdfs,'data':data,'equality':equality,'deltas':deltas}[sys.argv[1]]()
