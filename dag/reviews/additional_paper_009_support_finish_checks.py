"""Bounded artifact identity, all-row axiom parsing and PDF equality receipts."""
import collections,hashlib,json,re,sys,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_009_support';B=R/'papers/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates';O=H/'paper_009_support_inspection'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(s,x):(H/(P+s)).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def lf(b):return b.decode('utf-8').replace('\r\n','\n').replace('\r','\n').encode()
def bindings():
 c=load(H/(P+'_custody.json'));provenance=load(B/'docs/historical_evidence/provenance.json');out={};rows=[]
 with zipfile.ZipFile(R/c['archive_path']) as z:
  for e in provenance['records']:
   p='docs/historical_evidence/'+e['file'];raw=(B/p).read_bytes();member=next(r['member'] for r in c['zip_members'] if r['current_path']==(B/p).relative_to(R).as_posix());old=z.read(member);rows.append({'path':p,'expected_sha256':e['sha256'],'raw_sha256':sha(raw),'raw_match':sha(raw)==e['sha256'],'lf_match':sha(lf(raw))==e['sha256'],'archive_sha256':sha(old),'archive_match':sha(old)==e['sha256'],'archive_git_blob_match':hashlib.sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest()==e['git_blob_sha1']})
 out['historical_record_bindings']=rows;rows=[]
 for p,expected in load(B/'docs/v01_review_2026_10_02.json')['protected_artifacts_unchanged'].items():
  raw=(B/p).read_bytes();rows.append({'path':p,'expected_sha256':expected,'raw_sha256':sha(raw),'raw_match':sha(raw)==expected,'lf_match':sha(lf(raw))==expected})
 out['protected_artifact_bindings']=rows
 raw=(B/'lean4/full_axiom_report.txt').read_bytes();decl=[];headers=[]
 for n,line in enumerate(raw.decode().splitlines(),1):
  m=re.fullmatch(r"'(.*)' depends on axioms: \[(.*)\]",line)
  if m:decl.append({'line':n,'name':m[1],'axioms':m[2].split(', ') if m[2] else []})
  else:
   m=re.fullmatch(r"'(.*)' does not depend on any axioms",line)
   if m:decl.append({'line':n,'name':m[1],'axioms':[]})
   elif line.strip():headers.append({'line':n,'text':line})
 assert len(decl)==516 and len({x['name'] for x in decl})==516 and all(set(x['axioms'])<={'propext','Quot.sound','Classical.choice'} for x in decl)
 out['full_axiom_listing']={'sha256':sha(raw),'declarations':516,'headers':headers,'axiom_sets':dict(collections.Counter(', '.join(r['axioms']) or '(none)' for r in decl)),'rows':decl,'limit':'Every row parsed and checked; not a full manual raw-text reading or fresh kernel execution.'}
 out['renderer_header_check']={'author_line':[x for x in (B/'paper.md').read_text().splitlines()[:12] if 'Carroll' in x],'required_prefix':'Bare Metal Anchor','matches':any(x.startswith('Bare Metal Anchor') for x in (B/'paper.md').read_text().split('</div>',1)[0].splitlines())}
 save('_binding_checks.json',out);print(json.dumps({'records':out['historical_record_bindings'],'protected':{'rows':len(rows),'raw_matches':sum(x['raw_match'] for x in rows),'raw_or_lf':sum(x['raw_match'] or x['lf_match'] for x in rows)},'axioms':out['full_axiom_listing']['axiom_sets'],'renderer':out['renderer_header_check']},indent=2))
def pdfs():
 from PIL import Image
 inv=load(O/'pdf_inventory.json');pixels={};result=[]
 for i in (0,1):
  for n,p in enumerate(inv[i]['page_images'],1):
   with Image.open(R/p) as im:pixels[(im.size,sha(im.convert('RGB').tobytes()))]=(i,n)
 for i,row in enumerate(inv):
  q={'path':row['path'],'sha256':row['sha256'],'pages':row['pages'],'full_source_read':False}
  if i in (0,1):q.update(method='All pages directly visually reviewed on six complete contact sheets.',direct_visual_pages=list(range(1,row['pages']+1)),sheets=row['sheets'])
  elif i==6:
   assert (R/row['path']).read_bytes()==(R/inv[0]['path']).read_bytes();q.update(method='Exact raw PDF byte equality transfers ten directly observed manuscript pages.',base_path=inv[0]['path'])
  else:
   matches=[]
   for n,p in enumerate(row['page_images'],1):
    with Image.open(R/p) as im:k=(im.size,sha(im.convert('RGB').tobytes()))
    assert k in pixels,(i,n);j,page=pixels[k];matches.append({'page':n,'base_path':inv[j]['path'],'base_page':page,'rgb_sha256':k[1],'size':list(k[0])})
   q.update(method='Complete rendered RGB equality transfers already observed companion pages.',pixel_equality=matches)
  result.append(q)
 save('_pdf_review.json',{'pdfs':result,'total_pages':40,'direct_visual_pages':20,'raw_equal_pages':10,'pixel_equal_pages':10,'observations':['All manuscript equations, confusion table, gate-probe tables and final scope visible; no material clipping observed at review resolution.','Combined companion pages5-7 contain instructor key before quiz pages8-10, contradicting attempt-before-key instruction.','Historical PDF roles/paths and Oct2edition differ from renamed current prose and Oct23Markdown extension.'],'limit':'Complete page review/equality transfers; not binary PDF source reading, external link verification or validated pedagogy.'});print(json.dumps({'pages':40,'direct':20,'raw_equal':10,'pixel_equal':10}))
if __name__=='__main__':{'bindings':bindings,'pdfs':pdfs}[sys.argv[1]]()
