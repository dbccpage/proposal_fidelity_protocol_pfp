"""Artifact accounting/equality and focused retry; no original mutations."""
import difflib,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_007_support';BASE='papers/pfp/007_pfp_executable_lessons_and_evidence_boundaries/';PKG=ROOT/BASE;OUT=HERE/'paper_007_support_inspection'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads((HERE/(P+s)).read_text(encoding='utf-8'))
def write(s,x):(HERE/(P+s)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def retry():
 env=os.environ.copy();temp=OUT/'temporary';temp.mkdir(exist_ok=True);env.update(TEMP=str(temp),TMP=str(temp),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
 old=load('_probes.json');rows=[]
 for label,cwd,extra in [('current_cpython_retry',PKG,[]),('altered_reference_retry',PKG,['--notebook',str(OUT/'wrong_output.ipynb')]),('archive_cpython_retry',OUT/'archive_fraction_probe',[])]:
  cmd=[sys.executable,'-B','-X','utf8','tools/replay_companion_notebook.py',*extra];r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60);item={'id':label,'command':cmd,'cwd':str(cwd),'temporary_directory':str(temp),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr};rows.append(item);print(json.dumps(item))
 old['followup_replay_commands']=rows;old['initial_replay_failure']='Windows temporary directory access failure before cells; retained, not scored as successful rejection.';write('_probes.json',old)
def equality():
 from PIL import Image
 inv=json.loads((OUT/'pdf_inventory.json').read_text());base=inv[1];result=[]
 for idx,offset in [(2,0),(5,1),(3,7),(4,11)]:
  matches=[]
  for j,p in enumerate(inv[idx]['page_images']):
   with Image.open(ROOT/p) as a,Image.open(ROOT/base['page_images'][offset+j]) as b:matches.append(a.size==b.size and a.tobytes()==b.tobytes())
  assert all(matches)
  result.append({'path':inv[idx]['path'],'sha256':inv[idx]['sha256'],'base_path':base['path'],'base_sha256':base['sha256'],'base_pages':[offset+1,offset+len(matches)],'all_page_pixels_equal':matches})
 write('_pdf_equality.json',result);print(json.dumps({'total_pdf_pages':sum(r['pages'] for r in inv),'unique_pages_visually_reviewed':22,'pixel_transfers':result},indent=2))
def delta_accounting():
 custody=load('_custody.json');result=[]
 with zipfile.ZipFile(ROOT/custody['archive_path']) as z:
  for r in custody['zip_members']:
   if not r['current_exists']:continue
   try:a=z.read(r['member']).decode().replace('\r\n','\n');b=(ROOT/r['current_path']).read_bytes().decode().replace('\r\n','\n')
   except UnicodeDecodeError:continue
   name=r['current_path'].removeprefix(BASE)
   if name in ['MANIFEST.sha256','SHA256SUMS']:
    parse=lambda s:{line.split('  ',1)[1]:line.split('  ',1)[0] for line in s.splitlines() if line}
    before=parse(a);after=parse(b);translated={p.replace('_lev_landau_','_lev_examiner_').replace('_pfp_landau_companion','_pfp_examiner_companion'):h for p,h in before.items()}
    result.append({'path':r['current_path'],'archive_sha256':r['sha256'],'rows':len(before),'all_path_digest_pairs_equal_after_name_mapping':translated==after,'body_review':'parsed all pairs, not raw textual source read'});continue
   if name=='docs/first_publication_validation_2026_10_02.json':
    rules=[('omega_engine_symbol_game','pfp'),('omega_engine_education','education'),('omega_engine_atlas','atlas'),('_lev_landau_','_lev_examiner_')]
    changed=a
    for x,y in rules:changed=changed.replace(x,y)
    # Long historical compilation logs can contain residual split path fragments; record exact residual, no full-read claim.
    delta=''.join(difflib.unified_diff(changed.splitlines(True),b.splitlines(True),fromfile='archive_after_explicit_path_mapping',tofile='current'))
    p=OUT/'publication_receipt_residual_delta.txt';p.write_text(delta,encoding='utf-8')
    result.append({'path':r['current_path'],'archive_sha256':r['sha256'],'explicit_rules':rules,'residual_delta':p.relative_to(ROOT).as_posix(),'residual_lines':len(delta.splitlines()),'body_review':'bounded parsed receipt; long logs not promoted to full source reading'})
 write('_artifact_delta_accounting.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':{'retry':retry,'equality':equality,'deltas':delta_accounting}[sys.argv[1]]()
